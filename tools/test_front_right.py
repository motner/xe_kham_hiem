"""Test rieng motor banh truoc phai qua kenh B cua L298N phia truoc.
Ke xe len, chi cap nguon motor khi da san sang ngat nguon.
GPIO theo so do: IN3=25, IN4=33, ENB=32.
"""
from machine import Pin, PWM
from time import sleep

IN3_PIN = 25
IN4_PIN = 33
ENB_PIN = 32
PWM_FREQ = 1000
DUTY_PERCENT = 100  # 100% duty PWM.
RUN_SECONDS = 1

if not 0 < DUTY_PERCENT <= 100:
    raise ValueError('DUTY_PERCENT phai trong khoang 1..100')

in3 = Pin(IN3_PIN, Pin.OUT, value=0)
in4 = Pin(IN4_PIN, Pin.OUT, value=0)
enb = PWM(Pin(ENB_PIN), freq=PWM_FREQ, duty_u16=0)


def stop():
    enb.duty_u16(0)
    in3.value(0)
    in4.value(0)


def run(direction):
    """direction=1 chay mot chieu, direction=-1 chay chieu nguoc."""
    stop()
    sleep(0.3)  # Ngat PWM truoc khi doi chieu.
    if direction > 0:
        in3.value(1)
        in4.value(0)
    else:
        in3.value(0)
        in4.value(1)
    enb.duty_u16(int(DUTY_PERCENT * 65535 / 100))
    sleep(RUN_SECONDS)
    stop()


try:
    print('Banh truoc phai | IN3=GPIO25, IN4=GPIO33, ENB=GPIO32')
    print('PWM=%d%%, moi chieu %d giay.' % (DUTY_PERCENT, RUN_SECONDS))
    input('Ke xe len, bat nguon L298N va nhan Enter de thu: ')

    print('Thu chieu 1...')
    run(1)
    sleep(1)
    print('Thu chieu 2...')
    run(-1)
    print('Da thu xong hai chieu.')
finally:
    stop()
    enb.deinit()
    in3.value(0)
    in4.value(0)
    print('PWM da tat, chan IN3/IN4 da ve 0.')
