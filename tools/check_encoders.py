"""F5 de xac dinh encoder cua tung banh bang cach XOAY TAY, khong chay motor.
Khong chay dong thoi voi main.py. Ctrl+C dung script.
"""
import time
import network
from machine import Pin
import config
from encoder import Encoder


def main():
    # Ngat EN truoc, sau do dat cac chan chieu ve 0. Khong tao PWM.
    for pins in config.MOTOR_CHANNELS.values():
        Pin(pins['pwm'], Pin.OUT, value=0)
    for pins in config.MOTOR_CHANNELS.values():
        Pin(pins['in1'], Pin.OUT, value=0)
        Pin(pins['in2'], Pin.OUT, value=0)
    # Test offline de tranh Wi-Fi sleep anh huong IRQ36/39.
    network.WLAN(network.STA_IF).active(False)
    network.WLAN(network.AP_IF).active(False)
    encoders = []
    try:
        for gpio in config.ENCODER_PINS:
            encoders.append(Encoder(gpio, 1, sample_ms=200, filter_tau=0))
        print('Dong co da khoa. Xoay TAY tung banh, xem cot GPIO nao tang.')
        print('Moi gia tri la tong canh len OUT, KHONG phai RPM.')
        print('Thu tu cot: TRUOC TRAI, TRUOC PHAI, SAU TRAI, SAU PHAI')
        print('GPIO:', config.ENCODER_PINS)
        previous = time.ticks_ms()
        while True:
            time.sleep_ms(250)
            now = time.ticks_ms()
            dt = time.ticks_diff(now, previous) / 1000
            previous = now
            for encoder in encoders:
                encoder.sample(dt)
            print(['%s GPIO%d: %d' % (wheel['name'], wheel['encoder_a'], encoder.pulses)
                   for wheel, encoder in zip(config.WHEELS, encoders)])
    finally:
        for encoder in encoders:
            encoder.close()
        for pins in config.MOTOR_CHANNELS.values():
            Pin(pins['pwm'], Pin.OUT, value=0)


if __name__ == '__main__':
    main()
