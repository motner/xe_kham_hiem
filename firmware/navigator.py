"""Tu quay ve diem xuat phat theo duong da di, tranh vat can bang HC-SR04.

Moi chu ky update(dt) tra ve (rpm_trai, rpm_phai). Khi xong, active = False va
result cho biet ly do: return_home, return_blocked, return_timeout.

Trinh tu: xoay ve diem da luu -> dung on dinh -> chay toi -> lay diem tiep theo.
Gap vat can: dung -> quet -> chon goc trong -> xoay -> chay vong qua -> tinh lai huong.
Khong co cho trong thi xoay tai cho 90 do roi quet tiep (khong lui vi khong co cam bien
phia sau); qua so lan cho phep thi dung han.
"""
import math
from odometry import distance, wrap_angle

IDLE = 'idle'
TURN = 'turn'
DRIVE = 'drive'
SETTLE = 'settle'
AVOID_SCAN = 'avoid_scan'
AVOID_TURN = 'avoid_turn'
AVOID_DRIVE = 'avoid_drive'
AVOID_ROTATE = 'avoid_rotate'


class ReturnNavigator:
    def __init__(self, cfg, odometry, scanner=None):
        self.cfg = cfg
        self.odo = odometry
        self.scanner = scanner
        self.state = IDLE
        self.result = None
        self.elapsed = 0.0
        self.avoid_count = 0
        self._next = IDLE
        self._timer = 0.0
        self._heading = 0.0
        self._mark = 0.0
        self._seen_sweep = 0
        self._side = 0
        self._rate = 0.0
        self._last_th = odometry.th

    @property
    def active(self):
        return self.state != IDLE

    def start(self):
        self.result = None
        self.elapsed = 0.0
        self.avoid_count = 0
        self._side = 0
        self._rate = 0.0
        self._last_th = self.odo.th
        self.state = TURN

    def cancel(self):
        self.state = IDLE

    def _finish(self, result):
        self.result = result
        self.state = IDLE
        return 0.0, 0.0

    def _settle(self, next_state):
        self.state = SETTLE
        self._next = next_state
        self._timer = self.cfg.RETURN_SETTLE_MS / 1000
        return 0.0, 0.0

    def _goal(self):
        """Bo cac diem da toi; luon giu diem [0] la diem xuat phat."""
        route, odo = self.odo.route, self.odo
        while len(route) > 1 and distance(route[-1][0], route[-1][1], odo.x, odo.y) < self.cfg.RETURN_WAYPOINT_M:
            route.pop()
        goal = route[-1]
        return goal, distance(goal[0], goal[1], odo.x, odo.y)

    def _bearing_error(self, goal):
        return wrap_angle(math.atan2(goal[0] - self.odo.x, goal[1] - self.odo.y) - self.odo.th)

    def _pivot(self, error):
        rpm = self.cfg.RETURN_TURN_RPM if error > 0 else -self.cfg.RETURN_TURN_RPM
        return rpm, -rpm

    def _turn(self, error, done_state):
        """Xoay ve error (radian). Motor con troi sau khi ngat nen phai ngat som theo toc do xoay."""
        tolerance = math.radians(self.cfg.RETURN_TURN_TOLERANCE_DEG)
        if abs(error) < tolerance and abs(self._rate) < .3:
            return self._settle(done_state)
        predicted = error - self._rate * self.cfg.RETURN_TURN_COAST_S
        if abs(predicted) < tolerance or predicted * error < 0:
            # Cho xe dung han roi do lai; con lech thi xoay them mot nhip.
            return self._settle(self.state)
        return self._pivot(error)

    def _hold_heading(self, error):
        # Cac banh khong hoan toan bang nhau: khong sua huong thi xe tu cua dan.
        cfg = self.cfg
        steer = max(-cfg.RETURN_STEER_RPM, min(cfg.RETURN_STEER_RPM, error * cfg.RETURN_STEER_GAIN))
        return cfg.RETURN_DRIVE_RPM + steer, cfg.RETURN_DRIVE_RPM - steer

    def _front_blocked(self):
        s = self.scanner
        return s is not None and s.front_cm is not None and s.front_cm < self.cfg.RETURN_STOP_CM

    def _begin_avoid(self):
        self.avoid_count += 1
        if self.avoid_count > self.cfg.RETURN_MAX_AVOID:
            return self._finish('return_blocked')
        self._drop_blocked_route()
        return self._settle(AVOID_SCAN)

    def _drop_blocked_route(self):
        # Vat can nam tren duong cu: bo cac diem qua sat no, tru diem xuat phat.
        odo, reach = self.odo, self.scanner.front_cm / 100 + self.cfg.SCANNER_OFFSET_M
        ox = odo.x + reach * math.sin(odo.th)
        oy = odo.y + reach * math.cos(odo.th)
        radius = self.cfg.RETURN_OBSTACLE_RADIUS_M
        odo.route.keep(lambda x, y: distance(x, y, ox, oy) > radius)

    def _choose_opening(self):
        """Chon goc quet co du cho, uu tien gan huong ve va giu nguyen ben da chon."""
        cfg, odo = self.cfg, self.odo
        goal, _ = self._goal()
        goal_error = self._bearing_error(goal)
        best, best_score = None, None
        for angle, cm in self.scanner.last_sweep.items():
            if angle == 0:
                continue
            room = cfg.SCAN_MAX_CM if cm is None else cm
            if room < cfg.RETURN_CLEAR_CM:
                continue
            score = room + 40 * math.cos(math.radians(angle) - goal_error)
            if self._side and (angle > 0) == (self._side > 0):
                score += 60
            if best_score is None or score > best_score:
                best, best_score = angle, score
        return best

    def update(self, dt):
        if not self.active:
            return 0.0, 0.0
        self.elapsed += dt
        # Encoder cap nhat moi 100 ms, nhip nay co khi chua co so moi: phai loc toc do xoay.
        if dt > 0:
            raw = wrap_angle(self.odo.th - self._last_th) / dt
            self._rate += (raw - self._rate) * min(1, dt / .2)
        self._last_th = self.odo.th
        if self.elapsed > self.cfg.RETURN_TIMEOUT_S:
            return self._finish('return_timeout')
        scanner = self.scanner
        if scanner:
            scanner.defer = self.state in (TURN, AVOID_TURN, AVOID_ROTATE, SETTLE)
        # Dang quet thi dung lai, vi luc do cam bien khong nhin phia truoc.
        if scanner and scanner.sweeping and self.state != AVOID_SCAN:
            return 0.0, 0.0
        state, cfg, odo = self.state, self.cfg, self.odo
        if state == SETTLE:
            self._timer -= dt
            if self._timer > 0:
                return 0.0, 0.0
            self.state = self._next
            if self.state == AVOID_SCAN:
                self._seen_sweep = scanner.sweep_id
                scanner.request_sweep()
            elif self.state == AVOID_DRIVE:
                self._mark = odo.length
            return 0.0, 0.0
        if state == TURN:
            goal, dist = self._goal()
            if len(odo.route) == 1 and dist < cfg.RETURN_HOME_M:
                return self._finish('return_home')
            return self._turn(self._bearing_error(goal), DRIVE)
        if state == DRIVE:
            goal, dist = self._goal()
            if len(odo.route) == 1 and dist < cfg.RETURN_HOME_M:
                return self._finish('return_home')
            if self._front_blocked():
                return self._begin_avoid()
            error = self._bearing_error(goal)
            if abs(error) > math.radians(cfg.RETURN_REALIGN_DEG):
                return self._settle(TURN)
            return self._hold_heading(error)
        if state == AVOID_SCAN:
            if scanner.sweep_id == self._seen_sweep:
                return 0.0, 0.0
            angle = self._choose_opening()
            if angle is None:
                # Phia truoc deu chan: xoay tai cho de cam bien nhin sang huong khac.
                self.avoid_count += 1
                if self.avoid_count > cfg.RETURN_MAX_AVOID:
                    return self._finish('return_blocked')
                self._side = self._side or 1
                self._heading = wrap_angle(odo.th + math.radians(90 * self._side))
                self.state = AVOID_ROTATE
                return 0.0, 0.0
            self._side = 1 if angle > 0 else -1
            self._heading = wrap_angle(odo.th + math.radians(angle))
            self.state = AVOID_TURN
            return 0.0, 0.0
        if state == AVOID_TURN:
            return self._turn(wrap_angle(self._heading - odo.th), AVOID_DRIVE)
        if state == AVOID_DRIVE:
            if self._front_blocked():
                return self._begin_avoid()
            if odo.length - self._mark >= cfg.RETURN_AVOID_M:
                return self._settle(TURN)
            return self._hold_heading(wrap_angle(self._heading - odo.th))
        if state == AVOID_ROTATE:
            return self._turn(wrap_angle(self._heading - odo.th), AVOID_SCAN)
        return self._finish('return_error')

    def status(self):
        return {'active': self.active, 'state': self.state, 'result': self.result,
                'avoid': self.avoid_count, 'elapsed_s': round(self.elapsed, 1)}
