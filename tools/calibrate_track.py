"""Hieu chinh TRACK_WIDTH_M: xe skid-steer truot khi xoay nen gia tri nay KHAC so do bang thuoc.

Chay tren ESP32 bang Thonny/F5, khong chay dong thoi voi main.py.
Dat xe TREN SAN THAT, danh dau huong dau xe, de trong xung quanh. Xe se xoay tai cho
theo chieu kim dong ho den khi encoder tinh du 720 do (2 vong) roi dung.
"""
import math
import time
import config
from main import build_robot
from odometry import wrap_angle

TARGET_DEG = 720
RPM = config.RETURN_TURN_RPM


def main():
    robot = build_robot()
    try:
        print('Xe se xoay tai cho khoang', TARGET_DEG, 'do. Dat xe tren san, tranh xa vat can.')
        if input('Nhap TEST khi da san sang (Enter de thoat): ').strip() != 'TEST':
            return
        session = robot.arm()
        total, last = 0.0, robot.odometry.th
        sequence = 0
        previous = time.ticks_ms()
        started = previous
        while abs(total) < math.radians(TARGET_DEG):
            time.sleep_ms(config.CONTROL_PERIOD_MS)
            now = time.ticks_ms()
            dt = time.ticks_diff(now, previous) / 1000
            previous = now
            sequence += 1
            robot.command(session, sequence, 0, 1, RPM)
            robot.update(dt)
            total += wrap_angle(robot.odometry.th - last)
            last = robot.odometry.th
            if robot.fault or any(w.fault for w in robot.wheels):
                print('Dung vi loi:', robot.fault, [w.fault for w in robot.wheels])
                return
            if time.ticks_diff(now, started) > 60000:
                print('Qua 60 giay van chua du goc, dung lai.')
                return
        robot.release(session)
        # Cho xe dung han; xung quan tinh van duoc tinh vao goc.
        for _ in range(30):
            time.sleep_ms(config.CONTROL_PERIOD_MS)
            robot.update(config.CONTROL_PERIOD_MS / 1000)
            total += wrap_angle(robot.odometry.th - last)
            last = robot.odometry.th
        encoder_deg = abs(math.degrees(total))
        print('Encoder tinh xe da xoay: %.0f do.' % encoder_deg)
        actual = float(input('Xe THAT da xoay bao nhieu do (vi du 2 vong = 720, thieu 30 do = 690)? '))
        if actual <= 0:
            print('Goc khong hop le, khong tinh.')
            return
        print('Dat trong config.py: TRACK_WIDTH_M = %.3f' % (config.TRACK_WIDTH_M * encoder_deg / actual))
        print('Nap lai config.py roi chay lai bai nay; goc lech nho hon 5%% la dat.')
    finally:
        robot.close()


if __name__ == '__main__':
    main()
