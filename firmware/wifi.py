"""Ket noi Wi-Fi bat dong bo, khong chay vong sleep chan event loop."""
import asyncio
import time
import network


async def connect_wifi(config):
    if config.WIFI_MODE == 'AP':
        if len(config.AP_PASSWORD) < 8:
            raise ValueError('AP_PASSWORD can it nhat 8 ky tu')
        network.WLAN(network.STA_IF).active(False)
        wlan = network.WLAN(network.AP_IF)
        wlan.active(True)
        wlan.config(essid=config.AP_SSID, password=config.AP_PASSWORD, authmode=3,
                    channel=config.AP_CHANNEL)
        print('Wi-Fi:', config.AP_SSID)
    elif config.WIFI_MODE == 'STA':
        if not config.WIFI_SSID:
            raise ValueError('Can dien WIFI_SSID')
        network.WLAN(network.AP_IF).active(False)
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        disable_power_save(wlan, config)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        started = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), started) > config.CONNECT_TIMEOUT_SECONDS * 1000:
                wlan.disconnect()
                raise RuntimeError('Wi-Fi connection timeout')
            await asyncio.sleep_ms(100)
    else:
        raise ValueError('WIFI_MODE phai la AP hoac STA')
    print('Mo trinh duyet: http://' + wlan.ifconfig()[0])
    return wlan


def disable_power_save(wlan, config):
    """GPIO36/39 IRQ: tranh che do Wi-Fi sleep tren ESP32 classic."""
    if not getattr(config, 'WIFI_DISABLE_POWER_SAVE', False):
        return
    try:
        wlan.config(pm=wlan.PM_NONE)
    except (AttributeError, ValueError, OSError):
        if config.HARDWARE_ENABLED:
            raise RuntimeError('Firmware khong tat duoc Wi-Fi power save; can cap nhat MicroPython cho IRQ GPIO36/39')
        print('Canh bao: khong tat duoc Wi-Fi power save; dong co dang khoa.')
