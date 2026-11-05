"""Sinh docs/GU_WORM_DATABASE.md từ data/gu_worms/*.json (không sửa tay file đó)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys_path = str(ROOT)
import sys
sys.path.insert(0, sys_path)
from core.rules import GameData

d = GameData(ROOT / "data")
playable = [g for g in d.gu.values() if d.playable(g)]
rest = [g for g in d.gu.values() if not d.playable(g)]
lines = ["# GU_WORM_DATABASE", "",
         "> File sinh tự động bởi `tools/gen_gu_doc.py` từ `data/gu_worms/gu_seed.json` (nhập từ Cotrung (1).xlsx) và `gu_gameplay.json`. Không sửa tay.", "",
         f"- Tổng số Cổ Trùng nhập từ file Excel: **{len(d.gu)}** (đã gộp bản trùng *Thủy Toản Cổ*).",
         f"- Dùng được trong gameplay (đã có rank, thức ăn, chu kỳ nuôi): **{len(playable)}**, toàn bộ là số liệu **thiết kế tạm** (`provisional`), chưa đối chiếu nguyên tác.",
         f"- Chưa dùng được (thiếu rank/thức ăn/cổ phương, chưa xác minh): **{len(rest)}**.", "",
         "Lưu ý chất lượng dữ liệu nguồn: tên *Cổ Định Vận* có Hán tự 定运蛊 (Hán-Việt chuẩn là *Định Vận Cổ*); mục *Thư Trùng* trong file chỉ ghi \"quý hiếm\" nên chưa có công dụng cụ thể; một số mô tả trong file ghi rõ \"theo năng lực cổ trùng\" mà chưa có cơ chế.", "",
         "## Dùng được trong gameplay (tạm)", "",
         "| gu_id | Tên | Rank | Loại | Thức ăn | Chu kỳ (ngày TG) | Hiệu ứng cơ chế |", "|---|---|---|---|---|---|---|"]
for g in playable:
    lines.append(f"| `{g['gu_id']}` | {g['name']} | {g['rank']} | {g['type']} | {g['food']} x{g['feed_cost']} | {g['feeding_cycle_days']} | {json.dumps(g['effects'], ensure_ascii=False) if g['effects'] else 'chưa có (chờ hệ thống chiến đấu)'} |")
lines += ["", "## Chưa dùng được (chờ nghiên cứu)", "", "| gu_id | Tên | Hán tự | Công dụng theo file |", "|---|---|---|---|"]
for g in rest:
    lines.append(f"| `{g['gu_id']}` | {g['name']} | {g.get('name_han') or ''} | {(g['ability_text'] or '').replace('|', '/')} |")
(ROOT / "docs/GU_WORM_DATABASE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("ok", len(playable), len(rest))
