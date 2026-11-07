# ASCENSION_RULES (Thăng Tiên)

Nhãn: **canon** (có nguồn trong SOURCES.md), **design** (tự thiết kế để chạy được, không phải nguyên tác), **chưa** (chưa triển khai).

## 1. Đối chiếu đoạn mô tả bạn gửi với nguồn đã đọc

| Ý trong đoạn mô tả | Kết quả đối chiếu |
|---|---|
| Thăng tiên là bước từ Cổ Sư phàm nhân lên Cổ Tiên, không chỉ là đột phá thường | Đúng. Chênh lệch giữa Ngũ Chuyển và Lục Chuyển được xem là lớn nhất, một bên phàm một bên tiên (S9). |
| "Phải đạt đỉnh Lục Chuyển phàm nhân / Lục Chuyển Đại viên mãn" | **Sai**. Phàm nhân tối đa là Ngũ Chuyển; Lục Chuyển đã là Cổ Tiên (S2, S3, S9). Nguồn nói Cổ Sư Ngũ Chuyển là người thăng tiên (S7). Game dùng Ngũ Chuyển Đỉnh Phong. Câu "Tu vi đạt đỉnh Tam chuyển? Không." trong đoạn là câu thừa, đã bỏ. |
| Ba yếu tố Thiên khí, Địa khí, Nhân khí; cân bằng ba khí là then chốt | Đúng (S7, S8). |
| Nhân khí càng cao thì căn cơ càng vững, tiên khiếu càng tốt | Đúng (S8). Nguồn còn nói Nhân khí dày thể hiện kinh nghiệm sống và căn cơ (S7). |
| Ba khí hội tụ rồi ngưng tụ thành tiên khiếu, chân nguyên thành tiên nguyên | Phù hợp: khối khí nổ thành tiên khiếu, bên trong ba khí được điều hòa cân bằng, và được Phúc Địa (S7); nguyên Lục Chuyển màu green grape (S9). |
| "Phá khiếu: chủ động phá vỡ khiếu huyệt phàm nhân" | **Chưa tìm thấy xác nhận** trong nguồn đã đọc. Game chuyển thành: toàn bộ chân nguyên dồn vào quá trình (design). |
| Sau khi thăng tiên, mức dùng Nhân khí giảm, Cổ Tiên chủ yếu cân bằng Thiên khí và Địa khí | Đúng (S8); phần duy trì này **chưa** triển khai. |

Các chi tiết nguồn có mà đoạn mô tả không nêu: thăng tiên dễ bị dòm ngó nên thường có Cổ Tiên hộ pháp (S7, S10); Cổ Sư phải vừa vượt tai kiếp vừa cân bằng ba khí (S7); tai kiếp hình thành từ mất cân bằng Thiên khí và Địa khí trong tiên khiếu (S9); ném một Cổ Ngũ Chuyển vào khối khí lúc then chốt, phần khí dư có thể nâng Cổ phàm lên Tiên Cổ (S7).

## 2. Cơ chế trong game (`engines/ascension_engine.py`, tham số trong `rules.json: ascension`)

Điều kiện bắt đầu (`/thang-tien`): Ngũ Chuyển Đỉnh Phong; chân nguyên ≥ 90% Nguyên Hải; không đang di chuyển; hết hồi phục sau lần thất bại. Nơi thăng tiên là vùng đang đứng.

**Nhân khí** (0-100, design, tính từ hành trình đã sống chứ không lưu thành điểm riêng): căn cơ ×0.4, đột phá thành công (1 điểm mỗi lần, tối đa 20), Cổ luyện hóa thành công (3 điểm mỗi con, tối đa 15), số ngày hành trình (1 điểm mỗi 5 ngày, tối đa 10), năm tháng (tối đa 15). Bậc tiên khiếu: Hạ Phẩm dưới 40, Trung Phẩm từ 40, Thượng Phẩm từ 60, Cực Phẩm từ 80.

**Thiên khí và Địa khí**: mỗi vùng có hệ số riêng và mức bị dòm ngó (design). Lúc phân định, mỗi khí dao động ±20%. `cân bằng = 1 − |Thiên − Địa| / (Thiên + Địa)`.

**Tỉ lệ thành công** = `0.20 + 0.35 × cân bằng + 0.30 × Nhân khí/100 − 0.04 × mức dòm ngó`, kẹp trong [5%, 90%]. Không có đường lên 100%.

**Quá trình**: bắt đầu thì chân nguyên về 0 và nhân vật bị khóa 3 ngày thế giới (khoảng 3 giờ thật): không đi, không khai thác, không tu luyện; chỉ xem trạng thái. Kết quả được phân định lười ở thao tác kế tiếp sau khi hết hạn, nên người chơi ngoại tuyến vẫn có kết quả.

**Kết quả**:
- Thành công: có `immortal` (Lục Chuyển Cổ Tiên, bậc tiên khiếu, Nhân/Thiên/Địa khí lúc thăng tiên), thọ nguyên 1000 năm (design), không còn bị hạn tự bạo của Thập Tuyệt Thể. Không áp bốn tiểu cảnh giới của phàm nhân cho Cổ Tiên.
- Thất bại nhẹ (roll vượt ngưỡng dưới 25 điểm): mất 8-15 căn cơ, nghỉ 7 ngày thế giới.
- Thất bại nặng: mất 20-35 căn cơ; 50% Không Khiếu vỡ nát và tử vong, nếu sống thì lùi một tiểu cảnh giới và nghỉ 14 ngày thế giới.

Cổ Tiên hiện bị chặn khỏi các lệnh tu luyện và luyện hóa Cổ của phàm nhân (có thông báo rõ), vẫn đi lại, khai thác, nuôi Cổ.

## 3. Chưa triển khai (cố ý, không có lệnh giả)
Tiên Nguyên có sức chứa và tiêu hao, Đạo Ngân, Tiên Cổ, Thiên Kiếp và Địa Tai (cần chiến đấu), duy trì cân bằng Thiên/Địa khí, Phúc Địa sinh ra khi thăng tiên, Cổ hộ pháp và tiên vật liệu, Cổ Ngũ Chuyển làm nền cho Tiên Cổ (cần dữ liệu Cổ cấp cao), Tôn Giả.
