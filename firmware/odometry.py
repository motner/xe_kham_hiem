"""Vi tri xe tu encoder va duong da di.

Toa do (met): goc 0 la huong xe luc dat lai, goc duong la quay phai.
Sai so cong don khi banh truot: day la uoc luong, khong phai vi tri that.
"""
import math
from array import array


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def distance(ax, ay, bx, by):
    # MicroPython tren ESP32 khong co math.hypot.
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


class Route:
    """Lo trinh trong mang so cap san luc khoi dong: xe di xa khong cap phat them.

    Danh sach tuple se lam heap Python phai no ra giua luc chay, lay het RAM cua Wi-Fi.
    """

    def __init__(self, limit):
        self.data = array('f', bytes(8 * (limit + 2)))
        self.size = 0

    def __len__(self):
        return self.size

    def __getitem__(self, index):
        if index < 0:
            index += self.size
        if not 0 <= index < self.size:
            raise IndexError(index)
        return self.data[2 * index], self.data[2 * index + 1]

    def append(self, point):
        self.data[2 * self.size] = point[0]
        self.data[2 * self.size + 1] = point[1]
        self.size += 1

    def pop(self):
        self.size -= 1

    def clear(self):
        self.size = 0

    def keep(self, wanted):
        """Giu diem [0] va cac diem wanted(x, y) tra ve True."""
        data, used = self.data, min(self.size, 1)
        for index in range(1, self.size):
            x, y = data[2 * index], data[2 * index + 1]
            if wanted(x, y):
                data[2 * used], data[2 * used + 1] = x, y
                used += 1
        self.size = used

    def thin(self):
        """Bo xen ke, giu diem xuat phat va diem moi nhat."""
        data, last, used = self.data, self.size - 1, 0
        for index in range(0, self.size, 2):
            data[2 * used], data[2 * used + 1] = data[2 * index], data[2 * index + 1]
            used += 1
        if last % 2:
            data[2 * used], data[2 * used + 1] = data[2 * last], data[2 * last + 1]
            used += 1
        self.size = used


class Odometry:
    def __init__(self, track_m, route_spacing_m=0.10, route_limit=300,
                 trail_spacing_m=0.05, trail_size=16):
        if track_m <= 0:
            raise ValueError('track_m')
        self.track_m = track_m
        self.route_spacing_m = route_spacing_m
        self.route_limit = route_limit
        self.trail_spacing_m = trail_spacing_m
        self.trail_size = trail_size
        self.epoch = 0
        self.trail_seq = 0
        self.recording = True
        self.route = Route(route_limit)
        self.reset()

    def reset(self):
        self.epoch += 1
        self.x = self.y = self.th = self.length = 0.0
        # route: diem [0] luon la diem xuat phat; Navigator lay dan tu cuoi ve.
        self.route.clear()
        self.route.append((0.0, 0.0))
        # trail: vai diem moi nhat cho web ve duong, kieu (seq, x, y, kind). kind 1 = dang quay ve.
        self.trail = []
        self.trail_x = self.trail_y = 0.0

    def update(self, left_m, right_m):
        """left_m, right_m: quang duong moi ben vua di (co dau)."""
        d = (left_m + right_m) / 2
        dth = (left_m - right_m) / self.track_m
        mid = self.th + dth / 2
        self.x += d * math.sin(mid)
        self.y += d * math.cos(mid)
        self.length += abs(d)
        self.th = wrap_angle(self.th + dth)
        self._record()

    def _record(self):
        if distance(self.x, self.y, self.trail_x, self.trail_y) >= self.trail_spacing_m:
            self.trail_x, self.trail_y = self.x, self.y
            self.trail_seq += 1
            self.trail.append((self.trail_seq, round(self.x, 3), round(self.y, 3), 0 if self.recording else 1))
            if len(self.trail) > self.trail_size:
                self.trail.pop(0)
        if not self.recording:
            return
        last = self.route[-1]
        if distance(self.x, self.y, last[0], last[1]) >= self.route_spacing_m:
            self.route.append((self.x, self.y))
            if len(self.route) > self.route_limit:
                self.route.thin()

    def status(self):
        return {'x': round(self.x, 3), 'y': round(self.y, 3), 'th': round(self.th, 4),
                'length_m': round(self.length, 3), 'route': len(self.route), 'epoch': self.epoch}
