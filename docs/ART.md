# ART (pixel art và giao diện)

## Cổ Trùng
- 72 sprite lấy từ bảng sprite do bạn cung cấp (`assets/gu/source/sheet_user.png`, 12 cột x 6 hàng). `python tools/slice_gu_sheet.py` cắt từng ô, xóa nền bằng loang từ biên (giữ nguyên viền tối bên trong sprite), căn giữa và đổi cỡ 256x256 nền trong suốt thành `assets/gu/<gu_id>.png`. Xem nhanh: `assets/gu/_sheet.png`.
- Thứ tự ô trong bảng = thứ tự trong `gu_seed.json` bỏ hai con có ảnh riêng. **Đổi thứ tự hoặc thêm Cổ vào dữ liệu thì phải sắp lại bảng cho khớp**; công cụ báo lỗi nếu số ô khác số Cổ cần sprite.
- **Định Tiên Du** và **Xuân Thu Thiền** dùng ảnh riêng của bạn (`assets/gu/user_source/`), chỉ cắt vuông và đổi cỡ.
- Bộ sprite sinh bằng thuật toán trước đó được giữ ở `assets/gu/legacy/` (không còn dùng).

## Giao diện
- `assets/ui/banner_*.png` (960x320): world, character, cultivation, gu và 5 đại vực. Sinh bằng `python tools/gen_ui_art.py`.
- `assets/ui/orb_r1..r5.png`: quả cầu Nguyên Hải theo màu từng chuyển. `icon_stone/foundation/lifespan.png`.
- `core/pixel.py` vẽ lúc chạy: thẻ nhân vật (`/nhanvat`, `/khaikhieu`), lưới Kho Cổ (`/kho-co`), bản đồ (`/ban-do`). Chữ dùng DejaVu Sans Mono (kèm giấy phép trong `assets/fonts/`), tắt khử răng cưa để giữ nét pixel và đủ dấu tiếng Việt.
