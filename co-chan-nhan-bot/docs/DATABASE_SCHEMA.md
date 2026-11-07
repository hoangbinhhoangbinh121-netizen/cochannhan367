# DATABASE_SCHEMA

Mỗi tài liệu: `{"meta": {"rev": int, "updated": ISO, "checksum": sha256}, "data": {...}}`.

| Collection | Khóa | Nội dung chính |
|---|---|---|
| `players` | discord_id | id, name, gender, birth_world_day, awakened_world_day, aptitude{grade, ratio}, physique, lifespan_years, status, death, cultivation{rank, stage, essence, essence_updated_day, foundation}, location{region}, resources{nguyen_thach}, gu_ids[], cooldowns{} |
| `gu_instances` | instance_id | gu_id, state (stored/refined), created_world_day, refined_world_day, last_fed_world_day, vitality |
| `graveyard` | discord_id_ngày | bản sao nhân vật đã chết |
| `world_state` | `clock`, `resource_pools`, `market` (items[gu_id]{stock, demand, last_update_day}) | last_event_day; pools[`vùng:tài_nguyên`]{reserve, max_reserve, regen_per_day, last_update_day} |
| `history` | `world_log_<năm>` | entries[] sự kiện thế giới đã xảy ra |

Nguyên tắc: quyền sở hữu Cổ chỉ lưu một chỗ (`players.gu_ids`), thông tin loài Cổ chỉ lưu ở `data/gu_worms` (instance chỉ giữ `gu_id` và trạng thái riêng). Schema kiểm tra tại `models/*.py` mỗi lần ghi.

Chưa có: tài khoản thế lực, kho Cổ thế lực, chợ, Phúc Địa, NPC, bí cảnh (xem ROADMAP).
