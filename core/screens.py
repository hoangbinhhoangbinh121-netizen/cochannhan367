"""Mọi màn hình của game dưới dạng ảnh pixel. Hàm thuần: nhận dữ liệu service, trả về ảnh PIL.
Các cog chỉ việc gửi ảnh (core.ui.reply)."""
from __future__ import annotations

from PIL import Image, ImageDraw

from core import pixel
from core.fmt import thanh
from core.pixel import RANK_COLORS
from core.pixel_ui import BAD, GOOD, WARN, Bar, Columns, Gap, KV, Media, Notice, Picture, Rule, Text, render
from core.pixel import INK, MUTED

ACC = {"character": (142, 107, 191), "cultivation": (47, 158, 143), "gu": (201, 162, 39),
       "world": (74, 127, 181), "admin": (122, 122, 122), "error": (181, 72, 59)}
GOLD = (232, 200, 90)
QUALITY = {"tiên": "Tiên Cổ", "phàm": "Phàm Cổ", "đặc thù": "Cổ đặc thù"}
STATE_VI = {"fed": "no đủ", "hungry": "đang đói", "starving": "sắp chết đói", "dead": "đã chết đói"}
STATE_COLOR = {"fed": GOOD, "hungry": WARN, "starving": BAD, "dead": BAD}


def _banner(name: str, h: int = 120):
    p = pixel.banner_path(name)
    return [Picture(p, crop_h=h)] if p else []


# ---------- chung ----------
def message(title: str, text: str, accent=None, icon: str | None = None) -> Image.Image:
    return render(title, [Text(text, 16)], accent or ACC["character"], icon)


def error(text: str) -> Image.Image:
    return render("Không thể thực hiện", [Text(text, 16)], ACC["error"], "broken")


# ---------- nhân vật / Khai Khiếu ----------
def khaikhieu_confirm(name: str) -> Image.Image:
    return render("Lễ Khai Khiếu", _banner("character", 110) + [
        KV([("Tên", name)]), Gap(4),
        Text("Hy Vọng Cổ sẽ quyết định số bước bạn đi được, và số bước quyết định tư chất. "
             "Tư chất không thể chọn hay làm lại. Nếu tử vong, bạn mới được bắt đầu một đời mới.", 15),
        Notice("Xác nhận khai khiếu?", WARN)], ACC["character"], "star")


def ceremony_frame(idx: int, name: str, k: int | None) -> Image.Image:
    blocks = [Picture(pixel.ceremony_path(str(idx)))]
    if k is None:
        blocks.append(Text(f"{name} bước vào biển hoa. Từng điểm sáng Hy Vọng Cổ bay ra, nhập vào cơ thể và tụ lại ở bụng dưới...", 15))
    else:
        blocks.append(Bar(f"Bước thứ {k}", k, 50, ACC["character"], f"{k}/50"))
    return render("Khai Khiếu Đại Điển", blocks, ACC["character"], "star")


def ceremony_success(v: dict) -> Image.Image:
    c = v["ceremony"]
    return render(f"{v['name']} đã khai khiếu", [
        Picture(pixel.ceremony_path("success")),
        Text(f"Đi được {c['steps']} bước. Hy Vọng Cổ bùng nổ, Không Khiếu hình thành, Nguyên Hải xuất hiện.", 15),
        KV([("Tư chất", f"{v['grade']} ({thanh(v['ratio'])})", GOLD), ("Cảnh giới", v["realm"]),
            ("Nguyên Hải", f"sắc {v['essence_color']}, sức chứa {v['capacity']:.0f}")]),
        Notice("Bạn là Nhất Chuyển Cổ Sư. Hãy dùng /ban-menh-co để chọn Bản Mệnh Cổ.", GOOD)], ACC["character"], "star")


def ceremony_fail(steps: int) -> Image.Image:
    return render("Khai khiếu không thành", [
        Picture(pixel.ceremony_path("fail")),
        Text(f"Bạn chỉ đi được {steps} bước, ánh sáng Hy Vọng Cổ tan đi mà không đủ để mở Không Khiếu. Bạn không có tư chất tu luyện. "
             "Phải chờ một thời gian mới được dự Đại Điển lần nữa.", 15)], ACC["error"], "broken")


def profile(v: dict) -> Image.Image:
    card = pixel.profile_card(v)
    notes = [Notice(n, ACC["cultivation"]) for n in v.get("notices", [])] if v.get("notices") else []
    if not notes:
        return card
    h = sum(n.measure(672) for n in notes) + 16
    img = Image.new("RGBA", (card.width, card.height + h), pixel.BG)
    img.alpha_composite(card, (0, 0))
    d, y = ImageDraw.Draw(img), card.height + 4
    for n in notes:
        n.draw(img, d, 24, y, 672)
        y += n.measure(672)
    return img


# ---------- tu luyện ----------
def tuvi(v: dict, pv: dict) -> Image.Image:
    acc = RANK_COLORS[v["rank"]]
    blocks = _banner("cultivation", 110) + [
        KV([("Cảnh giới", v["realm"], GOLD), ("Nguyên Hải", f"sắc {v['essence_color']}")]), Gap(4),
        Bar("Chân nguyên", v["essence"], v["capacity"], acc, f"{v['essence']:.0f}/{v['capacity']:.0f}"),
        Text(f"Hồi {v['regen_per_day']:.1f} chân nguyên mỗi ngày thế giới.", 13, MUTED), Gap(4),
        Bar("Căn cơ", v["foundation"], 100, (224, 184, 64), f"{v['foundation']:.0f}/100"), Rule()]
    if pv["kind"] in ("ascension", "immortal"):
        blocks.append(Notice("\n".join(pv["blockers"]), ACC["cultivation"]))
    else:
        what = "lên chuyển mới" if pv["kind"] == "rank" else "lên tiểu cảnh giới kế tiếp"
        blocks.append(Text(f"Đột phá ({what})", 16, GOLD, True))
        blocks.append(KV([("Chân nguyên tối thiểu", f"{pv['min_essence']}"), ("Tiêu hao", f"{pv['cost']}"),
                          ("Tỉ lệ thành công", f"{pv['chance'] * 100:.0f}%", GOOD if pv["chance"] >= 0.5 else WARN)]))
    return render(f"Tu vi của {v['name']}", blocks, ACC["cultivation"], "ring")


def refine_result(r: dict) -> Image.Image:
    blocks = [KV([("Nguyên Thạch đã dùng", str(r["stones_used"])), ("Chân nguyên thu được", f"{r['essence_gained']:.1f}", GOOD)]), Gap(6),
              Bar("Chân nguyên", r["essence"], r["capacity"], ACC["cultivation"], f"{r['essence']:.0f}/{r['capacity']:.0f}")]
    if r["bonus"]:
        blocks.append(Notice(f"Cổ Trùng hỗ trợ: hiệu suất +{r['bonus'] * 100:.0f}%", GOOD))
    return render("Luyện hóa Nguyên Thạch", blocks, ACC["cultivation"], "stone")


def breakthrough_confirm(pv: dict) -> Image.Image:
    return render(f"Đột phá từ {pv['realm']}", [
        KV([("Chân nguyên hiện có", f"{pv['essence']:.1f}"), ("Tối thiểu cần", f"{pv['min_essence']}"), ("Tiêu hao", f"{pv['cost']}"),
            ("Tỉ lệ thành công", f"{pv['chance'] * 100:.0f}%", GOOD if pv["chance"] >= 0.5 else WARN)]), Gap(4),
        Notice("Thất bại làm hao tổn căn cơ và mất chân nguyên đã tiêu. Xác nhận?", WARN)], ACC["cultivation"], "flame")


def breakthrough_result(r: dict) -> Image.Image:
    if r["success"]:
        return render("Đột phá thành công", [Text(f"Cảnh giới mới: {r['realm']}", 20, GOOD, True),
                                              Text(f"Tỉ lệ lúc đột phá: {r['chance'] * 100:.0f}%", 14, MUTED)], ACC["cultivation"], "star")
    return render("Đột phá thất bại", [Text(f"Căn cơ tổn hại {r['foundation_loss']} điểm.", 18, BAD, True),
                                       Text("Hãy tích lũy lại chân nguyên trước khi thử lần nữa.", 15)], ACC["error"], "broken")


def ascension_preview(pv: dict) -> Image.Image:
    q = pv["qi"]
    blocks = [Bar("Nhân khí", pv["human"]["total"], 100, ACC["cultivation"], f"{pv['human']['total']:.0f}/100")]
    blocks.append(KV([(k, f"{v:.1f}") for k, v in pv["human"]["parts"].items()], 14))
    blocks += [Text(f"Tiên khiếu dự kiến: {pv['tier']}", 16, GOLD, True), Rule(),
               Text(f"Nơi thăng tiên: {pv['region_name']}", 16, INK, True),
               KV([("Thiên khí", f"{q['heaven']:.1f}"), ("Địa khí", f"{q['earth']:.1f}"), ("Cân bằng", f"{pv['balance'] * 100:.0f}%"),
                   ("Mức bị dòm ngó", f"{q['watch']}/3"),
                   ("Tỉ lệ thành công", f"{pv['chance'] * 100:.0f}% (còn dao động theo thiên tượng)", GOOD if pv["chance"] >= 0.5 else WARN)])]
    if pv["blockers"]:
        blocks.append(Notice("\n".join(pv["blockers"]), BAD))
    else:
        blocks.append(Notice(f"Kéo dài khoảng {pv['gather_minutes']:.0f} phút (giờ thật), bạn không thể làm gì khác. Toàn bộ chân nguyên dồn vào phá khiếu. "
                             "Thất bại làm tổn hại căn cơ, thất bại nặng có thể làm Không Khiếu vỡ nát và tử vong. Bạn chắc chắn?", WARN))
    return render("Thăng Tiên", blocks, RANK_COLORS[6], "star")


def ascension_state(st: dict) -> Image.Image:
    notes = [Notice(n, ACC["cultivation"]) for n in st["notices"]]
    if st["state"] == "immortal":
        i = st["immortal"]
        return render("Cổ Tiên", notes + [KV([("Tiên khiếu", i["tier"], GOLD), ("Nhân khí lúc thăng tiên", f"{i['human_qi']:.0f}/100"),
                                              ("Thiên khí / Địa khí", f"{i['heaven_qi']:.2f} / {i['earth_qi']:.2f}"), ("Cân bằng", f"{i['balance'] * 100:.0f}%")]),
                                          Notice("Hệ thống Tiên Nguyên, Đạo Ngân, Thiên Kiếp và Địa Tai chưa được triển khai.", WARN)], RANK_COLORS[6], "star")
    return render("Đang thăng tiên", [Text("Thiên khí, Địa khí và Nhân khí đang hội tụ.", 16),
                                      KV([("Còn khoảng", f"{st['minutes_left']:.0f} phút (giờ thật)")]),
                                      Notice("Trong lúc này bạn không thể làm việc khác. Quay lại dùng /thang-tien để xem kết quả.", WARN)], RANK_COLORS[6], "star")


def ascension_started(info: dict) -> Image.Image:
    return render("Thăng tiên bắt đầu", [Text("Trời đất rung chuyển, Thiên khí và Địa khí đổ về.", 16),
                                         KV([("Kết quả sau khoảng", f"{info['minutes']:.0f} phút (giờ thật)")]),
                                         Notice("Dùng /thang-tien để xem kết quả.", GOOD)], RANK_COLORS[6], "star")


# ---------- Cổ Trùng ----------
def gu_detail(g: dict) -> Image.Image:
    alias = " | ".join(x for x in (g.get("name_en"),) if x)
    if g["quality_status"] == "verified":
        rk = g.get("rank_observed")
        extra = f", chuyển {rk[0]}" + (f"-{rk[1]}" if rk[1] != rk[0] else "") if rk else ""
        cls = f"{QUALITY[g['quality']]}{extra} (đã đối chiếu)"
    else:
        cls = f"Chưa xác minh (đề xuất: {QUALITY[g['proposed_quality']]})"
    rows = [("Phân loại", cls)]
    if g.get("rank") is not None:
        rows += [("Cấp (tạm)", f"{g['rank']} chuyển"), ("Nuôi dưỡng", f"{g['food'].replace('_', ' ')}, chu kỳ {g['feeding_cycle_days']} ngày thế giới")]
    side = [Text(g["name"], 20, GOLD, True)] + ([Text(alias, 13, MUTED)] if alias else []) + [Gap(4), KV(rows, 14)]
    blocks = [Media(pixel.sprite_path(g["gu_id"]), side, 128), Gap(6), Text(g["ability_text"], 15)]
    if g.get("rank") is None:
        blocks.append(Notice("Chưa xác minh cấp bậc, thức ăn và cổ phương theo nguyên tác nên chưa dùng được trong game.", WARN))
    return render(f"Cổ Trùng: {g['name']}", blocks, ACC["gu"], "bone")


def gu_list(found: list[dict]) -> Image.Image:
    names = [g["name"] for g in found[:24]]
    half = (len(names) + 1) // 2
    left, right = [Text(n, 15) for n in names[:half]], [Text(n, 15) for n in names[half:]]
    return render(f"{len(found)} kết quả", [Columns(left, right)] + ([Text("(chỉ hiện 24 kết quả đầu, hãy gõ cụ thể hơn)", 13, MUTED)] if len(found) > 24 else []),
                  ACC["gu"], "bone")


def gu_inventory(inv: dict) -> Image.Image:
    return pixel.gu_grid(inv["items"], inv["slots"], inv["refined"])


def vital_confirm(gd: dict) -> Image.Image:
    side = [Text(gd["name"], 20, GOLD, True), Gap(4), KV([("Cấp (tạm)", f"{gd['rank']} chuyển")], 14)]
    return render("Chọn Bản Mệnh Cổ?", [Media(pixel.sprite_path(gd["gu_id"]), side, 128), Gap(6), Text(gd["ability_text"], 15),
        Notice("Bản Mệnh Cổ gắn với sinh mệnh bạn: luyện hóa thất bại không làm nó chết và nó không chết đói. Chỉ được chọn một lần, không đổi được. Xác nhận?", WARN)],
        ACC["gu"], "heart")


def vital_done(r: dict, gd: dict) -> Image.Image:
    side = [Text(r["name"], 20, GOLD, True), Text("trở thành Bản Mệnh Cổ của bạn", 14, MUTED), Gap(4), KV([("Mã", r["instance_id"])], 14)]
    return render("Bản Mệnh Cổ đã định", [Media(pixel.sprite_path(gd["gu_id"]), side, 128),
                  Notice("Dùng /luyen-co để luyện hóa nó và /nuoi-co để nuôi.", GOOD)], ACC["gu"], "heart")


def gu_refine(r: dict, gu_id: str) -> Image.Image:
    sp = pixel.sprite_path(gu_id)
    if r["success"]:
        side = [Text(r["name"], 20, GOLD, True), Text("đã nhập vào Không Khiếu", 14, GOOD, True), Gap(4),
                KV([("Tỉ lệ", f"{r['chance'] * 100:.0f}%"), ("Tiêu hao", f"{r['cost']:.1f} chân nguyên")], 14)]
        return render("Luyện hóa thành công", [Media(sp, side, 128)], ACC["gu"], "flame")
    tail = "Cổ Trùng đã chết trong quá trình luyện hóa." if r["died"] else "Cổ Trùng còn sống, có thể thử lại."
    side = [Text(r["name"], 20, GOLD, True), Text(tail, 14, BAD, True), Gap(4), KV([("Mất", f"{r['cost']:.1f} chân nguyên")], 14)]
    return render("Luyện hóa thất bại", [Media(sp, side, 128, border=BAD)], ACC["error"], "broken")


def gu_feed(r: dict, gu_id: str) -> Image.Image:
    sp = pixel.sprite_path(gu_id)
    if r["dead"]:
        return render("Cổ đã chết đói", [Media(sp, [Text(r["name"], 20, GOLD, True), Text("đã chết đói và được dọn khỏi kho.", 14, BAD, True)], 128, border=BAD)], ACC["error"], "skull")
    side = [Text(r["name"], 20, GOLD, True), Gap(4), KV([("Thức ăn", f"{r['cost']} {r['food'].replace('_', ' ')}"), ("Sinh lực", f"{r['vitality']}/100", GOOD)], 14)]
    return render("Đã cho ăn", [Media(sp, side, 128)], ACC["gu"], "cup")


# ---------- thế giới ----------
def world_status(s: dict) -> Image.Image:
    rows = []
    for r in s["regions"].values():
        rows.append(Text(r["name"], 16, GOLD, True))
        rows.append(Text(f"Thời tiết: {r['weather']}", 13, MUTED, False, 2))
        rows.append(Bar("Mạch Nguyên Thạch", r["stone_ratio"], 1.0, ACC["world"], f"{r['stone_ratio'] * 100:.0f}%", 10))
    return render("Cổ Chân Nhân", _banner("world", 120) + [Text(s["date"], 16, INK, True), Gap(6)] + rows, ACC["world"], "moon")


def gather(r: dict) -> Image.Image:
    if r["got"] == 0:
        return render("Khai thác", [Notice(f"Mạch Nguyên Thạch tại {r['region']} đã cạn, chờ mỏ hồi lại.", BAD)], ACC["error"], "stone")
    return render("Khai thác Nguyên Thạch", [KV([("Vùng", r["region"]), ("Nhận được", f"{r['got']} Nguyên Thạch", GOOD), ("Mức yêu cầu", str(r["requested"]))]), Gap(6),
                  Bar("Trữ lượng mạch mỏ", r["reserve_ratio"], 1.0, ACC["world"], f"{r['reserve_ratio'] * 100:.0f}%")], ACC["world"], "stone")


def map_screen(map_img: Image.Image, text: str, notices: list[str]) -> Image.Image:
    return render("Bản đồ", [Picture(map_img)] + [Text(text, 15)] + [Notice(n, ACC["world"]) for n in notices], ACC["world"], "mountain")


def travel_confirm(names: str, minutes: float, danger: int, chance: float, dest_name: str) -> Image.Image:
    return render(f"Hành trình tới {dest_name}", [KV([("Lộ trình", names), ("Thời gian", f"khoảng {minutes:.0f} phút (giờ thật)"),
                                                     ("Nguy hiểm tối đa", f"{danger}/5"), ("Nguy cơ phục kích", f"{chance * 100:.0f}%", WARN)]), Gap(4),
                  Notice("Phục kích làm mất một phần Nguyên Thạch. Trên đường bạn không thể khai thác. Xác nhận?", WARN)], ACC["world"], "chain")


def travel_started(dest_name: str, minutes: float) -> Image.Image:
    return render("Lên đường", [Text(f"Bạn lên đường tới {dest_name}.", 16), KV([("Dự kiến đến sau", f"khoảng {minutes:.0f} phút (giờ thật)")])], ACC["world"], "chain")


# ---------- chợ và giao dịch ----------
def market_listing(items: list[dict], stones: int | None) -> Image.Image:
    blocks = []
    if stones is not None:
        blocks += [KV([("Nguyên Thạch của bạn", str(stones), GOLD)]), Gap(4)]
    for it in items:
        gd_sprite = pixel.sprite_path(it["gu_id"])
        side = [Text(it["name"], 17, GOLD, True),
                KV([("Giá mua", f"{it['price']} Nguyên Thạch"), ("Tồn kho", f"{it['stock']}/{it['max_stock']}", GOOD if it["stock"] else BAD),
                    ("Chợ thu mua", f"{it['sell_price']} Nguyên Thạch")], 13)]
        blocks += [Media(gd_sprite, side, 64), Gap(4)]
    blocks.append(Notice("Giá thay đổi theo cung cầu: mua nhiều thì tăng, hàng tồn và nhu cầu hồi dần theo thời gian. Dùng /muaban mua và /muaban ban.", ACC["world"]))
    return render("Chợ Cổ Trùng", blocks, ACC["gu"], "cup")


def market_buy(r: dict) -> Image.Image:
    side = [Text(r["name"], 20, GOLD, True), Gap(4), KV([("Đã trả", f"{r['price']} Nguyên Thạch"), ("Còn lại", f"{r['stones_left']} Nguyên Thạch"), ("Mã", r["instance_id"])], 14)]
    return render("Đã mua Cổ Trùng", [Media(pixel.sprite_path(r["gu_id"]), side, 128),
                  Notice("Dùng /luyen-co để luyện hóa và /nuoi-co để nuôi.", GOOD)], ACC["gu"], "cup")


def market_sell(r: dict) -> Image.Image:
    side = [Text(r["name"], 20, GOLD, True), Gap(4), KV([("Chợ trả", f"{r['price']} Nguyên Thạch", GOOD), ("Hiện có", f"{r['stones_left']} Nguyên Thạch")], 14)]
    return render("Đã bán Cổ Trùng", [Media(pixel.sprite_path(r["gu_id"]), side, 128)], ACC["gu"], "cup")


def trade_offer(seller: str, buyer: str, gd: dict, price: int, fee: int) -> Image.Image:
    side = [Text(gd["name"], 20, GOLD, True), Gap(4),
            KV([("Người bán", seller), ("Người mua", buyer), ("Giá", f"{price} Nguyên Thạch", GOLD),
                ("Phí giao dịch", f"{fee} (bị hủy, người bán nhận {price - fee})")], 14)]
    return render("Đề nghị giao dịch", [Media(pixel.sprite_path(gd["gu_id"]), side, 128),
                  Notice(f"{buyer} bấm Đồng ý để hoàn tất. Đề nghị hết hạn sau 2 phút.", WARN)], ACC["gu"], "chain")


def trade_done(r: dict, seller: str, buyer: str) -> Image.Image:
    side = [Text(r["name"], 20, GOLD, True), Gap(4), KV([("Người bán", f"{seller} (nhận {r['seller_gets']})"), ("Người mua", f"{buyer} (trả {r['price']})"), ("Phí đã hủy", str(r["fee"]))], 14)]
    return render("Giao dịch hoàn tất", [Media(pixel.sprite_path(r["gu_id"]), side, 128)], ACC["gu"], "chain")
