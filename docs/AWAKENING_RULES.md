# AWAKENING_RULES (Khai Khiếu)

Khai Khiếu **không phải đột phá cảnh giới**: đó là nghi thức mở Không Khiếu và Nguyên Hải để một người thành Cổ Sư. Đột phá (`/dotpha`) chỉ có sau khi đã khai khiếu. Code tách riêng: `CharacterService.awaken` (khai khiếu) và `CultivationEngine.attempt_breakthrough` (đột phá); khai khiếu không cộng vào bộ đếm đột phá (có test).

## 1. Đối chiếu đoạn mô tả bạn gửi
| Ý trong đoạn mô tả | Kết quả |
|---|---|
| Người đủ tuổi dự Đại Điển, ánh sáng Hy Vọng Cổ nhập vào cơ thể, tụ ở bụng dưới, Không Khiếu hình thành | Đúng (S11, chương 5: mỗi điểm sáng là một Hy Vọng Cổ, bay vào người theo từng bước; Không Khiếu hiện ra dưới rốn, giữa hai quả thận). |
| Số bước: dưới 10 không có tư chất, 10-20 Đinh, 20-30 Bính, 30-40 Ất, 40-50 Giáp | Đúng, khớp từng số (S11). |
| Tư chất gắn với sức chứa Nguyên Hải | Đúng: Fang Yuan có sức chứa 44% là hạng Bính, sau này 90% là hạng Giáp (S2); tốc độ hồi chân nguyên cũng phụ thuộc tư chất (S1, S2). Khớp khoảng thành trong file của bạn. |
| Sau khi khai khiếu là Nhất Chuyển Cổ Sư | Đúng theo hệ cảnh giới (S3). Tuổi khai khiếu 15 khớp bảng tu vi của Fang Yuan (S2). |
| "Một lớp màng ánh sáng hình thành bảo vệ Không Khiếu" | **Chưa tìm thấy** trong đoạn nguồn đã đọc. Không đưa vào game. |
| Được chọn và luyện hóa Bản Mệnh Cổ | Chưa kiểm chứng chi tiết từ nguồn; game dùng thiết kế riêng (mục 3). |
| Ba liên kết sagaofgu.com | Mình chưa mở được các trang đó (xem SOURCES.md), nên đối chiếu bằng chương 5 và wiki thay thế. |

## 2. Đại Điển trong game
- `/khaikhieu` xác nhận (không làm lại được), rồi ghi kết quả vào dữ liệu trước, sau đó mới chiếu diễn tiến từng bước bằng cách sửa tin nhắn. Bot sập giữa chừng thì kết quả vẫn còn.
- Chọn nhóm theo trọng số (Đinh 40, Bính 35, Ất 18, Giáp 6.9, Thập Tuyệt Thể 0.1: design), rồi chọn số bước trong khoảng của nhóm: Đinh 10-19, Bính 20-29, Ất 30-39, Giáp 40-50 (biên thuộc nhóm cao hơn; canon ghi các khoảng chạm nhau).
- Thành = 0.02 × số bước, không vượt trần nhóm (Giáp tối đa 9.99 thành). Ví dụ 23 bước là Bính, 4.6 thành. Công thức tuyến tính là design; các biên nhóm là canon/file của bạn. Thập Tuyệt Thể: 10 thành, 50 bước (design).
- **Không có tư chất** (dưới 10 bước): có trong dữ liệu nhưng trọng số mặc định 0 để không ai bị khóa khỏi game bằng may rủi. Nếu bật, người đó không có nhân vật, phải chờ 30 ngày thế giới mới dự lại (`ceremony_log`), để không thể quay lại liên tục.
- Kết quả: nhân vật Nhất Chuyển Sơ Giai, tuổi 15, chân nguyên 50% Nguyên Hải, 30 Nguyên Thạch quà khởi đầu (design), **chưa có Cổ nào**.

## 3. Bản Mệnh Cổ (design)
- `/ban-menh-co`: chọn một Cổ làm Bản Mệnh Cổ, chỉ một lần. Lựa chọn hiện có: Nguyệt Quang Cổ, Tửu Trùng, Hùng Lực Cổ (các Cổ có nhãn `vital_gu_choice` trong `gu_gameplay.json`, số liệu tạm).
- Sau đó luyện hóa bằng `/luyen-co` như Cổ thường. Khác biệt (design): luyện hóa thất bại không giết nó, và nó không chết đói (sinh lực tối thiểu 1). Dấu hiệu lưu ở chính bản ghi Cổ (`vital: true`), không lưu trùng ở nhân vật.
- Chưa có: hiệu ứng liên kết sinh mệnh khi Bản Mệnh Cổ bị thương, đổi Bản Mệnh Cổ, các lựa chọn Bản Mệnh Cổ theo gia tộc. Cần nghiên cứu nguyên tác trước.
