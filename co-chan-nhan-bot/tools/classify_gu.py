"""Phân loại Phàm cổ / Tiên cổ / Đặc thù -> data/gu_worms/gu_classification.json.

Danh sách đề xuất (PROPOSED) lấy từ bảng phân loại người dùng đưa vào; CHỈ những mục có nguồn nguyên tác đã
đối chiếu mới được ghi `verified` và có `quality` thật. Mục còn lại giữ `quality = unknown` và đề xuất nằm ở
`proposed_quality` (không dùng cho gameplay) để không làm sai hệ thống chuyển số.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_gu_xlsx import slug  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

TIEN = ["Xuân Thu Thiền", "Định Tiên Du", "Trí Tuệ Cổ", "Tình Cổ", "Chí Tôn Tiên Thai Cổ", "Nhân Như Cố", "Sơn Như Cố",
        "Niên Lưu Như Thủy Cổ", "Thiên Nguyên Bảo Liên Cổ", "Độc Thệ Cổ", "Định Vận Cổ", "Liên Vận Cổ", "Đoạn Vận Cổ",
        "Nghịch Vận Cổ", "Vạn Ngã Tiên Cổ", "Mộng Điệp Tiên Cổ", "Đạo Sinh Cổ"]
PHAM = ["Tửu Trùng", "Nguyệt Quang Cổ", "Kiên Trì Cổ", "Huyết Lô Cổ", "Vận Khí Cổ", "Thần Niệm Cổ", "Cường Luyện Cổ",
        "Quang Giáp Cổ", "Thời Châm Cổ", "Đao Dực Cổ", "Tử Kỳ Cổ", "Thư Điệp Cổ", "Ghi Ảnh Cổ", "Cốt Mâu Cổ", "Bạch Ngọc Cổ",
        "Thiên Bồng Cổ", "Băng Tinh Cổ", "Thủy Toản Cổ", "Lam Điểu Băng Quan Cổ", "Hận Cổ", "Mộng Tạo Cổ", "Toàn Lực Cổ",
        "Thư Trùng", "Hùng Lực Cổ", "Bạch Trư Cổ", "Hắc Trư Cổ", "Cửu Nhãn Tửu Trùng", "Ẩn Tức Cổ", "Cốt Dực Cổ", "Huyết Nguyệt Cổ",
        "Huyết Cảm Cổ", "Huyết Bộ Cổ", "Tẩy Thủy Cổ", "Thanh Tâm Cổ", "Thanh Phong Luân Cổ", "Trừ Nhiệt Cổ", "Truy Phong Cổ",
        "Tàng Khí Cổ", "Liên Tâm Cổ", "Thông Thiên Cổ", "Nguyệt Nha Cổ", "Cá Sấu Lực Cổ", "Lôi Minh Cổ", "Thiết Cân Cổ", "Chó Nô Cổ",
        "Hạc Nô Cổ", "Lộc Nô Cổ", "Giấy Hạc Cổ", "Tâm Âm Cổ", "Hương Thảo Tam Bộ Cổ", "Hoa Nụ Cổ", "Cự Lực Cổ", "Khứu Khí Cổ",
        "Sư Tử Hống Cổ", "Phi Cốt Thuẫn Cổ"]
DAC_THU = ["Mệnh Cổ", "Hy Vọng Cổ"]
# Bảng gốc tự ghi chưa chắc cho các mục này
PHAM_UNSURE = {"Kiên Trì Cổ", "Vận Khí Cổ", "Cường Luyện Cổ", "Tử Kỳ Cổ", "Hận Cổ", "Mộng Tạo Cổ", "Liên Tâm Cổ"}
ALIAS = {"Định Vận Cổ": "gu_co_dinh_van", "Nhân Như Cố": "gu_nhan_nhu_co_co", "Sơn Như Cố": "gu_son_nhu_co_co"}  # file Excel ghi "Cổ Định Vận" (Hán tự 定运蛊)

# Đã đối chiếu nguyên tác: gu_name -> (chất lượng, rank quan sát được [min, max] hoặc None, nguồn, ghi chú)
VERIFIED = {
    "Xuân Thu Thiền": ("tiên", [6, 7], "S12 (ch.177, 1630, 1645)", "Rank 6 lúc Phương Nguyên luyện, sau nâng Rank 7; Bản Mệnh Cổ đời đầu của Phương Nguyên."),
    "Định Tiên Du": ("tiên", [6, 7], "S12 (ch.1753)", "Tiên Cổ Không Đạo; có bản Rank 7 (Phùng Cửu Ca). Chuyển số thay đổi theo bản và theo lần nâng cấp."),
    "Niên Lưu Như Thủy Cổ": ("tiên", [8, 8], "S12 (ch.1129, 1606)", "Tiên Cổ Thời Đạo Rank 8, sinh ra Niên Cổ."),
    "Nhân Như Cố": ("tiên", [6, 6], "S12 (ch.1680)", "Bản nguyên là Rank 6 (hiệu quả yếu với Cổ Tiên Rank 7-8)."),
    "Thiên Nguyên Bảo Liên Cổ": ("tiên", [6, 7], "S12 (ch.463)", "Là Tiên Cổ, có thể nâng từ Rank 6 lên Rank 7 mà vẫn giữ tên."),
    "Trí Tuệ Cổ": ("tiên", [9, 9], "S13 (Wikipedia)", "Rank 9; cũng là Cổ trong truyền thuyết Nhân Tổ (S11, ch.5)."),
    "Nguyệt Quang Cổ": ("phàm", [1, 1], "S14 (ch.8, 19, 157)", "Rank 1, đặc sản của làng Cổ Nguyệt; hay được chọn làm Bản Mệnh Cổ. Có công thức hợp luyện thành Huyết Nguyệt Cổ Rank 3."),
    "Tửu Trùng": ("phàm", [1, 1], "S14 (ch.8, 19)", "Rank 1, quý hơn Nguyệt Quang Cổ, là lựa chọn Bản Mệnh Cổ tốt cho Cổ Sư Nhất Chuyển."),
    "Bạch Trư Cổ": ("phàm", [1, 1], "S14 (ch.62, 64)", "Rank 1, hiếm, tăng sức mạnh vĩnh viễn; ăn thịt heo; có thể tiến hóa thành Bạch Ngọc Cổ Rank 2."),
    "Hắc Trư Cổ": ("phàm", [1, 1], "S14 (ch.62, 64)", "Rank 1, hiếm, tăng sức mạnh vĩnh viễn; ăn thịt heo."),
    "Bạch Ngọc Cổ": ("phàm", [2, 2], "S14 (ch.64)", "Rank 2, tiến hóa từ Bạch Trư Cổ kết hợp Ngọc Bì Cổ."),
    "Hy Vọng Cổ": ("đặc thù", None, "S11 (ch.5)", "Cổ trong truyền thuyết Nhân Tổ; ánh sáng của nó dùng trong Khai Khiếu Đại Điển. Chưa có chuyển số."),
}


def main() -> None:
    seed = json.loads((ROOT / "data/gu_worms/gu_seed.json").read_text(encoding="utf-8"))["gu"]
    by_id = {g["gu_id"]: g for g in seed}
    proposed: dict[str, str] = {}
    for label, names in (("tiên", TIEN), ("phàm", PHAM), ("đặc thù", DAC_THU)):
        for n in names:
            gid = ALIAS.get(n, f"gu_{slug(n)}")
            if gid not in by_id:
                raise SystemExit(f"Không khớp được '{n}' -> {gid}")
            if gid in proposed:
                raise SystemExit(f"Trùng: {n}")
            proposed[gid] = label
    missing = set(by_id) - set(proposed)
    if missing:
        raise SystemExit(f"Cổ chưa được phân loại: {sorted(missing)}")
    out = {}
    for gid, label in proposed.items():
        name = by_id[gid]["name"]
        key = next((n for n in VERIFIED if ALIAS.get(n, f"gu_{slug(n)}") == gid), None)
        if key:
            q, rk, src, note = VERIFIED[key]
            out[gid] = {"quality": q, "quality_status": "verified", "proposed_quality": label, "rank_observed": rk, "source": src, "note": note}
        else:
            note = "Bảng đề xuất tự ghi 'chưa xác định / cần đối chiếu'." if any(n for n in PHAM_UNSURE if ALIAS.get(n, f"gu_{slug(n)}") == gid) else None
            out[gid] = {"quality": "unknown", "quality_status": "unverified", "proposed_quality": label, "rank_observed": None, "source": None, "note": note}
    path = ROOT / "data/gu_worms/gu_classification.json"
    path.write_text(json.dumps({"_status": "quality chỉ có giá trị khi quality_status=verified; proposed_quality là đề xuất chưa xác minh", "gu": out},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {k: sum(1 for v in out.values() if v["proposed_quality"] == k) for k in ("tiên", "phàm", "đặc thù")}
    print(counts, "verified:", sum(1 for v in out.values() if v["quality_status"] == "verified"))


if __name__ == "__main__":
    main()
