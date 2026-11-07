# ROADMAP và trạng thái thật

## Hoàn thành (có test)
- Phase 3 phần lõi: JSON DB (ghi nguyên tử, checksum, giao dịch, journal, backup, recovery), thời gian thế giới, sự kiện theo seed, mỏ tài nguyên hữu hạn.
- Hệ thống 10 (nhân vật) và 03 (tu luyện Cổ Sư phàm nhân) ở mức cơ bản; hệ thống 02 (Cổ Trùng): sở hữu, luyện hóa, nuôi dưỡng, một hiệu ứng cơ chế (Tửu Trùng).
- Lệnh: `/khaikhieu /nhanvat /tuvi /tuluyen /dotpha /cotrung /kho-co /luyen-co /nuoi-co /thegioi /khaithac /ban-do /dichuyen /thang-tien /ban-menh-co /muaban /giaodich` và nhóm `/admin` (cap-co, cap-nguyen-thach, sao-luu, kiem-tra-du-lieu, tick-the-gioi).

- Hệ thống 01 (mức cơ bản): bản đồ năm đại vực, đường đi ngắn nhất theo thời gian, vị trí nội suy khi đang đi, phục kích, chặn khai thác khi đang đi (`engines/map_engine.py`, có test).
- Khai Khiếu Đại Điển đúng bảng số bước và Bản Mệnh Cổ (`AWAKENING_RULES.md`, có test).
- Thăng Tiên (`/thang-tien`): điều kiện, Nhân khí từ hành trình, khí theo vùng, quá trình theo thời gian, thành công/thất bại có hậu quả, trạng thái Cổ Tiên (xem `ASCENSION_RULES.md`, có test).
- Phân cấp Cổ Trùng: 12/74 con đã đối chiếu nguyên tác, còn lại ở mức đề xuất (`GU_CLASSIFICATION.md`, `phan_cap_co_trung.txt`).
- Chợ Cổ Trùng và giao dịch trực tiếp (`MARKET_RULES.md`): hàng tồn hữu hạn, giá theo cung cầu, thu mua lỗ, phí hủy, giao dịch nguyên tử chống nhân bản (có test chạy đồng thời).
- Giao diện pixel toàn bộ: 37 màn hình (`core/screens.py`), cảnh Đại Điển Khai Khiếu, phân loại Phàm cổ/Tiên cổ có đối chiếu (`GU_CLASSIFICATION.md`).
- Pixel art: 72 sprite Cổ Trùng (từ bảng sprite của bạn), banner, thẻ nhân vật, lưới Kho Cổ, bản đồ (xem `docs/ART.md`).

## Cố ý chưa làm (không có lệnh giả)
Tiên Nguyên/Đạo Ngân/Thiên Kiếp/Địa Tai của Cổ Tiên, Tôn Giả, lưu phái và Đạo Ngân (mới có danh sách tên), chiến đấu và sát chiêu, Phúc Địa/Động Thiên, bí cảnh, thế lực, đấu giá, thương đội, NPC và AI, thu phục Cổ hoang dã.

## Thứ tự đề xuất tiếp theo
1. Hệ thống Cổ Tiên: Tiên Nguyên, Đạo Ngân, Phúc Địa, Thiên Kiếp/Địa Tai (hiện Cổ Tiên chỉ đi lại, khai thác, nuôi Cổ). Nghiên cứu điều kiện thành Tôn.
2. Mở rộng bản đồ: thành trì, địa hình chi tiết trong từng đại vực, Cửu Thiên (hiện mới có 5 đại vực và hành trình giữa các vùng).
3. (Đã làm chợ cơ bản.) Mở rộng: đấu giá, thương đội, giá theo vùng.
3. Chiến đấu theo lượt (hệ thống 06), dùng dữ liệu Cổ và lưu phái.
5. NPC theo luật, thế lực.

Việc kỹ thuật còn nợ: chạy thử với Discord thật; test tải; dọn instance Cổ của người chơi chết; mở rộng backup (thử restore tự động).
