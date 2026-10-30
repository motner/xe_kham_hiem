"""Dem canh len A (1x). B tuy chon de xac dinh chieu; khong phai 4x."""
import math
import time


class Encoder:
    MASK = (1 << 28) - 1

    def __init__(self, pin_a, pin_b, counts_per_rev, inverted=False, sample_ms=100, filter_tau=0.10,
                 min_interval_us=0):
        from machine import Pin
        self.a = Pin(pin_a, Pin.IN)  # Dung pull-up ngoai neu module yeu cau.
        self.b = Pin(pin_b, Pin.IN) if pin_b is not None else None
        self.counts_per_rev = counts_per_rev
        self.inverted = inverted
        self.sample_seconds = sample_ms / 1000
        self.filter_tau = filter_tau
        self.count = 0
        self.travel_count = 0
        self.previous_count = 0
        self.previous_travel = 0
        self.pulses = 0
        self.position_counts = 0
        self.elapsed = 0.0
        self.no_pulse_seconds = 0.0
        self.rpm = 0.0
        self.raw_rpm = 0.0
        # Bo canh qua sat canh truoc: nhieu choi than motor tao xung gia cach nhau < 1-3 ms.
        self.min_interval_us = min_interval_us
        self.last_edge_us = None
        self.rejected = 0
        self._irq_ref = self._irq
        self.a.irq(trigger=Pin.IRQ_RISING, handler=self._irq_ref)

    def _irq(self, pin):
        # Chi dem; khong print, khong float, khong chay PID trong interrupt.
        if self.min_interval_us:
            now = time.ticks_us()
            # Khong cap nhat moc khi bo canh, de chuoi nhieu khong nuot mat canh that.
            if self.last_edge_us is not None and time.ticks_diff(now, self.last_edge_us) < self.min_interval_us:
                self.rejected += 1
                return
            self.last_edge_us = now
        direction = 1 if self.b is None or self.b.value() else -1
        if self.b is not None and self.inverted:
            direction = -direction
        self.count = (self.count + direction) & self.MASK
        self.travel_count = (self.travel_count + 1) & self.MASK

    def sample(self, dt):
        self.elapsed += dt
        if self.elapsed < self.sample_seconds:
            return False
        from machine import disable_irq, enable_irq
        irq = disable_irq()
        count, travel = self.count, self.travel_count
        enable_irq(irq)
        delta = (count - self.previous_count) & self.MASK
        if delta > (self.MASK + 1) // 2:
            delta -= self.MASK + 1
        travelled = (travel - self.previous_travel) & self.MASK
        self.previous_count, self.previous_travel = count, travel
        self.position_counts += delta
        self.pulses += travelled
        self.no_pulse_seconds = 0 if travelled else self.no_pulse_seconds + self.elapsed
        self.raw_rpm = delta * 60 / (self.counts_per_rev * self.elapsed)
        alpha = 1 - math.exp(-self.elapsed / self.filter_tau) if self.filter_tau else 1
        self.rpm += alpha * (self.raw_rpm - self.rpm)
        self.elapsed = 0.0
        return True

    def close(self):
        self.a.irq(handler=None)
