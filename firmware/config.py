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
# Tang dan tu BREAKAWAY_DUTY den khi banh nhuc nhich: banh nhay khong bi vot, banh kho van len duoc 100%.
# Do bang bench: FR (motor moi) tu dung yen on dinh tu duty 0.6 khi tien, 0.5 khi lui.
BREAKAWAY_DUTY = 0.35
BREAKAWAY_RAMP_PER_S = 1.0
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
ULTRASONIC_ECHO_PIN = 18  # HC-SR04 ra 5 V: PHAI chia ap xuong 3,3 V truoc khi vao GPIO.

# Quet vat can. Goc duong la ben phai xe, 0 la thang phia truoc.
SCANNER_ENABLED = True
SCAN_PERIOD_MS = 3000
SCAN_ANGLES = (-60, -30, 0, 30, 60)
SCAN_SETTLE_MS = 200       # Cho servo toi goc moi truoc khi do.
GUARD_PERIOD_MS = 100      # Giua cac lan quet: do thang phia truoc.
SCAN_MAX_CM = 150
SCANNER_OFFSET_M = 0.08    # Do lai: khoang cach tu tam xe toi cam bien.
SERVO_CENTER_US = 1500     # Chinh neu cam bien chua nhin thang khi o goc 0.
SERVO_US_PER_DEG = 10.5
SERVO_INVERTED = False     # Dat True neu goc duong lam servo quay sang trai.

# Vi tri va quay ve: cac gia tri duoi day can chinh lai tren xe that.
TRACK_WIDTH_M = 0.16       # Do lai: tam banh trai toi tam banh phai.
RETURN_DRIVE_RPM = 110     # Cao hon toc do toi thieu da do cua RL va FR.
RETURN_TURN_RPM = 110
RETURN_STEER_RPM = 10
RETURN_STEER_GAIN = 40
RETURN_TURN_TOLERANCE_DEG = 25
RETURN_TURN_COAST_S = 0.35 # Xe con xoay tiep sau khi ngat motor: do lai tren san.
RETURN_REALIGN_DEG = 55
RETURN_WAYPOINT_M = 0.40    # Nhin xa ngan nay tren duong cu; qua gan thi xe xoay lien tuc.
RETURN_HOME_M = 0.15
RETURN_SETTLE_MS = 400
RETURN_STOP_CM = 45        # Gom ca quang duong xe con troi sau khi ngat motor.
RETURN_CLEAR_CM = 70       # Mot huong phai trong it nhat chung nay moi duoc chon.
RETURN_OBSTACLE_RADIUS_M = 0.40
RETURN_AVOID_M = 0.50
RETURN_MAX_AVOID = 6
RETURN_TIMEOUT_S = 180
WIFI_DISABLE_POWER_SAVE = True  # Can chu y IRQ GPIO36/39 tren ESP32 classic.

# Thu tu cau hinh/test theo ket qua tren xe: truoc trai, sau phai, sau trai, truoc phai.
# Encoder da duoc nguoi dung xac nhan: FL=39, FR=36, RL=35, RR=34.
# Kenh da doi chieu bang test: FL=upper_a, FR=upper_b, RR=lower_a, RL=lower_b.
# Theo file test nguoi dung: hai motor truoc reverse=True, hai motor sau False.
# motor_channel: "upper_a", "upper_b", "lower_a", "lower_b".
# encoder_a: mot GPIO trong ENCODER_PINS, phai dung encoder cua motor do.
# Dia 20 khe, dem canh len A: 20 xung/vong NEU dia quay 1:1 voi banh.
# Duong kinh 60 mm la xap xi theo anh san pham; do lai banh thuc te de hieu chinh.
# Encoder trong anh chi co OUT (mot kenh): chi do do lon RPM, khong biet chieu.
# pid=(Kp, Ki, Kd): dau ra 0..1, sai so RPM, dt giay.
# Do tung banh, ke khong tai, pin day (11/2026): (0.008, 0.003) dao dong manh.
# Do lai 11/2026: FL (0.0022, 0.005), RR (0.001, 0.003), RL (0.002, 0.005).
# FR tam giu (0.002, 0.005): lan do cuoi banh yeu bat thuong, can do lai.
# FR voi Kp 0.003 bi bao ket. RL dao dong manh o 80-100 RPM: PID khong sua duoc.
WHEELS = [
    {"name": "front_left", "motor_channel": "upper_a",
     "encoder_a": 39, "motor_inverted": True,
     "counts_per_rev": 20, "diameter_mm": 65, "pid": (0.0022, 0.005, 0.0)},
    {"name": "rear_right", "motor_channel": "lower_a",
     "encoder_a": 34, "motor_inverted": False,
     "counts_per_rev": 20, "diameter_mm": 65, "pid": (0.001, 0.003, 0.0)},
    {"name": "rear_left", "motor_channel": "lower_b",
     "encoder_a": 35, "motor_inverted": False,
     "counts_per_rev": 20, "diameter_mm": 65, "pid": (0.002, 0.005, 0.0)},
    {"name": "front_right", "motor_channel": "upper_b",
     "encoder_a": 36, "motor_inverted": True,
     "counts_per_rev": 20, "diameter_mm": 65, "pid": (0.002, 0.005, 0.0)},
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
    if not (0.05 <= TRACK_WIDTH_M <= 1 and SCAN_PERIOD_MS > 0 and SCAN_SETTLE_MS > 0 and SCAN_ANGLES
            and all(-90 <= a <= 90 for a in SCAN_ANGLES) and GUARD_PERIOD_MS > 0 and 0 < SCAN_MAX_CM <= 400):
        raise ValueError("Thong so quet/ban do khong hop le")
    if not (0 < RETURN_DRIVE_RPM + RETURN_STEER_RPM <= MAX_RPM and 0 < RETURN_TURN_RPM <= MAX_RPM
            and RETURN_DRIVE_RPM > RETURN_STEER_RPM >= 0 and RETURN_STOP_CM < RETURN_CLEAR_CM <= SCAN_MAX_CM
            and RETURN_MAX_AVOID > 0 and RETURN_TIMEOUT_S > 0):
        raise ValueError("Thong so quay ve khong hop le")
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
        for key in ('in1', 'in2', 'pwm', 'encoder_a'):
            pin = motor_pins[key] if key in ('in1', 'in2', 'pwm') else wheel[key]
            if type(pin) is not int or pin < 0 or pin in pins:
                raise ValueError(wheel['name'] + ': GPIO thieu, trung hoac khong hop le: ' + key)
            if key in ('in1', 'in2', 'pwm') and pin not in output_pins:
                raise ValueError(wheel['name'] + ': GPIO khong ho tro output tren ESP32 classic')
            if key == 'encoder_a' and pin not in ENCODER_PINS:
                raise ValueError(wheel['name'] + ': encoder_a phai theo ENCODER_PINS trong so do')
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
