"""SG90 xoay HC-SR04: quet nhieu goc moi SCAN_PERIOD_MS, giua cac lan quet thi nhin thang.

Scanner chi la logic, phan cung truyen vao qua set_angle(do) va ping() -> cm hoac None,
nen test duoc tren may tinh. Goc duong la ben phai. update() chay trong vong PID:
moi lan ping khong qua vai chuc ms vi co timeout theo tam do toi da.
"""
import math

_PING_LIMIT_S = 0.06  # HC-SR04 can nghi khoang 60 ms giua hai lan do.


class Scanner:
    def __init__(self, cfg, set_angle, ping, close=None):
        self.set_angle = set_angle
        self.ping = ping
        self._close = close
        self.period = cfg.SCAN_PERIOD_MS / 1000
        self.angles = tuple(cfg.SCAN_ANGLES)
        self.settle = cfg.SCAN_SETTLE_MS / 1000
        self.guard_period = max(cfg.GUARD_PERIOD_MS / 1000, _PING_LIMIT_S)
        self.max_cm = cfg.SCAN_MAX_CM
        self.offset_m = cfg.SCANNER_OFFSET_M
        self.sweeping = False
        self.sweep_id = 0
        self.points = []
        self.point_seq = 0
        self.front_cm = None
        self.seen_echo = False
        self._index = 0
        self._wait = self.settle
        self._since_sweep = 0.0
        self._since_ping = self.guard_period
        self._since_point = 1.0
        self.set_angle(0)

    def _measure(self):
        value = self.ping()
        if value is None or not 2 <= value <= self.max_cm:
            return None
        self.seen_echo = True
        return value

    def _add_point(self, pose, angle, cm):
        if pose is None or cm is None:
            return
        a = pose.th + math.radians(angle)
        # Cam bien lap truoc tam xe; goc servo tinh tu cam bien.
        sx = pose.x + self.offset_m * math.sin(pose.th)
        sy = pose.y + self.offset_m * math.cos(pose.th)
        self.point_seq += 1
        self.points.append((self.point_seq, round(sx + cm / 100 * math.sin(a), 3),
                            round(sy + cm / 100 * math.cos(a), 3)))
        # Trang web lay 1 lan/giay va bo diem da co: 12 diem du cho vai giay mat ket noi.
        if len(self.points) > 12:
            self.points.pop(0)

    def _begin_sweep(self):
        self.sweeping = True
        self._since_sweep = 0.0
        self._index = 0
        self.front_cm = None
        self.set_angle(self.angles[0])
        self._wait = self.settle

    def _update_sweep(self, dt, pose):
        self._wait -= dt
        if self._wait > 0:
            return
        if self._index >= len(self.angles):
            # Servo da ve giua va on dinh: tro lai canh phia truoc.
            self.sweeping = False
            self.sweep_id += 1
            self._since_ping = self.guard_period
            return
        angle = self.angles[self._index]
        cm = self._measure()
        self._add_point(pose, angle, cm)
        self._index += 1
        if self._index < len(self.angles):
            self.set_angle(self.angles[self._index])
        else:
            self.set_angle(0)
        self._wait = self.settle

    def update(self, dt, pose=None):
        self._since_sweep += dt
        self._since_point += dt
        if self.sweeping:
            self._update_sweep(dt, pose)
            return
        if self._since_sweep >= self.period:
            self._begin_sweep()
            return
        self._since_ping += dt
        if self._wait > 0:
            self._wait -= dt
            return
        if self._since_ping < self.guard_period:
            return
        self._since_ping = 0.0
        cm = self._measure()
        self.front_cm = cm
        if cm is not None and self._since_point >= 0.3:
            self._since_point = 0.0
            self._add_point(pose, 0, cm)

    def status(self):
        return {'sweep_id': self.sweep_id, 'seen_echo': self.seen_echo,
                'front_cm': None if self.front_cm is None else round(self.front_cm, 1),
                'points': self.points}

    def close(self):
        if self._close:
            self._close()


def make_scanner(cfg):
    """Tao Scanner voi SG90 + HC-SR04 that. Chan Echo phai duoc chia ap xuong 3,3 V."""
    import time
    from machine import PWM, Pin, time_pulse_us
    servo = PWM(Pin(cfg.SERVO_PIN), freq=50, duty_u16=0)
    trigger = Pin(cfg.ULTRASONIC_TRIGGER_PIN, Pin.OUT, value=0)
    echo = Pin(cfg.ULTRASONIC_ECHO_PIN, Pin.IN)
    timeout_us = int(cfg.SCAN_MAX_CM * 58.3)
    sign = -1 if cfg.SERVO_INVERTED else 1

    def set_angle(angle):
        us = cfg.SERVO_CENTER_US + sign * angle * cfg.SERVO_US_PER_DEG
        us = max(500, min(2500, us))
        servo.duty_u16(int(us * 65535 / 20000))

    def ping():
        trigger.value(0)
        time.sleep_us(2)
        trigger.value(1)
        time.sleep_us(10)
        trigger.value(0)
        duration = time_pulse_us(echo, 1, timeout_us)
        return None if duration < 0 else duration / 58.3

    def close():
        servo.deinit()
        trigger.value(0)

    return Scanner(cfg, set_angle, ping, close)
