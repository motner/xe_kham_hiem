# Nhật ký bàn giao dự án xe ESP32

Cập nhật: 2026-10-29 tối (Asia/Ho_Chi_Minh)

File này ghi lại bối cảnh để một phiên Codex/tài khoản khác có thể tiếp tục dự án. Hãy đọc file này cùng [README.md](../README.md), [WIRING.md](WIRING.md) và [config.py](../firmware/config.py) trước khi sửa code.

**Đọc trước:** mục “Trạng thái hiện tại và điều chưa xong” là bản bàn giao
hiện hành. Các mục lịch sử lưu trạng thái ở từng thời điểm, có những câu
“đang chạy/chờ kết quả/False” đã hết hiệu lực; không dùng chúng để suy ra
trạng thái hiện tại. Lần cập nhật này chỉ bổ sung tài liệu/kết quả, không
sửa firmware, nạp lại, mở USB hoặc gửi lệnh điều khiển.

## Mục tiêu

Làm xe 4 bánh dùng ESP32-WROOM và MicroPython, có thể điều khiển bằng joystick trên web, đọc encoder và dùng PID để cân tốc độ các bánh. Đây là xe kiểu skid-steer: rẽ bằng cách đặt tốc độ hai bên khác nhau. PID tốc độ bánh không tự đảm bảo xe đi thẳng khi trượt bánh; chưa có IMU để giữ hướng.

## Cấu trúc dự án hiện tại

- `firmware/main.py`: điểm khởi chạy, kiểm tra cấu hình, khởi tạo xe và web.
- `firmware/config.py`: Wi-Fi, GPIO, thông số encoder/bánh, PID và giới hạn an toàn.
- `firmware/motor.py`, `encoder.py`, `pid.py`, `wheel.py`, `robot.py`: các lớp điều khiển phần cứng và logic xe trong `firmware/`.
- `firmware/wifi.py`, `web_server.py`, `web_main.py`: Wi-Fi và HTTP API trong `firmware/`.
- `firmware/http_transport.py`: socket HTTP nonblocking, xử lý lỗi I/O và đóng listener/client; module mới này phải có trên ESP32.
- `firmware/boot_info.py`: nhận diện lần khởi động, nguyên nhân reset/brownout.
- `firmware/web/index.html`: giao diện joystick, gồm HTML, CSS và JavaScript.
- `tools/test_motors.py`: bài thử PWM thủ công từng bánh, không dùng PID.
- `tools/check_encoders.py`: bài kiểm tra encoder bằng cách xoay bánh bằng tay.
- `tools/test_front_right.py`, `tools/test_rear_left.py`: bài thử riêng từng động cơ.
- `docs/WIRING.md`: bảng chân và ghi chú nối dây.
- `docs/SESSION_LOG.md`: nhật ký bàn giao này.
- `tests/`: kiểm thử trên máy tính; không nạp thư mục này lên ESP32.

Khi dùng Thonny, tải **các file `.py` bên trong `firmware/`** trực tiếp vào `/`
trên ESP32 và thư mục `firmware/web/` thành `/web/`, rồi chạy `/main.py`.
Khi cập nhật từ cấu trúc cũ, nạp lại `main.py` cùng `/web/index.html`.
Khi cần kiểm tra, tải thêm script tương ứng
trong `tools/` vào `/`. Các tên file không kèm thư mục trong hướng dẫn thao tác
và lịch sử bên dưới là tên trên thiết bị hoặc tên trước khi sắp xếp lại.

## Sơ đồ và thông tin người dùng đã xác nhận

- Module L298N phía trên điều khiển hai bánh trước; module phía dưới điều khiển hai bánh sau.
- Kênh A bên trái, kênh B bên phải theo hướng nhìn trong sơ đồ của người dùng.
- Động cơ: trước trái `upper_a` (IN1=GPIO27, IN2=GPIO26, ENA/PWM=GPIO14); trước phải `upper_b` (IN3=GPIO25, IN4=GPIO33, ENB/PWM=GPIO32); sau phải `lower_a` (IN1=GPIO17, IN2=GPIO16, ENA/PWM=GPIO22); sau trái `lower_b` (IN3=GPIO4, IN4=GPIO21, ENB/PWM=GPIO19), theo kết quả test người dùng mới nhất.
- Encoder OUT một kênh: trước trái GPIO39, trước phải GPIO36, sau trái GPIO35, sau phải GPIO34. Cấu hình/test hiện dùng thứ tự FL, RR, RL, FR theo kết quả test người dùng; danh sách chân theo thứ tự này là `(39, 34, 35, 36)`. GPIO34–39 là input-only, không có pull-up nội trên ESP32 cổ điển; cần mức logic 3.3 V và mạch kéo ngoài phù hợp.
- Servo GPIO23; HC-SR04 TRIG GPIO13, ECHO GPIO18 qua cầu chia áp. Nối chung GND giữa ESP32, driver và nguồn ngoài.
- Đĩa encoder được người dùng xác nhận 20 khe; cấu hình hiện đếm cạnh lên (1x), giả định 20 xung/vòng bánh nếu đĩa quay trực tiếp 1:1 với bánh. Bánh khoảng 60 mm theo ảnh mô tả sản phẩm; cần đo lại.

## Trạng thái hiện tại và điều chưa xong

- **8/11 01:05 — sau khi chuyển servo sang 5V của L298N: quét bật + hỏi web 0 reset trong 150 giây** (trước khi đổi 11 và 15 reset), web 295 lần được, 5 lần lỗi; cắm USB, không lệnh motor, mới đo một lần. Lần khởi động trước bài đo vẫn ghi `brownout` (01:02:19), chưa rõ thời điểm gây ra. HC-SR04 có tín hiệu, điểm quét đọc được. Chưa thử khi motor quay, chưa thử không USB.

- **8/11 00:57 — theo yêu cầu người dùng, đã bỏ tự quay về và né vật cản, giữ vẽ bản đồ; đã nạp lên bo, chưa commit.** Xóa `navigator.py`, `docs/TEST_QUAY_VE.md`, lộ trình `Route`, `/api/return` (giờ trả 404), nút Quay về và mô phỏng né; các thông số `RETURN_*`. `tests/test_navigator.py` đổi thành `tests/test_map.py`. Bản đồ vẫn dùng encoder cho đường đi và scanner cho điểm vật cản. 85 test Python và test JS đạt; test `test_avoids_with_low_floor_inertia` không còn vì tính năng đã bỏ. Quét bật + hỏi web trên firmware mới: vẫn 11 reset brownout trong 150 giây khi chưa đổi nguồn servo. Người dùng định lấy 5V từ chân ra của L298N cho servo, dây nâu về GND L298N (phải chung GND với ESP32); chưa thử. Bộ ổn áp của L298N yếu và cần áp pin đủ cao, nên servo có thể rung khi motor làm tụt pin.

- **8/11 00:48 — tách được yếu tố gây brownout, chưa sửa: scanner (servo + HC-SR04) cộng với Wi-Fi đang gửi.** Không lệnh motor, cắm USB, cùng dây, hỏi `/api/ping` 2 lần/giây: chạy bình thường 15 reset trong 150 giây, log ROM `SW_RESET` kèm dòng Brownout; `SCANNER_ENABLED = False` 0 reset trong 150 giây. Chạy bình thường không có truy cập web trước đó 0 reset trong 110 giây, nên cần cả hai. Mỗi cấu hình chỉ đo một lần; chưa tách servo với HC-SR04 (nghi servo vì kéo dòng lớn hơn); chưa đo điện áp; không biết người dùng đã rút những dây nào. Bài chỉ Wi-Fi tắt bị ngắt do cổng USB mất kết nối, không có kết quả. Firmware và `config.py` chưa đổi vì việc này.

- **8/11 00:30 — lại brownout khi đang cắm USB** (`raw 3`, reset khoảng 10 giây trước khi đọc), 25 giây sau đó không reset thêm. Tổng hợp: báo brownout thường ngay khi bật Wi-Fi; khoảng 20 phút đo tắt Wi-Fi chỉ có một lần board dừng chưa rõ lý do; chưa đo điện áp. Nghi nguồn cấp cho ESP32 không đủ khi Wi-Fi phát (cáp, cổng USB, tải trên VIN và 3V3, tiếp xúc breadboard). Thử tiếp: chỉ ESP32 với USB rồi gắn lại từng tải. Không tắt bộ phát hiện brownout.

- **8/11 — người dùng đo khoảng cách giữa 2 bánh là 10,5 cm (giữa bánh trái và phải; chưa rõ tâm-tâm hay mép).** Chưa đổi `TRACK_WIDTH_M` = 0,16: đây là giá trị hiệu dụng của xe skid-steer, thường lớn hơn số đo thước vì bánh trượt khi xoay; đặt 0,105 sẽ làm xe tưởng xoay nhiều hơn và dừng sớm hơn. Vẫn phải hiệu chỉnh trên sàn bằng bài xoay 720°.

- **8/11 rạng sáng — thay dây 2 bánh trước, đo lại FR và FL, đã nạp bộ mới lên bo; MỘT TEST ĐANG TRƯỢT, chưa commit.** Thông số trên xe: FR `(0.002, 0.005)`, RR `(0.002, 0.005)` (trước `(0.001, 0.003)`), FL `(0.0022, 0.005)`, RL `(0.002, 0.005)`. Theo luật chọn riêng: FR giữ bộ hiện tại 6/8 (K 408, τ 0,14, θ 0,08), FL giữ 8/8 (K 817, τ 0,39, θ 0,30). Bộ nạp KHÔNG theo luật riêng từng bánh mà theo lệch trái phải khi 4 bánh cùng chạy, 8 lượt mỗi cấu hình, không kẹt: bộ riêng lẻ lệch trung bình 5,9% (bỏ lượt nhiễu), bộ đang nạp 1,8%, SIMC ×2 cả 4 bánh 5,0% theo chiều ngược. Trong bộ đang nạp, FR vẫn kém khoảng 18 xung/10 giây so với ba bánh kia; một lượt −80 RPM RL chỉ 69 RPM, duty SD 0,084. RR chưa chạy riêng đủ 8 lượt với bộ này.
  - **`test_avoids_with_low_floor_inertia` trượt từ khi đổi RR** (`return_blocked`), không sửa test. Dãy kết quả theo RR không đơn điệu. Mô phỏng 25 vị trí vật cản: τ 0,12 về đích 18/25 so với 24/25 ở bộ cũ; τ 0,3 (gần số đo) 23/25 so với 24/25. Vật cản ≤ 0,1 m: τ 0,12 3 so với 2, τ 0,3 3 so với 5. Bản nạp lên bo đã chạy trước khi xem xong kết quả test. Quay về thật vốn đang lỗi và `TRACK_WIDTH_M` chưa hiệu chỉnh.
  - Nhiễu encoder FR: lượt 4 bánh đầu tiên lại lên 14.424 RPM, 1070 xung (2/2 lần đo, các lượt sau không); khi chỉ FL quay, FR nhận 99–121 xung trong 1,5 giây, tăng so với 44–48 trước khi thay dây; chưa biết bánh có quay theo không. Xe chưa thử đi thẳng trên sàn với bộ mới.

- **7/11 khuya — đã đo lại PID cả 4 bánh, xe kê bánh, USB, tắt Wi-Fi; CHƯA nạp thông số mới.** Mục "dừng ngay từ đầu" bên dưới là do pin motor chưa bật. Theo luật chốt trước: FR SIMC ×2 `(0.0003, 0.00442)` đạt 5/8; RR SIMC ×2 `(0.00088, 0.00218)` 8/8; FL giữ `(0.0022, 0.005)` 8/8; RL giữ `(0.002, 0.005)` 4/8, cả 3 bộ đều chưa đạt ở 60 RPM. Mô hình K/τ/θ: FR 430/0,07/0,30; RR 832/0,40/0,33; FL 886/0,41/0,30; RL 868/0,30/0,30. FR đo với cú đẩy 100%, ba bánh sau 80%.
  - **Phát hiện về đi thẳng:** 4 bánh cùng chạy, 3–10 giây chỉ lệch 0–3 xung giữa hai bên (trừ một lượt 80 RPM lệch do nhiễu FR); 3 giây đầu ở 110 RPM bên trái hơn khoảng 40 xung tổng hai bánh, mỗi bên cỡ một vòng bánh (khoảng 20 cm). Nghi do PID trái mạnh hơn phải nên tăng tốc nhanh hơn. Thử bộ đồng đều hơn (B, C trong `pidcmp.py`) KHÔNG hợp lệ: cả 4 bánh 0 xung, nghi nguồn motor đã tắt.
  - Nhiễu: lượt đầu 110 RPM encoder FR 888 xung so với khoảng 311 bình thường, có lúc đọc hơn 11.000 RPM. Board dừng một lần lúc 23:27 khi RR được đẩy 100% lúc lùi, không có log. Sau khi đo, 2 lần khởi động qua USB liên tiếp báo `brownout` (raw 3) ngay khi lên Wi-Fi, lần sau có vẻ nguồn motor đã tắt. Trang kết quả: https://claude.ai/artifact/WjCG8hUMguef2MVuCTVNWq; dữ liệu thô `pidall.json` ở scratchpad có thể mất. Tất cả đo không tải, chưa thử trên sàn.

- **7/11 khuya — đo PID lại dừng ngay từ đầu, chưa có thông số mới.** Cắm USB, được báo đã kê bánh. `front_right` tiến duty 0,2–0,8 có đẩy 100% đều 0 RPM. Dừng bài đo, thử cả 4 bánh duty ±1,0 mỗi lần 1,5 giây: **cả 4 bánh 0 xung ở cả hai chiều**. Encoder đứng yên đọc FL 1, RL 1, RR 1, FR 0. Vì cả 4 cùng mất, nghi nguyên nhân chung sau khi đấu lại: pin motor chưa bật, thiếu GND chung, hoặc nguồn encoder; chưa biết bánh có quay thật không. Script đo ở scratchpad `pidall.py`, `pidan.py` (tính toán đã thử với dữ liệu giả), có thể mất khi scratchpad bị xóa.

- **7/11 tối — lần hiệu chỉnh góc xoay đầu tiên KHÔNG dùng được, chưa đổi `TRACK_WIDTH_M`.** Lệnh xoay tại chỗ theo chiều kim đồng hồ ±110 RPM qua API, trên sàn. Sau 13 giây xe tính 739°, nhưng chỉ `front_left` có xung (4,125 m); `front_right`, `rear_left`, `rear_right` 0 xung và đều từng báo `encoder_or_stall`, không reset (cùng boot). Con số 739° chỉ đến từ một bánh nên không đại diện cho góc thật. Chưa biết ba bánh đứng yên thật (không đủ lực trên sàn, mất nguồn) hay vẫn quay mà encoder không đếm (dây sau khi đấu lại). Trên xe kê bánh trước đó cả 4 bánh đều có xung khi xoay tại chỗ. Lưu ý: khi nhiều bánh lỗi thì odometry bị lệch tương tự, có thể liên quan đến xoay thiếu lúc quay về.

- **7/11 tối — người dùng báo tự quay về lỗi và xe không đi thẳng; chưa sửa, chưa đo lại PID.** Status đọc khi xe đứng yên, không USB: `return_blocked`, né 7 lần (giới hạn 6) trong 51,2 giây, đi 3,24 m, dừng ở (0,134; 0,393) tức cách gốc 0,41 m, đầu xe quay ngược hướng về (th 0,38 rad, hướng về khoảng -161°), route 2 điểm. Boot ghi `brownout` khoảng 4 phút trước đó, nên điểm gốc và lộ trình có thể đã mất khi reset. Cảm biến khi đứng yên dao động 26–51 cm, thỉnh thoảng rỗng trong lúc quét; có vật khoảng 0,5 m phía trước. Nghi, chưa kiểm chứng: `TRACK_WIDTH_M` = 0,16 chưa hiệu chỉnh nên ước lượng góc sai; nhiễu cảm biến so với ngưỡng 45 cm. Chưa thấy lỗi logic trực tiếp; ý tưởng bỏ qua vật cản nằm sau điểm gốc không áp dụng cho lần này vì xe đang quay ngược. Không đi thẳng: một lượt đi thẳng 120 RPM trên xe kê bánh cho FL 100, RL 99, FR 92, RR 96 (phiên bị ngắt, chỉ tham khảo). PID cần xe kê bánh và cắm USB; không có encoder hai kênh hay cảm biến hướng nên PID chỉ cân tốc độ từng bánh, không bảo đảm xe thẳng trên sàn.

- **7/11 tối — thêm `MIN_WHEEL_RPM = 40` cho lệnh joystick, đã nạp lên bo.** Bên nào có mục tiêu dưới 40 RPM thì dừng hẳn; `_set_sides` của lộ trình quay về không bị giới hạn. Xác nhận trên bo: lệnh 24 RPM cho mục tiêu và PWM 0 ở cả 4 bánh, `reason=idle`, 28/30 lệnh qua được. 104 test Python và test JS đạt. Chưa commit, chưa thử rẽ thật với ngưỡng này, chưa thử trên sàn. Mức 40 chọn từ đo xe kê bánh, cần chỉnh lại trên sàn.

- **7/11 tối — đo rẽ trên xe kê bánh qua API, 2 lượt (khoảng 8 phút cùng một lần khởi động): KHÔNG tái hiện được `encoder_or_stall`, 0 lần ở mọi mức.** Bánh ngoài 120 RPM, bánh trong 100→10 RPM, tiến, lùi và xoay tại chỗ. Ở mức thấp bánh chạy giật: lượt 2, số mẫu có mục tiêu mà RPM = 0 (bánh trong): 40 RPM 1–5/17, 20 RPM 4–10/16, 10 RPM 7–12/17; đi thẳng 120 RPM 0–1/16. Giả thuyết "bánh trong tốc độ thấp gây lỗi" chỉ được ủng hộ một phần: thấy giật, chưa thấy báo lỗi; chưa thử trên sàn có tải. Không reset trong suốt lúc motor quay, nhưng boot trước bài đo ghi `brownout`, khoảng 40 giây trước lượt 1. FL lùi có xung trong cả bài. Lệnh web hay lỗi (409, timeout): web xe trễ trung bình 263 ms, tối đa 2 s khi đứng yên, router trễ tối đa 381 ms; script gửi lệnh và đọc status tuần tự nên cũng làm phiên dễ hết hạn. Do đó RPM trung bình thấp hơn mục tiêu ở nhiều mức không dùng để đánh giá PID.

- **7/11 tối — thêm tự thử lại bánh stall và đã nạp lên bo, CHƯA thử trên motor thật.** Người dùng báo lỗi xảy ra khi rẽ. Bánh báo `encoder_or_stall` nghỉ `STALL_RETRY_MS` = 2 giây rồi tự thử lại, tối đa `STALL_MAX_RETRIES` = 3 lần; có xung thì trả lại đủ số lần; hết lần thì chờ lần kéo joystick mới. Chỉ áp dụng khi `STOP_ALL_ON_ENCODER_STALL = False`. Sửa bản đồ: `_update_odometry` cộng quãng đường mới của từng bánh, trước đây trung bình giá trị tích lũy nên số bánh đổi là vị trí nhảy. Sửa chữ trên trang. 101 test Python và test JS đạt. Chưa commit. Nghi, chưa kiểm chứng: rẽ làm bánh trong có mục tiêu rất thấp (`left = throttle + steering`, ví dụ 0,7 và -0,5 cho khoảng 20 RPM), dưới mức bánh giữ được; nếu đúng thì tự thử lại chỉ giảm triệu chứng, cần đặt ngưỡng tốc độ tối thiểu. Cần đo trên xe kê bánh.

- **7/11 tối — người dùng lái và gặp `encoder_or_stall` ở `front_left` và `rear_left` cùng lúc, hỏi cách xóa.** Lỗi này đã tự xóa khi `arm` lần mới (thả joystick rồi kéo lại), không cần khởi động lại; dòng chữ "khởi động lại sau khi sửa lỗi" trên trang là gây hiểu nhầm, chưa sửa. Điều kiện báo: duty ≥ 0,20 mà 1,5 giây không có xung. Status lúc đọc: FL 434 xung, RL 361, RR 823, FR 1011 trong 173 giây từ lần brownout gần nhất. Chưa rõ nguyên nhân hai bánh trái cùng lỗi: bánh kẹt thật, encoder, hay nguồn.

- **7/11 tối — theo dõi lần 2, được nhờ rút dây đỏ servo (chưa xác nhận lại) và bật tắt pin 3 lần: 1 brownout lúc 22:08:51, mất phản hồi 7,5 giây.** Trước đó board đã chạy liên tục hơn 5 phút. Lúc 22:09:35 mất phản hồi 6,1 giây nhưng không reset. Chưa có giờ bật tắt thực tế nên chưa so được với lần 1.

- **7/11 tối — theo dõi 3 phút trong lúc người dùng được nhờ bật tắt pin motor 3 lần: đúng 3 lần brownout (khoảng 21:59:52, 22:00:04–10, 22:01:22–26), không gửi lệnh motor.** Giữa các lần có đoạn 65 giây và đoạn cuối 89 giây không reset dù servo vẫn quét, nên servo quét bình thường không tự gây reset liên tục. Chưa xác nhận giờ bật tắt thực tế. Người dùng cho biết servo và HC-SR04 lấy 5V từ chân VIN của ESP32, không có dây 5V L298N sang VIN. Thử tiếp: rút dây đỏ servo khỏi VIN rồi lặp bài bật tắt; nghi thêm đường GND chung. Chưa đo điện áp.

- **7/11 tối — brownout thật khi đang cắm USB, sau khi nối lại dây; chưa rõ nguyên nhân.** `/api/ping` lúc 21:47: `reason=brownout`, `cause=1`, `raw_cause=3`, reset khoảng 21:47:44; trong 75 giây theo dõi sau đó không reset thêm. MicroPython chỉ gán `cause=1` cho power-on hoặc brownout, còn `raw=1` mới là power-on, nên nhãn này đáng tin. Trang web giữ cảnh báo tới lần reset sau, không có nghĩa đang sụt áp liên tục. Chưa đo điện áp, chưa cho motor chạy. Nghi, chưa kiểm chứng: dòng khởi động khi bật nguồn motor nếu 5V L298N nối chung 5V/VIN ESP32; servo lấy 5V từ ESP32; 4 encoder và Wi-Fi cùng tải trên 3V3; chạm dây; cáp hoặc cổng USB yếu.

- **7/11 — người dùng nối lại dây, gắn jumper trên 2 L298N, cấp 3,3 V cho 4 encoder; ESP32 cấp qua USB. Chưa cho motor chạy.** Chưa rõ jumper ở ENA/ENB hay 5V-EN. Đo chỉ đọc: GPIO 14, 32, 22, 19 đều 0/50 khi kéo xuống và 50/50 khi kéo lên, tức không bị giữ ở mức cao, nhưng chỉ loại được jumper ENA/ENB nếu lúc đó nguồn motor đang bật (chưa biết). 4 encoder đứng yên: mức cao 100%, 0 lần đổi mức; chưa quay tay để xác nhận có xung.

- **7/11 — xe có lúc không mở được web sau khi rút/cắm USB, chưa rõ nguyên nhân.** Lúc lỗi: có `/dev/ttyUSB0`, laptop đúng Wi-Fi nhà, router trả lời, nhưng ping xe mất 100%, ARP `FAILED`. Không xem được trạng thái lỗi vì mở USB để reset đã xóa nó. Reset phần cứng (EN) qua USB: web lên lại; lặp 6/6 lần, 4,1–5,2 giây, không traceback; trang 79343 byte tải đủ. Chưa thử rút hẳn nguồn rồi cấp lại, chưa thử chạy không USB. Giả thuyết, chưa kiểm chứng: board đang chạy bằng nguồn riêng bị sụt áp hoặc hết 20 giây chờ Wi-Fi; `connect_wifi` báo lỗi là `main` dừng hẳn, không tự thử lại, phải reset mới có web.

- **7/11 — đo lại hai bánh trước: `front_left` tự lùi lại được giữa bài đo, chưa rõ vì sao (có thể tái phát).** Mục dưới nghi dây GPIO27 → IN1 và ghi lỗi "không dao động": nay không còn đúng, vì đường IN1 đã chạy được; nếu là tiếp xúc chập chờn thì vẫn chưa loại. Không biết người dùng có chỉnh gì giữa các lần đo không. Lần 2, FL lùi từ đứng yên: duty 0,3–0,75 gần như 0 xung (một lượt 33 RPM ở 0,5), 0,9 chỉ 6 xung, 1,0 đạt 279–456 RPM; ngay sau đó khởi động duty 0,5 đạt 20/20 cả hai chiều. Lần 3, FL lùi 201/291/330/342/366/402/420 RPM (duty 0,3→1,0), đảo chiều xen kẽ duty 0,5 đạt 12/12. Hai lần 1 và 2 đều lùi kém ở đầu phiên, nên nghi tiếp xúc chổi than/cổ góp hoặc mối nối, chưa kiểm chứng; thử tiếp: để nghỉ rồi đo lùi ngay đầu phiên.
  - Tốc độ FL tiến ở duty 1,0 tăng dần: 383 → 362 → 435–480 RPM; chưa đo áp pin nên chưa so sánh được. Xung lạ trên encoder FR ở duty 1,0 giảm từ 128–191 xuống 11–38 khi FL tiến, 5–8 khi FL lùi; vẫn chưa biết nguyên nhân. FR: duty 0,5 chỉ quay lần đầu rồi 0 (123, 0, 0; lùi 129, 0, 0), duty 0,6 ở lần 2 tiến 0/3 nhưng lần 3 đạt 3/3 (147–150), 0,75 đạt mọi lượt (165–177).

- **7/11 — thay L298N kênh trước, đo FR và FL (xe kê bánh, qua USB, tắt Wi-Fi, mỗi lần một bánh): `front_left` VẪN KHÔNG LÙI, chưa sửa.** FL tiến 143/238/310/347/371/365/383 RPM ở duty 0,3/0,4/0,5/0,6/0,75/0,9/1,0, khởi động duty 0,5 đạt 20/20; lùi 0 xung ở mọi duty (21/21 lượt, khởi động 0/20). Khi lệnh lùi, đọc lại GPIO27 (IN1) = 1, GPIO26 (IN2) = 0, PWM đúng, nên chân ESP32 không bị kéo xuống; triệu chứng giống hệt 6/11 dù đã thay driver, nên nghi dây GPIO27 → IN1 trước, chưa kiểm chứng. Thử phân biệt: tắt nguồn motor, đổi chỗ dây IN1/IN2 tại L298N; nếu vẫn chỉ quay khi GPIO26 lên thì lỗi ở GPIO27/dây, nếu đổi sang quay khi GPIO27 lên thì lỗi ở phía driver/motor. Khi nào xong phải đổi lại dây.
  - FR tiến 0/0/121/144/165/187/224, lùi 0/0/123/142/171/187/204 RPM cùng các mức duty; gần như không đổi so với driver cũ (tiến 149/170/188/202, lùi 151/175/188/204 ở 0,6/0,75/0,9/1,0), nên độ yếu của FR nhiều khả năng không do L298N. Khởi động: duty 0,5 tiến 1/20, lùi 12/20 (các lần hỏng liền nhau); duty 0,6 và 0,75 đều 15/15 cả hai chiều.
  - **Mới, chưa rõ nguyên nhân:** khi chỉ FL quay tiến, encoder FR (GPIO36) nhận 9–17 xung ở duty 0,5, 52–71 ở 0,75, 128–136 ở 1,0 trong 2,5 giây; RR, RL 0 xung. FR quay thì FL (GPIO39) 0 xung. Chưa biết bánh FR quay thật (rung) hay nhiễu/xuyên âm dây; nếu là nhiễu thì RPM của FR sẽ sai khi FL chạy nhanh. Chưa đo lại PID FR.

- **7/11 — ĐÃ TÌM RA VÀ SỬA cú sập Wi-Fi khi lái (mục này thay các chẩn đoán "chưa rõ nguyên nhân" cùng ngày bên dưới).** Nguyên nhân: heap Python ban đầu 56 KB, code dùng khoảng 51 KB nên nới lên 112 KB. Khi cần một đoạn liền mà không còn, MicroPython nới thêm và lấy **toàn bộ khối lớn nhất còn lại** của RAM hệ thống (khoảng 18 KB), Wi-Fi/lwIP còn dưới 1 KB nên tê liệt; board vẫn báo đang nối. Bằng chứng: lấy `total - blk` trong 8 log, 4 lần không sập luôn 112.240 byte, 4 lần sập nhảy lên 128–133 KB đúng lúc RAM hệ thống tụt. **Sai lầm cần tránh lặp lại:** `gc.mem_free()` trên bản này cộng cả phần còn có thể nới (`max new split`), nên `mem_alloc + mem_free` gần như không đổi; vì vậy trước đây kết luận nhầm "heap Python không nới" và rút lại giả thuyết đúng. Muốn đo heap thật phải trừ khối lớn nhất của `esp32.idf_heap_info(esp32.HEAP_DATA)` hoặc đọc `micropython.mem_info()`. Mức "26 hay 85 KB" trước đây tưởng ngẫu nhiên thực ra là heap đã nới hay chưa: `gc.collect()` trả lại vùng heap trống hoàn toàn.
  - **Hai nguồn, cần sửa cả hai:** (1) `Odometry.route` là list tuple lớn dần theo quãng đường: xe đứng yên, bơm điểm giả thì sập ở khoảng 130 điểm (gần ngưỡng mảng nhân đôi ở 128), đó là lý do trước đây chỉ sập khi xe chạy. Thay bằng lớp `Route` trên mảng `array('f')` cấp sẵn. (2) `json.dumps` của status cần đoạn liền khoảng 2,2 KB: thay bằng `JsonBuffer` ghi từng phần vào bộ đệm 3 KB cấp sẵn. Thêm: gửi không sao chép (`memoryview`, `SocketStream.write`). Chưa bắt được trực tiếp lệnh cấp phát bị từ chối; kết luận dựa trên các lần thử dưới đây.
  - **Ma trận thử (motor quay thật, xe kê bánh, 5 phút):** chỉ `JsonBuffer`, script: sập sau khoảng 85 giây. Chỉ `Route`, script: đạt; cùng bản đó với Chrome: sập sau khoảng 45 giây. Cả hai, Chrome có đo trên board: đạt (heap ≤ 112 KB, RAM hệ thống thấp nhất 15 KB, ping xe mất 0,3%, 0 lần mất kết nối). Cả hai, Chrome không đo, khởi động thường: đạt (ping xe mất 0%, 0 lần mất kết nối, 0 `command_timeout`, 50 request bị trình duyệt hủy `ERR_ABORTED`). 96 test Python và test JS đạt trên bản cuối.
  - **Vẫn chưa thử:** chạy bằng pin không USB, xe chạy trên sàn, hai điện thoại cùng lúc, chạy lâu hơn 5 phút, tải trang giữa lúc đang chạy. Biên RAM vẫn mỏng (hệ thống 15–26 KB); muốn rộng hơn cần đưa code vào firmware (frozen modules). Lỗi `can't cancel self` khi Ctrl-C vẫn còn: board kẹt tới khi reset phần cứng, chỉ xảy ra lúc dừng bằng Ctrl-C, không ảnh hưởng khi chạy thường.

- **7/11 — chẩn đoán web mất phản hồi (`/api/status` quá 1200 ms), CHƯA sửa.** Ghi 30 phút qua USB với nhịp báo mỗi giây: vòng điều khiển luôn chạy (gap ≤ 92 ms sau khi khởi động), 1 thiết bị vẫn nối, không reset, không traceback, motor chỉ chạy 4 giây đầu nên lần này không phải do motor hay sụt áp; lúc đó có cắm USB. `/api/ping` đạt 45/950 lần. Board in `memory allocation failed` khi cấp 1,6–2,8 KB (vào nhánh `robot.stop('server_error')`), và `HTTP I/O error` ECONNABORTED, -203. RAM Python thấp nhất 448 byte. Đo trên bo, không motor: `robot.update` cấp phát khoảng 23 KB/giây, tắt scanner gần như không đổi; mỗi lần tạo status 4,2 KB, JSON 2446 byte; heap IDF (Wi-Fi/lwIP dùng) còn 25 KB sau `build_robot`, thấp hơn nữa khi tắt GC để đo. Giả thuyết chính, chưa kiểm chứng: heap Python nở lấn IDF nên Wi-Fi/socket thiếu bộ nhớ. Bản ghi bị nhiễu: `nmcli dev wifi` chạy mỗi 5 giây có thể làm laptop quét Wi-Fi, ping 1 lần/giây cũng thêm tải. Khi mở cổng USB, board khởi động lại. Ctrl-C vào main còn báo `RuntimeError: can't cancel self` ở `http_transport.py:166` khi dọn dẹp.

- **7/11 — đã sửa theo giả thuyết thiếu RAM và nạp lên bo, CHƯA xác nhận hết lỗi trên web thật.** Nạp bằng `tools/deploy.py` mới: module dạng `.mpy` (mpy-cross 1.29.0.post2), `config.py` và `main.py` giữ dạng nguồn; `.py` cũ đã xóa khỏi bo. Sửa: dọn RAM mỗi giây và khi khởi động; `accept` gặp `ECONNABORTED` hoặc thiếu RAM không còn dừng xe và không tạo lại listener; request thiếu RAM trả 503, không dừng xe; bớt cấp phát trong `pid.py`, `encoder.py`, `robot.py`; status từ 2446 còn 1904 byte. Đo lại: RAM hệ thống sau `build_robot` từ 25 KB lên 88 KB (chưa bật Wi-Fi); `robot.update` chỉ giảm từ 23 còn 21 KB/giây. Lúc bật Wi-Fi, chưa có client: RAM hệ thống khoảng 28 KB, RAM Python thấp nhất khoảng 55 KB. 90 test đạt, JS đạt.

- **7/11 — sau bản sửa RAM, xe đi được 9,09 m nhưng web vẫn lỗi; giả thuyết "heap Python lấn RAM Wi-Fi" KHÔNG được dữ liệu ủng hộ.** Ghi từ board: RAM hệ thống (IDF) đang khoảng 23 KB tụt còn 1–3 KB trong 2 giây và hồi lại khi laptop rời mạng, trong khi RAM Python không tăng tương ứng (152/230 giây có thiết bị nối ở dưới 5 KB). Không có `oom`, không có `HTTP I/O error`. Giả thuyết mới, chưa kiểm chứng: lượng gói mạng hoặc gói chờ gửi cho laptop chiếm RAM; laptop nối `CR7-GOAT` đặt ESP32 làm gateway mặc định nên toàn bộ ứng dụng có thể đang gửi lưu lượng Internet tới ESP32. Kiểm tra tiếp: lái bằng điện thoại (laptop rời `CR7-GOAT`), rồi thử chế độ STA. Cũng ghi nhận 1 lần `encoder_or_stall:front_right` khi lùi ở duty 1,0.

- **7/11 — giả thuyết laptop cũng bị loại một phần, nghi nghẽn đường phát Wi-Fi của ESP32.** Điện thoại (laptop không ở `CR7-GOAT`, motor chưa chạy) cũng làm IDF tụt từ 21 KB xuống 1,6 KB. Log từng request (`rec4`): `read_request` nhanh (TB 15 ms, không lượt nào quá 1 giây), nhưng 36 phản hồi bị hủy ở mốc 2 giây khi đang gửi, kể cả phản hồi 12 byte; RAM Python vẫn còn, `oom` = 0; motor về 0 trong khoảng 1 giây sau khi mất lệnh. Suy luận chưa đo trực tiếp: gói chờ phát đầy bộ đệm Wi-Fi vì khung tin không tới được thiết bị. Lỗi này đã có từ 29/10 (iPhone và laptop, `4WAY_HANDSHAKE_TIMEOUT`), không phải do phần bản đồ mới. Kênh 11 có `9a9_Ext` (70%) và `VTVCAB_330720` (52%). Bước kế tiếp: thử chế độ STA với `Phong tang 2` để tách lỗi AP và lỗi phát của board.

- **7/11 — tìm ra và sửa một nguyên nhân của thông báo "chưa phản hồi /api/status": mất gói Wi-Fi cộng ngưỡng quá chặt.** `config.py` đang ở `WIFI_MODE="STA"` với `Phong tang 2` (trong file có mật khẩu Wi-Fi, đừng commit). Tái hiện bằng Chrome thật, xe đứng yên, không gửi lệnh chạy: board trả lời trong 12–30 ms, không cancel, IDF không sập, nhưng ping từ laptop tới router (không qua ESP32) mất khoảng 2% và tới khoảng 270 ms. Mỗi request là một kết nối TCP mới; mất 1 gói làm TCP chờ khoảng 1 giây, vượt ngưỡng 1200 ms và trang dừng xe ngay. Sửa `index.html`: status chờ 2500 ms, 3 lần lỗi liên tiếp mới báo mất kết nối; lệnh điều khiển chờ 400 ms và thử lại ngay, 3 lần lỗi liên tiếp mới dừng. `COMMAND_TIMEOUT_MS` giữ 700 ms. Sửa `web_server.py`: trang HTML được 20 giây để gửi (giới hạn 2 giây từng cắt trang ở 63 KB). So sánh Chrome 3 phút: trước 14 request bị hủy và báo lỗi nhiều lần; sau 3 request bị hủy và không báo lỗi. **Chưa giải quyết:** cú sập IDF xuống dưới 1 KB chỉ thấy khi người thật dùng trang, chưa tái hiện được ở script hay Chrome không lái; chưa thử bản mới khi lái thật.

- **7/11 — tự tái hiện được cú sập khi lái (xe kê bánh, motor chạy thật), CHƯA tìm ra nguyên nhân gốc.** Chrome thật bằng phím mũi tên: sập sau khoảng 35 giây; script gửi lệnh: sập sau khoảng 65–70 giây (3 lần lặp được). Cùng lượng lệnh nhưng tốc độ 0: không sập trong 3 phút. Khi sập: IDF từ 23 KB còn 1–2 KB trong 1 giây, tổng heap Python không tăng tương ứng, board vẫn báo nối và RSSI tốt, vòng điều khiển chạy đều, motor về 0; ping xe mất khoảng 94% trong khi ping router mất 2,4%; IDF thường không hồi kể cả khi hết traffic (có lúc tự hồi sau vài giây). Ping lúc chưa sập: motor đứng 7,1%, motor quay 6,5%. `disconnect()` + `connect()` KHÔNG cứu được (không nối lại trong khoảng 1,5 phút, IDF khoảng 5 KB); reset board thì hết. Chỉ Wi-Fi + motor + ngắt encoder, không web, không PID: 100 giây không sập, IDF 83–85 KB, nhưng chỉ 1 lần. IDF sau `connect_wifi` lúc 26 KB, lúc 85 KB, chưa rõ quy luật; chương trình thật luôn 26 KB (8/8 lần), kể cả khi nối Wi-Fi trước rồi soft reset; chưa thử được chạy web với 85 KB. Chưa đo điện áp nguồn. Bài T1 (motor không ngắt encoder) chưa chạy được do lỗi gửi code. Script tái hiện ở scratchpad: `exp.py`, `drive.py`, `expan.py`, `win.py`.

- **7/11 — đã nạp toàn bộ `firmware/*.py`, `web/index.html` và `calibrate_track.py` lên bo, đọc lại khớp.** `config.py` đổi FL thành `(0.0022, 0.005)`; RR, RL, FR giữ nguyên. Bo khởi động tới "Web/PID san sang", không brownout; CHƯA thử web qua Wi-Fi hay chạy trên sàn. Đã nới vật cản trong `test_avoids_obstacle_placed_on_the_way_back` lên ±0,45 m vì test nhạy với Kp (88 test đạt). Mô phỏng đổi Kp FL từ 0,0016 đến 0,003: luôn về đích, nhưng có trường hợp không né (`avoid 0`) và sát vật tới 0,02 m. Lần nạp này ping thật đọc 17 cm, có thể HC-SR04 đã nối; chưa xác nhận cầu chia áp Echo.

- **6/11 khuya — đo PID cả 4 bánh, xe kê bánh, không tải (96 lượt đạt và 1 lượt kẹt, không reset). Sau đó FL đã vào `config.py`.** Chạy SIMC, SIMC ×2 và bộ hiện tại ở ±60 và ±110 RPM. Theo luật chọn định trước: FL `(0.0022, 0.005)`, RR `(0.001, 0.003)`, RL `(0.002, 0.005)`, FR `(0.0002, 0.0128)`. Mô hình FR không tin cậy (K 189, τ 0,02 chạm biên lưới dò, đo ở duty 0,5–0,6), nên bộ của FR chỉ nhỉnh hơn `(0.002, 0.005)` trong sai số đo. RL và FR ở 60 RPM chưa ổn định với mọi bộ; RL đặc biệt dao động duty lớn. **FR yếu đi rõ trong lần đo này:** duty 0,6 giữ 108 RPM, 110 RPM cần duty 0,54–0,58, trong khi đo trước đó cùng tối duty 0,6 đạt 149 RPM và 120 RPM chỉ cần duty 0,40; chưa rõ nguyên nhân. Khuyên giữ FR `(0.002, 0.005)`, tìm nguyên nhân rồi đo lại. FL cũng kẹt nhiều lúc đo đặc tính (duty 0,25 và 0,30 không quay cả 4/4 lần dù 0,20 quay được).

- **6/11 khuya — sau khi người dùng thay dây: `front_left` khi đã quay thì ổn, nhưng có lúc không khởi động được, ở CẢ HAI chiều.** Duty 0,5: khởi động từ đứng yên tiến 8/10, lùi 7/10, các lần hỏng nằm liền nhau; một lần tiến duty 0,75 cũng 0 xung. Chạy liên tục 30 giây mỗi chiều: trung vị 300 RPM, không nhịp nào tụt (112/112). Ba bánh còn lại đúng kênh, quay cả hai chiều. Vì lỗi không còn theo chiều lùi, giả thuyết dây IN1 yếu đi; nay nghi chổi than hoặc cổ góp motor (điểm chết theo vị trí rotor) hoặc mối hàn tại motor; chưa kiểm chứng. Chưa đo PID cho `front_left`. Thử xoay tay (duty 0,5): 51 lần khởi động đầu, kẹt 2 lần, đều khi lùi; khi đang kẹt mà chưa chạm bánh thử lại 0/6 lần quay; sau khi xoay tay 1/2 lần quay. Phù hợp với điểm chết theo vị trí rotor nhưng mẫu còn ít, chưa kết luận; chưa đổi motor sang kênh khác để kiểm chứng.

- **6/11 khuya — `front_left` không lùi được.** Sau khi dây hết lệch kênh: lệnh tiến duty 0,3–1,0 cho 131–341 RPM, lệnh lùi 0 xung ở mọi duty (21/21 lượt). Khi lùi, ESP32 đặt GPIO27 (IN1) = 1, GPIO26 (IN2) = 0 đúng như code. Lỗi đã có từ trước khi chỉnh dây motor (các lượt PID lùi đều kẹt), nhưng lúc 17:20 cùng ngày bánh này vẫn lùi được. Nghi dây GPIO27 → IN1 hoặc nửa cầu OUT1 của L298N phía trên; chưa đo điện áp. **Đo lại sau đó: bánh đã lùi bình thường** (6/6 lượt, duty 0,5–1,0, cửa sổ 1,5 giây: lùi 224/305/337 RPM, tiến 196/221/236 RPM). Chưa xác nhận nguyên nhân; nếu do dây lỏng thì lỗi có thể quay lại. `front_right` không yếu như đã báo: 124–130 RPM ở duty 0,75 trong 1,5 giây, phù hợp với 170 RPM đo trong 2,5 giây; con số "hơn 200 xung" trước đó là tính sai (đúng là khoảng 85 xung).

- **6/11 khuya — sau khi người dùng chỉnh dây motor `front_left`, kênh motor bị lệch: CHƯA đo được PID.** Lệnh chạy `front_right` (kênh `upper_b`, GPIO 25/33/32) làm bánh `rear_left` quay theo quan sát của người dùng; encoder GPIO36 của `front_right` ≈ 0 xung, encoder GPIO35 của `rear_left` tới khoảng 1048 xung sau 3 lượt ở duty 1,0. Trước lúc chỉnh dây, cùng bài đo cho `front_right` có xung đúng kênh. Cần kiểm tra lại dây giữa L298N và motor, rồi chạy kiểm tra từng kênh trước khi đo tiếp. Kết quả của lần chạy này không dùng được.

- **6/11 tối — đã thay motor `front_right`, đo riêng bánh này (chỉ bánh này chạy, qua USB, không Wi-Fi): đạt.** Vòng hở cùng cách đo với motor cũ (từ đứng yên, 2,5 giây, mới đo 3 lần mỗi mức, cũ 1 lần), duty 0,6/0,75/0,9/1,0: tiến mới 149/170/188/202 RPM, cũ 266/323/–/366; lùi mới 151/175/188/204 RPM, cũ 0/0/335/360. Motor mới chậm hơn khoảng 45% ở duty cao, chưa rõ do motor, mức pin hay xung nhiễu của motor cũ. Từ đứng yên: lùi ổn định từ duty 0,5 (cũ 0,9); tiến ổn định từ 0,6 như cũ, ở 0,5 chưa ổn định (16/89/128 RPM). PID hiện tại `(0.002, 0.005, 0)` không đổi: 2 giây cuối đạt 57/90/117 RPM khi tiến và 61,5/90/123 RPM khi lùi cho mục tiêu 60/90/120; đảo chiều liên tục 4 đoạn không báo lỗi. **Chưa xác nhận:** chiều quay thật (encoder một kênh không biết chiều), chạy cùng `front_left` và cả 4 bánh, chạy có tải trên sàn. SG90/HC-SR04 chưa lắp.

- **6/11 tối — mô phỏng web có né vật cản.** Chế độ mô phỏng: bấm lên bản đồ để đặt hoặc gỡ vật cản 30 cm, xe né theo trình tự của `navigator.py` (viết lại bằng JavaScript, hệ số riêng cho mô phỏng). Bản `index.html` này mới ở trên máy, CHƯA nạp lên bo.

- **6/11 tối — viết xong tự quay về, tránh vật cản, quét HC-SR04; đã nạp lên bo, CHƯA chạy trên sàn.**
  Hướng dẫn: `docs/TEST_QUAY_VE.md`. File mới: `firmware/odometry.py`, `scanner.py`, `navigator.py`,
  `tools/calibrate_track.py`, `tests/test_navigator.py`. API mới: `/api/return`, `/api/map_reset`;
  `/api/status` có thêm `pose`, `trail`, `nav`, `scan`. Nút Quay về trên web đã chạy với xe thật.
  - Đổi cú đẩy khởi động: `BREAKAWAY_DUTY` 0,35 tăng dần `BREAKAWAY_RAMP_PER_S` 1,0/giây đến khi bánh
    quay, thay cho mức cố định 0,75. Ảnh hưởng cả khi lái joystick; PID đo trước đó dùng mức cũ.
  - Đã kiểm trên bo thật không chạy motor: import, logic chạy được, vòng lâu nhất 25 ms, ping không
    có cảm biến mất 9 ms, RAM trống khoảng 80 KB. SG90 và HC-SR04 chưa được nối nên chưa kiểm phần cứng.
  - Mô phỏng (không trượt): về cách điểm đầu khoảng 0,1–0,5 m. Xe xoay ít hơn 20% so với encoder tính:
    lệch khoảng 1,7 m, nên phải hiệu chỉnh `TRACK_WIDTH_M`. Các thông số `RETURN_*` đều chưa chỉnh trên xe.

- **6/11 — thêm panel “Bản đồ khám phá” vào `firmware/web/index.html`.** Tính vị trí ngay
  trên trình duyệt từ `signed_distance_m` trong `/api/status` (1 lần/giây), hàm `mapStep`,
  `mapScan`, `drawMap`. Mô phỏng có phòng ảo để thử vẽ vật cản. Chưa có HC-SR04/SG90 và
  firmware chưa gửi điểm quét, nên trên xe thật chỉ vẽ đường đi. Khoảng cách hai bên bánh
  đang để 16 cm (giá trị tạm, cần đo). Chưa thử đường đi trên xe thật.
  Đổi giao diện sang chủ đề rừng rậm (chỉ CSS và SVG nhúng, không tải gì từ Internet). Bỏ ô
  “Giới hạn tốc độ”: joystick hết cỡ gửi `max_rpm` bằng `MAX_RPM` của firmware (120), giới
  hạn này vẫn còn trong `config.py` và `Robot.command`.
  Thêm nút “Quay về” chỉ trong mô phỏng: xoay đầu rồi đi ngược `map.route` (không trượt bánh).
  Bản này mới ở trên máy, CHƯA nạp lên bo; xe thật chưa có chế độ tự quay về.

- **6/11 chiều — đo lại với pin đầy (kê không tải); thay mục đo trước về PID.** Đã nạp
  `config.py`: RR `(0.001, 0.003, 0.0)`; FL, RL, FR `(0.002, 0.005, 0.0)`. Không có
  brownout trong cả buổi đo pin đầy, kể cả khi chạy 4 bánh.
  - Đo đáp ứng bậc và tính SIMC ra bộ riêng: FL `(0.0007, 0.0020)`, RR `(0.0006, 0.0015)`,
    RL `(0.0008, 0.0020)`, FR `(0.0009, 0.0025)`. Duty đều hơn nhưng khởi động chậm, đẩy
    0,75 nhiều hơn, nên không dùng. Bộ chia theo K cũng không tốt hơn `(0.002, 0.005)`.
  - Chạy 4 bánh qua `Robot`: FR báo `encoder_or_stall` ở cả 2 đoạn phải quay lùi (Lùi 100,
    Xoay phải 100). FL báo kẹt ở Tiến 60, dù chạy một mình thì ổn. Chạy lại lần 2: FR vẫn
    kẹt ở cả 2 đoạn đó (4/4 lần quay lùi); FL kẹt ở Tiến 120, không kẹt ở Tiến 60, nên
    lỗi FL thất thường và chỉ thấy khi tiến. Không có brownout.
  - Thử FR vòng hở từ lúc đứng yên, mỗi mức 1 lần: một mình, tiến bắt đầu quay ở duty 0,60,
    lùi ở 0,90 (lùi 0,75 không quay), đạt 360 RPM ở duty 1,0. Vậy chân IN và kênh L298N vẫn
    chạy được cả hai chiều; `BREAKAWAY_DUTY` 0,75 thấp hơn ngưỡng lùi nên báo kẹt. Khi FL
    tiến 0,4 còn FR lùi, FR không quay kể cả duty 1,0 và FL tụt từ 122 xuống 22 RPM khi tăng
    duty FR. Nghi FR kẹt kéo sụt nguồn L298N trên; chưa đo điện áp, chưa kiểm tra cơ khí FR.
  - Người dùng đã đặt mua motor mới cho FR. Sau khi lắp: kiểm tra chiều (`motor_inverted`),
    encoder, rồi đo lại PID FR và chạy lại bài 4 bánh.
  - FL cần duty 0,49–0,60 khi FR cùng quay, nhưng chỉ 0,27–0,28 khi FR đã dừng vì lỗi; hai
    bánh sau gần như không đổi. Nghi nguồn hoặc dây của L298N phía trên (hai bánh trước)
    bị sụt khi cùng chạy; chưa đo điện áp.
  - RL dao động mạnh ở 80–100 RPM với mọi bộ hệ số, nghi cơ khí, chưa kiểm tra.

- **6/11 — đo PID từng bánh trên xe (kê không tải, USB, không Wi-Fi).** Đã nạp lên
  bo `config.py`, `encoder.py`, `wheel.py`, `main.py`, `pid.py`, `robot.py` (bản đã bỏ
  encoder hai kênh; bánh 65 mm; SSID đổi thành `CR7-GOAT`). Đổi PID cả 4 bánh thành
  `(0.002, 0.005, 0.0)` và đã nạp `config.py`. Chưa chạy đồng thời 4 bánh, chưa thử
  trên sàn và chưa thử qua web.
  - **Chưa giải quyết: sụt áp.** Bài đo lại dừng ở 21/96 sau 3 lần board tự khởi động
    lại, firmware ghi `reason: brownout` (`raw_cause` 3), khi đang chạy một bánh:
    RR 60 RPM, FR 120 RPM, RL 120 RPM. Khoảng 130 lần chạy trước đó không bị. Chưa đo
    điện áp; người dùng báo pin đã hết và đang sạc, nên đây là nguyên nhân khả dĩ nhất.
    Phải đo lại khi pin đầy trước khi thử 4 bánh.
  - Lần dừng ở 48/66 trước đó là do người dùng rút nhầm cáp USB, không phải lỗi xe.
  - Vòng hở, RPM theo duty 0,20 / 0,30 / 0,40 / 0,50: FL 40/137/222/276; RR
    70/199/305/370; RL 0/2/182/256; FR 0/0/102/172. Tức khoảng 1000 RPM mỗi 1,0 duty,
    nên Kp 0,008 quá lớn và là nguyên nhân chính gây dao động.
  - Tốc độ thấp nhất giữ được (không tải): RL khoảng 96 RPM ở duty 0,32 (0,30 thì
    dừng); FR khoảng 66–76 RPM ở duty 0,38–0,39 (0,37 còn chập chờn). FL và RR chạy tốt
    ở 60 RPM. Dưới các mức này RL/FR kẹt rồi vọt, PID không sửa được; nghi do ma sát cơ
    khí, chưa kiểm tra.
  - Bác bỏ đề xuất cũ `ENCODER_SAMPLE_MS = 200`, Ki 0,0015: 200 ms thường dao động mạnh
    hơn 100 ms, Ki 0,0015 để lại sai số lớn. Giữ 100 ms.
  - Cú đẩy `BREAKAWAY_DUTY = 0,75` là nguồn vọt lúc khởi động của FL/RR, vì hai bánh
    này chỉ cần khoảng 0,20. Chưa đổi; có thể tách ngưỡng theo từng bánh.

- **4/11 — bỏ phần hỗ trợ encoder hai kênh (chỉ trên máy, CHƯA nạp lên bo).**
  Xe chỉ có encoder một kênh (OUT) nên đã xóa phần không dùng: `encoder_b` và
  `encoder_inverted` khỏi `WHEELS` + `validate_hardware()` (config.py);
  `Encoder(pin_a, counts_per_rev, sample_ms, filter_tau, min_interval_us)` không
  còn `pin_b`/`inverted`, bỏ `count`, `previous_count`, `position_counts`,
  `raw_rpm` (thành biến cục bộ) và `signed_rpm` trong `status()`. Còn một bộ
  đếm `travel_count`. Sửa theo `main.py`, `tools/check_encoders.py`,
  `tools/test_motors.py`, test, README, WIRING. **Phải nạp đồng bộ `config.py`,
  `main.py`, `encoder.py`, `wheel.py`** (chữ ký `Encoder` đổi: nạp lẻ sẽ lỗi).
  58 unittest đạt; chưa chạy trên xe thật. Nếu sau này mua encoder hai kênh thì
  phải thêm lại phần kênh B.

- **4/11 — thêm quãng đường có dấu (chỉ trên máy, CHƯA nạp lên bo).**
  `wheel.py`: `position_pulses` cộng/trừ số xung theo `self.direction` (chiều
  đã lệnh gần nhất; xung quán tính sau khi dừng tính theo chiều cũ, vì
  `stop()` giữ `direction`). `status()` thêm `position_pulses` và
  `signed_distance_m`; `distance_m` giữ nguyên (tổng không dấu). Encoder 1
  kênh nên đây là suy luận từ lệnh, không phải đo: sai vài xung khi bánh bị
  đẩy tay/trôi lúc motor tắt, và `direction == 0` (chưa từng lệnh) tính +1.
  Test mới `test_position_follows_commanded_direction_including_coasting`;
  58 unittest đạt. Chưa kiểm trên xe thật và chưa hiện lên giao diện web.

- **31/10 — bài thử cuối sau khi người dùng thay dây bánh trước: cả 4 bánh
  chạy hết bài, không lỗi.** Chạy qua USB (nguồn từ máy tính), `Robot` thật,
  ~85 s liên tục, `command()` gửi mỗi 50 ms, mục tiêu 60 RPM (throttle 0,5,
  max_rpm 120). Trước khi thay dây, bài thử hai bánh trước/bốn bánh khóa
  `encoder_or_stall` ở FR (4/5 lần), có lần cả FL; sau khi thay dây thì không
  còn. Số xung (20 xung = 1 vòng bánh):
  - Tiến 20 s: FL 394, RR 448, RL 410, FR 396 (nửa sau cao hơn nửa đầu, không
    có dấu hiệu giảm dần). Lùi 15 s: FL 284, RR 315, RL 282, FR 287.
  - Rẽ phải/trái 8 s: bên đích quay (FL 178, RL 179; RR 186, FR 159), bên còn
    lại đứng. Đảo chiều đột ngột tiến-lùi-tiến 4 s mỗi pha: không lỗi.
  - Chạy riêng FR 30 s tiến + 20 s lùi: tốc độ ổn định 60–80 RPM, không giảm.
  - `duty` trung bình ở 60 RPM: FR 0,38–0,41 so với RR 0,19–0,20, FL 0,24–0,25,
    RL 0,28–0,29, nên FR vẫn là bánh phải gắng sức nhất. Chu kỳ vòng lặp lớn
    nhất 77 ms (ngưỡng 250 ms).
  - Còn lại: PID dao động và vọt 8–15% trên mục tiêu (số đo RPM thô, mỗi xung
    = 30 RPM ở cửa sổ 100 ms); chưa thử đặt xe xuống sàn có tải; chưa thử qua
    web/joystick với nguồn mới; chưa thử nguồn sạc dự phòng. Chưa chỉnh
    `ENCODER_SAMPLE_MS`/`Ki`; đề xuất 200 ms và 0,0015, chờ người dùng đồng ý.
  - Mức kiểm chứng: đo trên bo thật nhưng chỉ một lần cho bài đầy đủ; lần
    thành công riêng lẻ của FR trước khi thay dây cũng từng không lặp lại.

- **29/10 tối — bản mới nhất, thay cho mục "HARDWARE_ENABLED=False" bên dưới:
  bo đang chạy `HARDWARE_ENABLED=True`, motor đã quay lại qua web/PID.** Bốn
  thay đổi trong phiên này (đã nạp, đọc lại khớp từng byte, backup trong
  `.device-backups/{transport-fix,fault-retry,breakaway,diag,breakaway75}-20261029/`):
  1. `http_transport.py`: tác vụ accept bắt mọi `Exception` (kể cả
     `MemoryError`), đóng socket, gọi `on_error` (dừng xe), `gc.collect()`,
     chờ 250 ms rồi nhận tiếp. Trước đó chỉ bắt `OSError` nên tác vụ có thể
     chết im lặng, web mất trong khi PID vẫn chạy. Đây là cơ chế khớp với log
     cũ, chưa chứng minh là nguyên nhân duy nhất. Sau bản này người dùng chỉ
     còn 1–2 lần mất phản hồi và tự phục hồi. Test
     `test_memory_error_while_accepting_does_not_kill_server`.
  2. `robot.py`: `arm()` xóa lỗi có thể thử lại (`control_loop_late`,
     `encoder_or_stall:*` của bánh) khi không có phiên; trước đây các lỗi này
     bị chốt đến khi reset bo. `motor_stop_error`/ngoại lệ vẫn chốt. Robot và
     Wheel in `Loi: ...` (kèm duty, chiều, rpm, xung, giây không xung) ra USB.
  3. `wheel.py` + `config.py`: `BREAKAWAY_DUTY=0.75`, `BREAKAWAY_DELAY_MS=300`.
     Bánh có mục tiêu RPM mà đứng yên >300 ms được cấp tối thiểu duty này tới
     khi có xung; đảo chiều xóa bộ đếm stall. Bản đầu 0,35 là quá thấp.
  4. Đo trực tiếp (PWM cố định 0,6 s/mức, bánh kê cao): trước trái và sau phải
     quay từ 30%; sau trái cần ~60%; trước phải lùi cần ~70%. Vì vậy 0,35 bị báo
     `encoder_or_stall` khi rẽ/lùi. Xe có thể giật nhẹ ở tốc độ thấp.
  Hai lỗi phần cứng tìm ra bằng bài đo trực tiếp (không phải lỗi code):
  **trước trái lùi 0 xung** do dây GPIO27→IN1 chập chờn (sau khi cắm lại thì
  lùi bình thường), và **pin 7,4 V yếu** làm bánh trước phải dừng ở lần lùi
  cuối (số xung chiều tiến giảm dần 197→152). Sau khi người dùng thay pin,
  bài thử PID 10 thao tác (tiến, lùi, quay phải/trái, rẽ nhẹ, chậm 25 RPM) qua
  `Robot` trên bo: **không còn lỗi bánh/robot**. Chưa thử lại bằng joystick
  web sau khi thay pin, chưa thử có tải trên sàn, chưa tune PID. RPM đọc vẫn
  nhảy mạnh do 20 xung/vòng ở cửa sổ 100 ms.
  Chưa giải thích được vì sao trước phải/sau trái từng báo mất xung khi lùi
  trong lúc dây GPIO27 còn lỏng; nghi sụt nguồn nhưng chưa đo điện áp.
  Giữ `STOP_ALL_ON_ENCODER_STALL=False`. Nạp lại cần `http_transport.py`,
  `robot.py`, `wheel.py`, `config.py`.
  **Cập nhật cuối ngày — bánh trước phải:** sau khi thay pin, qua web vẫn có
  lần `encoder_or_stall:front_right` khi lùi (log USB: duty 0,99, dir -1,
  169 xung trước đó, 1,5 s không xung). Bật Wi-Fi AP rồi chạy 6 vòng tiến/lùi
  qua PID trên bo không tái hiện, nên không quy cho Wi-Fi. Bánh này luôn có số
  xung thấp nhất và yếu dần theo vòng (34→11). Người dùng xoay tay thấy bánh
  trước phải nặng hơn và dây motor màu vàng có cục thiếc hàn nhô ra. **Chỉ
  mới tháo bánh ra lắp lại và cắm lại dây; chưa hàn lại hai đầu dây motor,
  cục thiếc vẫn còn.** Bài thử PID trên bo (10 pha tiến/lùi 80 RPM, AP bật)
  sau đó cho trước phải 21–27 xung khi tiến, 44–54 khi lùi, tương đương ba
  bánh kia, không stall; nhưng người dùng báo qua web bánh trước phải VẪN
  lỗi. Hai pha đầu và bài đo riêng trước phải trước đó ra 0 xung ở cả bốn
  bánh; nghi nguồn motor 7,4 V chưa bật lúc đó (suy đoán, chưa đo điện áp),
  từ pha thứ ba tự chạy lại. Nguyên nhân bánh trước phải chưa xác định; cần
  xử lý đầu hàn/cơ khí rồi thử lại. Nếu vẫn stall, cân nhắc cho xe tự thử
  lại bánh stall sau ~1 s (chưa làm; bánh hỏng thật sẽ bị cấp điện lặp lại).
  **Đo điện áp/đo xung bánh trước phải (PWM 100% cố định, 8 s, kê cao):**
  tiến 3,5–5,3 V/1223 xung, lùi 3,6–5,3 V/1498 xung; trước trái tiến
  3,7–5,8 V/1068–1176 xung. Motor và nguồn cấp trước phải không khác trước
  trái. Bài 40 đoạn đổi hướng đột ngột ~60 s qua PID không lỗi. Người dùng
  xác nhận khi web báo `encoder_or_stall:front_right` thì bánh THẬT SỰ đứng
  yên (không phải encoder mất xung). Mọi lần lỗi trước phải ghi nhận đều ở
  `dir -1` (lùi = IN3/GPIO25 lên cao vì `motor_inverted=True`), giống lỗi dây
  GPIO27→IN1 của trước trái trước đó. Nghi dây GPIO25→IN3 (hoặc cọc OUT3/OUT4)
  tiếp xúc chập chờn; chưa xác nhận.
  **Bài lắc dây** (trước phải lùi 100% liên tục 20 s, in xung mỗi 0,5 s,
  người dùng lắc dây GPIO25/IN3/OUT3/OUT4): không lần nào tụt về 0 đột ngột,
  nên chưa thấy dấu hiệu tiếp xúc chập chờn. Nhưng xung giảm ĐỀU từ ~200
  xuống 28 mỗi 0,5 s trong 20 s dù PWM cố định 100%. Khớp với việc bánh
  này "yếu dần theo vòng" và chỉ lỗi khi lái web lâu: nghi motor/hộp số bị
  bó dần khi nóng (bánh nặng hơn khi xoay tay), hoặc L298N/pin; cần so cùng
  bài với bánh trước trái để tách.
  Người dùng sờ: motor/hộp số trước phải và tản nhiệt L298N trước đều KHÔNG
  nóng. Cùng bài 20 s cho trước trái (cùng module L298N, cùng pin): 2,5 s đầu
  0 xung dù PWM 100% lùi (lỗi lùi trước trái/GPIO27 có thể vẫn chập chờn),
  sau đó đều 65–82 xung/0,5 s, không giảm dần. Vậy suy giảm là riêng trước
  phải, không phải L298N/pin. Lưu ý: 65–200 xung/0,5 s cao hơn nhiều so với
  motor TT thông thường (~30 xung/0,5 s nếu 20 khe, 1:1 với bánh), nên có thể
  encoder đếm thừa cạnh; "giảm dần" của trước phải có thể một phần do tín hiệu
  encoder, không chắc là tốc độ thật. Cần xoay tay đúng 10 vòng
  (`check_encoders.py`, kỳ vọng ~200) và quan sát bằng mắt khi chạy 20 s.
  **Xoay tay trước phải ~10 vòng (motor tắt, IRQ riêng GPIO36):** 180 xung
  (18/vòng nếu đúng 10 vòng), khoảng cách ngắn nhất giữa hai xung 25,6 ms,
  0 xung cách nhau <2 ms: encoder không đếm thừa/dội ở tốc độ tay. Chưa kiểm
  tra nhiễu từ motor khi đang chạy (có thể là lý do số xung khi chạy cao).
  **Khi motor trước phải chạy lùi 100% 20 s (IRQ riêng đo khoảng cách xung):**
  ngắn nhất 58 µs; 331 xung cách nhau <1 ms, 474 xung 1–3 ms, 1086 xung
  3–10 ms, 472 xung >10 ms. Với đĩa 20 khe, <3 ms tương ứng >1000 RPM bánh,
  không thể có thật → **encoder trước phải nhận xung giả do nhiễu motor**
  (GPIO36 input-only, không pull-up nội). Số xung/0,5 s: 67→146 vài giây đầu
  rồi giảm còn 13–17 ổn định từ giây ~10; phần "giảm dần" có thể là nhiễu
  giảm chứ chưa chắc tốc độ thật giảm. Chờ người dùng xác nhận bằng mắt.
  Hướng xử lý đề xuất: tụ 100 nF hai cực motor (và motor–vỏ), pull-up/tụ lọc
  cho OUT encoder, tách dây encoder khỏi dây motor; phần mềm bỏ cạnh cách
  nhau <~4 ms trong IRQ (chưa làm).
  Người dùng xác nhận bằng mắt: bánh trước phải CHẬM DẦN RÕ khi chạy liên tục.
  **Đã làm và nạp lọc nhiễu encoder:** `Encoder(min_interval_us=...)` bỏ cạnh
  cách cạnh hợp lệ trước < `ENCODER_MIN_INTERVAL_US=4000` (không cập nhật mốc
  khi bỏ), đếm `rejected`; status bánh có `noise`. Test mới qua (57 unittest).
  Nạp `/encoder.py`, `/wheel.py`, `/main.py`, `/config.py`, đọc lại khớp;
  backup `.device-backups/debounce-20261029/`.
  Chạy lại trước phải lùi 100% 20 s với lọc: lần này chỉ 3 xung bị bỏ (nhiễu
  thay đổi theo lượt). Xung thật/0,5 s: 32–40 lúc đầu (~200–240 RPM, hợp lý
  cho motor TT), giảm dần 19→14→11, rồi từ giây ~17 **về 0: bánh dừng hẳn dù
  PWM vẫn 100%**. Tái hiện được lỗi không qua PID/web. Motor/hộp số không nóng.
  Cần tách motor trước phải với kênh B L298N trước (đổi dây motor hai bánh
  trước giữa OUT1/2 và OUT3/4 rồi chạy lại kênh B).
  Người dùng KHÔNG đổi dây OUT mà đổi dây điều khiển: "tháo IN1/2 thay bằng
  IN3/4" trên L298N trước. **Cấu hình hiện KHÔNG khớp dây; không lái web.**
  Quét tổ hợp (2 s/lượt, PWM 100%): IN 27/26 + PWM 14 hoặc 32 → không bánh nào
  quay; IN 25/33 + PWM 14 hoặc 32 → trước trái quay (311–339 xung/2 s), GPIO36
  có 3–13 xung lẻ. Trước trái quay với CẢ HAI chân PWM nên nghi ENA đang được
  kéo cao (jumper) hoặc dây EN không như cấu hình; kênh B (motor trước phải)
  không chạy với bất kỳ tổ hợp nào. Nghi dây GPIO32→ENB hoặc IN3/IN4 tiếp xúc
  kém (có thể cũng giải thích bánh trước phải yếu dần); chưa xác nhận. Đang
  hỏi người dùng sơ đồ dây hiện tại và trạng thái jumper ENA/ENB.
  Hóa ra dây trước phải chưa cắm vào IN3/IN4 và một lượt quét ra 0 hết vì
  nguồn motor tắt. Sau khi cắm và bật nguồn, quét lại: 25/33 + PWM 14 hoặc 32
  → trước trái quay cả hai chiều (ENA có vẻ luôn bật, nghi jumper ENA);
  27/26 + PWM 32 → trước phải quay CHỈ khi GPIO26 cao (220 xung/2 s), khi
  **GPIO27 cao thì 1 xung (không quay)**. Lỗi đi theo dây GPIO27: trước đó
  trước trái (IN1=GPIO27) cũng hỏng chiều lùi chập chờn. Nghi chân GPIO27 hoặc
  dây dupont của nó; chưa đo.
  Bài 20 s kênh B qua GPIO26 cao + PWM 32: trước phải 62→16–19 xung/0,5 s
  (124 xung nhiễu bị lọc), vẫn chậm dần dù đã đổi dây điều khiển → chậm dần
  không do dây GPIO25/33; còn lại motor/hộp số trước phải, dây motor OUT3/OUT4
  hoặc kênh B L298N. Bước tiếp: đổi dây OUT motor giữa hai kênh.
  **Sau khi đổi dây OUT** (motor trước phải → OUT1/2 kênh A, trước trái →
  OUT3/4 kênh B, dây IN giữ như trên): kênh B (GPIO26 cao, PWM 32) chạy motor
  trước trái đều 59–69 xung/0,5 s suốt 20 s → **kênh B L298N tốt**. GPIO27 cao
  + PWM 32 giờ chạy được (52–77) → dây GPIO27 đã ổn sau khi người dùng xử lý.
  Kênh A (motor trước phải): PWM 14 → không quay cả hai chiều; PWM 32 → quay
  (44–67 xung/0,5 s). Trước đó (motor trước trái trên kênh A) chạy với cả PWM
  14 lẫn 32. Vậy GPIO32 bật được cả ENA và ENB, còn GPIO14 lúc được lúc
  không → nghi ENA và ENB bị nối chung (jumper/dây/chạm) và dây GPIO14 lỏng.
  Nếu GPIO14 và GPIO32 cùng nối một nút EN, hai chân output kéo ngược nhau
  (một cao một thấp) làm EN ở mức lơ lửng → motor yếu/chập chờn và có thể
  hại chân ESP32; khớp với việc bánh trước yếu dần. Chưa xác nhận.
  Encoder GPIO36 đếm 24–52 xung/0,5 s (612 nhiễu bị lọc) khi chỉ motor trước
  trái chạy và motor trước phải không có điện → dây encoder trước phải nhận
  nhiễu rất mạnh, bộ lọc 4 ms chưa đủ; cần pull-up/tụ lọc và đi dây tách.
  Người dùng xác nhận không có jumper nối ENA–ENB và đã **trả toàn bộ dây về
  đúng cấu hình gốc**. Kiểm tra chéo EN (1,5 s/lượt, PWM 100%, đếm cả 4
  encoder, lọc 4 ms): mỗi bánh quay cả hai chiều với đúng chân PWM của nó,
  không làm quay bánh khác: FL 203/183, RR 257/251, RL 218/220, FR 103/179
  (tiến/lùi). Chéo FL IN + PWM32 và FR IN + PWM14 (PWM gốc ép thấp) → 0 hết:
  **EN không còn dính nhau**; hiện tượng một PWM bật hai kênh lúc trước là do
  dây đang đổi dở. Bánh trước phải vẫn yếu nhất (103 khi tiến) và nhiễu nhất
  (22/136 xung bị lọc; bánh khác 0–4). Chưa chạy lại bài 20 s với dây gốc.
  **Kết thúc phiên 29/10:** người dùng sẽ mua motor mới thay bánh trước phải
  (ngày 30/10). Đã đối chiếu SHA-256 toàn bộ 12 file `.py` + `/web/index.html`
  trên bo với `firmware/`: tất cả khớp, không cần nạp thêm; soft reboot, web
  ready, boot `4a3a67783afe3659`, không brownout. Bo đang `HARDWARE_ENABLED=True`,
  `BREAKAWAY_DUTY=0.75`, `ENCODER_MIN_INTERVAL_US=4000`, dây đúng cấu hình.
  Việc tiếp: thay motor trước phải (nên hàn tụ 100 nF hai cực mỗi motor), chạy
  lại bài 20 s và bài PID 10 thao tác, rồi thử web; xem lại `BREAKAWAY_DUTY`
  khi motor mới có ngưỡng khởi động thấp hơn.
- **30/10:** người dùng báo cấp nguồn ESP32 bằng USB thì chạy không sao,
  chuyển sang bộ giảm áp (đầu vào chung pin 7,4 V với motor) thì bị lỗi; chưa
  rõ lỗi gì (mất web, reset, khung brownout đỏ?). Trùng với brownout đã xác
  nhận trên bo mới ngày 29/10 khi dùng giảm áp. Đang hỏi thông tin; chưa đổi code.
  Người dùng chỉnh đầu ra giảm áp lên 5,157 V, vẫn lỗi. Probe qua Wi-Fi (không
  USB, bo chạy giảm áp), 10/10 `/api/ping` thành công: boot
  `b62c0e6d0fcc2797`, **reason=brownout, raw_cause=3, brownout=true**,
  uptime ~51–70 s → lần reset gần nhất ~50 s trước là brownout. Tăng áp đầu ra
  không đủ; nghi sụt ngắn khi motor kéo dòng (pin chung). Hướng tiếp: tụ
  470–1000 µF sát 5V/VIN ESP32, dây ngắn/to, bộ giảm áp đủ dòng, hoặc nguồn
  riêng cho ESP32 (sạc dự phòng USB, tháo OUT+ giảm áp). Máy tính đã về Wi-Fi cũ.
  Người dùng chọn cấp ESP32 bằng sạc dự phòng 10000 mAh qua cáp USB của bo
  (tháo OUT+ giảm áp khỏi 5V/VIN, giữ GND chung; lưu ý sạc dự phòng tự tắt khi
  dòng thấp). Phương án nguồn đã tư vấn: encoder giữ 3V3 của ESP32; HC-SR04
  lấy 5V/VIN phía ESP32 (vẫn qua cầu chia áp ECHO); servo SG90 lấy 5 V từ bộ
  giảm áp cũ (phía pin motor) kèm tụ 470–1000 µF, không lấy từ ESP32 và không
  nối thẳng 7,4 V; mọi GND nối chung. Chưa kiểm chứng brownout sau khi đổi
  nguồn. Servo/HC-SR04 vẫn chưa có code.
  Dọn dẹp: xóa các thư mục `__pycache__` (gốc, firmware, tests, tools). Giữ
  `.device-backups/` (11 MB, đã gitignore; gồm bản flash gốc 4 MB của bo mới
  trong `new-board-20261029-153729` và log chứng cứ được nhắc trong nhật ký).
  Dùng các bài đo trực tiếp qua raw REPL khi cần chẩn đoán: mở cổng serial
  làm bo reset, phải đợi ~5 s trước khi Ctrl+C.

### Kết quả mới nhất: vẫn mất kết nối khi người dùng thử chạy

- Sau bản sửa EIO + giảm RAM HTML + cleanup, đã hướng dẫn tải lại web,
  đăng nhập, tắt camera, giữ bánh kê cao, bật nguồn motor và kéo tiến
  **80 RPM khoảng 1 giây rồi thả**. Người dùng trả lời nguyên văn:
  **“Vẫn mất phản hồi hoặc mất Wi-Fi”. Lỗi chính CHƯA được giải quyết.**
  Câu trả lời chưa phân biệt timeout HTTP với SSID biến mất, chưa cho biết
  bánh thực tế quay thế nào; không tự điền các chi tiết đó.
- Logger USB `13978` **đã kết thúc/đóng cổng**, không còn ghi nền. Kết quả
  `manual-drive-usb.json`: **300,0 giây; 1 boot header ban đầu khi mở serial;
  0 thông báo brownout; không traceback; web khởi động thành công**.
  File `.log` chỉ có startup (527 byte), không thêm reset hoặc dòng
  `HTTP I/O error:` trong cửa sổ này. Boot ID: `b62fb8a3fee32c6c`,
  power_on/cause1/raw1/brownout false. Chưa có timestamp chính xác của
  thao tác người dùng để chứng minh toàn bộ lần lỗi nằm trong cửa sổ log.
  Không suy ra đã loại trừ mọi sụt nguồn, hoặc mọi lần mất mạng đều reset.
- Log/manifest bản cuối nằm tại
  **`.device-backups/runtime-cleanup-20261029-181038/`**. Lượt logger này
  không gửi lệnh motor từ agent. Chưa có probe Wi-Fi/API sau phản hồi lỗi
  mới nhất; chưa mở lại serial hoặc reset để giữ trạng thái lỗi nếu còn.

### Thiết bị, nguồn và cấu hình đang dùng

- **Bo MỚI**: ESP32-D0WD-V3 rev3.1, flash 4 MB, MicroPython **v1.29.0**
  (2026-08-24), CP2102 `/dev/ttyUSB0`, ID `ec64c9b8a9a0`, AP/BSSID
  **`ec:64:c9:b8:a9:a1`**. Bo cũ có BSSID `38:3e:51:6f:a3:61`.
  Cổng ổn định: `/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0`.
- Source và config đã nạp: **`HARDWARE_ENABLED=True`**; bốn motor/encoder
  GPIO được khởi tạo, khởi động ở PWM=0 và chưa arm. Config nạp/đọc lại
  đối chiếu tại `.device-backups/hardware-enable-20261029-181726/`.
  `STOP_ALL_ON_ENCODER_STALL=False` vẫn là thay đổi tạm theo yêu cầu người
  dùng: lỗi encoder/stall khóa bánh lỗi, không dừng toàn bộ các bánh khác.
  Giữ watchdog **700 ms**, timeout lệnh web **600 ms**, status/ping **1200 ms**;
  không tăng các mốc này để che lỗi mất phản hồi.
- Giữ Wi-Fi riêng **ESP32-Web**, AP WPA2, **2,4 GHz, kênh 11 (2462 MHz)**,
  trang **`http://192.168.4.1`**. Tài khoản đã đặt theo người dùng trong
  `firmware/config.py`. Thông báo hệ điều hành “không có Internet” là
  bình thường với AP này, khác timeout API trên trang điều khiển.
  Camera iPhone: `http://192.168.4.2:8080/stream.mjpg`, yêu cầu tắt khi chẩn đoán.
- Cấu hình nguồn của bài thử gần nhất: **USB cấp ESP32; OUT+ bộ giảm áp
  đã tách khỏi 5V/VIN; pin 7,4 V cấp motor; GND chung; bánh kê cao**.
  Đã yêu cầu bật nguồn motor để thử; **chưa xác nhận đã tắt lại sau thử**.
  Không coi trạng thái motor-off trước nạp là trạng thái hiện tại.
  Người dùng đã xác nhận tháo đủ 4 jumper ENA/ENB; hai 5V-EN cũng đã tháo
  vì đang cấp 5 V logic bên ngoài. Không yêu cầu lắp lại 5V-EN theo suy đoán.

### Những gì đã sửa/nạp và mức kiểm chứng

- Đã sửa đóng socket khi quá tải, báo timeout có đường API thay AbortError
  mơ hồ; thả joystick/về vùng chết gửi STOP trả lease, bỏ reply cũ, ngừng
  gửi control lúc đứng yên. Watchdog và yêu cầu arm lại sau lỗi vẫn giữ.
- **Có crash EIO thật ở bản trước** trong
  `.device-backups/release-fix-20261029-172006/manual-drive-usb.log`:
  `OSError: [Errno 5] EIO`, main → asyncio.run → wait_io_event → `>>>`.
  Thêm `http_transport.py` dùng socket nonblocking/yield 10 ms để HTTP
  không dùng poller chung; bắt lỗi từng request/listener, dừng/hủy lease,
  đóng socket và mở lại listener khi cần. Không tự arm hoặc reset Wi-Fi.
  Chưa xác định nguyên nhân gốc gây EIO của socket; log mới nhất không
  ghi lại traceback này, nên không gán mọi lần mất mạng mới cho cùng lỗi.
- `FileBody`/`main.load_html` stream trang theo khối **1024 byte**, không
  giữ toàn bộ ~48 KB HTML trong RAM. `main.main` giữ robot/server bên ngoài
  coroutine để dừng/deinit motor và đóng listener/client trong finally,
  kể cả lỗi scheduler. Ba module `http_transport.py`, `web_server.py`,
  `main.py` đã nạp/đọc lại đối chiếu byte trong backup runtime-cleanup.
  `web/index.html`, `test_wifi.py` và config đã cập nhật ở các lượt trước.
- Kiểm thử cuối đã có: **53 unittest**, Node joystick qua; model bốn bánh
  giả lập không GPIO: **30/30** chu kỳ Chrome kéo/thả ở port8081; app chính
  port80 với GPIO thật: **10/10** chu kỳ kéo/thả ở **0 RPM**, sau thả
  armed false/lease rỗng, PWM/target=0, không control traffic lúc đứng yên.
  Log `fake-wheel-browser-181549.json` và `release-browser-181915.json`
  trong runtime-cleanup. Boot app thật khi test: `cb81b659c96e212e`; sau đó
  mở logger tạo boot `b62fb8a3fee32c6c`, không coi đổi ID này là reset tự phát.
  **Các test 0 RPM/model không chứng minh chạy motor thật đã ổn.**
- Brownout đã được xác nhận ở bo cũ và một lượt bo mới dùng giảm áp
  (`hardware-enable-20261029-162313/external-power-probe-163642.json`).
  Điều đó không chứng minh mọi timeout mới đều do nguồn; đồng hồ đo tĩnh
  cũng chưa loại trừ nhiễu/sụt áp ngắn. Chưa kết luận bo mới hỏng, nguồn
  là nguyên nhân duy nhất, hoặc IRQ encoder ngập.

## Lịch sử kỹ thuật — trạng thái tại từng thời điểm

Các ghi chú dưới đây là lịch sử, không phải tiến trình đang chạy. Các session
tool cũ không được coi là còn hoạt động. Trạng thái hiện hành ở mục trên.

- **Đang kiểm chứng bản giảm RAM HTML, motor vẫn khóa.** 35/35 status
  GPIO-disabled giữ nguyên dây/USB đã qua (`api-check-175424.json` trong
  web-only-diag backup), nhưng chưa đủ để kết luận GPIO gây mất mạng vì
  response/luồng lệnh khác khi bật 4 bánh. Đã chuẩn bị đối chiếu 4 Wheel
  giả lập trong RAM, giữ cùng giao diện/API/status đầy đủ, không GPIO.
  Lượt đầu lỗi mô hình FakeEncoder thiếu counts_per_rev; đã sửa và kiểm
  tra cục bộ status/control của model. Lượt tiếp theo không chạy được do
  MemoryError khi `main.load_html` cấp phát 48.640 byte trong môi trường
  chẩn đoán RAM. Hai lỗi này thuộc bài thử tạm, không gán thành lỗi user
  hoặc bằng chứng GPIO hỏng. Log `.initial-model-error` và
  `fake-wheel-browser-175647.json`, `fake-wheel-browser-175921.json` trong
  io-fix backup; không kết luận phép so sánh từ các lượt setup lỗi.
  **Cải thiện bộ nhớ:** `FileBody` giữ path/size, `main.load_html` không
  đọc hết trang; `WebServer.respond` mở file và gửi từng 1024 byte, đóng
  file khi hoàn tất/abort. Giảm khoảng 48 KB HTML giữ thường trực, giữ
  bytes response cho API và compatibility tests. tools/test_wifi cũng dùng
  FileBody. README cập nhật. **52 unittest + Node joystick qua**, gồm
  file lớn 64 KB byte-exact/Content-Length, không read vượt 1 KB, đóng
  file khi writer lỗi. Chưa khẳng định áp lực RAM là nguyên nhân duy nhất
  của EIO/timeout trong app thông thường (MemoryError bắt được ở harness).
  Đã nạp/byte verify web_server.py, main.py, test_wifi.py; backup
  `.device-backups/memory-fix-20261029-180450/`, web ready, Hardware False,
  boot `2234b7e35027b8c8`. Đang chạy 30 chu kỳ Chrome 0 RPM với 4 bánh
  giả lập không GPIO, RAM-only health; session `47369`. Kết thúc script
  phải khôi phục main bình thường với HARDWARE_ENABLED=False. Source
  GPIO hiện vẫn False, không hướng dẫn chạy motor trước khi bật lại và
  xác nhận kết quả thử mới.
- **Trạng thái mới nhất: `HARDWARE_ENABLED=False` ĐÃ NẠP để chẩn đoán riêng
  Wi-Fi, chưa cho thử quay motor tiếp.** HTTP I/O fix đã xử lý EIO giả lập
  và qua 80 status, nhưng Chrome 0 RPM qua 3 chu kỳ rồi timeout; lượt ghi
  USB đồng thời tiếp theo cũng timeout, trong cửa sổ đó 0 reset/brownout/
  traceback/HTTP I/O error. Không coi sửa EIO là đã sửa toàn bộ mất mạng.
  Log io-fix backup: `release-browser-174234.json`, `release-browser-174514.json`,
  `zero-rpm-simultaneous-usb.json`/`.log`. Đã chạy thêm logger **chỉ RAM**
  (`/tmp/xe_esp32-io-ram-health.py`) bọc main.WebServer, ghi health mỗi 2 giây
  trong lúc Chrome thử 0 RPM. Lại timeout, nhưng PID vẫn ~43–58 ms, fault
  null, PWM cả 4=0, raw encoder counts cả 4=0, active/sockets trở về 0,
  free heap dao động 12.544–49.680 byte và được GC thu hồi. Không có bằng
  chứng IRQ encoder ngập hoặc coroutine đã chết trong lượt này. AP active
  true; client_connected true rồi false, nhưng Chrome tự khôi phục mạng PC
  sau lỗi nên chưa gán việc false đó thành nguyên nhân ban đầu. Log
  `ram-health.json`, `ram-health-usb.log`; cuối test khôi phục main bình thường,
  không lưu wrapper vào firmware. Nguồn motor vẫn tắt theo xác nhận người dùng.
  Để tách yếu tố GPIO, đã đổi source config False, README ghi rõ khóa tạm,
  sao lưu/nạp riêng config/byte verify rồi soft reboot. Backup
  `.device-backups/web-only-diag-20261029-175241/`, boot
  `934dede07cf3aafd`, dòng HARDWARE_ENABLED=False và web ready đã xác nhận.
  Đang chạy 35 status khi vẫn giữ nguyên dây/USB, session `23740`; cần
  xem kết quả trước khi quyết định thử bo không dây ngoại vi. Chưa yêu cầu
  người dùng tháo dây và chưa kết luận nguồn/GPIO/Wi-Fi là nguyên nhân duy nhất.
- **29/10 — ĐÃ BẮT TRACEBACK THẬT khi người dùng vừa chạy 1 giây mất kết
  nối: `OSError: [Errno 5] EIO` tại `asyncio/core.py:wait_io_event`.** Log
  `.device-backups/release-fix-20261029-172006/manual-drive-usb.log`:
  sau web ready, chương trình thoát qua main.py → asyncio.run →
  run_until_complete → wait_io_event, về `>>>`. Logger tổng 296,5 giây,
  một reset ban đầu do mở serial, 0 brownout, traceback xuất hiện khoảng
  cửa sổ 210–240 giây. Đây là bằng chứng chương trình chết trong lượt này;
  không gán lượt này thành brownout. Nguyên nhân gốc làm socket poll EIO
  (kết nối/driver/nhiễu/descriptor) chưa xác định. Mã nguồn MicroPython
  v1.29.0 ports/esp32/modsocket.c trả EIO khi select() socket lỗi; core
  wait_io_event gọi poller bên ngoài khối try xử lý task nên lỗi làm thoát
  cả scheduler. Đã dừng logger, người dùng xác nhận tắt 7,4 V, giữ USB và
  OUT+ giảm áp tách trước khi sửa/nạp.
  **Bản sửa HTTP I/O:** thêm `firmware/http_transport.py` dùng socket
  nonblocking + sleep async 10 ms; không đưa socket HTTP vào poller chung.
  EIO đọc/ghi được bắt trong từng request, dừng xe/hủy lease; listener lỗi
  được đóng và mở lại sau 250 ms, không reset Wi-Fi hoặc tự arm. Giữ tối
  đa 4 kết nối và deadline request/response cũ. `main.main` giữ tham chiếu
  Robot bên ngoài asyncio.run, đóng motor trong finally đồng bộ ngay cả
  khi scheduler lỗi trước khi coroutine chạy được finally. `run(robot=None)`
  vẫn dùng riêng được; khi truyền Robot, coroutine dừng đầu ra và đóng
  server, main mới deinit motor. Frontend thả/trả lease và mọi watchdog,
  GPIO/chiều quay/auth/Wi-Fi vẫn giữ bản mới nhất.
  Test trên máy: **51 unittest + Node joystick qua**, có TCP localhost thật,
  EIO read/write dừng lease nhưng HTTP còn dùng được, EIO listener mở lại,
  đóng request chưa đủ header, cleanup kể cả scheduler EIO/KeyboardInterrupt.
  Backup trước nạp `.device-backups/io-fix-20261029-173631/`, đã nạp và
  đối chiếu byte `/http_transport.py`, `/web_server.py`, `/main.py`.
  Native test ban đầu qua TCP loopback trên MCU timeout; đã đổi phần
  fault-injection sang socket giả lập rõ ràng và giữ kiểm tra listener bind
  thật, tách khỏi kiểm tra Wi-Fi bên ngoài. Một lượt setup bind -203 và
  việc socket MCU không có getsockname được chẩn đoán/điều chỉnh test;
  app đã khởi động được qua cold boot. Native test cuối **EIO read/write/
  listener đều xử lý, 3 HTTP handler tiếp theo trả 200, listener mở lại**,
  không khởi tạo GPIO motor trong selftest. Log `native-eio-handler-selftest.log`.
  Sau soft reboot, web ready, boot ID `2b42c86f1f409571`. Qua Wi-Fi thật:
  **6/6 kết nối quá tải đóng, 80/80 status thành công**, cùng boot ID,
  đủ 4 bánh/PWM target 0/không arm. Log `socket-check-174146.json`.
  Đang chạy Chrome 10 chu kỳ kéo/thả ở 0 RPM, session `13453`. Chưa có
  kết quả chạy motor thật với bản HTTP I/O mới. Cần nạp đủ module mới nếu
  dùng Thonny; README đã ghi phụ thuộc `http_transport.py`.
- **29/10 — người dùng chạy lâu hơn nhưng mất phản hồi lúc THẢ joystick;
  đã nạp bản sửa trả phiên khi thả.** Trước sửa, probe không reset ghi
  boot ID `e2c5bab40c5e1d2c` vẫn giống lượt trước, uptime ~572–577 giây;
  6 public ping đầu thành công (một phản hồi 935 ms), 6 mẫu sau timeout,
  tải trang cũng timeout; ICMP 9/10. Không có boot mới đọc được trong phần
  timeout nên chưa biết có reset sau đó. Log socket-fix backup:
  `unresponsive-web-probe-171721.json`. Không khẳng định lỗi nguồn hoặc
  phần mềm là nguyên nhân duy nhất.
  Phát hiện frontend giữ lease và gửi `/api/control` tốc độ 0 mỗi 150 ms
  cả sau khi thả, lệnh dừng 0 còn phải chờ request đang bận. Đã đổi `stop`
  và thao tác về vùng chết thành trả lease ngay bằng `/api/stop`, tăng
  generation để hủy xử lý reply cũ, ngừng heartbeat khi đứng yên. Nhánh
  STOP không chờ controlBusy; kéo mới vẫn đợi STOP trước rồi lấy lease mới.
  Watchdog 700 ms và timeout điều khiển 600 ms giữ nguyên. Thêm regression:
  thả không giữ lease/không traffic control lúc đứng yên, STOP ngay khi
  request chuyển động đang pending, bỏ qua reply cũ, về vùng chết trả lease.
  Bản cũ thất bại assertion còn session, bản mới qua toàn bộ Node. Python
  45 test vẫn qua. README cập nhật hành vi thả mới.
  Người dùng xác nhận tắt 7,4 V, giữ USB và OUT+ giảm áp tách; đã nạp riêng
  `/web/index.html`, backup/byte verify đúng bo ID `ec64c9b8a9a0`, web ready.
  Backup `.device-backups/release-fix-20261029-172006/`.
  Chrome thật dùng CDP mousePressed/mouseReleased **10/10 chu kỳ ở 0 RPM**:
  sau mỗi lần thả session null, armed false, 0 request control trong thời
  gian đứng yên, HTTP status 200/online, đủ 4 bánh PWM/target=0. Boot ID
  `af35790162374fdc` không đổi, máy tính khôi phục mạng cũ. Có gửi arm,
  control với max_rpm=0 và stop; **không gửi yêu cầu quay bánh**. Log
  `release-browser-172208.json`. Chưa kiểm chứng khi motor quay/dừng thật.
  Đang mở logger USB chỉ đọc 300 giây, session `60014`, stop file
  `/tmp/xe-esp32-release-fix-stop-monitor`; log `manual-drive-usb.log`/`.json`
  trong backup release-fix. Mở serial có thể reset ban đầu; cần đợi web
  ready rồi cho người dùng tải lại trang/đăng nhập, USB cấp ESP32, OUT+ vẫn
  tách, kê bánh, bật motor và thử tiến ngắn/thả để đối chiếu. Chưa có phản
  hồi của người dùng về chạy thật sau bản sửa thả này.
- **Sau sửa socket, người dùng báo “trang web không phản hồi”.** Probe qua
  Wi-Fi không mở USB/reset/arm: đúng BSSID bo mới, signal 100/100;
  12/12 public HTTP ping thành công, 10/10 ICMP, tải `/` HTTP 200 đủ
  48.458 byte khớp bản nguồn mới. Boot ID `e2c5bab40c5e1d2c`, power_on/
  raw1/brownout false, uptime ~169,3–180,2 giây giữ nguyên trong cửa sổ thử.
  Khác ID logger trước, không biết người dùng đã cấp nguồn lại lúc nào;
  không suy diễn nguồn đã được loại trừ hoặc lỗi gián đoạn đã hết.
  Log `unresponsive-web-probe-171033.json` trong backup socket-fix.
  Sau thử tự khôi phục mạng ban đầu; đọc NetworkManager thấy máy tính ở
  `Phong tang 2`, chỉ có wlo1, Ethernet unavailable. Vì vậy nếu người dùng
  mở bằng máy tính này, cần nối lại ESP32-Web khi dùng địa chỉ 192.168.4.1.
  Không tự giữ PC trên AP qua nhiều tool call vì mất Internet của phiên trợ
  lý; mọi probe phải tự restore trong finally. Đang hỏi người dùng lỗi hiện
  trên máy tính/iPhone/cả hai để phân biệt, chưa đổi firmware thêm.
- **Sau bản sửa socket — logger USB đã kết thúc, chưa có xác nhận quay bánh.**
  `manual-drive-usb.json` ghi 180,1 giây, một reset ban đầu khi mở serial,
  0 thông báo brownout, 0 traceback, web ready. Người dùng chỉ phản hồi
  Wi-Fi có mạng nhưng báo không có Internet; đã giải thích ESP32-Web là
  mạng AP nội bộ, giữ kết nối và mở `http://192.168.4.1`. Không coi câu trả
  lời này là đã thử joystick hoặc xác nhận motor hoạt động/mất mạng đã hết.
  Logger session 66956 đã đóng; không nói đang tiếp tục ghi log nếu chưa
  mở logger mới. Chưa mở lại vì mở serial có thể reset và làm mất phiên
  đăng nhập. Vẫn chờ người dùng vào web và thử ngắn theo hướng dẫn trước.
- **29/10 — sửa đóng socket khi quá tải và báo lỗi AbortController, đã nạp.**
  Người dùng báo kéo joystick một lúc hiện `signal is aborted without reason`,
  lặp hai lần rồi web mất phản hồi/Wi-Fi ngắt. Xác nhận lần này ESP32 chỉ
  dùng USB, OUT+ giảm áp đã tách, pin 7,4 V chỉ cấp motor. Không quy mọi
  lần lỗi này cho nguồn hoặc coi brownout trước đó là nguyên nhân đã đủ.
  Phát hiện `WebServer.handle` nhánh `active_clients >= 4` chỉ gọi
  `writer.close()`. MicroPython v1.29.0 `extmod/asyncio/stream.py` cho thấy
  Stream.close là no-op, socket chỉ đóng trong `wait_closed`; nhánh từ chối
  có thể giữ socket chờ GC. Thêm regression với writer có đúng ngữ nghĩa
  này: bản cũ thất bại, bản sửa qua. Dùng chung `close_client` có deadline
  cho cả nhánh từ chối và cleanup thường; chỉ giảm active_clients sau cleanup.
  Frontend gom fetch/đọc JSON vào `requestJSON`, phân biệt deadline cục bộ
  thành TimeoutError có đường API và số ms, thay thông báo AbortError mơ hồ.
  Không tăng timeout điều khiển 600 ms hoặc watchdog 700 ms, không tự chạy
  lại sau lỗi, không đổi chân/chiều quay/Wi-Fi/STOP_ALL_ON_ENCODER_STALL.
  Test: **45 unittest và joystick Node đều qua**, gồm hủy phản hồi, quá tải
  rồi phục hồi, timeout lệnh dừng/trả lease và timeout lúc đọc body JSON.
  Người dùng đã tắt motor 7,4 V, giữ USB và OUT+ tách để nạp. Đã sao lưu,
  nạp/đọc lại từng byte `/web_server.py`, `/web/index.html` vào đúng bo mới
  `ec64c9b8a9a0`; web khởi động thành công. Backup
  `.device-backups/socket-fix-20261029-165814/`.
  Trên bo thật: giữ 4 request thiếu header, **6/6 kết nối vượt giới hạn đóng
  trong 44–102 ms**; tiếp theo **80/80 authenticated status thành công**,
  đủ 4 bánh/không arm/PWM và target 0, boot ID `c5bc79dafa876a76` không đổi.
  Chrome thật đăng nhập/poll **15/15 online**, HTTP 200, render đủ 4 bánh,
  không gửi lệnh motor; mỗi lượt đã khôi phục Wi-Fi PC. Chưa chứng minh lỗi
  mất mạng khi motor quay đã hết. Đang mở logger USB 180 giây (chỉ đọc),
  chờ web ready rồi hướng dẫn người dùng tải lại trang/đăng nhập, giữ kê
  bánh, bật pin motor với USB cấp ESP32/OUT+ vẫn tách, thử tiến ngắn để
  đối chiếu log. Session logger `66956`, stop file
  `/tmp/xe-esp32-socket-fix-stop-monitor`; log `manual-drive-usb.log`/`.json`
  trong backup sửa socket. Mở serial có thể gây một reset ban đầu; không
  tính reset đó là mất kết nối khi lái. Chưa có kết quả thử motor sau sửa.
- **29/10 — xác nhận brownout trên BO MỚI khi dùng bộ giảm áp.** Người
  dùng báo để yên sau khi chuyển về nguồn giảm áp vẫn mất phản hồi, rồi
  Wi-Fi bị ngắt. Probe qua đúng BSSID `ec:64:c9:b8:a9:a1`, không mở serial,
  không reset và không gửi lệnh motor, đọc được boot ID `eb557b8394012fe4`,
  `reason=brownout`, `cause=1`, `raw_cause=3`, `brownout=true`. Đối chiếu
  MicroPython v1.29.0 `ports/esp32/modmachine.c`: ESP_RST_POWERON và
  ESP_RST_BROWNOUT cùng trả MP_PWRON_RESET; IDF v5.5.2
  `components/esp_system/port/soc/esp32/reset_reason.c` trả hint brownout
  với reset CPU/core software, nên kết hợp này xác nhận brownout của lần
  boot gần nhất. Chưa chứng minh mọi lần timeout đều trùng brownout hoặc
  bộ giảm áp là linh kiện hỏng. Trong cửa sổ probe 12 giây: 12/12 public
  HTTP ping, 10/10 ICMP thành công, boot ID không đổi, uptime ~169,5–180,5
  giây. Không coi cửa sổ ngắn này là lỗi đã hết. Máy tính đã về Wi-Fi cũ.
  Log `.device-backups/hardware-enable-20261029-162313/external-power-probe-163642.json`.
  Giữ xe chưa chạy; cần kiểm tra điện áp đường giảm áp → 5V/VIN → 3V3
  ngay lúc mất kết nối, ưu tiên MIN/MAX nếu có. Số đo đứng yên cũ không
  loại trừ sụt áp ngắn. Phần cứng vẫn True; chưa thay code/nạp thêm.
- **29/10, sau khi nối dây bo mới — đã bật phần cứng nhưng CHƯA chạy motor.**
  Người dùng xác nhận đã nối dây, kê đủ bốn bánh, đang quan sát. Ban đầu dùng
  riêng bộ giảm áp; để nạp, đã xác nhận tắt nguồn 7,4 V, tách OUT+ bộ giảm áp
  khỏi ESP32 và cắm USB. Đã đổi `firmware/config.py` thành
  `HARDWARE_ENABLED=True`, cập nhật README, chạy validate_hardware trên máy.
  Nạp riêng `/config.py` vào đúng board ID `ec64c9b8a9a0`, sao lưu cấu hình
  cũ, đọc lại đối chiếu byte, tạo đủ bốn Wheel trong REPL để xác nhận ready,
  không arm, không fault, toàn bộ PWM/target bằng 0, rồi close và soft reboot.
  Web khởi động thành công; backup `.device-backups/hardware-enable-20261029-162313/`.
  Bản backup trước `.device-backups/hardware-enable-20261029-162139/` là lượt
  thất bại khi chưa vào raw REPL, chưa ghi cấu hình. **Chưa gửi lệnh motor.**
  Tuy nhiên kiểm tra API sau nạp: 1/10 mẫu thành công, 9 timeout dù RSSI
  khoảng -35 dBm; máy tính đã trả về mạng cũ. Sau lỗi, mở USB ghi 18 giây
  thấy 79 chuỗi `rst:`/POWERON_RESET lặp, không traceback, không thông báo
  brownout, sau đó web chạy lên. Lượt USB trước nạp cũng có 80 chuỗi `rst:`
  khi phần cứng còn False. Không gán tất cả thành brownout hoặc khẳng định
  thời điểm reset trùng API vì mở serial có thể gây reset; đang đối chiếu
  bằng log USB liên tục trong cùng lượt API. Chưa cho thử chạy xe đến khi
  rõ kết quả; nguồn motor vẫn tắt theo xác nhận gần nhất của người dùng.
  **Lượt đối chiếu tiếp theo:** giữ USB logger mở trong suốt lượt API,
  10/10 status thành công, không fault/arm, đủ bốn bánh PWM/target=0;
  boot ID `f14d65c5b65e9877` giữ nguyên. Log tổng 37,3 giây có một reset
  khi mở serial, trong giai đoạn API có 0 reset/brownout/traceback.
  Lưu `simultaneous-usb-api.json` và `.log` trong backup nạp trên.
  Không coi lượt thành công ngắn này là đã sửa lỗi gián đoạn trước đó.
  Đã hướng dẫn người dùng rút USB, nối lại OUT+ bộ giảm áp vào 5V/VIN,
  bật 7,4 V, giữ xe kê cao, đăng nhập lại và để yên 1 phút chưa kéo
  joystick. Đang chờ kết quả trên nguồn giảm áp; chưa gửi lệnh motor.
- **29/10 — đã nạp và kiểm tra bo ESP32 MỚI, chỉ USB, không dây ngoại vi.**
  Người dùng đã xác nhận bo mới chỉ cắm USB máy tính. Chip
  ESP32-D0WD-V3 rev3.1, flash 4 MB, CP2102 `/dev/ttyUSB0`, MAC gốc
  `ec:64:c9:b8:a9:a0`, BSSID AP `ec:64:c9:b8:a9:a1`; khác bo cũ
  BSSID `38:3e:51:6f:a3:61`. Đã sao lưu toàn bộ flash gốc 4 MB và
  đối chiếu digest với thiết bị trước khi erase, cài MicroPython chính thức
  v1.29.0 (2026-08-24), nạp đủ 13 file (12 Python và `/web/index.html`),
  kiểm tra cú pháp trên bo và đọc lại đối chiếu từng byte. Backup/log/manifest:
  `.device-backups/new-board-20261029-153729/`.
  **`firmware/config.py` và cấu hình đã nạp đều `HARDWARE_ENABLED=False`**;
  joystick khóa, không khởi tạo Motor/Encoder/PWM/IRQ, không gửi lệnh motor.
  README đã cập nhật trạng thái này. `tools/test_wifi.py` cũng đã nạp thành
  `/test_wifi.py`; mặc định bo vẫn chạy `/main.py` đầy đủ ở chế độ khóa.
  Giữ Wi-Fi riêng ESP32-Web, địa chỉ `http://192.168.4.1`, đăng nhập như cũ.
- **Kết quả thử bo mới:** log USB liên tục 300,1 giây ghi nhận 0 brownout,
  0 traceback, web khởi động thành công; có một POWERON reset khi mở cổng
  serial, không có reset bất thường tiếp theo. API xác thực 35/35 mẫu
  thành công trong khoảng 35 giây, không fault, motor chưa sẵn sàng/chưa arm.
  Sau khi đóng serial, Chrome headless tải trang thật, đăng nhập, kiểm tra
  giao diện 35 mẫu đều online, HTTP status 200/render thành công, rồi đăng
  xuất. Cả hai lượt giữ cùng boot ID `f044eb258f6baa5c`. Mỗi lượt Wi-Fi tự
  khôi phục mạng máy tính ban đầu; không nhầm 5 phút log USB thành 5 phút
  polling API. Log: `stability-usb.json`, `api-check-160022.json`,
  `browser-160833.json` trong backup trên. Lượt API trước đó không có mẫu
  vì cache quét mạng chưa nhận BSSID mới; quét lại rồi kết nối thành công.
  Người dùng đang thử Safari iPhone và báo trang vẫn kết nối; chưa có xác
  nhận riêng đã đủ 3 phút. Chỉ xác nhận bo mới ổn trong các bài thử không
  tải này; **chưa thử nguồn giảm áp, motor, encoder mới hoặc chứng minh bo
  cũ hỏng**. Muốn thử xe cần nối dây đúng và bật lại phần cứng sau khi xác
  nhận sẵn sàng quan sát/kê bánh. Kiểm thử máy tính: 43 unittest và bài
  `node tests/test_joystick.cjs` đều qua.
- Người dùng báo vẫn mất mạng và cho rằng nguồn đã đúng; sau chỉnh
  jumper chưa thử lại khi đứng yên/camera tắt. Probe không USB/reset:
  association timeout 12 giây, chưa đọc được boot/API. Scan thấy đúng
  MAC 38:3e:51:6f:a3:61, signal 84/100, channel11; log chỉ tới trying
  authenticate, chưa có handshake completed trong lần thử này. Không
  kết luận ESP32 hỏng hoặc nguồn đã được loại trừ. Chuẩn bị
  `tools/test_wifi.py`: Robot([],config), chỉ web/AP, không import/khởi
  tạo Motor/Encoder/PWM/IRQ, joystick khóa, health mỗi 10 giây, không sửa
  main.py/config.py. Đã kiểm tra cú pháp; chưa chạy lên bo. Đang hỏi người
  dùng tắt 7,4 V, tách riêng dây OUT+5 V bộ giảm áp khỏi ESP32, chỉ cắm
  USB để thử trong RAM; không cần tháo cả bộ dây. Chưa có xác nhận làm
  xong nên không mở serial/nạp. Log probe:
  `/tmp/xe-esp32-after-jumpers-link-check.json`.
- **Cập nhật sau chỉnh dây:** người dùng đã xác nhận tháo đủ bốn jumper
  ENA/ENB. Số đo khi đứng yên: nguồn 8,06 V; OUT bộ giảm áp 4,9 V;
  chân 5V/VIN ESP32 4,6 V; chân 3V3 ESP32 3,3 V. Chênh OUT/ESP khoảng
  0,3 V nếu cùng điều kiện đo; cần đo lại cùng mốc GND và kiểm tra đường
  OUT+/OUT−, dây/đầu nối, chưa kết luận bộ giảm áp hỏng hoặc nguồn đã ổn
  khi chịu tải. Probe qua Wi-Fi (không mở USB, không reset, không motor):
  20/20 public ping thành công, boot ID `18c831d8e5873780` giữ nguyên,
  uptime khoảng 94–113 giây, reason power_on/raw1/brownout false,
  latencies ở mẫu in 63–79 ms. Log `/tmp/xe-esp32-after-voltage-check.json`.
  Đã trả máy tính về Wi-Fi ban đầu. Chưa thử motor/encoder mới có tải;
  cần xác nhận kê bánh và quan sát mới được thử động cơ.
- **Đã xác nhận sơ đồ nguồn thực tế khi lỗi:** đầu ra bộ giảm áp 5 V nối
  chân 5V/VIN ESP32; lúc mất kết nối chỉ dùng bộ giảm áp, không cắm USB.
  Đầu vào bộ giảm áp dùng CHUNG nguồn 7,4 V với motor. Vì vậy không quy
  mọi lần mất kết nối cho USB máy tính. Tắt nguồn 7,4 V trong cấu hình
  này cũng tắt ESP32; chỉ hướng dẫn tắt 7,4 V khi thử USB riêng đã cách ly
  OUT+ bộ giảm áp. Chưa rõ các lượt ghi log qua USB trước đó có cách ly
  bộ giảm áp hay không; không tự suy diễn. Đã hướng dẫn phép đo nguồn
  ngoài: sau khi tắt mọi nguồn/tháo đủ ENA/ENB, rút USB, bật nguồn 7,4 V,
  không gửi lệnh motor; đo pin, đầu ra bộ giảm áp, chân 5V ESP32 và chân
  3V3 ESP32 so với GND tương ứng. Đang chờ số đo; chưa biết pin yếu,
  bộ giảm áp tụt áp/nhiễu, dây/đầu nối hoặc tải/GPIO là phần gây brownout.
- **Chi tiết nguồn mới cần xác minh:** người dùng vừa nói có nguồn ngoài
  qua bộ giảm áp xuống 5 V cấp ESP32. Điều này bổ sung cho thông tin trước
  đó "chỉ USB máy tính"; không tiếp tục coi đường nguồn chỉ có USB. Đang
  hỏi OUT 5 V nối chân nào (5V/VIN/USB/3V3), lúc lỗi có đồng thời cắm USB
  và bật bộ giảm áp không, và đầu vào bộ giảm áp có chung pin 7,4 V motor
  không. Chưa có câu trả lời. Không mở USB/reset/nạp thêm trong lúc chưa
  rõ có hai nguồn nối chung. Khi kiểm tra USB riêng cần tắt mọi nguồn rồi
  tách OUT+ bộ giảm áp khỏi đường 5V ESP32; chỉ tắt đầu vào bộ giảm áp
  chưa chứng minh đã cách ly nguồn/cấp ngược. Khi thử bộ giảm áp riêng,
  rút USB, đo điện áp đầu ra trước khi nối bo; 5 V không được vào 3V3.
  Không được khẳng định việc nối song song là nguyên nhân đã xác nhận;
  mới chỉ xác nhận brownout và người dùng chưa tháo ENA/ENB trước đó.
- **Xác nhận mới: người dùng nói CHƯA THÁO các jumper ENA/ENB.** Không tiếp
  tục reset/nạp/chạy PWM trong trạng thái này. Hai driver nhận PWM ngoài
  từ ESP32 nên các jumper nối ENA/ENB lên 5 V phải tháo (4 jumper cho 2
  mạch), khác jumper nguồn 5V-EN vốn đã tháo. Đã hướng dẫn tắt pin 7,4 V
  và rút USB trước khi chỉnh, giữ dây PWM đúng chân ENA/ENB: trên A/FL=14,
  trên B/FR=32, dưới A/RR=22, dưới B/RL=19. Chưa có xác nhận tháo xong;
  chưa được kết luận brownout đã hết hoặc GPIO chưa hỏng. Sau chỉnh phải
  thử USB/motor power off trước, xác nhận web ổn, chỉ thử motor khi có
  xác nhận kê bánh/quan sát và cấp nguồn motor đúng. Tài liệu module:
  https://docs.sunfounder.com/projects/sf-components/en/latest/component_l298n_module.html
  (ENA/ENB jumper nối 5 V).
- Người dùng hiện chỉ có USB máy tính, chưa tiện tháo dây. Thử phương án
  giảm TX trong RAM: ngắt AP/STA và giữ REPL 8 giây không thấy brownout;
  sau đó chạy main với wrapper định đặt txpower=8.5 dBm sau connect_wifi.
  Bo brownout trước khi tới dòng RAM_TXPOWER_DBM, chưa tới web ready:
  13 brownout trong cửa sổ 25 giây. **Mức TX thấp chưa hề áp dụng**, không
  được ghi là đã thử chạy ổn ở TX thấp hoặc kết luận RF là phần gây lỗi.
  Log `.device-backups/low-tx-ram-20261029-133453/usb.log`; không ghi flash,
  không gửi lệnh motor. Chưa có thay đổi firmware để người dùng chạy thử.
  Đã hỏi thêm tình trạng bốn jumper ENA/ENB ở hai L298N vì trước đây chỉ
  xác nhận tháo 5V-EN; không được nhầm hai loại jumper. Khi có PWM ngoài,
  ENA/ENB phải tháo jumper nối 5V, tránh đấu GPIO vào đường 5V. Đây là
  giả thuyết đấu dây cần xác nhận, chưa được coi là nguyên nhân đã tìm ra.
- **Bằng chứng mới nhất 29/10 ~13:20: xác nhận brownout lặp lại.** Người
  dùng chưa tiện tháo dây; mở USB để chuẩn bị ghi log với iPhone thì ngay
  sau lần POWERON do mở USB, bo liên tục in `E BOD: Brownout detector was
  triggered` và boot SW_RESET. Ghi được ít nhất 42 lần brownout trước khi
  yêu cầu dừng monitor. Không gửi lệnh arm/motor; chưa tới
  DIAGNOSTIC_READY. Log và số đếm cuối trong
  `.device-backups/idle-diag-20261029-132049/{usb.log,summary.json}`.
  Đã dừng chẩn đoán và thử trả về main.py, nhưng log không tới web ready
  vì vẫn brownout; không báo cho người dùng rằng web đã ổn. Không cài file
  tạm lên bo, không tắt detector hoặc sửa ngưỡng reset. Chưa xác định phần
  gây sụt áp là cáp/cổng USB, tiếp xúc, ổn áp trên bo hay tải/dây ngoại vi.
  Người dùng được báo không cần tiếp tục test Safari lúc này và đã hỏi
  có củ sạc USB 5 V/sạc dự phòng để thử với cáp hiện tại không. Lần ghi
  log trước thành công không phủ nhận lỗi nguồn gián đoạn đã xác nhận.
- Tiếp theo ngày 29/10: người dùng xác nhận Safari/iPhone cũng mất phản
  hồi khi đứng yên, camera tắt. Chạy chẩn đoán tạm trong RAM với web/PID
  thật, giữ USB mở 300 giây, log health mỗi 10 giây; không arm/chạy motor.
  Không ghi nhận brownout/reset/exception hoặc cạn bộ nhớ; GC tự thu hồi,
  native heap khoảng 23–28 KB, native low-water khoảng 15,9 KB. Hai lượt
  API 38 giây, tổng 76/76 status thành công, cùng boot ID; sóng -56/-57 dBm.
  Đây không phải phép thử API liên tục 5 phút; chưa tái hiện lỗi của người
  dùng. Log `.device-backups/idle-diag-20261029-131028/`. Đã tự về main.py
  bình thường, không cài file chẩn đoán lên bo; KeyboardInterrupt cuối log
  là chủ động kết thúc phép thử, không phải lỗi tự phát.
  USB CH340 device có power/control=on, runtime active, suspended_time=0;
  chưa có bằng chứng USB autosuspend. AP báo pm=1 và nhánh AP chưa gọi
  disable_power_save, nhưng tài liệu ESP-IDF nói modem-sleep chỉ hoạt động
  ở STA, nên không được coi pm=1 là nguyên nhân AP rớt mạng. Không sửa
  firmware thêm trong lượt này. Đã hỏi người dùng thử cô lập bo: tắt nguồn
  7,4 V/rút USB trước khi tháo dây ngoại vi, rồi chỉ cấp USB riêng ESP32;
  đang chờ xác nhận có thể thực hiện. Cần tiếp tục kiểm tra nguồn/nhiễu
  phần cứng, firmware/radio khi tái hiện được; không được báo đã sửa dứt điểm.
- Chẩn đoán tiếp ngày 29/10 sau bản sửa web: người dùng xác nhận AP vẫn
  nhìn thấy liên tục, xe đứng yên/camera tắt cũng mất phản hồi. Kernel của
  laptop (driver mt7921e) ghi `Connection to AP 38:3e:51:6f:a3:61 lost`
  lúc 12:53:16, tự nối lại 12:53:19; lúc thử lại 12:55:28 bị reason 15
  `4WAY_HANDSHAKE_TIMEOUT`. Mật khẩu profile khớp config; probe chưa mở
  USB/reset bo cũng thất bại ở association, chưa có IP nên chưa đọc được
  boot ID/cause hiện tại. Không được khẳng định là brownout mới hoặc lỗi
  web render. Chưa sửa thêm firmware/cấu hình trong lượt này. Lưu log tại
  `.device-backups/disconnect-20261029-125942/`. Đã hỏi người dùng thử
  Safari trên iPhone cùng AP, camera tắt, để yên 2–3 phút nhằm phân biệt
  lỗi laptop với lỗi AP/bo; đang chờ kết quả. Profile có hai BSSID lịch sử
  nhưng scan hiện tại chỉ có 38:3e:51:6f:a3:61 và các lỗi cũng đúng MAC đó,
  chưa có bằng chứng nối nhầm AP trùng tên. Power save từng xác minh OFF
  khi nối ESP32-Web, không được lấy trạng thái ON của Wi-Fi nhà làm bằng
  chứng profile ESP32 bị bật tiết kiệm điện.
- Ngày 29/10/2026: sửa web ghép encoder theo `wheel.name` thay vì chỉ số
  danh sách. Thứ tự firmware là FL, RR, RL, FR còn các ô web là FL, FR, RL, RR;
  trước đây hai ô trước phải/sau phải bị đảo. Giảm status từ 400 ms xuống
  1000 ms, không polling khi tab ẩn, không chạy ping chồng với status.
  Chu kỳ gửi lệnh 150 ms và watchdog 700 ms giữ nguyên; lỗi API vẫn dừng
  điều khiển ngay, phục hồi kết nối không tự chạy lại. Thông báo mất kết nối
  phân biệt timeout 1,2 giây, lỗi HTTP và lỗi liên lạc Wi-Fi. Kiểm thử Node
  có dữ liệu khác nhau cho từng bánh, thứ tự firmware, stop/reconnect và
  không tự arm lại; kiểm thử Chrome với robot giả lập cũng đạt. Đã nạp
  `/web/index.html`, đối chiếu toàn bộ byte, startup sẵn sàng; sao lưu tại
  `.device-backups/20261029-124538/`. Giảm tải API chưa chứng minh đã xử lý
  hết lỗi mất Wi-Fi/sụt nguồn khi chạy motor hoặc camera. Sau nạp đã thử
  Chrome với bo thật: 35/35 mẫu vẫn trực tuyến, một boot ID xuyên suốt,
  37 status request và 1 ping trong khoảng 37 giây; render API HTTP 200,
  đủ bốn bánh. Không gửi lệnh arm/chạy motor, không bật camera. Đã trả máy
  về Wi-Fi nhà sau phép thử để gửi kết quả cho người dùng.
- Ngày 29/10/2026, theo yêu cầu hiện sụt nguồn trên web: bổ sung BootInfo
  (ID ngẫu nhiên theo lần chạy server, reset reason, raw cause, uptime) trong
  `boot_info.py`. Chỉ đọc RTC_CNTL_RESET_STATE_REG 0x3FF48034 trên ESP32 classic
  khi tên chip kết thúc `with ESP32`; không đọc địa chỉ này trên S3/C3/chip khác,
  không ghi thanh ghi hoặc flash. Theo nguồn MicroPython modmachine.c, power-on
  và ESP_RST_BROWNOUT cùng trả PWRON_RESET; đối chiếu raw CPU reset 3/12 với
  PWRON_RESET hoặc raw 15 để xác nhận brownout. Soft reset được xét trước để
  tránh gán lại reset hardware cũ. Không đủ dữ liệu thì giữ nguyên nhân mơ hồ.
  API ping công khai chỉ bổ sung boot diagnostic; status/login và HTTP error
  trả cùng boot ID. API điều khiển/status vẫn yêu cầu xác thực. Web so sánh ID,
  đọc ping mỗi 2 giây khi chưa đăng nhập/mất kết nối, hiện khung đỏ xác nhận
  brownout hoặc thông báo reset/cấp nguồn lại chưa rõ. Khung nằm ngoài cả login
  và dashboard, lưu ID/cảnh báo trong sessionStorage cùng tab đến khi Đã đọc;
  giữ cảnh báo brownout đã thấy qua reset kế tiếp, không tự mở lại motor.
  Trong lúc bo tắt/chưa online không thể hiện xác nhận mới; mất điện hoàn toàn
  hoặc reset tiếp trước khi web đọc có thể làm mất nguyên nhân trước đó.
  43 test Python và JS đều qua. Chrome + HTTP cục bộ/motor giả kiểm tra mất
  phiên do brownout, cảnh báo còn trên login/reload, nút Đã đọc và reset mềm
  không bị gán nhầm đều qua; ảnh `/tmp/xe-esp32-brownout-alert.png` đã xem.
  Đã nạp `/boot_info.py`, `/web_server.py`, `/main.py`, `/web/index.html`,
  đọc lại khớp từng byte và probe trực tiếp MicroPython đều qua. Trên bo
  Generic ESP32, lần đọc thật cause=1/raw=1 báo power_on (không brownout);
  sau soft reboot cause=5/raw=1 báo soft_reset, web lên sẵn sàng. Đã kiểm tra
  phân loại brownout bằng mã reset giả trên bo, chưa chủ động gây brownout.
  Sao lưu ba file cũ tại `.device-backups/20261029-111107/` (boot_info là mới).
  Chế độ STOP_ALL_ON_ENCODER_STALL=False hiện tại vẫn được giữ. Chưa gửi
  lệnh motor hoặc cố tạo sụt nguồn để kiểm tra phần này.
  Nguồn thuật toán: MicroPython ports/esp32/modmachine.c và ESP-IDF v5.5
  components/soc/esp32/register/soc/rtc_cntl_reg.h, reg_base.h;
  esp_system/port/soc/esp32/reset_reason.c, esp32/rom/rtc.h.
- Ngày 29/10/2026, người dùng yêu cầu tạm bỏ dừng toàn xe khi bánh lỗi và
  nạp để chạy thử. Đã thêm `STOP_ALL_ON_ENCODER_STALL=False` trong config.
  Robot chỉ bỏ lan truyền lỗi `encoder_or_stall:*` lên lỗi toàn xe: Wheel vẫn
  tự dừng/giữ lỗi, ba bánh còn lại tiếp tục PID và nhận lệnh. Lỗi khác, trễ
  vòng điều khiển, watchdog mất lệnh 700 ms, nút DỪNG/nhả quyền vẫn dừng cả xe.
  Config cũ thiếu cờ này mặc định vẫn dừng toàn xe. Status bổ sung
  `wheel_faults`, `stop_all_on_encoder_stall`; web hiển thị rõ chế độ thử và
  bánh đã dừng, không trả lease chỉ vì một bánh stall. Khôi phục bằng cách
  đặt cờ True, nạp lại config và khởi động lại. Chế độ thử không tự hết hạn.
  37 test Python và kiểm thử JS đều qua, bao gồm stall thật trong mô hình
  giả vẫn giữ bánh khỏe/lease, watchdog vẫn dừng cả xe, strict-mode dừng toàn
  xe và UI không tự trả quyền khi chỉ có lỗi riêng từng bánh. Đã nạp ba file
  `/config.py`, `/robot.py`, `/web/index.html`, đọc lại khớp từng byte, chạy
  kiểm tra chế độ thử/watchdog/strict-mode trên MicroPython bằng motor giả
  đều qua; sau soft reboot log báo `Web/PID san sang.`. Bản cũ sao lưu tại
  `.device-backups/20261029-103948/`. Chưa gửi lệnh chạy motor thật ở lần này.
- Phép đo mới sau khi người dùng xác nhận camera IP 192.168.4.2:8080,
  xe đặt gần 0,5–1 m và camera tắt: dùng IP máy tính tạm 192.168.4.10/24,
  đồng thời giữ USB ghi log và đọc status 60 lần trong 30 giây. RSSI thực tế
  -52 dBm (lần xa trước -74 dBm), power-save off; 60/60 thành công, trung bình
  91,1 ms, tối đa 268,7 ms. USB chỉ có boot lúc mở cổng, không brownout/reset
  tiếp theo hoặc traceback. Không chạy motor. Phép dò .2 không có ping/ARP
  hoặc camera trả lời khi camera tắt; chưa xác nhận được trùng IP thực tế.
  Đã lưu riêng profile NetworkManager ESP32-Web: IPv4 manual
  192.168.4.10/24, gateway 192.168.4.1, DNS trống để tách địa chỉ máy tính khỏi
  camera .2; đây là dự phòng trùng IP, không khẳng định đã tìm được lỗi trùng
  IP. Không đổi kết nối đang dùng hoặc profile Wi-Fi nhà. Giá trị IPv4 cũ
  auto/addresses trống/gateway trống/DNS trống được lưu trong manifest.
  Bằng chứng tại `.device-backups/20261028-214924/near-camera-off-*.json`
  và `near-camera-off-usb.log`. Giữ AP kênh 11, power-save profile off.
  Đây mới là phép thử gần/camera tắt/không chạy motor trong 30 giây, không
  chứng minh ổn định khi bật video hoặc có tải. Brownout đã bắt được ở phép
  trước vẫn chưa được sửa phần cứng; không xóa cảnh báo nguồn trong bàn giao.
- Kết luận phép chẩn đoán Wi-Fi mới nhất: đã bắt được brownout đồng thời
  với lỗi mạng/phiên đăng nhập, không còn chỉ suy đoán từ SSID. Khi giữ USB
  mở và đọc GET status (không gửi bất kỳ lệnh motor nào), USB ghi
  `E BOD: Brownout detector was triggered` tại khoảng giây 69,3, sau đó
  `SW_RESET`, khởi động web lại; cùng phép đo, HTTP từ timeout/no-route
  chuyển sang 401 do token trong RAM bị mất. Kết quả 43/60 status thành công,
  17 lỗi; mức sóng cache cuối phép đo 79% trên kênh 11. Nguồn ESP32 chưa ổn
  định ngay cả khi không chạy motor. Chưa xác định do cáp, cổng USB, tiếp xúc,
  regulator/bo hay tải phụ; không khẳng định pin motor 7,4V yếu vì bo dùng USB.
  Bản ghi bằng chứng được lưu trong `.device-backups/20261028-214924/`:
  `brownout-usb.log`, `brownout-link-check.json`, `brownout-api-check.json`;
  manifest ghi `network_stability_verified=false` và
  `brownout_during_read_only_test=true`. Sau reset web đã lên lại; máy tính
  đã trả về mạng ban đầu. Không gửi lệnh motor trong các kiểm tra mạng.
  Giữ nguyên lựa chọn AP ESP32-Web/kênh 11 và powersave=disable riêng profile.
  Trước đó đã thử tắt HUPCL trên `/dev/ttyUSB0` theo tài liệu Espressif vì
  chế độ này đang bật; lưu cờ cũ trong manifest. Phép thử sau khi tắt vẫn ghi
  nhận brownout nên HUPCL không giải quyết lỗi nguồn. ModemManager có chạy,
  nhưng log đọc được chưa chứng minh nó dò ESP32; không dừng dịch vụ này.
  Phép ICMP/HTTP ngắn 15 giây từng qua 30/30 + 30/30, không chứng minh ổn định
  lâu dài. Không tiếp tục sửa giao thức HTTP hay tăng công suất Wi-Fi để
  che lỗi nguồn; cần xử lý nguồn phần cứng trước, rồi đo lại khi chạy có tải.
- Người dùng đã chọn giữ mạng riêng ESP32. Ngày 28/10/2026 đã thêm
  `AP_CHANNEL=11` trong config và truyền kênh vào `wlan.config()` ở chế độ AP;
  không đổi SSID, mật khẩu, IP, polarity/PID/watchdog. Quét tại máy tính thấy
  ESP32-Web kênh 1 signal=50%; kênh 11 có ít mạng lân cận hơn kênh 1/6 trong
  lần đo, không phải phép đo phổ nhiễu RF. Máy tính có profile powersave=default,
  cấu hình hệ thống `wifi.powersave=3`; đã đặt riêng profile ESP32-Web thành
  powersave=2 (disable). Không thay ưu tiên hoặc tự kết nối của Wi-Fi nhà.
  Nguồn mới qua 35 test Python. Đã sao lưu/nạp `/config.py`, `/wifi.py`, đọc lại
  khớp từng byte, kiểm tra trên MicroPython AP kênh 11/IP 192.168.4.1 và khởi
  động web thành công. Bản cũ và manifest tại `.device-backups/20261028-214924/`;
  manifest ghi cấu hình powersave cũ=0 để khôi phục khi cần. Helper ban đầu
  so giá trị nmcli với số 2 trong khi nmcli trả chuỗi `disable`; đã xác nhận
  lại giá trị và hoàn tất manifest, không nạp lại bo chỉ vì lỗi so sánh này.
  Kiểm tra HTTP qua AP mới: 60 GET status, 51 thành công, 9 timeout trong
  58,3 giây; RTT HTTP trung bình 394,6 ms, tối đa 3949,2 ms ở các mẫu thành
  công. Chưa khắc phục dứt điểm mất kết nối. Không gửi lệnh motor.
  Thử IP máy tính tạm 192.168.4.10 để loại trừ camera từng ở .2: powersave
  thực tế off, RSSI -74 dBm; không thấy .2 trả ping/ARP/camera, đăng nhập API
  cũng timeout. Không lưu IP tĩnh, profile ESP32 vẫn DHCP/auto, máy trả về
  Wi-Fi cũ sau mỗi phép thử. Chưa có bằng chứng xác nhận trùng IP. Đang chờ
  người dùng đặt xe cách máy tính 0,5–1 m, tắt camera để so sánh tín hiệu/lỗi.
  Log: `/tmp/xe-esp32-ap-link-check.json`,
  `/tmp/xe-esp32-ap-static-link-check.json`.
- Chẩn đoán mất Wi-Fi tiếp ngày 28/10/2026: người dùng báo mạng ESP32-Web
  biến mất rồi xuất hiện khi điều khiển bằng máy tính. Hai lần đọc USB thụ động
  90 giây và 240 giây chỉ có một POWERON_RESET ngay khi mở cổng, sau đó web
  sẵn sàng; không có brownout, traceback hay boot mới trong hai cửa sổ này.
  Báo lỗi đầu đến sau khi cửa sổ 90 giây kết thúc, không khớp được thời điểm.
  Trong lúc ghi 240 giây người dùng tiếp tục phản ánh mất mạng, nhưng không
  bắt được reset trong log; chưa thể kết luận pin/nguồn gây lần ngắt hiện tại.
  NetworkManager ghi máy tính kết nối ESP32-Web lúc 21:37:58 (192.168.4.2),
  đến 21:39:18 rời mạng với `new-activation`, supplicant reason=3,
  locally_generated=1, rồi sang Phong tang 2. Không dùng sự kiện chuyển mạng
  này để khẳng định nguyên nhân của lỗi trang web xảy ra trước đó.
  Dữ liệu Wi-Fi lưu trên máy ghi ESP32-Web signal=50%, kênh 1; máy hiện ở
  Phong tang 2 kênh 2. Đây là cache, không phải phép đo RF liên tục.
  Đã giải thích AP xe không cung cấp Internet; sau đó người dùng chọn giữ AP
  riêng. Tại thời điểm phép đọc này chưa sửa config hay Wi-Fi trên máy,
  không gửi lệnh motor và không tắt brownout detector. Log USB nằm tại
  `/tmp/xe-esp32-wifi-drop.log`, `/tmp/xe-esp32-wifi-drop-long.log`.
- Kết quả kiểm tra mới nhất ngày 28/10/2026: người dùng báo chỉ bánh sau phải
  quay qua joystick và yêu cầu đối chiếu chiều với bản cũ. Đã đối chiếu ba bản
  sao lưu `20261028-162133`, `20261028-162212`, `20261028-173218`: mapping GPIO,
  `WHEELS`, polarity đều giống nguồn hiện tại; `motor.py` giống từng byte.
  Đã đọc lại `/motor.py` và phần cấu hình bánh trên ESP32, xác nhận khớp nguồn.
  Sau khi người dùng xác nhận cả bốn bánh kê cao, nguồn 7,4V bật và đang quan
  sát, đã chạy riêng FL, RR, RL, FR bằng PWM trực tiếp 100% trong 1 giây/lượt,
  tự tắt toàn bộ đầu ra rồi đợi 1,5 giây trước khi đọc xung. Người dùng xác nhận
  cả bốn lượt đúng vị trí và đúng chiều tiến. Xung đúng kênh FL=147, RR=170,
  RL=146, FR=134; lượt RL có thêm 2 xung RR, không đổi mapping từ số này.
  Thử riêng PID FL ở 80 RPM tối đa 3 giây có 56 xung, không fault. Thử cả bốn
  bánh bằng Robot/control_loop hiện tại, Wi-Fi AP bật, lệnh tiến 80 RPM trong
  khoảng 3 giây, giữ nguyên watchdog/stall: FL=42, RR=52, RL=39, FR=39 xung,
  `final_fault=None`, cuối bài tự dừng toàn bộ motor. RR bắt đầu có xung khoảng
  0,6 giây, hai bánh trước khoảng 1,1–1,3 giây; thử chỉ 1 giây chưa đủ để kết
  luận bánh không chạy. Các phép đo cho thấy RPM còn dao động, chưa tune PID.
  Đã khôi phục main, log `Web/PID san sang.`, không brownout trong 9 giây
  theo dõi lần khởi động này. Người dùng sau đó xác nhận trên web thật:
  chọn 80 RPM, kéo hết joystick tiến 2–3 giây thì cả bốn bánh quay, không lỗi.
  Không sửa hoặc nạp lại firmware, không đổi polarity/PID/ngưỡng bảo vệ;
  chỉ cập nhật tài liệu. Chưa thử có tải trên sàn hoặc xác nhận nguồn ổn định
  dài hạn. Log thí nghiệm: `/tmp/xe-esp32-wheel-bench.log`,
  `/tmp/xe-esp32-wheel-pid.log`, `/tmp/xe-esp32-wheel-pid-all.log` cùng các
  file `*-restore.log`. Trước bài thử USB, đã tạm chuyển máy từ Wi-Fi nhà sang
  ESP32-Web để đọc API: hai mẫu cho thấy bo ready, reason boot, không fault;
  mẫu tiếp theo timeout. Đã trả máy về mạng cũ, không gửi lệnh motor qua API
  trong phép đọc này. Log: `/tmp/xe-esp32-status-check.jsonl`.
- Kiểm tra tiếp với nguồn 7,4V: theo yêu cầu người dùng, theo dõi USB
  thụ động 35 giây, không gửi lệnh motor. Một POWERON_RESET xuất hiện ngay
  khi mở cổng; sau đó `Web/PID san sang.`, không có brownout hoặc traceback.
  Lần theo dõi tiếp theo 90 giây cũng chỉ có boot lúc mở cổng rồi web sẵn
  sàng, không brownout/traceback. Đã yêu cầu người dùng đăng nhập và kéo tiến
  khoảng 1 giây với bánh kê cao; chưa nhận xác nhận kết quả chuyển động/lỗi,
  vì vậy chưa kết luận xe chạy được từ log khởi động đơn thuần. Log:
  `/tmp/xe-esp32-74v-power-check.log`, `/tmp/xe-esp32-74v-joystick-check.log`.
- Chẩn đoán tiếp ngày 28/10/2026: người dùng báo kéo joystick bị mất
  đăng nhập. Theo dõi USB thụ động 45 giây không thấy brownout/traceback;
  có một POWERON_RESET ngay khi mở cổng (không xem đây là reset do joystick).
  Người dùng xác nhận lần thử này không bị đăng xuất, nhưng nhận lỗi
  `encoder_or_stall:front_left`. Code báo lỗi khi duty từ 20% mà không có
  xung trong khoảng 1,5 giây; lỗi được chốt và dừng toàn bộ motor, không tự
  xóa khi đăng nhập lại. Chưa quan sát được bánh có quay lúc lỗi hay không.
  Đã tạm dừng main, đặt tất cả EN và chân chiều về 0, tắt Wi-Fi và đọc encoder
  khi người dùng xoay bánh bằng tay. Lần đo đầu chưa xác nhận được thao tác
  vì người dùng cần hỏi hướng xác định trước trái. Lần đo lại ghi nhận GPIO39
  tăng từ 0 lên 200 xung; chứng minh có phản hồi trong điều kiện motor
  tắt/Wi-Fi tắt, chưa xác nhận được khi motor chạy hoặc nguồn chịu tải.
  Không gửi lệnh chạy motor và không sửa firmware/ngưỡng bảo vệ.
  Khi soft reboot khôi phục web sau lần đo đầu, log lại có 2 lần
  `Brownout detector was triggered`, nên lỗi nguồn vẫn tái diễn cả khi chưa
  chạy motor. Reset sẽ mất token trong RAM, giải thích được hiện tượng phải
  đăng nhập lại; chưa bắt được log reset trùng thời điểm kéo joystick.
  Đã làm rõ nguồn: người dùng có nguồn motor 7,4V nhưng đã tắt khi thử
  trước đó; dây 5V ESP32 vào cọc 5V logic L298N, không phải bằng chứng motor
  lấy nguồn từ USB. Người dùng xác nhận đã tháo 5V-EN trên cả hai L298N.
  Nguồn motor bị tắt giải thích được lỗi không có xung khi ra lệnh chạy;
  brownout vẫn là hiện tượng riêng đã quan sát, chưa xác định nguyên nhân.
  Sau phép đo lần hai đã khôi phục main và xác nhận `Web/PID san sang.`;
  khoảng 9 giây khởi động được ghi nhận không có brownout. Firmware không đổi.
  Log tạm trên máy tính:
  `/tmp/xe-esp32-joystick-reset.log`, `/tmp/xe-esp32-encoder-hand-test.log`,
  `/tmp/xe-esp32-encoder-restore.log`.
- Bản sửa mới nhất ngày 28/10/2026 trong mã nguồn: bỏ thời hạn 30 phút của
  phiên đăng nhập, bỏ nút/bảng Mở điều khiển xe. Sau đăng nhập, joystick dùng
  trực tiếp; lần kéo đầu tiên tự lấy lease motor. Đăng nhập và heartbeat khi
  joystick ở tâm không tự lấy lease hoặc quay motor. DỪNG, mất tiêu điểm và
  đăng xuất vẫn trả quyền/dừng; lần kéo mới có thể lấy quyền lại. Đã xử lý hủy
  lần kéo khi phản hồi lấy quyền về muộn, và chờ xác nhận trả lease cũ trước
  khi lấy lease cho lần kéo tiếp theo. Watchdog mất lệnh 700 ms giữ nguyên.
  Phiên đăng nhập không còn dựa trên thời gian; ESP32 giữ tối đa 4 phiên trong
  RAM, đăng nhập thêm sẽ thay phiên ít dùng không đang giữ xe, không làm mất
  quyền của người đang điều khiển. Các trường hợp này đã qua 35 kiểm thử Python,
  kiểm thử JS và Chrome + HTTP dùng motor giả. Hai file cần nạp là
  `/web_server.py` và `/web/index.html`.
  Sau khi người dùng cắm lại USB, đã nạp `/web_server.py` và `/web/index.html`
  thành công, đọc lại xác nhận từng byte và kiểm tra xác thực trên MicroPython:
  không hết hạn theo thời gian, từ chối mật khẩu sai, đăng xuất thu hồi token,
  thay phiên cũ để giới hạn RAM đều đạt. Bài kiểm tra dùng Robot rỗng, không
  tạo GPIO hoặc lấy lease motor. Bản cũ được sao lưu tại
  `.device-backups/20261028-202425/`.
  Lần soft reboot đầu sau khi nạp ghi nhận 5 lần
  `Brownout detector was triggered` trong khoảng 10 giây và khởi động lại
  liên tục. Người dùng xác nhận bo chỉ cấp nguồn qua USB máy tính và hiện
  chưa có cáp/cổng khác để thử. Các lần đọc log tiếp theo ghi nhận web đã lên
  `Web/PID san sang.`; theo dõi thêm 20 giây ghi nhận một lần boot bình thường,
  không có brownout hoặc traceback. Manifest đã ghi `startup_ready=true`,
  `initial_startup_ready=false`, `device_auth_verified=true`; log đầu và log
  kiểm tra sau (`startup-followup.log`) đều được giữ trong thư mục sao lưu.
  Nguồn USB có dấu hiệu chập chờn ở lần đầu, chưa xác định được cáp/cổng/bo;
  không tắt brownout detector hoặc thay đổi giới hạn motor. Chưa gửi lệnh
  motor thật trong quá trình nạp và kiểm tra.
- Ngày 28/10/2026: theo yêu cầu thay CONTROL_KEY bằng đăng nhập, đã xóa khóa
  khỏi cấu hình/giao diện và thay bằng `LOGIN_USERNAME`, `LOGIN_PASSWORD`.
  Tên đăng nhập là `admin`, mật khẩu được đặt theo thông tin người dùng gửi,
  chỉ lưu trong `firmware/config.py`. Trang mở màn hình đăng nhập trước;
  đăng nhập thành công mới hiện bảng điều khiển, đăng nhập chưa mở motor.
  ESP32 cấp mã phiên ngẫu nhiên, bảo vệ API trạng thái/điều khiển bằng Bearer,
  phiên hết hạn sau 30 phút không hoạt động, tối đa 4 phiên. Mã phiên được lưu
  theo tab bằng sessionStorage; đăng xuất thu hồi phiên và dừng xe nếu đang
  giữ quyền điều khiển. Phiên đăng nhập khác không gửi lệnh cho lease motor
  của phiên đang điều khiển được. Mô phỏng vẫn dùng được mà không đăng nhập.
  Đã qua 34 kiểm thử Python, kiểm thử JS và kiểm tra Chrome với HTTP thật,
  phần cứng giả (sai mật khẩu, đăng nhập, tải lại trang, đăng xuất).
  Đã sao lưu 3 file cũ tại `.device-backups/20261028-174602/`, nạp lại
  `/config.py`, `/web_server.py`, `/web/index.html` và xác nhận từng byte.
  Kiểm tra ngay trên MicroPython đã xác nhận API chặn truy cập chưa đăng nhập,
  từ chối mật khẩu sai, chấp nhận cấu hình mới và vô hiệu hóa phiên khi đăng xuất;
  bài kiểm tra này dùng Robot rỗng, không tạo GPIO hoặc mở lease motor.
  Sau đó ESP32 khởi động lại thành công và báo `Web/PID san sang.`.
- Ngày 28/10/2026, theo yêu cầu nạp toàn bộ để chạy thử: đã nạp 10 module
  chương trình, 4 script kiểm tra phần cứng và `/web/index.html` qua
  `/dev/ttyUSB0`. Cả 15 file được đọc lại và xác nhận khớp từng byte với bản
  trên máy tính; các file Python được kiểm tra biên dịch trên bo. Sao lưu
  trước khi nạp gồm 17 file tại `.device-backups/20261028-173218/`.
  ESP32 khởi động lại thành công, báo `Wi-Fi: ESP32-Web`, địa chỉ
  `http://192.168.4.1` và `Web/PID san sang.`. Chưa mở khóa hoặc gửi lệnh motor.
  27 kiểm thử Python và kiểm thử giao diện/joystick/camera đều đạt trước khi
  nạp. Kiểm tra HTTP từ máy tính tới web và camera trong lần nạp này bị timeout;
  trạng thái khởi động được xác nhận qua USB. Người dùng cần giữ iPhone phát
  camera trong app và thiết bị xem cùng mạng ESP32-Web khi chạy thử.
- Camera iPhone: người dùng đã cung cấp ảnh SimpleIPCamera với URL
  `http://192.168.4.2:8080/stream.mjpg`. Đã thêm khung camera cạnh joystick,
  ô sửa URL, nút bật/tắt và xử lý lỗi trong `firmware/web/index.html`.
  Trình duyệt tải hình trực tiếp từ iPhone; không chuyển luồng video qua ESP32.
  Camera chỉ bật thủ công trong chế độ ESP32 thực, tắt khi chuyển mô phỏng
  hoặc rời trang. Bật camera không mở khóa motor; mất hình không tự dừng xe.
  Ngày 28/10/2026 đã nạp riêng `/web/index.html`, đọc lại xác nhận khớp từng
  byte và khởi động lại thành công. Bản web cũ nằm trong
  `.device-backups/20261028-170312/`. 27 kiểm thử Python, kiểm thử joystick/API/
  camera và kiểm tra hiển thị bằng Chrome đều đạt. Chưa xác nhận được hình
  camera thật: máy tính kết nối URL bị timeout; thử từ ESP32 trả
  `OSError(118,)`. Sau lần kiểm tra, ESP32 đã khởi động lại và báo web sẵn sàng.
  Cần kiểm tra iPhone vẫn ở Wi-Fi ESP32-Web, app còn Start Server và URL còn
  đúng; sau khi kết nối lại có thể cần bật lại server trên iPhone.
- Ngày 28/10/2026: đã nạp thực tế qua USB `/dev/ttyUSB0` lên ESP32 chạy
  MicroPython 1.29.0. Cả 10 module Python trong `/` và `/web/index.html` đã được
  đọc lại, xác nhận khớp từng byte với bản nguồn. Sau soft reboot, Shell báo
  `Wi-Fi: ESP32-Web`, `http://192.168.4.1` và `Web/PID san sang.`. Chưa gửi lệnh
  mở điều khiển hoặc chạy motor, chưa kiểm chứng truy cập bằng trình duyệt.
  Bản sao lưu trước khi nạp nằm trong `.device-backups/20261028-162212/`
  (đã loại khỏi Git). Backend kết nối ESP32 của Thonny đã được dừng để nhường
  cổng USB; nếu cần dùng lại Thonny, chọn Stop/Restart backend để kết nối lại.
- Trạng thái mới nhất: `HARDWARE_ENABLED=True`, `MAX_DUTY=1.0`; cả bốn bánh có PID khởi đầu `(0.008, 0.003, 0.0)`. `LOGIN_USERNAME` và `LOGIN_PASSWORD` đã được đặt trong `config.py` theo yêu cầu người dùng; giao diện CONTROL_KEY cũ đã được thay bằng đăng nhập. Hệ số PID chưa được tune trên xe thật; người dùng cần nạp config và thử với bánh kê khỏi đất.
- `config.py` hiện đặt `motor_inverted=True` cho hai bánh trước, `False` cho hai bánh sau; chiều trước phải cần xác minh lại sau khi nạp.
- Người dùng báo chiều bánh trước phải bị ngược; đã đảo riêng `front_right.motor_inverted` và cần xác minh bằng test số 4.
- Phiên làm việc trước không có ESP32 cắm vào để chạy thử vật lý. Các test trên máy tính (27 test và kiểm thử motor giả) từng qua theo ghi chú phiên trước; cần chạy lại nếu code thay đổi. Test giả không xác nhận dây, chân hay chiều motor trên xe thật.
- Khi sửa file trên komputer, thay đổi **không tự nạp vào ESP32**. Người dùng cần tải các file đã đổi lên thiết bị bằng Thonny, sau đó khởi động lại/re-run.

## Cách người dùng thử từng bánh trong Thonny

1. Kê cả bốn bánh khỏi mặt đất và chuẩn bị ngắt nguồn motor ngay lập tức.
2. Dừng chương trình đang chạy bằng Ctrl+C. Nạp `test_motors.py`, `motor.py`, `encoder.py`, `config.py` lên thư mục gốc của thiết bị MicroPython.
3. Mở `test_motors.py`, nhấn F5; trong Shell nhập `TEST` khi chương trình hỏi.
4. Menu lấy trực tiếp từ `config.WHEELS`: hiện `1`=trước trái, `2`=sau phải, `3`=sau trái, `4`=trước phải. Script hiện dùng **100% PWM trong 1 giây**, không phải 30%; đây là test độc lập không PID và sẽ tắt Wi-Fi. Nhập `-1` đến `-4` để thử chiều ngược; `q` để thoát. Mục này mô tả công cụ, không phải kết quả thử mới.
5. Ghi lại bánh thực sự quay, chiều quay khi lệnh dương (tiến), và encoder GPIO nào tăng. Nếu chọn 1 bánh mà bánh khác quay thì dừng nguồn và kiểm tra dây/channel trước khi đổi config.

Nếu đã nhập `1` ở câu hỏi đầu tiên `Nhap TEST...`, chương trình thoát bình thường; cần chạy lại và nhập `TEST` trước, rồi mới nhập số bánh.

## An toàn và các ghi chú quan trọng

- Test motor phải thực hiện khi bánh được kê lên. Đừng đặt xe trên sàn ở lần thử đầu.
- L298N cần tháo jumper ENA/ENB nếu GPIO ESP32 điều khiển PWM các chân EN; kiểm tra đúng module và nguồn trước khi cấp motor.
- Không cấp tín hiệu 5 V trực tiếp vào GPIO ESP32; ECHO HC-SR04 phải qua cầu chia áp.
- Đừng nạp cả thư mục `tests/` lên ESP32. Nạp các module `.py` cần thiết vào `/` và giao diện vào `/web/index.html`.
- Thonny F5 chạy nội dung editor nhưng không tự chép toàn bộ các module còn thiếu; lỗi `ImportError: no module named 'config'` nghĩa là `config.py` chưa nằm trên thiết bị hoặc chưa được nạp đúng chỗ.

## Lịch sử tóm tắt trao đổi

- Ngày 28/10/2026: tách thêm giao diện vào `firmware/web/index.html`, sửa
  `main.load_html()` và đường dẫn kiểm thử giao diện. Trên ESP32 giữ các module
  Python trong `/`, giao diện ở `/web/index.html`; phải nạp lại cả `main.py` và
  thư mục `web/` khi cập nhật từ cấu trúc cũ.
- Ngày 28/10/2026: theo yêu cầu người dùng, chia dự án thành `firmware/`,
  `tools/`, `tests/`, `docs/`; cập nhật đường dẫn kiểm thử, hướng dẫn nạp Thonny
  và đường dẫn tìm module trong VS Code. Giữ nguyên nội dung firmware và các
  script kiểm tra phần cứng; trên ESP32 vẫn dùng các file trực tiếp trong `/`.
- Đã giải thích AP là ESP32 phát Wi-Fi riêng; STA là ESP32 kết nối Wi-Fi router. Web chỉ truy cập global nếu có hạ tầng trung gian/Internet; ESP32 không tự biến thành hosting công khai.
- Đã tạo cấu trúc xe điều khiển web + PID và giao diện joystick; người dùng yêu cầu bỏ thư mục `web_esp32` và đặt file dự án ở ngoài thư mục đó.
- Đã giải thích cách chạy HTML bằng trình duyệt và cách nạp file MicroPython bằng Thonny.
- Người dùng cung cấp sơ đồ L298N, vị trí encoder, hướng lắp xe và đĩa encoder 20 khe; các chi tiết này được ghi vào `WIRING.md`/`config.py`.
- Người dùng hỏi test motor thật; đã tạo/đưa hướng dẫn dùng `test_motors.py`, nhưng chưa có kết quả đo phần cứng được gửi lại.
- Đoạn test độc lập do người dùng dán khai báo hai motor trước `reverse=True`, hai motor sau `reverse=False`; config dự án hiện phản ánh khai báo đó. Sau đó người dùng báo chiều bánh trước sai, nên cần dựa trên test phần cứng để cập nhật polarity.
- Người dùng vừa xác nhận đoạn chương trình độc lập của họ chạy motor đúng chiều. Logic đảo chiều trong `motor.py` tương đương; config giữ `motor_inverted=True` cho trước trái/phải và `False` cho sau trái/phải. Người dùng cũng xác nhận encoder FL=39, FR=36, RL=35, RR=34. Đã chuẩn hóa thứ tự `ENCODER_PINS` và đầu ra `check_encoders.py` theo thứ tự bánh để tránh nhầm do trước đây danh sách chẩn đoán in GPIO theo thứ tự sơ đồ `(35,34,39,36)`.
- Đối chiếu sơ đồ: module phía trên ESP32 là cầu trước, module phía dưới là cầu sau. Người dùng báo kết quả test mới nhất: số 2 chạy sau phải, số 3 chạy sau trái; config đã ghép số 2/lower_a với RR, số 3/lower_b với RL. Chạy `tests/test_wiring.py` để khóa mapping.
- Người dùng xác nhận thứ tự hiện tại của `test_motors.py`: 1=trước trái, 2=sau phải, 3=sau trái, 4=trước phải. `WHEELS` và menu test cùng thứ tự; Robot xác định bên trái/phải theo tên bánh.
- Người dùng yêu cầu test lấy đúng cấu hình thay vì tự ghi nhãn theo vị trí. `test_motors.py` hiện duyệt trực tiếp `config.WHEELS` và tạo nhãn hiển thị từ `wheel['name']`, nên menu và báo cáo encoder sẽ bám theo đúng cấu hình. Đã sửa cả nhãn tuple cũ bị sai.
- Người dùng báo bánh trước phải quay ngược chiều; đã đổi `front_right.motor_inverted` lại thành `True` trong `config.py`. Cần nạp lại `config.py` lên ESP32 và kiểm chứng bằng test số 4; chiều vật lý chưa được xác nhận lại trong phiên này.
- Đã tạo `test_front_right.py`, test độc lập kênh B L298N trước phải bằng GPIO25/33/32, PWM tối đa 35%, chạy mỗi chiều 1 giây rồi tự tắt.
- Đã tạo `test_rear_left.py`, test độc lập theo mapping hiện tại `rear_left=lower_b`, IN3/IN4/ENB là GPIO4/21/19; PWM tối đa 35%, mỗi chiều 1 giây rồi tự tắt.
- Đồng bộ `test_motors.py` lên PWM 35% để bằng các bài test riêng; các test tổng hợp và test riêng đều chạy mỗi chiều trong 1 giây. Mức 30%, 35% và 60–100% từ code khác nhau có thể làm motor khởi động lúc được lúc không do lực khởi động và sụt áp của L298N.
- Theo yêu cầu mới nhất, ba file test motor (`test_motors.py`, `test_front_right.py`, `test_rear_left.py`) dùng 100% duty PWM; mỗi lần chạy vẫn tối đa 1 giây rồi tự ngắt. Duty PWM không tương ứng tuyến tính với tốc độ bánh.
- `config.MAX_DUTY=1.0` cho phép tối đa 100% PWM cho cả bốn bánh. Theo yêu cầu chạy qua web, phần cứng đã bật, điền PID khởi đầu và khóa điều khiển; cần test vật lý trước khi chạy xe trên mặt đất.

## Hướng tiếp tục

1. Ưu tiên probe **chỉ đọc qua Wi-Fi trước khi mở serial/reset**: đúng BSSID
   bo mới, đo association/RSSI, ICMP, `/api/ping`, HTTP `/`, boot ID/uptime.
   Đối chiếu boot `b62fb8a3fee32c6c`; nếu ID đổi, hỏi việc người dùng có
   cấp nguồn/reset lại không trước khi kết luận. Làm rõ lần lỗi mới nhất
   chỉ timeout web hay SSID cũng biến mất, và thiết bị đang xem là gì.
2. Máy tính dùng `wlo1`, mạng gốc gần nhất `Phong tang 2`; profile ESP32-Web
   có IP tĩnh `192.168.4.10/24`. Mọi script đổi mạng phải **tự khôi phục
   kết nối ban đầu trong cùng script bằng finally**, tránh mất đường mạng
   của phiên trợ lý. Sau test, người dùng cần nối lại ESP32-Web để mở web.
   Quét lại trước khi chọn BSSID nếu NetworkManager còn cache bo cũ.
3. Nếu cần ghi log USB mới, giữ cổng mở suốt bài thử và ghi mốc thời gian
   người dùng kéo/thả/lúc lỗi. Mở cổng có thể reset một lần và mất đăng nhập;
   tách lần reset này khỏi lỗi tự phát. Logger cũ đã kết thúc; không tiếp
   tục chờ session `13978`. Sao lưu log cũ trước khi chạy lại script vì nó
   ghi đè `manual-drive-usb.log`/`.json`.
4. Dựa vào bằng chứng mới để chọn phép thử cô lập cùng firmware/điều kiện
   (web/API, GPIO, ngoại vi/nguồn), thay vì sửa tiếp theo phỏng đoán. Trước
   khi sửa/nạp hoặc tháo dây cần xác nhận motor đã tắt, USB cấp bo và OUT+
   giảm áp vẫn tách. Nếu tháo encoder để thử bo riêng, khóa khởi tạo GPIO
   trước; không để GPIO34–39 trôi rồi coi đó là bài thử bo độc lập.
5. Công cụ tạm có thể tham khảo trong `/tmp` (không bảo đảm còn ở phiên sau):
   `xe_esp32-unresponsive-web-probe.py`, `xe_esp32-runtime-final-monitor.py`.
   **Đọc trước khi chạy**: probe hiện còn trỏ backup socket-fix cũ, cần đổi
   nơi lưu kết quả; monitor mở USB và ghi đè log. Pointer bản cuối:
   `/tmp/xe-esp32-runtime-fix-backup-path`. Python có serial/esptool/pipkin:
   `/home/sang/apps/thonny/bin/python3`. Kiểm tra cổng bận trước khi dùng,
   không chiếm cổng từ Thonny của người dùng. Các deployer cũ có metadata
   Hardware False hoặc hash cũ; không chạy lại máy móc.

Yêu cầu cuối của người dùng ở lượt bàn giao này là **cập nhật log cho phiên
khác đọc**. Đã ghi lại kết quả mới; chưa thực hiện probe hoặc phép thử mới.
Mục tiêu đang dang dở vẫn là sửa mất phản hồi/mất Wi-Fi khi chạy xe.
