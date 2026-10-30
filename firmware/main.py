"""Diem vao MicroPython: luu file nay o /main.py de tu chay khi cap nguon."""
import asyncio
import time
import config
from robot import Robot
from web_server import WebServer, FileBody


def build_robot():
    config.validate_hardware()
    if not config.HARDWARE_ENABLED:
        print('HARDWARE_ENABLED=False: web hoat dong, khong khoi tao GPIO dong co.')
        return Robot([], config)
    from motor import Motor
    from encoder import Encoder
    from wheel import Wheel
    wheels = []
    try:
        for settings in config.WHEELS:
            pins = config.MOTOR_CHANNELS[settings['motor_channel']]
            motor = Motor(pins['in1'], pins['in2'], pins['pwm'],
                          settings['motor_inverted'], config.PWM_FREQUENCY)
            encoder = None
            try:
                encoder = Encoder(settings['encoder_a'], settings['encoder_b'], settings['counts_per_rev'],
                                  settings['encoder_inverted'], config.ENCODER_SAMPLE_MS, config.ENCODER_FILTER_TAU,
                                  getattr(config, 'ENCODER_MIN_INTERVAL_US', 0))
                wheel = Wheel(settings['name'], motor, encoder, settings, config)
            except Exception:
                motor.close()
                if encoder:
                    encoder.close()
                raise
            wheels.append(wheel)
        return Robot(wheels, config)
    except Exception:
        for wheel in wheels:
            try:
                wheel.close()
            except Exception as error:
                print('Cleanup:', error)
        raise


def load_html():
    filename = globals().get('__file__', '')
    base = filename.rsplit('/', 1)[0] + '/' if '/' in filename else '/'
    return FileBody(base + 'web/index.html')


async def control_loop(robot):
    period = config.CONTROL_PERIOD_MS
    previous = time.ticks_ms()
    deadline = time.ticks_add(previous, period)
    while True:
        await asyncio.sleep_ms(max(0, time.ticks_diff(deadline, time.ticks_ms())))
        now = time.ticks_ms()
        dt = time.ticks_diff(now, previous) / 1000
        previous = now
        robot.update(dt)
        deadline = time.ticks_add(deadline, period)
        # Khong chay burst PID de bu nhieu chu ky khi CPU bi tre.
        if time.ticks_diff(deadline, now) <= 0:
            deadline = time.ticks_add(now, period)


async def run(robot=None, resources=None):
    owns_robot = robot is None
    if owns_robot:
        robot = build_robot()
    server = None
    try:
        from wifi import connect_wifi
        wlan = await connect_wifi(config)
        server = WebServer(robot, config, load_html())
        if resources is not None:
            resources['server'] = server
        print('Boot:', server.boot_info.snapshot())
        await server.start()
        print('Web/PID san sang. Ctrl+C de dung tat ca dong co.')
        await control_loop(robot)
    finally:
        try:
            if owns_robot:
                robot.close()
            else:
                robot.stop('shutdown')
        finally:
            if server:
                await server.close()


def main():
    robot = build_robot()
    resources = {}
    try:
        asyncio.run(run(robot, resources))
    finally:
        # Also runs if asyncio's scheduler fails outside the run coroutine.
        try:
            robot.close()
        finally:
            try:
                server = resources.get('server')
                if server:
                    server.close_nowait()
            finally:
                asyncio.new_event_loop()


if __name__ == '__main__':
    main()
