"""Thong tin khoi dong; chi doc nguyen nhan reset, khong ghi thanh ghi/flash."""
import binascii
import os
import time


def now_ms():
    return time.ticks_ms() if hasattr(time, 'ticks_ms') else int(time.monotonic() * 1000)


def reset_details(machine, board):
    cause = raw = None
    if machine is None:
        return {'reason': 'unknown', 'brownout': False, 'cause': cause, 'raw_cause': raw}
    try:
        cause = machine.reset_cause()
    except (AttributeError, OSError):
        pass

    # ESP32 classic ONLY. RTC_CNTL_RESET_STATE_REG, RESET_CAUSE_PROCPU[5:0].
    # ESP-IDF: components/soc/esp32/register/soc/{reg_base,rtc_cntl_reg}.h.
    if board.endswith('with ESP32'):
        try:
            raw = machine.mem32[0x3FF48034] & 0x3F
        except (AttributeError, OSError, ValueError):
            pass

    def matches(name):
        value = getattr(machine, name, None)
        return value is not None and cause == value

    if matches('BROWNOUT_RESET') or matches('BROWN_OUT_RESET'):
        reason = 'brownout'
    elif matches('SOFT_RESET'):
        # Raw hardware reason can predate a MicroPython soft reboot.
        reason = 'soft_reset'
    elif raw == 15 or (matches('PWRON_RESET') and raw in (3, 12)):
        # MicroPython maps ESP_RST_POWERON and ESP_RST_BROWNOUT to PWRON_RESET.
        # ESP-IDF brownout ISR can restart in software (raw 3/12), retaining
        # ESP_RST_BROWNOUT as its hint. A true power-on has raw reason 1.
        reason = 'brownout'
    elif matches('PWRON_RESET'):
        reason = 'power_on' if raw == 1 else 'power_on_or_brownout'
    elif matches('WDT_RESET'):
        reason = 'watchdog'
    elif matches('DEEPSLEEP_RESET'):
        reason = 'deep_sleep'
    elif matches('HARD_RESET'):
        reason = 'hard_reset'
    else:
        reason = 'unknown'
    return {'reason': reason, 'brownout': reason == 'brownout',
            'cause': cause, 'raw_cause': raw}


class BootInfo:
    def __init__(self):
        try:
            import machine
        except ImportError:
            machine = None
        try:
            board = os.uname().machine
        except AttributeError:
            board = ''
        self.details = reset_details(machine, board)
        self.boot_id = binascii.hexlify(os.urandom(8)).decode()
        self.started = now_ms()

    def snapshot(self):
        now = now_ms()
        elapsed = time.ticks_diff(now, self.started) if hasattr(time, 'ticks_diff') else now - self.started
        return dict(self.details, id=self.boot_id, uptime_ms=max(0, elapsed))
