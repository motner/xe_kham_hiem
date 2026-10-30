"""Driver 2 chan chieu IN1/IN2 + 1 chan PWM/EN doc lap moi motor."""


class Motor:
    def __init__(self, in1, in2, pwm, inverted=False, frequency=1000):
        from machine import Pin, PWM
        self.pwm = None
        self.in1 = Pin(in1, Pin.OUT, value=0)
        self.in2 = Pin(in2, Pin.OUT, value=0)
        self.inverted = inverted
        self.output = 0.0
        self.pwm = PWM(Pin(pwm), freq=frequency, duty_u16=0)

    def set_output(self, output):
        output = max(-1.0, min(1.0, output))
        physical = -output if self.inverted else output
        # Tat PWM truoc khi thay doi chieu.
        old = -self.output if self.inverted else self.output
        if physical == 0 or physical * old <= 0:
            self.pwm.duty_u16(0)
        self.in1.value(1 if physical > 0 else 0)
        self.in2.value(1 if physical < 0 else 0)
        self.pwm.duty_u16(int(abs(physical) * 65535))
        self.output = output

    def stop(self):
        self.set_output(0)

    def close(self):
        self.stop()
        self.pwm.deinit()
