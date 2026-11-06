# Hướng dẫn test tự quay về và tránh vật cản

Firmware đã nạp lên ESP32. Các thuật toán đã qua test mô phỏng trên máy tính, nhưng **chưa từng chạy trên sàn thật**, nên hãy làm đúng thứ tự dưới đây. Luôn để sẵn công tắc ngắt nguồn motor trong tầm tay.

## 1. Nối phần cứng (tắt nguồn trước)

| Linh kiện | Chân | Nối vào |
|---|---|---|
| SG90 | Tín hiệu (cam) | GPIO 23 |
| SG90 | VCC (đỏ) | Nguồn 5 V riêng, không lấy từ chân 3V3 |
| SG90 | GND (nâu) | GND chung với ESP32 |
| HC-SR04 | VCC | 5 V |
| HC-SR04 | Trig | GPIO 13 |
| HC-SR04 | Echo | **Qua cầu chia áp** vào GPIO 18 |
| HC-SR04 | GND | GND chung |

Cầu chia áp cho chân Echo: Echo → điện trở 1 kΩ → GPIO 18 → điện trở 2 kΩ → GND. Nối thẳng 5 V vào GPIO có thể làm hỏng ESP32.

Lắp HC-SR04 trên servo sao cho **nhìn thẳng về đầu xe khi servo ở giữa**. Đo khoảng cách từ tâm xe tới cảm biến rồi sửa `SCANNER_OFFSET_M` trong `config.py`.

## 2. Kê bánh lên, kiểm tra từng phần

1. Bật nguồn, kết nối Wi-Fi `CR7-GOAT`, mở `http://192.168.4.1`.
2. **Quét:** cứ 3 giây servo phải xoay qua 5 góc rồi về giữa.
   - Nếu góc dương làm servo quay sang trái: đặt `SERVO_INVERTED = True`.
   - Nếu chưa nhìn thẳng: chỉnh `SERVO_CENTER_US`.
3. **Khoảng cách:** đưa tay trước cảm biến; dòng "Phía trước" trên bản đồ phải đổi đúng. Nếu báo "Chưa nhận tín hiệu", kiểm tra dây.
4. **Motor mới:** kéo joystick tiến và lùi, cả 4 bánh phải quay đúng chiều. Nếu `front_right` quay ngược, đổi `motor_inverted` của bánh đó.
5. **Xoay tại chỗ:** kéo joystick sang phải; hai bánh trái tiến, hai bánh phải lùi, không bánh nào báo kẹt.

## 3. Hiệu chỉnh trên sàn (bắt buộc)

Trong mô phỏng, nếu xe xoay ít hơn 20% so với encoder tính thì xe dừng cách điểm xuất phát khoảng 1,7 m. Vì vậy không được bỏ qua bước này.

1. Chạy `tools/calibrate_track.py` bằng Thonny, nhập `TEST` khi xe đã đặt trên sàn trống.
2. Xe xoay khoảng 2 vòng. Nhập góc thật xe đã xoay.
3. Sửa `TRACK_WIDTH_M` trong `config.py` theo số script in ra, nạp lại, chạy lại đến khi lệch dưới 5%.
4. Lái thẳng 1 m bằng joystick, so số "Đã đi" trên web với thước. Nếu lệch nhiều, đo lại `diameter_mm`.

## 4. Thử trên sàn, tăng dần độ khó

Mỗi lần thử: đặt xe vào điểm xuất phát, đánh dấu sàn, bấm **Đặt lại bản đồ**.

| Lần | Cách làm | Đạt khi |
|---|---|---|
| 1 | Lái thẳng 1 m, bấm **Quay về** | Xe xoay đầu, về gần điểm đầu |
| 2 | Lái có một khúc cua | Xe đi theo đường cũ |
| 3 | Lái thẳng 2 m, đặt hộp lớn chắn giữa đường, bấm **Quay về** | Xe dừng trước hộp, vòng qua, đi tiếp |
| 4 | Vây xe bằng hộp ở mọi phía | Xe dừng hẳn, báo không tìm được đường |

Bấm **DỪNG** bất cứ lúc nào để hủy. Sau mỗi lần, ghi lại khoảng cách từ xe tới điểm xuất phát.

## 5. Thông số nên chỉnh

| Hiện tượng | Thông số trong `config.py` |
|---|---|
| Xoay quá đà, lắc qua lại | Tăng `RETURN_TURN_COAST_S`, hoặc giảm `RETURN_TURN_RPM` |
| Xoay còn thiếu nhiều | Giảm `RETURN_TURN_COAST_S` |
| Xe dừng quá gần vật cản | Tăng `RETURN_STOP_CM` |
| Né vật cản không đủ xa | Tăng `RETURN_AVOID_M` |
| Quay về quá chậm vì dừng quét | Tăng `SCAN_PERIOD_MS` |
| Bánh giật khi khởi động | Giảm `BREAKAWAY_DUTY` hoặc `BREAKAWAY_RAMP_PER_S` |
| Bánh chậm mới chịu quay | Tăng `BREAKAWAY_DUTY` |

## Giới hạn đã biết

- **Xe không về chính xác tuyệt đối.** Vị trí chỉ tính từ encoder nên sai số cộng dồn khi bánh trượt. Thêm MPU6050 sẽ giúp giữ hướng tốt hơn.
- **Cảm biến chỉ nhìn phía trước.** Xe không thấy vật ở phía sau và hai bên khi đang chạy, nên có thể quệt vật ở bên hông.
- **Vật mềm hoặc mặt nghiêng** có thể không phản xạ về HC-SR04, xe sẽ không thấy.
- **Xe dừng để quét.** Khi quay về, xe dừng khoảng 1,5 giây mỗi lần quét nên đi khá chậm.
- **Mất Wi-Fi:** xe vẫn tiếp tục tự về và không thể hủy qua web; dùng công tắc nguồn. Xe tự dừng sau `RETURN_TIMEOUT_S` (180 giây).
- **Chuyển tab hoặc thoát trang** sẽ hủy quay về và dừng xe (nếu trang còn gửi được lệnh).
