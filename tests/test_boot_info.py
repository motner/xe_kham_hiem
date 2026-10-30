"""Reset reporting must not label ordinary power-on/software resets as brownout."""
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'firmware'))
import boot_info


def machine_fake(cause, raw):
    return types.SimpleNamespace(PWRON_RESET=1, HARD_RESET=2, WDT_RESET=3,
                                 DEEPSLEEP_RESET=4, SOFT_RESET=5,
                                 reset_cause=lambda: cause, mem32={0x3FF48034: raw})


class BootInfoTests(unittest.TestCase):
    def test_classic_brownout_hardware_and_idf_software_reset_hint(self):
        for raw in (3, 12, 15):
            with self.subTest(raw=raw):
                info = boot_info.reset_details(machine_fake(1, raw), 'Generic ESP32 module with ESP32')
                self.assertTrue(info['brownout'])
                self.assertEqual(info['reason'], 'brownout')
                self.assertEqual(info['raw_cause'], raw)

    def test_power_on_and_soft_or_hard_reset_are_not_brownout(self):
        for cause, raw, reason in ((1, 1, 'power_on'), (5, 15, 'soft_reset'),
                                   (2, 3, 'hard_reset'), (3, 7, 'watchdog')):
            with self.subTest(cause=cause, raw=raw):
                info = boot_info.reset_details(machine_fake(cause, raw), 'Generic ESP32 module with ESP32')
                self.assertFalse(info['brownout'])
                self.assertEqual(info['reason'], reason)

    def test_other_chips_do_not_read_classic_registers_or_confirm_brownout(self):
        class NoReads:
            def __getitem__(self, address):
                raise AssertionError('Classic ESP32 register read on another chip')
        machine = machine_fake(1, 3)
        machine.mem32 = NoReads()
        info = boot_info.reset_details(machine, 'ESP32S3 module with ESP32S3')
        self.assertIsNone(info['raw_cause'])
        self.assertFalse(info['brownout'])
        self.assertEqual(info['reason'], 'power_on_or_brownout')

    def test_missing_register_access_keeps_power_reason_ambiguous(self):
        machine = machine_fake(1, 3)
        del machine.mem32
        info = boot_info.reset_details(machine, 'Generic ESP32 module with ESP32')
        self.assertFalse(info['brownout'])
        self.assertEqual(info['reason'], 'power_on_or_brownout')
        self.assertEqual(boot_info.reset_details(None, '')['reason'], 'unknown')

    def test_boot_identity_stable_per_instance_and_uptime_advances(self):
        clock = [100]
        with patch.object(boot_info, 'now_ms', lambda: clock[0]):
            info = boot_info.BootInfo()
            first = info.snapshot()
            clock[0] = 350
            later = info.snapshot()
            other = boot_info.BootInfo().snapshot()
        self.assertEqual(first['id'], later['id'])
        self.assertEqual(later['uptime_ms'], 250)
        self.assertNotEqual(first['id'], other['id'])


if __name__ == '__main__':
    unittest.main()
