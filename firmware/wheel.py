"""Mot banh = Motor + Encoder + PID toc do. Encoder 1 kenh do do lon RPM."""
from pid import PID


class Wheel:
    def __init__(self, name, motor, encoder, settings, cfg):
        self.name, self.motor, self.encoder = name, motor, encoder
        self.diameter_mm = settings['diameter_mm']
        self.pid = PID(*settings['pid'], limit=cfg.MAX_DUTY)
        self.accel = cfg.ACCEL_RPM_PER_SECOND
        self.reverse_wait = cfg.REVERSE_WAIT_MS / 1000
        self.reverse_rpm = cfg.REVERSE_SAFE_RPM
        self.stall_seconds = cfg.STALL_TIMEOUT_MS / 1000
        self.stall_duty = cfg.STALL_MIN_DUTY
        self.breakaway_duty = min(getattr(cfg, 'BREAKAWAY_DUTY', 0.0), cfg.MAX_DUTY)
        self.breakaway_delay = getattr(cfg, 'BREAKAWAY_DELAY_MS', 300) / 1000
        self.breakaway_ramp = getattr(cfg, 'BREAKAWAY_RAMP_PER_S', 0.0)
        self.limit_duty = cfg.MAX_DUTY
        self.still_elapsed = 0.0
        self.requested = 0.0
        self.target = 0.0
        self.direction = 0
        self.reverse_elapsed = 0.0
        self.stall_elapsed = 0.0
        self.fault = None
        # Encoder 1 kenh khong biet chieu: vi tri co dau tinh theo chieu da lenh gan nhat.
        self.position_pulses = 0
        self.counted_pulses = 0

    def set_target_rpm(self, rpm):
        self.requested = rpm

    def stop(self):
        self.requested = 0.0
        self.target = 0.0
        self.stall_elapsed = 0.0
        self.still_elapsed = 0.0
        self.reverse_elapsed = 0.0
        self.pid.reset()
        self.motor.stop()
        # Giu direction cu de chan dao chieu khi banh van con quan tinh.

    def update(self, dt):
        sampled = self.encoder.sample(dt)
        pulses = self.encoder.pulses
        if pulses != self.counted_pulses:
            # Ke ca xung quan tinh sau khi dung: direction giu chieu cu (xem stop()).
            self.position_pulses += (pulses - self.counted_pulses) * (self.direction or 1)
            self.counted_pulses = pulses
        if self.fault or self.requested == 0:
            self.stop()
            return
        desired_direction = 1 if self.requested > 0 else -1
        if self.direction and desired_direction != self.direction:
            self.motor.stop()
            self.target = 0
            self.pid.reset()
            self.reverse_elapsed += dt
            self.stall_elapsed = self.still_elapsed = 0.0
            if self.reverse_elapsed < self.reverse_wait or abs(self.encoder.rpm) > self.reverse_rpm:
                return
        self.direction = desired_direction
        self.reverse_elapsed = 0
        step = self.accel * dt
        magnitude = abs(self.target)
        magnitude += max(-step, min(step, abs(self.requested) - magnitude))
        self.target = desired_direction * magnitude
        duty = self.pid.update(magnitude, abs(self.encoder.rpm), dt)
        # Muc tieu RPM thap (re nhe): PID tich phan cham hon luc ma sat tinh, nen bi
        # bao stall gia truoc khi banh nhuc nhich. Banh dung yen thi cap duty khoi dong.
        if magnitude > 0 and abs(self.encoder.rpm) < 1:
            self.still_elapsed += dt
            if self.still_elapsed >= self.breakaway_delay:
                push = self.breakaway_duty + (self.still_elapsed - self.breakaway_delay) * self.breakaway_ramp
                duty = max(duty, min(push, self.limit_duty))
        else:
            self.still_elapsed = 0.0
        self.motor.set_output(desired_direction * duty)
        if duty >= self.stall_duty:
            self.stall_elapsed += dt
            if sampled and self.encoder.no_pulse_seconds == 0:
                self.stall_elapsed = 0
            if self.stall_elapsed >= self.stall_seconds:
                self.fault = 'encoder_or_stall:' + self.name
                print('Loi:', self.fault, 'duty', round(duty, 2), 'dir', self.direction,
                      'rpm', round(self.encoder.rpm, 1), 'xung', self.encoder.pulses,
                      'khong_xung_s', round(self.encoder.no_pulse_seconds, 1))
                self.stop()
        else:
            self.stall_elapsed = 0

    def signed_distance_m(self):
        return self.position_pulses / self.encoder.counts_per_rev * 3.14159265 * self.diameter_mm / 1000

    def status(self):
        return {'name': self.name, 'target_rpm': round(self.target, 2),
                'rpm': round(abs(self.encoder.rpm), 2),
                'pulses': self.encoder.pulses, 'pwm': round(self.motor.output, 3),
                'distance_m': self.encoder.pulses / self.encoder.counts_per_rev * 3.14159265 * self.diameter_mm / 1000,
                'position_pulses': self.position_pulses,
                'signed_distance_m': self.signed_distance_m(),
                'diameter_mm': self.diameter_mm, 'counts_per_rev': self.encoder.counts_per_rev,
                'fault': self.fault}

    def close(self):
        try:
            self.motor.close()
        finally:
            self.encoder.close()
