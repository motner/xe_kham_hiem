"""Dieu phoi 4 banh; lease 1 nguoi dieu khien, sequence, watchdog lenh."""
import math
import time
import os
import binascii


def now_ms():
    if hasattr(time, 'ticks_ms'):
        return time.ticks_ms()
    return int(time.monotonic() * 1000)


def elapsed_ms(now, before):
    return time.ticks_diff(now, before) if hasattr(time, 'ticks_diff') else now - before


class Robot:
    def __init__(self, wheels, cfg, clock=now_ms):
        self.wheels, self.cfg, self.clock = wheels, cfg, clock
        self.ready = bool(wheels) and len(wheels) == 4
        self.session = None
        self.sequence = -1
        self.last_command = clock()
        self.fault = None
        self.reason = 'boot' if self.ready else 'hardware_disabled'
        self.loop_ms = 0
        self.left = self.right = 0.0

    def check_timeout(self):
        if self.session and elapsed_ms(self.clock(), self.last_command) > self.cfg.COMMAND_TIMEOUT_MS:
            self.stop('command_timeout')

    def clear_recoverable_faults(self):
        # Tre vong lap va banh khong co xung chi dung xe; lan keo moi duoc thu lai,
        # khong phai khoi dong lai bo. Loi dung motor/ngoai le van bi chot.
        if self.fault == 'control_loop_late':
            print('Xoa loi:', self.fault)
            self.fault = None
        for wheel in self.wheels:
            if wheel.fault and wheel.fault.startswith('encoder_or_stall:'):
                print('Xoa loi:', wheel.fault)
                wheel.fault = None
                wheel.stall_elapsed = 0.0

    def arm(self):
        self.check_timeout()
        if self.ready and not self.session:
            self.clear_recoverable_faults()
        if not self.ready or self.fault:
            raise ValueError(self.fault or 'hardware_disabled')
        if self.session:
            raise ValueError('controller_busy')
        self.stop('armed')
        self.session = binascii.hexlify(os.urandom(16)).decode()
        self.sequence = -1
        self.last_command = self.clock()
        return self.session

    def command(self, session, sequence, throttle, steering, max_rpm):
        self.check_timeout()
        if not self.ready or self.fault or not self.session or session != self.session:
            raise ValueError('invalid_or_expired_session')
        if type(sequence) is not int or sequence < 0 or sequence > 1000000000 or sequence <= self.sequence:
            raise ValueError('stale_sequence')
        if not all(type(x) in (int, float) and math.isfinite(x) for x in (throttle, steering, max_rpm)):
            raise ValueError('invalid_number')
        if not (-1 <= throttle <= 1 and -1 <= steering <= 1 and 0 <= max_rpm <= self.cfg.MAX_RPM):
            raise ValueError('command_out_of_range')
        left, right = throttle + steering, throttle - steering
        scale = max(1, abs(left), abs(right))
        self.left, self.right = left / scale * max_rpm, right / scale * max_rpm
        self.sequence = sequence
        self.last_command = self.clock()
        self.reason = 'running' if self.left or self.right else 'idle'
        for wheel in self.wheels:
            # Thu tu danh sach la thu tu test; ben trai/phai lay tu ten banh.
            target = self.left if wheel.name.endswith('_left') else self.right
            wheel.set_target_rpm(target)
            if wheel.requested == 0:
                wheel.stop()

    def stop(self, reason='stopped'):
        self.session = None
        self.left = self.right = 0
        self.reason = reason
        first_error = None
        for wheel in self.wheels:
            try:
                wheel.stop()
            except Exception as error:
                first_error = error
        if first_error:
            self.fault = 'motor_stop_error'
            raise first_error

    def release(self, session):
        # Lenh dung tre tu phien cu khong duoc huy phien moi.
        if session and session == self.session:
            self.stop('released')

    def update(self, dt):
        self.loop_ms = round(dt * 1000, 1)
        self.check_timeout()
        if dt <= 0 or dt * 1000 > self.cfg.MAX_LOOP_GAP_MS:
            self.fault = 'control_loop_late'
            print('Loi:', self.fault, self.loop_ms, 'ms')
            self.stop(self.fault)
            return
        if self.fault:
            return
        try:
            for wheel in self.wheels:
                wheel.update(dt)
                if wheel.fault:
                    if (wheel.fault.startswith('encoder_or_stall:')
                            and not getattr(self.cfg, 'STOP_ALL_ON_ENCODER_STALL', True)):
                        # Wheel da tu dung/giu loi; van cap nhat PID cac banh khac.
                        continue
                    self.fault = wheel.fault
                    print('Loi:', self.fault)
                    self.stop(self.fault)
                    break
        except Exception:
            self.fault = 'control_exception'
            self.stop(self.fault)
            raise

    def status(self):
        wheels = [wheel.status() for wheel in self.wheels] if self.ready else None
        return {'device': 'esp32-web', 'motor_ready': self.ready and not self.fault,
                'encoder_ready': self.ready, 'armed': self.session is not None,
                'fault': self.fault, 'reason': self.reason, 'max_rpm': self.cfg.MAX_RPM,
                'wheel_faults': [wheel.fault for wheel in self.wheels if wheel.fault],
                'stop_all_on_encoder_stall': getattr(self.cfg, 'STOP_ALL_ON_ENCODER_STALL', True),
                'loop_ms': self.loop_ms, 'command_timeout_ms': self.cfg.COMMAND_TIMEOUT_MS,
                'left_target': self.left, 'right_target': self.right, 'wheels': wheels}

    def close(self):
        try:
            self.stop('shutdown')
        finally:
            for wheel in self.wheels:
                try:
                    wheel.close()
                except Exception as error:
                    print('Cleanup:', error)
