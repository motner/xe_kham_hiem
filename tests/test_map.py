"""Mo phong vat ly: chay dung Robot/Wheel/PID/Odometry/Scanner tren may tinh.

Motor dung so do that (K, vung chet, luc khoi dong). Vi tri that cua xe tinh rieng, co truot
banh khi xoay, nen co the so voi vi tri ma firmware uoc luong.
"""
import math
import pathlib
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'firmware'))
import config
from odometry import Odometry
from robot import Robot
from scanner import Scanner
from wheel import Wheel

# K (RPM moi 1,0 duty), duty bat dau co toc do, duty de nhuc nhich tu luc dung yen.
PLANT = {'front_left': (1110, .15, .25), 'rear_right': (1371, .14, .25),
         'rear_left': (983, .19, .40), 'front_right': (902, .28, .50)}


class SimMotor:
    tau = .36  # Do khi ke banh; tren san xe dung nhanh hon.

    def __init__(self, name):
        self.k, self.dead, self.start = PLANT[name]
        self.output = 0.0
        self.omega = 0.0  # RPM that, co dau.

    def set_output(self, x):
        self.output = x

    def stop(self):
        self.output = 0.0

    def close(self):
        self.stop()

    def step(self, dt):
        duty = abs(self.output)
        goal = 0.0
        moving = abs(self.omega) > 1
        if duty >= (self.dead if moving else self.start):
            goal = (duty - self.dead) * self.k * (1 if self.output > 0 else -1)
        self.omega += (goal - self.omega) * (1 - math.exp(-dt / self.tau))
        if goal == 0 and abs(self.omega) < 3:
            self.omega = 0.0


class SimEncoder:
    """Dem xung nguyen nhu encoder that, khong biet chieu quay."""
    counts_per_rev = 20

    def __init__(self, motor):
        self.motor = motor
        self.rpm = 0.0
        self.pulses = 0
        self.no_pulse_seconds = 0.0
        self.exact = 0.0
        self.counted = 0
        self.elapsed = 0.0

    def sample(self, dt):
        self.exact += abs(self.motor.omega) / 60 * 20 * dt
        self.elapsed += dt
        if self.elapsed < .1:
            return False
        whole = int(self.exact)
        travelled = whole - self.counted
        self.counted = whole
        self.pulses += travelled
        self.no_pulse_seconds = 0 if travelled else self.no_pulse_seconds + self.elapsed
        raw = travelled * 60 / (20 * self.elapsed)
        self.rpm += (1 - math.exp(-self.elapsed / .1)) * (raw - self.rpm)
        self.elapsed = 0.0
        return True

    def close(self):
        pass


class World:
    def __init__(self, turn_slip=1.0, obstacles=()):
        self.x = self.y = self.th = 0.0
        self.turn_slip = turn_slip      # 0,9: xe that xoay it hon 10% so voi encoder tinh.
        self.segments = []
        for box in obstacles:
            self.add_box(*box)
        self.boxes = list(obstacles)
        self.min_clear = 9.0
        self.servo = 0.0
        self.pings = []
        self.sensor_ok = True

    def add_box(self, x0, y0, x1, y1):
        self.segments += [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]

    def add_obstacle(self, *box):
        self.add_box(*box)
        self.boxes.append(box)

    def ray(self, ox, oy, angle):
        dx, dy, near = math.sin(angle), math.cos(angle), None
        for x1, y1, x2, y2 in self.segments:
            ex, ey = x2 - x1, y2 - y1
            det = dx * ey - dy * ex
            if abs(det) < 1e-9:
                continue
            t = ((x1 - ox) * ey - (y1 - oy) * ex) / det
            u = ((x1 - ox) * dy - (y1 - oy) * dx) / det
            if t > 0 and 0 <= u <= 1 and (near is None or t < near):
                near = t
        return near

    def ping(self):
        self.pings.append(self.servo)
        if not self.sensor_ok:
            return None
        sx = self.x + config.SCANNER_OFFSET_M * math.sin(self.th)
        sy = self.y + config.SCANNER_OFFSET_M * math.cos(self.th)
        # Chum song HC-SR04 rong, khong phai mot tia: lay diem gan nhat trong khoang +-12 do.
        hits = [self.ray(sx, sy, self.th + math.radians(self.servo + a)) for a in (-12, -6, 0, 6, 12)]
        hits = [h for h in hits if h is not None and h <= config.SCAN_MAX_CM / 100]
        return min(hits) * 100 if hits else None

    def set_angle(self, angle):
        self.servo = angle

    def clearance(self):
        best = 9.0
        for x0, y0, x1, y1 in self.boxes:
            dx = max(x0 - self.x, 0, self.x - x1)
            dy = max(y0 - self.y, 0, self.y - y1)
            best = min(best, math.sqrt(dx * dx + dy * dy))
        return best


class Sim:
    DT = .05

    def __init__(self, world=None, scanner=True):
        self.world = world or World()
        self.now = 0
        self.motors = {}
        wheels = []
        for w in config.WHEELS:
            motor = SimMotor(w['name'])
            self.motors[w['name']] = motor
            settings = {'pid': w['pid'], 'diameter_mm': w['diameter_mm']}
            wheels.append(Wheel(w['name'], motor, SimEncoder(motor), settings, config))
        self.scanner = Scanner(config, self.world.set_angle, self.world.ping) if scanner else None
        self.robot = Robot(wheels, config, clock=lambda: self.now, scanner=self.scanner)
        self.session = None
        self.seq = 0

    def tick(self, n=1):
        for _ in range(n):
            self.now += int(self.DT * 1000)
            self.robot.update(self.DT)
            for m in self.motors.values():
                m.step(self.DT)
            k = math.pi * config.WHEELS[0]['diameter_mm'] / 1000 / 60 * self.DT
            left = (self.motors['front_left'].omega + self.motors['rear_left'].omega) / 2 * k
            right = (self.motors['front_right'].omega + self.motors['rear_right'].omega) / 2 * k
            w = self.world
            d = (left + right) / 2
            dth = (left - right) / config.TRACK_WIDTH_M * w.turn_slip
            w.x += d * math.sin(w.th + dth / 2)
            w.y += d * math.cos(w.th + dth / 2)
            w.th = math.atan2(math.sin(w.th + dth), math.cos(w.th + dth))
            w.min_clear = min(w.min_clear, w.clearance())

    def drive(self, throttle, steering, seconds, rpm=110):
        if not self.session:
            self.session = self.robot.arm()
        for _ in range(int(seconds / self.DT)):
            self.seq += 1
            self.robot.command(self.session, self.seq, throttle, steering, rpm)
            self.tick()

    def park(self):
        self.robot.release(self.session)
        self.session = None
        self.tick(30)


def fake_cfg(**values):
    base = {k: getattr(config, k) for k in dir(config) if k.isupper()}
    base.update(values)
    return types.SimpleNamespace(**base)


class OdometryTests(unittest.TestCase):
    def test_straight_and_turn(self):
        odo = Odometry(.2)
        for _ in range(10):
            odo.update(.11, -0 + .11)
        self.assertAlmostEqual(odo.y, 1.1)
        self.assertAlmostEqual(odo.x, 0)
        self.assertEqual(len(odo.trail), 10)
        odo.update(.1 * math.pi / 2, -.1 * math.pi / 2)  # Xoay phai 90 do tai cho.
        self.assertAlmostEqual(odo.th, math.pi / 2)
        self.assertAlmostEqual(odo.y, 1.1)
        odo.update(1, 1)
        self.assertAlmostEqual(odo.x, 1)

    def test_reset(self):
        odo = Odometry(.2)
        odo.update(1, 1)
        epoch = odo.epoch
        odo.reset()
        self.assertEqual((odo.x, odo.y, odo.th, odo.trail), (0, 0, 0, []))
        self.assertEqual(odo.epoch, epoch + 1)


class ScannerTests(unittest.TestCase):
    def make(self, distance=100, **cfg):
        self.angles, self.pinged = [], []

        def ping():
            self.pinged.append(self.angles[-1])
            value = distance() if callable(distance) else distance
            return value
        return Scanner(fake_cfg(**cfg), self.angles.append, ping)

    def test_sweeps_every_period_and_returns_to_center(self):
        s = self.make()
        starts, was = [], False
        t = 0.0
        for _ in range(int(11 / .05)):
            s.update(.05)
            t += .05
            if s.sweeping and not was:
                starts.append(t)
            was = s.sweeping
        self.assertEqual(s.sweep_id, 3)
        self.assertEqual(len(starts), 3)
        self.assertAlmostEqual(starts[1] - starts[0], 3, delta=.1)
        self.assertEqual(self.angles[-1], 0)

    def test_measures_only_after_settling(self):
        s = self.make()
        for _ in range(int(5 / .05)):
            s.update(.05)
        self.assertEqual([a for a in self.pinged if a != 0][:2], [-60, -30])

    def test_pings_are_spaced_for_sensor(self):
        s = self.make()
        for _ in range(int(2.5 / .05)):
            s.update(.05)
        self.assertLessEqual(len(self.pinged), int(2.5 / .1) + 1)
        self.assertGreater(len(self.pinged), 10)

    def test_real_obstacle_is_seen(self):
        s = self.make(distance=20)
        for _ in range(10):
            s.update(.05)
        self.assertEqual(s.front_cm, 20)

    def test_no_echo_means_unknown(self):
        s = self.make(distance=None)
        for _ in range(int(4 / .05)):
            s.update(.05)
        self.assertIsNone(s.front_cm)
        self.assertFalse(s.seen_echo)
        self.assertEqual(s.points, [])

    def test_points_use_pose_and_angle(self):
        s = self.make(distance=100, SCAN_ANGLES=(90,), SCANNER_OFFSET_M=0, SCAN_PERIOD_MS=50)
        pose = types.SimpleNamespace(x=1.0, y=2.0, th=0.0)
        for _ in range(int(.5 / .05)):
            s.update(.05, pose)
        self.assertEqual(s.points[0][1:], (2.0, 2.0))

    def test_points_buffer_is_bounded(self):
        s = self.make()
        pose = types.SimpleNamespace(x=0.0, y=0.0, th=0.0)
        for _ in range(int(60 / .05)):
            s.update(.05, pose)
        self.assertLessEqual(len(s.points), 32)
        self.assertGreater(s.point_seq, 32)


class ScannerHardwareTests(unittest.TestCase):
    def test_servo_pulse_and_echo_conversion(self):
        from unittest.mock import patch
        from scanner import make_scanner
        duties = []

        class FakePWM:
            def __init__(self, *a, **k): pass
            def duty_u16(self, value): duties.append(value)
            def deinit(self): pass

        class FakePin:
            IN, OUT = 0, 1
            def __init__(self, *a, **k): pass
            def value(self, *a): pass

        pulse = {'us': 583}
        machine = types.SimpleNamespace(PWM=FakePWM, Pin=FakePin, time_pulse_us=lambda pin, level, timeout: pulse['us'])
        fake_time = types.SimpleNamespace(sleep_us=lambda us: None)
        with patch.dict(sys.modules, {'machine': machine, 'time': fake_time}):
            s = make_scanner(config)
            self.assertAlmostEqual(duties[-1], 1500 * 65535 / 20000, delta=1)
            s.set_angle(60)
            self.assertAlmostEqual(duties[-1], (1500 + 60 * config.SERVO_US_PER_DEG) * 65535 / 20000, delta=1)
            s.set_angle(180)
            self.assertAlmostEqual(duties[-1], 2500 * 65535 / 20000, delta=1)
            self.assertAlmostEqual(s.ping(), 10, places=3)
            pulse['us'] = -1
            self.assertIsNone(s.ping())
            s.close()


class MapTests(unittest.TestCase):
    def test_map_reset_refused_while_moving(self):
        sim = Sim()
        sim.drive(1, 0, 3)
        with self.assertRaisesRegex(ValueError, 'vehicle_moving'):
            sim.robot.reset_map()
        sim.park()
        sim.robot.reset_map()
        self.assertEqual(sim.robot.odometry.trail, [])

    def test_driving_draws_trail_and_scan_points(self):
        sim = Sim()
        sim.world.add_obstacle(-.5, 1.0, .5, 1.3)
        sim.drive(1, 0, 2)
        self.assertGreater(len(sim.robot.odometry.trail), 3)
        self.assertGreater(sim.scanner.point_seq, 0)

    def test_return_and_avoid_are_gone(self):
        sim = Sim()
        self.assertFalse(hasattr(sim.robot, 'start_return'))
        self.assertFalse(hasattr(sim.robot, 'navigator'))
        self.assertNotIn('nav', sim.robot.status())

    def test_status_is_json_ready_and_small(self):
        import json
        sim = Sim()
        sim.drive(1, 0, 3)
        text = json.dumps(sim.robot.status())
        self.assertLess(len(text), 4096)
        data = json.loads(text)
        self.assertIn('pose', data)
        self.assertIn('points', data['scan'])


class ConfigTests(unittest.TestCase):
    def test_config_is_consistent(self):
        config.validate_hardware()


if __name__ == '__main__':
    unittest.main()
