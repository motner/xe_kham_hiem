# Xe ESP32: joystick web + PID tốc độ 4 bánh

MicroPython, không cần thư viện ngoài. Web server dùng `asyncio`, vòng PID chạy
trên ESP32 độc lập với tốc độ tải trang. Dự án điều khiển xe vi sai/skid-steer:
trái/phải quay với tốc độ khác nhau để rẽ. Không dành cho xe đánh lái bằng servo
nếu chưa thay phần phối trộn chuyển động.

**Cấu hình hiện tại `HARDWARE_ENABLED = True`: đã bật lại motor/encoder để kiểm tra xe sau bản sửa I/O và RAM.**
Motor khởi tạo ở trạng thái dừng; kê bánh và kiểm tra dây/nguồn trước khi thử.
Đặt `False` và nạp `config.py` khi cần thử web mà không khởi tạo GPIO.
PID trong `config.py` là hệ số khởi đầu, chưa hiệu chỉnh trên xe thật. Kê xe khỏi mặt đất khi kiểm tra lần đầu.

Đã điền chân hai L298N, vị trí encoder, đĩa 20 khe và bánh khoảng 60 mm theo thông tin của bạn. Xem [WIRING.md](docs/WIRING.md)
để đối chiếu bảng GPIO và xác định cặp động cơ–encoder trước khi bật phần cứng.

## Các file

```text
xe_esp32/
├── firmware/       # Chương trình MicroPython
│   ├── main.py
│   ├── ...         # Các module .py điều khiển xe, Wi-Fi và HTTP
│   └── web/
│       └── index.html  # Giao diện web (HTML, CSS, JavaScript)
├── tools/          # Script kiểm tra motor, encoder trên ESP32
├── tests/          # Kiểm thử trên máy tính
├── docs/           # Sơ đồ đấu dây và nhật ký bàn giao
└── README.md
```

Các module Python trong bảng dưới nằm trong `firmware/`, giao diện nằm trong
`firmware/web/`. Các script thử
phần cứng nằm trong `tools/`; tài liệu nằm trong `docs/`.

| File | Vai trò |
|---|---|
| `main.py` | Kiểm tra cấu hình, tạo thiết bị, kết nối Wi-Fi, chạy vòng điều khiển; tự chạy khi cấp nguồn |
| `config.py` | Wi-Fi, tài khoản đăng nhập, GPIO, thông số encoder/bánh/PID và giới hạn |
| `motor.py` | Class Motor: driver IN1 + IN2 + PWM, đầu ra có dấu -1…1 |
| `encoder.py` | Class Encoder: đếm cạnh lên A, tùy chọn B để xác định chiều, tính/lọc RPM |
| `pid.py` | PID theo dt thực, giới hạn công suất, chống tích phân quá mức |
| `wheel.py` | Ghép Motor + Encoder + PID; tăng tốc có giới hạn, chờ khi đảo chiều, phát hiện mất xung |
| `robot.py` | Phối hợp 4 bánh, một phiên điều khiển, chống lệnh cũ, hết hạn lệnh thì dừng |
| `wifi.py` | Kết nối AP hoặc STA bất đồng bộ |
| `web_server.py` | HTTP server bất đồng bộ, API lệnh/trạng thái |
| `http_transport.py` | Socket HTTP nonblocking, đóng kết nối lỗi và khôi phục socket lắng nghe khi lỗi I/O |
| `boot_info.py` | Mã lần khởi động và nguyên nhân reset để web nhận diện brownout/khởi động lại |
| `web_main.py` | Tên chạy cũ: gọi `main.main()`, không phải server độc lập nữa |
| `web/index.html` | Joystick cảm ứng/chuột, biểu đồ, bộ đếm, trạng thái và đăng nhập |
| `tests/` | Kiểm thử trên máy tính, không tải lên ESP32 |
| `tools/` | `test_wifi.py` thử web không khởi tạo motor/encoder; `test_motors.py`, `test_front_right.py`, `test_rear_left.py`, `check_encoders.py` thử phần cứng thủ công |
| `docs/` | [Đấu dây](docs/WIRING.md) và [nhật ký bàn giao](docs/SESSION_LOG.md) |

Luồng: joystick → API → Robot → RPM đặt mỗi Wheel → PID → PWM → motor.
Encoder phản hồi RPM về PID; web đọc bản trạng thái mỗi khoảng 1000 ms.
PID tốc độ giúp cân tốc độ bánh, không bảo đảm giữ hướng khi trượt bánh hay
đường kính bánh sai. Chưa có IMU/PID giữ góc hướng.

HTTP dùng socket nonblocking bên trong task để lỗi socket được xử lý tại
từng kết nối, tránh lỗi `EIO` thoát khỏi poller chung của MicroPython.
Trang HTML được đọc/gửi từng khối 1 KB, không giữ cả trang trong RAM.
Khi gặp EIO, xe dừng và hủy phiên điều khiển; web tiếp tục phục vụ kết nối
mới, không tự chạy lại. `main.py` cũng đóng motor ở lớp ngoài cùng nếu
vòng chạy bất đồng bộ thoát bất thường. Khi cập nhật bản này phải nạp thêm
`http_transport.py` cùng `web_server.py` và `main.py`.

## Nạp bằng Thonny

1. Chọn **MicroPython (ESP32)** và đúng cổng USB. Nhấn Ctrl+C để dừng code cũ.
2. Sao lưu `main.py` hiện có trên thiết bị nếu cần.
3. Trong **View → Files**, mở thư mục `firmware/` trên máy tính, chọn toàn bộ
   các file `.py` bên trong, rồi **Upload to /** ở thiết bị.
   Tải thêm thư mục `firmware/web/` thành `/web/` trên ESP32. Nếu tải từng file,
   tạo thư mục `/web` trên thiết bị rồi tải `index.html` vào đó.
   Tải các file Python trực tiếp vào `/`, không tải nguyên thư mục `firmware/`.
   Không tải `tests/`, `docs/` hoặc `__pycache__/`.
   Các script trong `tools/` chỉ tải thêm vào `/` khi cần kiểm tra phần cứng.
4. Cấu hình hiện bật phần cứng bằng `HARDWARE_ENABLED=True`; kê bánh trước khi thử. Khởi động lại ESP32,
   hoặc mở `/main.py` trên thiết bị và F5. Sau khi sửa module/cấu hình, khởi động
   lại để tránh dùng module cũ trong bộ nhớ.
5. Xem IP trong Shell. Mặc định AP: Wi-Fi **ESP32-Web**, mật khẩu **12345678**,
   IP thường `http://192.168.4.1`. Chọn giữ kết nối nếu máy báo không có Internet.
6. Để dùng Wi-Fi nhà, sửa `WIFI_MODE="STA"`, `WIFI_SSID`, `WIFI_PASSWORD`, tải
   lại `config.py`. Máy tính/điện thoại phải truy cập được IP nội bộ của ESP32.
7. Chọn **Mô phỏng giao diện** để thử mà không kích hoạt động cơ. Mở HTML trực
   tiếp trên máy tính cũng tự chọn mô phỏng.

Theo lựa chọn hiện tại, xe giữ `WIFI_MODE="AP"`, tên `ESP32-Web`, IP
`192.168.4.1`. `AP_CHANNEL=11` được chọn sau khi quét các mạng lân cận ngày
28/10/2026; có thể chọn lại kênh 1–11 khi môi trường thay đổi. Khi sửa kênh,
cần nạp cả `config.py` và `wifi.py` nếu thiết bị còn dùng bản chưa hỗ trợ
`AP_CHANNEL`. Mạng xe không cung cấp Internet; giữ máy điều khiển kết nối
`ESP32-Web` trong lúc lái. Nếu bị ngắt, thử tắt camera và đặt xe cách máy tính
0,5–1 m để phân biệt tải video/khoảng cách với lỗi phần mềm hoặc nguồn.

Chế độ thử hiện tại đặt `STOP_ALL_ON_ENCODER_STALL=False` trong `config.py`:
bánh báo `encoder_or_stall` tự dừng và giữ lỗi, các bánh khác vẫn nhận lệnh
và cập nhật PID. Web hiển thị chế độ thử và tên bánh lỗi. Chỉ thử khi bốn bánh
được kê khỏi mặt đất. Mất lệnh 700 ms, nút DỪNG, lỗi vòng điều khiển và lỗi
khác vẫn dừng toàn xe. Để khôi phục dừng toàn xe khi encoder/stall lỗi, đặt
`STOP_ALL_ON_ENCODER_STALL=True`, nạp lại `config.py` rồi khởi động lại.

Các tên như `config.py`, `main.py` trong hướng dẫn chạy chỉ file trên ESP32;
bản nguồn tương ứng trên máy tính là `firmware/config.py`, `firmware/main.py`.
Sau khi sửa file trên máy tính, cần tải lại file đó lên thiết bị.
Chỉ nhấn F5 một file không tự tải các module còn lại lên ESP32.
`boot.py` hiện có có thể giữ nguyên nếu không khởi chạy phần điều khiển cũ.

Đường dẫn cần có trên ESP32 là `/main.py`, `/config.py`, các module `.py` khác
và `/web/index.html`. Khi cập nhật từ cấu trúc cũ, cần nạp lại cả `main.py` và
thư mục `web/` để đường dẫn giao diện khớp nhau.

## Cảnh báo sụt nguồn trên web

Khi ESP32 reset và kết nối lại, web đọc nguyên nhân reset ngay cả khi phiên
đăng nhập đã mất. Brownout được xác nhận sẽ hiện khung đỏ **Đã ghi nhận sụt
nguồn ESP32**, giữ tới khi nhấn **Đã đọc**, kể cả tải lại trang trong cùng tab.
Reset/cấp nguồn lại chưa đủ bằng chứng sẽ có thông báo riêng, không gán thành
brownout. Xe không tự chạy lại; đăng nhập và thao tác joystick mới để chạy.
Trong lúc bo mất nguồn hoặc chưa kết nối lại, web chỉ có thể báo mất phản hồi.
Mất điện hoàn toàn hoặc reset thêm trước khi web kết nối lại có thể làm mất
nguyên nhân brownout trước đó. Bộ chẩn đoán không đo điện áp pin theo thời gian
thực. Khi cập nhật, nạp thêm `/boot_info.py` cùng `/main.py`, `/web_server.py`
và `/web/index.html`.

## Xem camera iPhone khi lái xe

1. Trên iPhone, mở SimpleIPCamera, kết nối Wi-Fi `ESP32-Web` và nhấn
   **Start Server**. Cho phép Camera và Mạng cục bộ nếu được hỏi; giữ app mở.
2. Máy tính hoặc điện thoại thứ hai cũng kết nối `ESP32-Web`, mở
   `http://192.168.4.1`, đăng nhập để vào bảng điều khiển.
3. Trong khung **Camera iPhone**, kiểm tra địa chỉ rồi bấm **Bật camera**.
   Địa chỉ hiện tại theo app là `http://192.168.4.2:8080/stream.mjpg`.
   Nếu IP của iPhone thay đổi, nhập lại đúng địa chỉ app hiển thị.
4. **Tắt camera** ngắt luồng hình; thao tác này không thay nút **DỪNG** xe.
   Bật camera không gửi lệnh quay motor. Camera được tắt trong mô phỏng.

Trình duyệt lấy video trực tiếp từ iPhone; ESP32 phục vụ giao diện và điều khiển
xe. Mất hình camera không tự dừng xe. Sau khi cập nhật
`firmware/web/index.html` lên `/web/index.html`, khởi động lại ESP32 và tải lại
trang để giao diện mới được đọc vào bộ nhớ.

## Cấu hình phần cứng trước khi bật

Bản này hỗ trợ mỗi động cơ có **một kênh driver IN1/IN2/PWM độc lập**, ví dụ
kiểu điều khiển L298N. Các driver có STBY/EN chung hoặc giao thức khác cần
bổ sung xử lý phù hợp trước khi dùng. Không tự suy đoán chân hay kích hoạt STBY.

Điền 4 phần tử `WHEELS` theo thứ tự bài test: `front_left`, `rear_right`,
`rear_left`, `front_right`. Robot xác định bên trái/phải theo tên bánh, không theo vị trí trong danh sách. Cho mỗi bánh:

- `motor_channel`: chọn một trong `upper_a`, `upper_b`, `lower_a`, `lower_b`.
  GPIO IN1/IN2/PWM đã lưu trong `MOTOR_CHANNELS` theo ảnh; phải chọn đúng vị trí bánh.
- `encoder_a`: GPIO đầu ra xung A. `encoder_b`: GPIO B hoặc `None` nếu một kênh.
- `motor_inverted`: đảo chiều sao cho lệnh dương đưa xe tiến.
- `encoder_inverted`: đảo dấu encoder A/B nếu cần; một kênh không xác định chiều.
- `counts_per_rev`: số **cạnh lên A / một vòng bánh sau hộp số**. Code dùng 1x,
  không nhân 4 như giải mã quadrature 4x. Đã biết xung/vòng motor thì cần tính tỉ số truyền.
- `diameter_mm`: đường kính thực tế của từng bánh.
- `pid`: bộ `(Kp, Ki, Kd)`, sai số RPM, dt giây, đầu ra PWM chuẩn hóa. Cấu hình
  hiện dùng `(0.008, 0.003, 0.0)` làm giá trị khởi đầu; cần quan sát và hiệu chỉnh trên xe.

`config.validate_hardware()` kiểm tra giá trị thiếu, GPIO trùng và các giới hạn
trước khi tạo bất kỳ motor nào. Nó **không** xác nhận GPIO đó có tồn tại, hỗ trợ
output/PWM, hay an toàn cho quá trình boot trên biến thể bo của bạn; cần đối chiếu
pinout ESP32 cụ thể. Các ngõ vào chỉ-input không dùng cho chân điều khiển motor.
Encoder dùng `Pin.IN` không pull nội; cần điện trở ngoài nếu cảm biến yêu cầu.
Tín hiệu đưa vào ESP32 phải phù hợp mức logic 3.3 V; các mạch dùng chung GND.

Tài khoản đăng nhập được đặt bằng `LOGIN_USERNAME` và `LOGIN_PASSWORD`
trong `firmware/config.py`. ESP32 kiểm tra thông tin, cấp phiên đăng nhập riêng
cho mỗi tab và yêu cầu phiên hợp lệ khi đọc trạng thái hoặc gửi lệnh.
Mật khẩu không được nhúng vào HTML hay lưu trong trình duyệt; mã phiên được
lưu trong `sessionStorage` để tải lại trang trong cùng tab không phải đăng nhập
lại. Phiên đăng nhập không tự hết hạn theo thời gian; đăng xuất hoặc khởi động
lại ESP32 sẽ thu hồi phiên. Để giới hạn RAM, ESP32 giữ tối đa 4 phiên; nếu đăng
nhập thêm, phiên ít dùng nhất không đang giữ xe sẽ được thay thế.
Bấm **Đăng xuất** để thu hồi phiên; nếu đang giữ quyền điều khiển thì xe dừng.
HTTP nội bộ không mã hóa thông tin đăng nhập; nếu đưa ra Internet cần HTTPS.

`HARDWARE_ENABLED` hiện đã bật để chạy web điều khiển. Mở IP của ESP32,
đăng nhập bằng tài khoản đã đặt trong `config.py`, rồi dùng joystick trực tiếp.
Ban đầu kiểm tra khi bánh được kê khỏi mặt đất và có cách ngắt nguồn động cơ.

## Điều khiển thật

- Mở web qua IP ESP32, nhập tên đăng nhập và mật khẩu để vào bảng điều khiển.
- Nếu cấu hình hợp lệ, joystick sẵn sàng ngay sau khi đăng nhập; không có nút mở điều khiển. Đăng nhập chưa cấp lệnh quay motor.
- Lần kéo joystick đầu tiên tự lấy quyền điều khiển, chỉ một trình duyệt giữ xe
  tại một thời điểm. Khi đang kéo, heartbeat gửi 150 ms/lần;
  các tab khác vẫn có thể xem trạng thái/camera.
- Giữ và kéo joystick: lên/xuống = tiến/lùi, ngang = quay tại chỗ, chéo = phối hợp rẽ.
  Vùng chết 10%; càng xa tâm càng gần giới hạn RPM đã đặt.
- Thả joystick hoặc đưa về vùng chết: gửi lệnh dừng và trả quyền ngay,
  dừng gửi heartbeat điều khiển khi đứng yên. Nút DỪNG/phím cách,
  mất tiêu điểm/ẩn trang cũng trả quyền và dừng xe. Kéo joystick lại để
  lấy phiên mới; không tự chạy lại khi joystick đang ở tâm.
- Gói lệnh có số thứ tự, phiên hết hạn không nhận lại lệnh cũ. Chỉ lệnh điều khiển
  hợp lệ gia hạn thời gian; xem `/api/status` không giữ xe chạy.
- Quá `COMMAND_TIMEOUT_MS=700` ms không có lệnh hợp lệ: tự dừng trên ESP32.
- `MAX_DUTY=1.0` cho phép PWM tối đa 100% trên cả bốn bánh. `MAX_RPM=120` là giới hạn tốc độ
  yêu cầu, chưa được xác nhận là tốc độ đạt được của xe.

Đường kính/xung-vòng ở web chỉ chỉnh được trong mô phỏng. Trong chế độ thật,
web hiện thông số bánh trước trái; thay đổi cấu hình thực bằng `config.py`.
RPM hiển thị là độ lớn; `signed_rpm` trong API chỉ có khi encoder có B.
Quãng đường là trung bình độ dài bánh đã quay, không phải độ dịch chuyển xe.
Không dùng số liệu này để khẳng định xe đang đi thẳng hoặc định vị chính xác.

## PID, chu kỳ và lỗi

Vòng điều khiển mặc định 50 ms, encoder cập nhật mỗi 100 ms, lọc bậc một với
hằng số thời gian 0.10 s. PID dùng dt đo thực và giá trị tốc độ mới nhất; chu kỳ
PID nhanh hơn cửa sổ encoder không tạo thêm thông tin đo. Với encoder ít xung,
ở tốc độ thấp cần kéo dài cửa sổ đo hoặc thay cách ước lượng bằng thời gian giữa xung.
Ví dụ 20 xung/vòng và cửa sổ 100 ms: mỗi xung tương ứng 30 RPM, khá thô.

PID điều khiển độ lớn tốc độ; chiều motor được áp dụng riêng. Tích phân chỉ tăng
khi không đẩy đầu ra sâu hơn vào bão hòa; reset khi dừng. Khi đổi dấu tốc độ,
PWM về 0, chờ ít nhất 400 ms và RPM đo giảm dưới ngưỡng 5 trước khi đảo chiều.
Không có phanh chủ động/giữ vị trí: dừng hiện tại đưa PWM về 0, xe có thể trôi theo quán tính.

Các lỗi giữ trạng thái dừng đến khi sửa nguyên nhân và khởi động lại:

- `encoder_or_stall:<bánh>`: đủ công suất (`STALL_MIN_DUTY`) nhưng lâu không có xung.
- `control_loop_late`: khoảng chạy vòng điều khiển vượt `MAX_LOOP_GAP_MS=250` ms.
- `control_exception`: lỗi trong vòng đọc encoder/điều khiển.

Đây là cơ chế phần mềm, không thay thế ngắt nguồn động cơ. `asyncio` trên MicroPython
không phải điều khiển thời gian thực cứng: nếu interpreter treo hoàn toàn thì vòng
kiểm tra timeout cũng không chạy. Encoder tần số cao có thể cần bộ đếm phần cứng
hoặc triển khai ESP-IDF/C++ tùy tốc độ thực tế; cần kiểm tra mất xung trên xe.

Để hiệu chỉnh, bắt đầu một bánh/tốc độ thấp, lấy đồ thị RPM đặt/đo, chọn P trước,
thêm I để giảm sai số ổn định, chỉ thêm D nếu dữ liệu đo đủ sạch. Bản này chưa có
màn hình hiệu chỉnh từng bánh; có thể gọi Wheel trong bài thử riêng trên bàn.
Không tăng hệ số PID để bù lỗi chân, cực tính hoặc counts_per_rev sai.

## API

`GET /` và `/api/ping` công khai. `POST /api/login` nhận JSON
`{"username":"...","password":"..."}`, trả mã `token` cùng tên đăng nhập.
`GET /api/status` và các POST còn lại cần header `Authorization: Bearer <token>`.
Các POST cần `Content-Type: application/json`. Các mã phiên đăng nhập và phiên
điều khiển motor độc lập; chỉ phiên đăng nhập đang giữ quyền điều khiển mới gửi
lệnh cho phiên motor đó được.

```text
POST /api/logout    {} → thu hồi phiên đăng nhập, dừng xe nếu đang điều khiển
POST /api/arm       {} → {"session":"..."} (giao diện tự gọi khi bắt đầu kéo joystick)
POST /api/control   {"session":"...","sequence":1,"throttle":0.4,"steering":0.1,"max_rpm":80}
POST /api/stop      {"session":"..."} → hủy phiên tương ứng, dừng xe
```

`throttle` và `steering` nằm trong [-1,1]; `max_rpm` trong [0,MAX_RPM].
Sequence tăng dần trong một phiên; dừng với token phiên cũ không hủy phiên mới.
Không mở CORS và không nhận lệnh GET. HTTP request được giới hạn header/body,
thời gian đọc/ghi và số kết nối đồng thời để giảm tải RAM.

## Kiểm thử trên máy tính

```bash
cd /home/sang/xe_esp32
python3 -m unittest discover -s tests -v
node tests/test_joystick.cjs
```

Các test dùng phần cứng giả và mô hình động cơ đơn giản; không xác nhận chân,
hiệu năng thời gian thực, độ ổn định PID hay khả năng giữ hướng trên xe thật.

Tài liệu: [MicroPython asyncio](https://docs.micropython.org/en/latest/library/asyncio.html),
[Pin](https://docs.micropython.org/en/latest/library/machine.Pin.html),
[PWM](https://docs.micropython.org/en/latest/library/machine.PWM.html).

## Thử từng động cơ thật bằng Thonny

`tools/test_motors.py` là bài thử PWM thủ công, độc lập với PID và
`HARDWARE_ENABLED`. Không đặt file này thành `main.py`.

1. Kê các bánh khỏi mặt đất, chuẩn bị ngắt nguồn động cơ.
2. Dừng chương trình cũ bằng Ctrl+C. Nạp `tools/test_motors.py` cùng
   `firmware/motor.py`, `firmware/encoder.py`, `firmware/config.py` vào `/`
   trên ESP32; trên thiết bị các file có tên `test_motors.py`, `motor.py`,
   `encoder.py`, `config.py`.
3. F5 `test_motors.py`, nhập `TEST` vào Shell khi đã sẵn sàng.
4. Nhập `1`, `2`, `3`, `4` theo thứ tự đã xác nhận: trước trái, sau phải, sau trái, trước phải.
   Mỗi lệnh chỉ chạy một motor ở PWM 100% trong 1 giây, tự ngắt rồi chờ 1.5 giây.
   Nhập số âm để thử chiều lùi; `q` hoặc Ctrl+C để kết thúc.
5. Ghi lại bánh thực sự quay, chiều quay, số xung cả 4 encoder. Chỉ có xung đúng
   kênh chưa chứng minh vị trí/chiều đúng; encoder một kênh không đo được chiều.

Nếu motor chưa quay ở 100% PWM, không kết luận dây sai:
kiểm tra nguồn, tải, jumper ENA/ENB và driver. Script tắt Wi-Fi khi thử encoder,
không cung cấp điều khiển web đồng thời. Đây không phải kết quả thử thật: cần
chạy trên bo mạch để có số đo.
