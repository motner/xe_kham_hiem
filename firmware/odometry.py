"""Vi tri xe tu encoder va duong da di.

Toa do (met): goc 0 la huong xe luc dat lai, goc duong la quay phai.
Sai so cong don khi banh truot: day la uoc luong, khong phai vi tri that.
"""
import math


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def distance(ax, ay, bx, by):
    # MicroPython tren ESP32 khong co math.hypot.
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


class Odometry:
    def __init__(self, track_m, trail_spacing_m=0.05, trail_size=16):
        if track_m <= 0:
            raise ValueError('track_m')
        self.track_m = track_m
        self.trail_spacing_m = trail_spacing_m
        self.trail_size = trail_size
        self.epoch = 0
        self.trail_seq = 0
        self.reset()

    def reset(self):
        self.epoch += 1
        self.x = self.y = self.th = self.length = 0.0
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
            self.trail.append((self.trail_seq, round(self.x, 3), round(self.y, 3)))
            if len(self.trail) > self.trail_size:
                self.trail.pop(0)

    def status(self):
        return {'x': round(self.x, 3), 'y': round(self.y, 3), 'th': round(self.th, 4),
                'length_m': round(self.length, 3), 'epoch': self.epoch}
