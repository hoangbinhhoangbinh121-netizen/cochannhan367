# CULTIVATION_RULES (Cổ Sư phàm nhân, Phase 3)

Tất cả công thức nằm trong `engines/cultivation_engine.py`, tham số ở `data/config/rules.json`. Trạng thái: design trừ khi ghi khác.

**Nguyên Hải (sức chứa)**: `capacity = 160 × stage_mult[stage] × aptitude_ratio`, đơn vị là "phần" chân nguyên của chính chuyển hiện tại. `stage_mult = [1.0, 1.7, 2.9, 4.9]` (mỗi lần đột phá tăng khoảng 70%; bản cân bằng trước là 100 và 1.0/1.5/2.25/3.4). Vì 1 phần chuyển sau = 10 phần chuyển trước (canon), giá trị quy đổi luôn tăng nghiêm ngặt qua cả 20 cảnh giới (có test).

**Hồi chân nguyên theo thời gian**: `regen/ngày TG = capacity × (0.12 + 0.24 × ratio)`, nhân 2 cho Thập Tuyệt Thể. Tính lười theo `essence_updated_day`, nên người chơi ngoại tuyến vẫn hồi.

**Luyện hóa Nguyên Thạch**: `hiệu suất = min(1, 0.6 + 0.4 × ratio + bonus Cổ)`; `Nguyên Thạch mỗi phần = stones_per_portion[chuyển] / hiệu suất` với bảng `[1, 4, 16, 64, 256]`. Chỉ tiêu hao đúng lượng cần để lấp đầy Nguyên Hải, không rút thừa.

**Đột phá**: yêu cầu chân nguyên ≥ 90% sức chứa, tiêu hao 80% sức chứa. Xác suất = `base + (ratio − 0.5) × 0.4 + (căn cơ − 50) / 250 (+0.10 nếu Thập Tuyệt Thể)`, kẹp trong [5%, 95%]. `base`: 80%, 65%, 50% cho ba bước tiểu cảnh giới; 30% khi lên chuyển mới. Thất bại: mất chân nguyên đã tiêu và 3-8 căn cơ. Thành công còn được bồi thêm 25% sức chứa mới. Lên chuyển mới: chân nguyên còn lại chia 10 (đổi đơn vị phần), thọ nguyên tăng theo bảng.

**Ngũ Chuyển Đỉnh Phong**: không có đột phá bằng nút bấm. Engine trả về điều kiện còn thiếu cho Thăng Tiên.

**Tử vong**: hết thọ nguyên; riêng Thập Tuyệt Thể thêm hạn 40 năm kể từ khai khiếu (user). Tử vong được ghi nhận ở lần tương tác kế tiếp (giao dịch commit rồi mới báo lỗi). Đời cũ chuyển vào `graveyard`, Cổ của đời cũ bị xóa.

**Chưa có**: Không Khiếu chi tiết, Căn Cơ ảnh hưởng ngoài đột phá, Cổ hỗ trợ đột phá, Tiên Khiếu/Đạo Ngân (Cổ Tiên).

**Dùng Cổ**: chi phí luyện hóa Cổ là 5% sức chứa (trước là 10%); chi phí kích hoạt của các Cổ chơi được đã giảm một nửa (design).
