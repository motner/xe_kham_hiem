"""Thu Wi-Fi/web rieng, khong khoi tao GPIO motor/encoder.

Tren bo: dat cung thu muc voi config.py, wifi.py, robot.py, web_server.py, http_transport.py,
boot_info.py va web/index.html. Chay bang REPL/Thonny sau khi cach ly cac
nguon cap; Ctrl+C de ket thuc. Khong thay main.py hay ghi lai config.py.
"""
import asyncio
import gc
import config
from robot import Robot
from web_server import WebServer, FileBody
from wifi import connect_wifi


async def run():
    # Robot rong: khong tao Motor, Encoder, PWM hay dang ky ngat GPIO.
    robot = Robot([], config)
    server = None
    print('WIFI TEST: chi web, motor/encoder khong duoc khoi tao.')
    try:
        wlan = await connect_wifi(config)
        server = WebServer(robot, config, FileBody('/web/index.html'))
        await server.start()
        print('WIFI TEST READY:', server.boot_info.snapshot())
        print('Mo web, dang nhap va de yen. Joystick se bi khoa.')
        while True:
            print('WIFI TEST HEALTH:', server.boot_info.snapshot(),
                  'ap_active:', wlan.active(),
                  'clients:', server.active_clients,
                  'heap_free:', gc.mem_free())
            await asyncio.sleep_ms(10000)
    finally:
        robot.close()
        if server:
            await server.close()


def main():
    try:
        asyncio.run(run())
    finally:
        asyncio.new_event_loop()


if __name__ == '__main__':
    main()
