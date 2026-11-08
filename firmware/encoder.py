"""Dem canh len A (1x). Encoder mot kenh: chi do do lon RPM, khong biet chieu quay."""
import math
import time


class Encoder:
    MASK = (1 << 28) - 1

    def __init__(self, pin_a, counts_per_rev, sample_ms=100, filter_tau=0.10, min_interval_us=0):
        from machine import Pin, disable_irq, enable_irq
        self._disable_irq, self._enable_irq = disable_irq, enable_irq
        self.a = Pin(pin_a, Pin.IN)
        self.counts_per_rev = counts_per_rev
        self.sample_seconds = sample_ms / 1000
        self.filter_tau = filter_tau
        self.travel_count = 0 # số xung ko dấu
        self.previous_travel = 0 # travel ở lần trước
        self.pulses = 0 # tổng số xung
        self.elapsed = 0.0 # thời gian cộng dồn từ lần tính RPM trước
        self.no_pulse_seconds = 0.0 # thời gian chưa có xung
        self.rpm = 0.0 # tốc độ đã làm mượt
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
        self.travel_count = (self.travel_count + 1) & self.MASK

    def sample(self, dt):
        self.elapsed += dt
        if self.elapsed < self.sample_seconds:
            return False
        irq = self._disable_irq()
        travel = self.travel_count
        self._enable_irq(irq)
        travelled = (travel - self.previous_travel) & self.MASK
        self.previous_travel = travel
        self.pulses += travelled
        self.no_pulse_seconds = 0 if travelled else self.no_pulse_seconds + self.elapsed
        raw_rpm = travelled * 60 / (self.counts_per_rev * self.elapsed)
        alpha = 1 - math.exp(-self.elapsed / self.filter_tau) if self.filter_tau else 1
        self.rpm += alpha * (raw_rpm - self.rpm)
        self.elapsed = 0.0
        return True

    def close(self):
        self.a.irq(handler=None)
