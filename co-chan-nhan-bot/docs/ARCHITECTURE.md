# ARCHITECTURE

Phân tầng, mỗi tầng chỉ gọi tầng dưới:

`cogs` (lệnh, giao diện) → `services` (quy tắc có IO, giao dịch) → `engines` (hàm thuần, không IO) và `database` (JsonStore, Transaction).

- **cogs**: chỉ nhận lệnh, gọi service, dựng embed. Không đọc/ghi JSON, không chứa số liệu gameplay.
- **services**: mọi thay đổi dữ liệu đi qua `BaseService.mutate`, mở một `Transaction` khóa trước toàn bộ tài liệu liên quan, kiểm tra tử vong, rồi commit. Lỗi quy tắc ném `GameError`, không ghi gì.
- **engines**: công thức thuần (tu luyện, thời gian, kinh tế, sự kiện, thời tiết). Test không cần Discord.
- **database**: mỗi thực thể một file (`players/<discord_id>.json`, `gu_instances/<id>.json`...), bọc `{meta: {rev, checksum, updated}, data}`.
- **core**: bot, scheduler asyncio, lỗi, quyền, giao diện chung.
- **data**: toàn bộ dữ liệu gameplay (`rules.json`, Cổ Trùng, sự kiện, vùng). Đổi cân bằng không cần sửa code.

## Bảo đảm của lớp JSON
Ghi nguyên tử (file tạm, fsync, `os.replace`, giữ `.bak`); checksum SHA-256 và tự khôi phục từ `.bak` khi hỏng; revision cho khóa lạc quan; khóa file `flock` giữa tiến trình và `asyncio.Lock` trong tiến trình; giao dịch nhiều tài liệu khóa theo thứ tự cố định (không deadlock) và commit qua journal, nên chuyển vật phẩm không nhân bản hay mất khi sập giữa chừng (đã test phát lại journal và 60 giao dịch chuyển đồng thời).

## Thế giới không dừng
Đồng hồ thế giới là hàm của giờ thật (1 giờ thật = 1 ngày thế giới). Chân nguyên, mỏ, đói của Cổ đều tính lười theo mốc thời gian. Sự kiện thế giới bắt kịp theo seed ngày (tối đa 400 ngày), nên tắt bot lâu rồi bật lại vẫn tái hiện đúng.

## Giới hạn đã biết
- Ghi nhiều file nhỏ có fsync: ổn cho hàng trăm người chơi hoạt động; hàng nghìn cần đo. Hướng nâng cấp không phá kiến trúc: thay `JsonStore` bằng backend khác sau cùng giao diện `get/put/transaction`.
- Thao tác chỉ chạy trên một tiến trình bot (khóa asyncio); `flock` chỉ chống ghi đè giữa tiến trình, không thay cho khóa logic.
- Cogs Discord chưa được chạy với Discord thật trong môi trường dựng dự án (không có mạng, chưa cài discord.py): mới biên dịch và rà soát.
