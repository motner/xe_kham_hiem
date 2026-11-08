# GPIO theo ảnh sơ đồ của bạn

Nguồn: ảnh gửi ngày 12/10/2026. Link Canva không đọc được trong phiên này;
đối chiếu trực tiếp các nhãn GPIO trong ảnh. Bo trong ảnh là ESP32-WROOM.

Trong dự án trên máy tính, các module nằm trong `firmware/`, script kiểm tra
nằm trong `tools/`. Khi nạp bằng Thonny, tải các file cần dùng trực tiếp vào
`/` trên ESP32; các tên file bên dưới là tên sau khi nạp lên thiết bị.

## Hai module L298N

Theo sơ đồ mới nhất bạn gửi: **module nằm phía trên ESP32 điều khiển hai bánh
trước; module nằm phía dưới ESP32 điều khiển hai bánh sau**. Bài test thực tế
xác nhận trên module sau: kênh A chạy bánh sau phải, kênh B chạy bánh sau trái.
Kênh A dùng IN1/IN2/ENA; kênh B dùng IN3/IN4/ENB. Trong class Motor,
cặp IN3/IN4 của kênh B được đưa vào tham số in1/in2 của đối tượng tương ứng.

| Kênh trong config | Chân chiều 1 | Chân chiều 2 | Chân PWM |
|---|---|---|---|
| `upper_a` | IN1 → GPIO27 | IN2 → GPIO26 | ENA → GPIO14 |
| `upper_b` | IN3 → GPIO25 | IN4 → GPIO33 | ENB → GPIO32 |
| `lower_a` | IN1 → GPIO17 | IN2 → GPIO16 | ENA → GPIO22 |
| `lower_b` | IN3 → GPIO4 | IN4 → GPIO21 | ENB → GPIO19 |

Đã điền các chân này vào `MOTOR_CHANNELS` trong `config.py`.
Nếu module đang gắn jumper **ENA/ENB** kéo enable lên mức cao, tháo jumper đó
để ESP32 điều khiển PWM đúng các chân ENA/ENB. Đây **không phải** jumper `5V-EN`
của bộ ổn áp; cấu hình nguồn 5 V phụ thuộc module thực tế.

## Encoder quang một kênh

Các module trong ảnh có OUT, VCC, GND, không phải encoder A/B hai kênh.

| Encoder nhìn từ trái sang phải trong ảnh | OUT |
|---|---|
| 1 | GPIO35 |
| 2 | GPIO34 |
| 3 | GPIO39 |
| 4 | GPIO36 |

VCC nối 3V3, GND nối GND chung như ảnh. Encoder một kênh, không có kênh B (cấu hình chỉ có `encoder_a`).
GPIO34–39 chỉ làm input, không có pull-up/pull-down nội: nếu OUT cần pull-up,
phải dùng pull-up ngoài về 3.3 V hoặc điện trở đã có trên module.

Theo Espressif, cần tránh IRQ36/39 khi dùng ADC hoặc Wi-Fi/Bluetooth với sleep.
Bản này không đọc ADC, không bật Bluetooth hay gọi lightsleep/deepsleep; ở chế độ
STA, `wifi.py` đặt `pm=PM_NONE` trước khi kết nối. AP không dùng chế độ tiết kiệm
điện của station. Nếu firmware không hỗ trợ tắt power-save mà bật phần cứng,
chương trình dừng khởi tạo để bạn cập nhật firmware.

## Servo và HC-SR04

| Thiết bị | Chân tín hiệu |
|---|---|
| Servo | S → GPIO23 |
| HC-SR04 | TRIG → GPIO13 |
| HC-SR04 | ECHO → GPIO18 qua cầu chia áp |

Các chân được khai báo và dành riêng trong config, chưa kích hoạt servo hoặc
thêm chức năng đo khoảng cách/tránh vật cản. Không đưa phép đo chờ Echo vào
vòng PID vì có thể làm trễ vòng điều khiển.

Ảnh thể hiện Echo qua 1 kΩ tới nút GPIO18, từ nút đó qua hai điện trở 1 kΩ
nối tiếp xuống GND: tỷ lệ 2/(1+2), 5 V xuống xấp xỉ 3.33 V.
Phải giữ cầu chia áp, không nối Echo 5 V trực tiếp vào ESP32.
Servo và HC-SR04 dùng nguồn 5 V bên ngoài như sơ đồ, nối chung GND với ESP32 và driver.
Code không xác nhận điện áp thực tế, jumper ổn áp L298N hay cách cấp nguồn cho
chính ESP32: cần kiểm tra trên phần cứng. Sơ đồ này không áp dụng nguyên xi cho
ESP32-WROVER dùng GPIO16/17 cho PSRAM hoặc các biến thể ESP32 khác.

## Vị trí encoder đã được bạn xác nhận

| Bánh | GPIO encoder |
|---|---|
| Trước trái (`front_left`) | 39 |
| Trước phải (`front_right`) | 36 |
| Sau trái (`rear_left`) | 35 |
| Sau phải (`rear_right`) | 34 |

Đã điền `encoder_a` theo bảng này trong `WHEELS`. `ENCODER_PINS` và
`check_encoders.py` dùng cùng thứ tự bánh `(39, 34, 35, 36)` để kết quả chẩn đoán
không bị nhầm với thứ tự dây đi từ trái sang phải trên sơ đồ.

## Ghép động cơ–encoder đã xác nhận

| Bánh | Kênh L298N | Chân chiều | PWM | Encoder |
|---|---|---|---|---|
| Trước trái | `upper_a` | 27, 26 | 14 | 39 |
| Trước phải | `upper_b` | 25, 33 | 32 | 36 |
| Sau trái | `lower_b` | 4, 21 | 19 | 35 |
| Sau phải | `lower_a` | 17, 16 | 22 | 34 |

Đã điền `motor_channel` và `encoder_a` vào từng bánh trong `config.py`.
`motor_inverted=True` cho trước trái và trước phải, `False` cho hai bánh sau.
Cấu hình dùng chung cho `test_motors.py` và chương trình PID. Ngày 28/10/2026,
đã thử riêng cả bốn bánh qua USB với xe kê cao, PWM 100% trong 1 giây mỗi bánh;
người dùng xác nhận từng lượt quay đúng bánh, đúng chiều tiến. Xung encoder
đúng kênh lần lượt FL=147, RR=170, RL=146, FR=134 (gồm thời gian bánh trôi
sau khi tắt PWM, không dùng để suy ra RPM ổn định).
Thử PID cả bốn bánh ở 80 RPM có bật Wi-Fi trong khoảng 3 giây không báo lỗi;
sau khi khôi phục web, người dùng xác nhận kéo hết joystick tiến 2–3 giây ở
80 RPM thì cả bốn bánh quay, không báo lỗi. Chưa xác nhận chạy có tải trên sàn
hoặc cân chỉnh PID để tốc độ ổn định.
Không đổi encoder sang bánh khác để sửa chiều quay.

Cách kiểm tra lại trên phần cứng:

1. Theo dây OUT1/OUT2 (kênh A) và OUT3/OUT4 (kênh B) của từng L298N để biết bánh.
2. Trong Thonny dừng `main.py`, tải `check_encoders.py`, `config.py`, `encoder.py`
   lên ESP32 rồi F5 `check_encoders.py`. Script khóa EN, tắt Wi-Fi, không chạy motor.
3. Xoay bằng tay từng bánh; script in rõ tên bánh và GPIO theo thứ tự FL, RR, RL, FR.
4. Đối chiếu bảng ghép động cơ–encoder đã xác nhận; chỉ sửa WHEELS nếu dây thực tế khác bảng.
5. Đếm xung qua nhiều vòng bánh rồi chia số vòng để tìm `counts_per_rev`;
   đo đường kính bánh và hiệu chỉnh PID. Khởi động lại để chạy web sau bài thử.

Chưa điền PID và tài khoản đăng nhập trong config thì giữ
`HARDWARE_ENABLED=False`. Mặc định web và mô phỏng vẫn sử dụng được.

Tài liệu: [ESP32 GPIO](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/gpio.html),
[MicroPython WLAN PM_NONE](https://docs.micropython.org/en/latest/library/network.WLAN.html),
[L298](https://www.st.com/en/motor-drivers/l298.html).

## Thông số đĩa và bánh theo sản phẩm đã gửi

- Đĩa encoder: **20 khe**, người dùng xác nhận. Code đếm cạnh lên (1x),
  cấu hình `counts_per_rev=20` cho cả bốn bánh với giả định đĩa quay 1:1 với bánh.
  Nếu đĩa nằm trước hộp số thì phải nhân số xung với tỉ số truyền tương ứng.
- Đường kính bánh: **khoảng 6 cm** theo mô tả sản phẩm, điền `diameter_mm=60`.
  Cần đo lại đường kính bánh thật khi hiệu chỉnh tốc độ dài/quãng đường.
- Kiểm chứng bằng `check_encoders.py`: xoay một bánh 10 vòng, bộ đếm tương ứng
  tăng khoảng 200 xung. Bài thử không cấp công suất động cơ.
- Với 20 xung/vòng, cửa sổ đo hiện tại 100 ms có bước lượng tử 30 RPM.
  Số đo tốc độ thấp sẽ thô; cần đánh giá lọc/cửa sổ đo hoặc đo chu kỳ xung khi
  hiệu chỉnh PID. Chưa bật phần cứng và chưa tự gán hệ số PID từ thông số sản phẩm.
