"""Sinh docs/GU_CLASSIFICATION.md và docs/phan_cap_co_trung.txt từ gu_classification.json (không sửa tay)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.rules import GameData  # noqa: E402

d = GameData(ROOT / "data")
NAMES = {"tiên": "Tiên cổ", "phàm": "Phàm cổ", "đặc thù": "Đặc thù"}
group = lambda k: [g for g in d.gu.values() if g["proposed_quality"] == k]
ranks = lambda g: (f"{g['rank_observed'][0]}" if g["rank_observed"][0] == g["rank_observed"][1] else f"{g['rank_observed'][0]}-{g['rank_observed'][1]}") if g.get("rank_observed") else "-"
verified = sum(1 for g in d.gu.values() if g["quality_status"] == "verified")

md = ["# GU_CLASSIFICATION (Phàm cổ / Tiên cổ / Đặc thù)", "",
      "> File sinh tự động bởi `tools/gen_gu_classification_doc.py`. Không sửa tay. Bản chữ thuần: `phan_cap_co_trung.txt`.", "",
      "Quy tắc: chỉ mục có nguồn nguyên tác mới được ghi `verified` và có `quality` thật; mục còn lại để `unknown` (kèm `proposed_quality` là đề xuất từ bảng bạn đưa vào) và **không dùng cho gameplay** cho tới khi xác minh. Dữ liệu: `data/gu_worms/gu_classification.json` (sinh bởi `tools/classify_gu.py`).", "",
      "Nền tảng: Rank 1-5 là Cổ phàm, từ Rank 6 là Tiên Cổ (S13, S6). Tiên Cổ độc nhất và có thể nâng chuyển số mà vẫn giữ tên (S12).", "",
      "## Tổng hợp", "", "| Nhóm | Số lượng (đề xuất) | Đã đối chiếu |", "|---|---|---|"]
for k in ("tiên", "phàm", "đặc thù"):
    g = group(k); md.append(f"| {NAMES[k]} | {len(g)} | {sum(1 for x in g if x['quality_status'] == 'verified')} |")
md += [f"| Tổng | {len(d.gu)} | {verified} |", ""]
txt = [f"PHÂN CẤP CỔ TRÙNG ({len(d.gu)} con, {verified} con đã đối chiếu nguyên tác)", "=" * 60,
       "[ĐÃ XÁC MINH] = có nguồn nguyên tác; [ĐỀ XUẤT] = từ bảng người dùng cung cấp, chưa xác minh, chưa dùng cho gameplay.", ""]
for k, title in (("tiên", "I. TIÊN CỔ (Lục Chuyển trở lên)"), ("phàm", "II. PHÀM CỔ (Nhất đến Ngũ Chuyển)"), ("đặc thù", "III. CỔ ĐẶC THÙ")):
    g = group(k)
    md += [f"## {title}", "", "| Tên | Trạng thái | Chuyển số quan sát được | Nguồn / ghi chú |", "|---|---|---|---|"]
    txt += [title, "-" * 60]
    for x in sorted(g, key=lambda x: (x["quality_status"] != "verified", x["name"])):
        if x["quality_status"] == "verified":
            md.append(f"| {x['name']} | **đã đối chiếu** | {ranks(x)} | {x['source']}: {x['note']} |")
            txt.append(f"[ĐÃ XÁC MINH] {x['name']} | chuyển {ranks(x)} | {x['source']}")
        else:
            md.append(f"| {x['name']} | chưa xác minh | - | {x['note'] or 'đề xuất trong bảng gốc'} |")
            txt.append(f"[ĐỀ XUẤT]     {x['name']}" + (f"  ({x['note']})" if x["note"] else ""))
    md.append(""); txt.append("")
md += ["## IV. Đính chính so với bảng gốc", "",
       "- **Định Tiên Du** không cố định ở Lục Chuyển: nguồn có bản Rank 7 (S12); chuyển số thay đổi theo bản và theo lần nâng cấp.",
       "- **Chí Tôn Tiên Thai Cổ** (bảng gốc ghi Cửu Chuyển): nguồn đã đọc chỉ nhắc Cổ này trong nghi thức của Ảnh Tông và việc Phương Nguyên đoạt nó, **không nêu chuyển số**; giữ chưa xác minh. Các Tiên Cổ khác (Tình Cổ, Sơn Như Cố, Độc Thệ Cổ, các Cổ Vận Đạo, Vạn Ngã Tiên Cổ, Mộng Điệp Tiên Cổ, Đạo Sinh Cổ) cũng chưa có nguồn xác nhận.",
       "- **Trí Tuệ Cổ**: Rank 9 có nguồn (S13); đồng thời là Cổ trong truyền thuyết Nhân Tổ (S11), cần phân biệt với Cổ Tiên thông thường.",
       "- **Hùng Lực Cổ** (Bear Strength Gu của tộc Hùng) được nhắc cùng loại với Nguyệt Quang Cổ nhưng nguồn không ghi rõ Rank nên chưa xác minh.",
       "- Đã xác minh thêm 5 Phàm cổ: Nguyệt Quang, Tửu Trùng, Bạch Trư, Hắc Trư (Rank 1) và Bạch Ngọc Cổ (Rank 2).",
       "- Bảng gốc xếp hầu hết Cổ còn lại là Phàm cổ mà không dẫn nguồn từng con: giữ ở mức đề xuất. Chuyển số không suy ra được từ tên hay công dụng.", "",
       "## V. Cấu trúc dữ liệu trong code", "",
       "`quality`, `quality_status`, `proposed_quality`, `rank_observed` [min, max] hoặc null, `source`, `note`. Trường `rank` (gameplay) tách riêng; với Cổ chơi được đã xác minh, `rank` phải khớp `rank_observed` (có test)."]
txt += ["LƯU Ý", "- Chuyển số không suy ra được từ tên hay công dụng; mỗi Cổ cần nguồn riêng.",
        "- Tiên Cổ cùng tên có thể tăng chuyển số khi nâng cấp; Định Tiên Du có cả bản Rank 6 và Rank 7.",
        "- Chí Tôn Tiên Thai Cổ chưa xác minh được chuyển số.", f"- Bảng gốc có 75 dòng nhưng Thủy Toản Cổ trùng hai lần nên còn {len(d.gu)} con."]
(ROOT / "docs/GU_CLASSIFICATION.md").write_text("\n".join(md) + "\n", encoding="utf-8")
(ROOT / "docs/phan_cap_co_trung.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
print("ok", verified)
