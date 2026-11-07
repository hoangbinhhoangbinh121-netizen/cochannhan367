# Cổ Chân Nhân Bot

Discord MMORPG mô phỏng thế giới Reverend Insanity. Python + discord.py, dữ liệu JSON, **không gọi AI bên ngoài** (mọi quy luật chạy bằng luật và dữ liệu).

Trạng thái thật và việc cố ý chưa làm: `docs/ROADMAP.md`. Số nào là nguyên tác, số nào là thiết kế tạm: `docs/CANON_RULES.md`.

## Chạy
```bash
pip install -r requirements.txt
cp .env.example .env      # điền DISCORD_TOKEN, OWNER_IDS (và DEV_GUILD_ID khi phát triển)
python main.py
```
Mời bot với scope `bot` và `applications.commands`; không cần intent đặc quyền.

## Kiểm thử (không cần Discord)
```bash
python -m unittest discover -s tests -t .
```

## Hình ảnh
Toàn bộ giao diện là ảnh pixel (xem `docs/ART.md`). Tạo lại: `python tools/gen_pixel_art.py` (sprite Cổ cũ, đã thay bằng bảng sprite của bạn; cắt lại bảng bằng `python tools/slice_gu_sheet.py`) và `python tools/gen_ui_art.py` (banner, biểu tượng). Cần Pillow.

## Dữ liệu
- `data/config/rules.json`: toàn bộ con số cân bằng (đổi không cần sửa code).
- `data/gu_worms/source_cotrung.xlsx` → `python tools/import_gu_xlsx.py` → `gu_seed.json` (74 Cổ Trùng, chưa xác minh rank). `gu_gameplay.json` là số liệu tạm cho 5 Cổ chơi được. `python tools/gen_gu_doc.py` sinh lại `docs/GU_WORM_DATABASE.md`.
- Lưu phái, sát chiêu, thể chất: mới có tên (từ file của bạn).

## Lệnh hiện có
Người chơi: `/khaikhieu /nhanvat /tuvi /tuluyen /dotpha /cotrung /kho-co /luyen-co /nuoi-co /thegioi /khaithac /ban-do /dichuyen /thang-tien /ban-menh-co /muaban (xem, mua, ban) /giaodich`.
Quản trị (ID 1530490044098285711 được cấu hình sẵn trong `config.py`, thêm người khác qua OWNER_IDS; có nhật ký `logs/admin.log`): `/admin cap-co, cap-nguyen-thach, sao-luu, kiem-tra-du-lieu, tick-the-gioi`.

## Vận hành
Sao lưu tự động theo `BACKUP_INTERVAL_MINUTES` vào `backups/` (zip, xoay vòng). Khởi động tự phát lại giao dịch dang dở và quét file hỏng. Khôi phục thủ công: dừng bot, gọi `database.recovery.restore_backup(zip, data_dir)`.
