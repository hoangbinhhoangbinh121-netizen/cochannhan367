# CANON_RULES

Nhãn trạng thái: **canon** (có nguồn trong SOURCES.md), **user** (do chủ dự án quy định trong file đính kèm), **design** (cơ chế gameplay tự thiết kế, KHÔNG phải nguyên tác), **unverified** (chưa có nguồn đủ chắc, chưa triển khai).

## Cảnh giới

| Quy tắc | Giá trị trong code | Trạng thái | Nguồn |
|---|---|---|---|
| Cổ Sư phàm nhân gồm 5 chuyển, mỗi chuyển 4 tiểu cảnh giới | `rules.json: ranks` | canon | S3 |
| Màu chân nguyên theo chuyển | Thanh Đồng, Xích Thiết, Bạch Ngân, Hoàng Kim, Tử Tinh; tiên nguyên Lục Chuyển: Thanh Bồ Đào (green grape) | canon (tên Hán-Việt là cách dịch của dự án) | S1, S2, S3 |
| 1 phần chân nguyên chuyển sau = 10 phần chuyển trước | `portion_ratio: 10` | canon | S1 |
| Tiểu cảnh giới khác nhau nhỏ hơn chênh lệch giữa các chuyển | `stage_capacity_mult: 1.0/1.5/2.25/3.4` | design (số cụ thể) | ý canon ở S1 |
| Lục Chuyển trở lên là Cổ Tiên, không dùng bốn tiểu cảnh giới của Cổ Sư | engine chặn ở Ngũ Chuyển Đỉnh Phong; lên Cổ Tiên chỉ qua `/thang-tien` | canon (phân biệt) | S2, S3, S6 |
| Thọ nguyên theo chuyển (100/150/200/300/500) | `lifespan_years` | **design** | chưa xác minh |

## Tư chất và thể chất

| Quy tắc | Trạng thái | Nguồn |
|---|---|---|
| Đinh 2-4 thành, Bính 4-6, Ất 6-8, Giáp 8-9.9, Thập Tuyệt Thể 10 thành | **user** (file Thể chất, tư chất); khớp ví dụ nguyên tác (Bính 44%, Giáp 90%) | file người dùng, S2 |
| Số bước Đại Điển: dưới 10 không tư chất, 10-20 Đinh, 20-30 Bính, 30-40 Ất, 40-50 Giáp | canon | S11 |
| Thành = 0.02 × số bước; trọng số xuất hiện; nhóm không tư chất tắt mặc định; Bản Mệnh Cổ không chết khi luyện hóa thất bại hay chết đói | **design** | |
| Danh sách 10 Thập Tuyệt Thể | **user** | file người dùng |
| Thập Tuyệt Thể không thăng tiên kịp thời hạn thì Không Khiếu tự bạo, chết | **user**; thời hạn 40 năm là design | file người dùng |
| Thập Tuyệt Thể hồi chân nguyên nhanh | canon (hệ số 2.0 là design) | S1 |
| Trọng số xuất hiện các tư chất khi khai khiếu | design | |

Khai Khiếu và Bản Mệnh Cổ: xem `AWAKENING_RULES.md`. Khoảng thành lấy theo file của chủ dự án, đổi được trong `rules.json` mà không sửa code.

## Tôn Giả, Thăng Tiên

| Quy tắc | Trạng thái |
|---|---|
| Cửu Chuyển Cổ Tiên KHÔNG tự động là Tôn Giả; Tôn Giả cực hiếm, số lượng cùng tồn tại giới hạn | canon (S4); code: chưa có đường nào lên Tôn Giả |
| Không có Cửu Chuyển Sơ/Trung/Cao/Đỉnh | theo yêu cầu dự án; code không tạo |
| Điều kiện thành Tôn chi tiết (lưu phái, Đạo Ngân, ý Thiên Đạo, Vạn Kiếp...) | **unverified**, cần nghiên cứu nguyên tác trước khi code |
| Thăng Tiên: chỉ từ Ngũ Chuyển; cần cân bằng Thiên/Địa/Nhân khí; Nhân khí cao thì tiên khiếu tốt hơn; có thể thất bại; thành công sinh tiên khiếu và Phúc Địa | canon (S7, S8, S9); chi tiết xem `ASCENSION_RULES.md` |
| Thời lượng, công thức, Nhân khí từ hành trình, khí theo vùng, hậu quả thất bại, thọ nguyên 1000 năm | **design** |
| Độ Kiếp (Thiên Kiếp, Địa Tai), Đạo Ngân, Tiên Nguyên có sức chứa, Phúc Địa sau thăng tiên | chưa triển khai |

## Cổ Trùng

| Quy tắc | Trạng thái |
|---|---|
| Tiên Cổ (Lục Chuyển trở lên) là độc nhất, không có hai con giống nhau | canon (S6); chưa triển khai |
| Cổ phải đủ cấp mới dùng hiệu quả; Cổ cao hơn tu vi tốn kém | canon (ý chung); design (công thức) |
| Rank, loại, thức ăn, chu kỳ nuôi của 74 Cổ trong file Excel | **unverified**; chỉ 5 Cổ có số liệu thiết kế tạm, gắn `provisional` |
| Cổ cần được nuôi, bỏ đói thì suy yếu rồi chết | canon (ý chung); design (chu kỳ, tốc độ suy giảm) |

## Lưu phái và sát chiêu

38 lưu phái và 20 sát chiêu từ file người dùng đã nạp ở dạng **chỉ có tên** (`status: name_only`). Gợi ý cần kiểm tra: *Vũ đạo* và *Trụ đạo* trong danh sách có thể tương ứng Không Gian Đạo và Thời Gian Đạo của nguyên tác (宇 và 宙); chưa xác minh nên chưa gán nghĩa trong code.

## Bản đồ và di chuyển

| Quy tắc | Trạng thái |
|---|---|
| Năm đại vực Nam Cương, Bắc Nguyên, Đông Hải, Tây Mạc, Trung Châu; Trung Châu ở giữa | canon (vị trí tương đối) |
| Tọa độ, đường nối, địa hình, độ nguy hiểm, tốc độ đi (120 đơn vị/ngày TG, +10% mỗi chuyển), tỉ lệ phục kích 4% mỗi bậc nguy hiểm, mất 10-25% Nguyên Thạch | **design** |
| Sinh thái, thú hoang và phục kích bằng chiến đấu thật | chưa có (hiện chỉ trừ Nguyên Thạch) |

## Chợ và giao dịch

| Quy tắc | Trạng thái |
|---|---|
| Nguyên Thạch là tiền tệ của Cổ Sư | canon |
| Giá gốc từng Cổ, hàng tồn tối đa, tốc độ hồi hàng, công thức cung cầu, thu mua 50%, phí 5% | **design** (`MARKET_RULES.md`) |
