"""PID toc do: dt theo giay, dau ra PWM chuan hoa (0..limit)."""
import math


class PID:
    def __init__(self, kp, ki, kd, limit=0.4):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.limit = limit
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.previous_measurement = None

    def update(self, target, measured, dt):
        if not all(math.isfinite(x) for x in (target, measured, dt)) or dt <= 0:
            raise ValueError("PID input/dt invalid")
        error = target - measured
        # Dao ham tren measurement de tranh derivative kick khi doi setpoint.
        derivative = 0.0 if self.previous_measurement is None else -(measured - self.previous_measurement) / dt
        self.previous_measurement = measured
        candidate = self.integral + self.ki * error * dt
        raw = self.kp * error + candidate + self.kd * derivative
        # Conditional integration: khong tich luy them theo huong bao hoa.
        if not ((raw > self.limit and error > 0) or (raw < 0 and error < 0)):
            self.integral = max(-self.limit, min(self.limit, candidate))
        output = self.kp * error + self.integral + self.kd * derivative
        return max(0.0, min(self.limit, output))
