# "AP": phat Wi-Fi rieng. "STA": ket noi Wi-Fi nha ban.
WIFI_MODE = "AP"

AP_SSID = "CR7-GOAT"
AP_PASSWORD = "12345678"  # It nhat 8 ky tu.
AP_CHANNEL = 11  # Kenh 2.4 GHz; chon trong 1..11 theo muc nhieu tai noi dung xe.

WIFI_SSID = ""
WIFI_PASSWORD = ""
CONNECT_TIMEOUT_SECONDS = 20

# Chi bat sau khi dien va kiem tra het thong so phan cung ben duoi.
HARDWARE_ENABLED = True  # Da sua I/O/RAM; bat GPIO de thu xe ke cao.
DRIVER_TYPE = "IN1_IN2_PWM"  # Moi motor can 2 chan chieu + 1 PWM rieng.
# Tai khoan dang nhap trang dieu khien; chi luu tren ESP32.
LOGIN_USERNAME = "admin"
LOGIN_PASSWORD = "24122006"
PWM_FREQUENCY = 1000
MAX_RPM = 120
MAX_DUTY = 1.0  # Toi da 100% duty PWM cho ca 4 banh.
CONTROL_PERIOD_MS = 50
MAX_LOOP_GAP_MS = 250
ENCODER_SAMPLE_MS = 100
ENCODER_FILTER_TAU = 0.10
# Bo xung cach nhau < 4 ms (= 750 RPM banh voi dia 20 khe): do thuc te banh truoc phai
# co hang tram xung gia < 3 ms do nhieu motor; motor TT that chi ~200-300 RPM.
ENCODER_MIN_INTERVAL_US = 4000
COMMAND_TIMEOUT_MS = 700
ACCEL_RPM_PER_SECOND = 100
REVERSE_WAIT_MS = 400
REVERSE_SAFE_RPM = 5
STALL_TIMEOUT_MS = 1500
STALL_MIN_DUTY = 0.20
# Banh dung yen qua BREAKAWAY_DELAY_MS ma co muc tieu RPM: cap it nhat duty nay de thang ma sat tinh.
BREAKAWAY_DUTY = 0.75  # Do bang bench: RL can ~0.6, FR lui can ~0.7 de bat dau quay.
BREAKAWAY_DELAY_MS = 300
# THU TAM: False chi dung banh encoder/stall loi; doi lai True sau khi thu.
STOP_ALL_ON_ENCODER_STALL = False

# Theo SO DO MOI NHAT: L298N nam phia tren ESP32 = 2 banh truoc;
# L298N phia duoi ESP32 = 2 banh sau. Test thuc te: kenh A=SAU PHAI, B=SAU TRAI.
# Trong dict, in1/in2 cua kenh B tuong ung chan that IN3/IN4 tren L298N.
MOTOR_CHANNELS = {
    "upper_a": {"in1": 27, "in2": 26, "pwm": 14},  # TRUOC TRAI: IN1, IN2, ENA
    "upper_b": {"in1": 25, "in2": 33, "pwm": 32},  # TRUOC PHAI: IN3, IN4, ENB
    "lower_a": {"in1": 17, "in2": 16, "pwm": 22},  # SAU PHAI theo test: IN1, IN2, ENA
    "lower_b": {"in1": 4, "in2": 21, "pwm": 19},   # SAU TRAI theo test: IN3, IN4, ENB
}
# GPIO encoder theo thu tu WHEELS/test da xac nhan: FL, RR, RL, FR.
ENCODER_PINS = (39, 34, 35, 36)
# 3 chan nay da duoc noi theo anh, khong duoc dung lai cho motor/encoder.
# Hien moi danh dau chan; chua chay servo hay do khoang cach trong vong PID.
SERVO_PIN = 23
ULTRASONIC_TRIGGER_PIN = 13
ULTRASONIC_ECHO_PIN = 18
WIFI_DISABLE_POWER_SAVE = True  # Can chu y IRQ GPIO36/39 tren ESP32 classic.

# Thu tu cau hinh/test theo ket qua tren xe: truoc trai, sau phai, sau trai, truoc phai.
# Encoder da duoc nguoi dung xac nhan: FL=39, FR=36, RL=35, RR=34.
# Kenh da doi chieu bang test: FL=upper_a, FR=upper_b, RR=lower_a, RL=lower_b.
# Theo file test nguoi dung: hai motor truoc reverse=True, hai motor sau False.
# motor_channel: "upper_a", "upper_b", "lower_a", "lower_b".
# encoder_a: mot GPIO trong ENCODER_PINS, phai dung encoder cua motor do.
# Dia 20 khe, dem canh len A: 20 xung/vong NEU dia quay 1:1 voi banh.
# Duong kinh 60 mm la xap xi theo anh san pham; do lai banh thuc te de hieu chinh.
# Encoder trong anh chi co OUT: encoder_b=None, chi do do lon RPM.
# pid=(Kp, Ki, Kd): dau ra 0..1, sai so RPM, dt giay; can hieu chinh.
WHEELS = [
    {"name": "front_left", "motor_channel": "upper_a",
     "encoder_a": 39, "encoder_b": None, "motor_inverted": True,
     "encoder_inverted": False, "counts_per_rev": 20, "diameter_mm": 60, "pid": (0.008, 0.003, 0.0)},
    {"name": "rear_right", "motor_channel": "lower_a",
     "encoder_a": 34, "encoder_b": None, "motor_inverted": False,
     "encoder_inverted": False, "counts_per_rev": 20, "diameter_mm": 60, "pid": (0.008, 0.003, 0.0)},
    {"name": "rear_left", "motor_channel": "lower_b",
     "encoder_a": 35, "encoder_b": None, "motor_inverted": False,
     "encoder_inverted": False, "counts_per_rev": 20, "diameter_mm": 60, "pid": (0.008, 0.003, 0.0)},
    {"name": "front_right", "motor_channel": "upper_b",
     "encoder_a": 36, "encoder_b": None, "motor_inverted": True,
     "encoder_inverted": False, "counts_per_rev": 20, "diameter_mm": 60, "pid": (0.008, 0.003, 0.0)},
]


def validate_hardware():
    """Kiem tra truoc khi khoi tao bat ky GPIO nao."""
    import math
    if not isinstance(LOGIN_USERNAME, str) or not 1 <= len(LOGIN_USERNAME) <= 64:
        raise ValueError("LOGIN_USERNAME can tu 1 den 64 ky tu")
    if not isinstance(LOGIN_PASSWORD, str) or not 1 <= len(LOGIN_PASSWORD) <= 128:
        raise ValueError("LOGIN_PASSWORD can tu 1 den 128 ky tu")
    if not HARDWARE_ENABLED:
        return
    if DRIVER_TYPE != "IN1_IN2_PWM":
        raise ValueError("Driver chua duoc ho tro: " + DRIVER_TYPE)
    if not (0 < MAX_DUTY <= 1 and 0 < MAX_RPM <= 200):
        raise ValueError("MAX_DUTY / MAX_RPM khong hop le")
    if not (0 < CONTROL_PERIOD_MS <= ENCODER_SAMPLE_MS < STALL_TIMEOUT_MS):
        raise ValueError("Chu ky dieu khien/encoder/stall khong hop le")
    if not (CONTROL_PERIOD_MS < MAX_LOOP_GAP_MS < COMMAND_TIMEOUT_MS):
        raise ValueError("MAX_LOOP_GAP_MS / COMMAND_TIMEOUT_MS khong hop le")
    if not (ACCEL_RPM_PER_SECOND > 0 and REVERSE_WAIT_MS >= ENCODER_SAMPLE_MS and REVERSE_SAFE_RPM >= 0
            and 0 < STALL_MIN_DUTY <= MAX_DUTY and ENCODER_FILTER_TAU >= 0 and PWM_FREQUENCY > 0):
        raise ValueError("Thong so dieu khien khong hop le")
    expected = ('front_left', 'rear_right', 'rear_left', 'front_right')
    if len(WHEELS) != 4 or tuple(w['name'] for w in WHEELS) != expected:
        raise ValueError("WHEELS can dung thu tu test FL, RR, RL, FR")
    pins = {SERVO_PIN, ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN}
    channels = set()
    # Danh sach GPIO ESP32 classic co the output, loai chan flash 6..11.
    output_pins = {0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33}
    for wheel in WHEELS:
        channel = wheel['motor_channel']
        if channel not in MOTOR_CHANNELS or channel in channels:
            raise ValueError(wheel['name'] + ': can gan motor_channel rieng cho tung banh')
        channels.add(channel)
        motor_pins = MOTOR_CHANNELS[channel]
        for key in ('in1', 'in2', 'pwm', 'encoder_a', 'encoder_b'):
            pin = motor_pins[key] if key in ('in1', 'in2', 'pwm') else wheel[key]
            if key == 'encoder_b' and pin is None:
                continue
            if type(pin) is not int or pin < 0 or pin in pins:
                raise ValueError(wheel['name'] + ': GPIO thieu, trung hoac khong hop le: ' + key)
            if key in ('in1', 'in2', 'pwm') and pin not in output_pins:
                raise ValueError(wheel['name'] + ': GPIO khong ho tro output tren ESP32 classic')
            if key == 'encoder_a' and pin not in ENCODER_PINS:
                raise ValueError(wheel['name'] + ': encoder_a phai theo ENCODER_PINS trong so do')
            if key == 'encoder_b' and pin is not None:
                raise ValueError('So do nay dung encoder mot kenh OUT, encoder_b phai la None')
            pins.add(pin)
        for key in ('counts_per_rev', 'diameter_mm'):
            value = wheel[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(wheel['name'] + ': can dien ' + key)
        gains = wheel['pid']
        if not isinstance(gains, (tuple, list)) or len(gains) != 3:
            raise ValueError(wheel['name'] + ': can dien pid=(Kp, Ki, Kd)')
        if not all(type(k) in (int, float) and math.isfinite(k) and k >= 0 for k in gains) or not any(gains):
            raise ValueError(wheel['name'] + ': he so PID khong hop le')
