"""Chuyển Cotrung.xlsx -> data/gu_worms/gu_seed.json.

Chỉ giữ dữ liệu CÓ trong file: tên, Hán tự, tên Anh, công dụng.
rank/path/food... KHÔNG tự bịa: để null cho tới khi nghiên cứu xong
(xem data/gu_worms/gu_gameplay.json cho phần gameplay tạm)."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent


def slug(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def parse(xlsx: Path) -> list[dict]:
    ws = load_workbook(xlsx, read_only=True).active
    cells = [str(r[0]).strip() for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    entries: list[dict] = []
    # Khối 1: hai cột "Tên (Hán)" | "Công dụng"
    for row in ws.iter_rows(min_row=2, values_only=True):
        a, b = (row + (None, None))[:2]
        if a and b and not str(a).lstrip().startswith(("*", "Công dụng")) and not re.match(r"^\d+\.", str(a)):
            m = re.match(r"^(.*?)\s*\((.*?)\)\s*$", str(a).strip())
            name, han = (m.group(1), m.group(2)) if m else (str(a).strip(), None)
            entries.append({"name": name.strip(), "han": han, "english": None, "ability": str(b).strip()})
    # Khối 2: tên ở một ô, "Công dụng: ..." ở ô kế tiếp (hoặc cùng ô, ngăn bằng xuống dòng)
    i = 0
    while i < len(cells):
        head = re.sub(r"\*", "", cells[i]).strip()
        m = re.match(r"^(\d+)\.\s*(.*?)\s*\((.*?)\)\s*$", head.split("\n")[0])
        if m:
            ability = None
            rest = head.split("\n", 1)[1] if "\n" in head else ""
            if "Công dụng:" in rest:
                ability = rest.split("Công dụng:", 1)[1].strip()
            elif i + 1 < len(cells) and cells[i + 1].startswith("Công dụng:"):
                ability = cells[i + 1].split("Công dụng:", 1)[1].strip()
                i += 1
            entries.append({"name": m.group(2).strip(), "han": None, "english": m.group(3).strip(), "ability": ability})
        i += 1
    merged: dict[str, dict] = {}
    for e in entries:
        key = slug(e["name"])
        if key in merged:  # trùng tên: gộp thông tin còn thiếu
            for k in ("han", "english"):
                merged[key][k] = merged[key][k] or e[k]
            continue
        merged[key] = e
    out = []
    for key, e in merged.items():
        out.append({"gu_id": f"gu_{key}", "name": e["name"], "name_han": e["han"], "name_en": e["english"],
                    "ability_text": e["ability"], "rank": None, "tier": "unknown", "path": None,
                    "verified": False})
    return out


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/gu_worms/source_cotrung.xlsx"
    data = parse(src)
    out = ROOT / "data/gu_worms/gu_seed.json"
    out.write_text(json.dumps({"_source": "file người dùng: Cotrung (1).xlsx",
                               "_status": "rank/path/food chưa xác minh (null)", "gu": data},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(data)} Cổ Trùng -> {out}")


if __name__ == "__main__":
    main()
