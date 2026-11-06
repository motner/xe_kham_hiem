"""Bai thu THUC tren xe, chay thu cong bang Thonny/F5, khong doi ten main.py.
Ke 4 banh khoi mat dat, chuan bi ngat nguon motor. Chi chay mot banh moi lan.
Khong can HARDWARE_ENABLED=True hay PID; day la bai thu PWM rieng co xac nhan.
"""
import time
import config
from motor import Motor
from encoder import Encoder

DUTY = 1.00          # 100% duty PWM; khong dong nghia voi toc do banh.
RUN_MS = 1000       # Moi lan quay 1 giay roi tat PWM.
COAST_MS = 1500     # Cho banh cham lai truoc khi thu lan khac.
LABELS = {
    'front_left': 'TRUOC TRAI',
    'front_right': 'TRUOC PHAI',
    'rear_left': 'SAU TRAI',
    'rear_right': 'SAU PHAI',
}


def wheel_label(wheel):
    """Hien thi nhan theo ten banh trong config.WHEELS."""
    return LABELS.get(wheel['name'], wheel['name'].upper())


def check_config():
    if not (0 < DUTY <= 1.00 and 0 < RUN_MS <= 1500):
        raise ValueError('Bai thu gioi han PWM <=100%, thoi gian <=1500 ms')
    if len(config.WHEELS) != 4:
        raise ValueError('Can 4 banh trong config')
    used = set()
    for wheel in config.WHEELS:
        pins = config.MOTOR_CHANNELS[wheel['motor_channel']]
        for gpio in (pins['in1'], pins['in2'], pins['pwm'], wheel['encoder_a']):
            if type(gpio) is not int or gpio in used:
                raise ValueError('GPIO thieu hoac trung')
            used.add(gpio)


def snapshot(encoders):
    from machine import disable_irq, enable_irq
    irq = disable_irq()
    try:
        # Chi doc so dem trong vung khoa IRQ; tao tuple sau khi mo lai IRQ.
        a = encoders[0].travel_count
        b = encoders[1].travel_count
        c = encoders[2].travel_count
        d = encoders[3].travel_count
    finally:
        enable_irq(irq)
    return (a, b, c, d)


def pulse_motor(motor, direction):
    try:
        motor.set_output(direction * DUTY)
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < RUN_MS:
            time.sleep_ms(20)  # Cho phep Ctrl+C ngat som.
    finally:
        motor.stop()


def main():
    check_config()
    from machine import Pin
    import network
    # EN tat truoc khi khoi tao driver, moi lan chi mot motor duoc kich hoat.
    for pins in config.MOTOR_CHANNELS.values():
        Pin(pins['pwm'], Pin.OUT, value=0)
    for pins in config.MOTOR_CHANNELS.values():
        Pin(pins['in1'], Pin.OUT, value=0)
        Pin(pins['in2'], Pin.OUT, value=0)
    network.WLAN(network.STA_IF).active(False)
    network.WLAN(network.AP_IF).active(False)
    motors, encoders = [], []
    try:
        for wheel in config.WHEELS:
            pins = config.MOTOR_CHANNELS[wheel['motor_channel']]
            motors.append(Motor(pins['in1'], pins['in2'], pins['pwm'], wheel['motor_inverted'], config.PWM_FREQUENCY))
            encoders.append(Encoder(wheel['encoder_a'], 1))  # Chi dem xung, khong tinh RPM.
        print('\nTHU DONG CO THAT: 100% PWM, 1 giay/lan, khong PID.')
        print('Ke 4 banh khoi mat dat. Chuan bi cong tac ngat nguon motor.')
        print('Khong bam RESET de dung: RESET co the chay lai main.py.')
        if input('Nhap TEST khi da san sang (Enter de thoat): ').strip() != 'TEST':
            return
        while True:
            print('\nChon banh:')
            for test_index, wheel in enumerate(config.WHEELS):
                print('%d = %s | %s | encoder GPIO%d' % (test_index + 1, wheel_label(wheel), wheel['motor_channel'], wheel['encoder_a']))
            choice = input('1..4 de quay tien; -1..-4 de quay lui; q de thoat: ').strip()
            if choice.lower() == 'q':
                break
            if choice not in ('1','2','3','4','-1','-2','-3','-4'):
                print('Lenh khong hop le, khong chay motor.')
                continue
            test_index = abs(int(choice)) - 1
            selected = test_index
            direction = 1 if int(choice) > 0 else -1
            wheel = config.WHEELS[selected]
            print('CHAY %s, %s; quan sat dung BANH va CHIEU quay.' % (wheel_label(wheel), 'TIEN' if direction > 0 else 'LUI'))
            before = snapshot(encoders)
            pulse_motor(motors[selected], direction)
            print('PWM da ve 0; cho banh dung...')
            time.sleep_ms(COAST_MS)
            after = snapshot(encoders)
            counts = [(end - start) & Encoder.MASK for start, end in zip(before, after)]
            for i, (wheel, count) in enumerate(zip(config.WHEELS, counts)):
                print('  %-11s GPIO%d: +%d xung%s' % (wheel_label(wheel), wheel['encoder_a'], count, ' <- encoder mong doi' if i == selected else ''))
            if counts[selected] == 0:
                print('CHUA XAC NHAN: encoder mong doi khong co xung. Kiem tra banh co quay, nguon, jumper EN va cam bien.')
            elif any(count for i, count in enumerate(counts) if i != selected):
                print('CAN KIEM TRA: encoder banh khac cung tang; co the nham day, nhieu hoac banh khac bi xoay.')
            else:
                print('Encoder phan hoi dung kenh; van can ban xac nhan dung vi tri banh va chieu quay.')
            print('Neu chieu sai, sua motor_inverted cua dung banh trong config.py. Khong doi encoder sang banh khac.')
    finally:
        for motor in motors:
            try:
                motor.close()
            except Exception as error:
                print('Loi dung motor:', error)
        for encoder in encoders:
            encoder.close()
        for pins in config.MOTOR_CHANNELS.values():
            Pin(pins['pwm'], Pin.OUT, value=0)
        print('Ket thuc bai thu, tat ca EN da ve 0.')


if __name__ == '__main__':
    main()
