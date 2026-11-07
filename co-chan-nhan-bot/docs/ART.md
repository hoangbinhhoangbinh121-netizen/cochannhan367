# ART (pixel art và giao diện)

## Cổ Trùng
- 72 sprite lấy từ bảng sprite do bạn cung cấp (`assets/gu/source/sheet_user.png`, 12 cột x 6 hàng). `python tools/slice_gu_sheet.py` cắt từng ô, xóa nền bằng loang từ biên (giữ nguyên viền tối bên trong sprite), căn giữa và đổi cỡ 256x256 nền trong suốt thành `assets/gu/<gu_id>.png`. Xem nhanh: `assets/gu/_sheet.png`.
- Thứ tự ô trong bảng = thứ tự trong `gu_seed.json` bỏ hai con có ảnh riêng. **Đổi thứ tự hoặc thêm Cổ vào dữ liệu thì phải sắp lại bảng cho khớp**; công cụ báo lỗi nếu số ô khác số Cổ cần sprite.
- **Định Tiên Du** và **Xuân Thu Thiền** dùng ảnh riêng của bạn (`assets/gu/user_source/`), chỉ cắt vuông và đổi cỡ.
- Bộ sprite sinh bằng thuật toán trước đó được giữ ở `assets/gu/legacy/` (không còn dùng).

## Giao diện: toàn bộ màn hình là ảnh pixel
Mọi phản hồi của game (hồ sơ, tu vi, luyện hóa, đột phá, thăng tiên, Cổ Trùng, thế giới, bản đồ, hành trình, quản trị, thông báo lỗi và cả bảng xác nhận) là một ảnh pixel 720 px rộng; Discord chỉ làm khung gửi ảnh và hai nút Xác nhận/Hủy (nút là thành phần của Discord nên không vẽ pixel được).
- `core/pixel_ui.py`: bộ dựng khối (tiêu đề + biểu tượng 8x8, văn bản tự xuống dòng, bảng nhãn-giá trị, thanh chia ô, hộp thông báo, ảnh/banner, sprite kèm nội dung, hai cột) và `render()` ghép thành màn hình có khung pixel.
- `core/screens.py`: tất cả màn hình của game (hàm thuần, nhận dữ liệu service, trả ảnh); cog chỉ gọi `core.ui.reply`. Muốn đổi giao diện một lệnh chỉ cần sửa hàm tương ứng ở đây. Có test dựng thử 37 màn hình.
- `core/pixel.py`: thẻ nhân vật, lưới Kho Cổ, bản đồ. `core/pixel_icons.py`: 33 biểu tượng 8x8. Màu nhấn theo hệ thống (nhân vật tím, tu luyện xanh ngọc, Cổ vàng, thế giới xanh dương, quản trị xám, lỗi đỏ, Cổ Tiên xanh bồ đào).
- Chữ dùng DejaVu Sans Mono tắt khử răng cưa (đủ dấu tiếng Việt, **không có Hán tự**), nên Hán tự của Cổ Trùng được gửi kèm dạng chữ thường trong tin nhắn `/cotrung`.
- Đại Điển Khai Khiếu: `assets/ui/ceremony_0..4.png` (biển ánh sáng Hy Vọng Cổ, vẽ rộng ra từ ảnh của bạn), `ceremony_success.png` (ảnh khai khiếu thành công của bạn đã pixel hóa 32 màu), `ceremony_fail.png`; sinh bằng `python tools/gen_ceremony_art.py`. Ảnh nguồn nằm ở `assets/ui/source/`.

## Hiển thị tư chất
`core/fmt.thanh`: 10 thành chỉ dành cho Thập Tuyệt Thể; các hạng khác làm tròn xuống nên Giáp Đẳng tối đa hiện 9.9 thành (trước đây 0.999 bị làm tròn thành "10.0", đã sửa và có test).

## Cổ Trùng
Toàn bộ 74 Cổ đều có hình (72 từ bảng sprite của bạn, 2 là ảnh riêng của bạn) và được dùng trong mọi màn hình; có test kiểm tra.
