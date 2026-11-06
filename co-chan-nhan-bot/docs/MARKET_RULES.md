# MARKET_RULES (Chợ và giao dịch, hệ thống 05 và 09 mức cơ bản)

Nhãn: **canon** = có nguồn nguyên tác; **design** = thiết kế tạm. Nguyên Thạch là tiền tệ của Cổ Sư (canon); mọi con số giá, hàng tồn, phí là design (`data/config/market.json`).

## Chợ NPC (`/muaban xem | mua | ban`)
- Hiện bán 5 Cổ Trùng có dữ liệu gameplay (Nguyệt Quang, Tửu Trùng, Hùng Lực, Bạch Trư, Hắc Trư). Cổ chưa xác minh rank/nuôi dưỡng thì không có trong chợ.
- **Hàng tồn hữu hạn**: mỗi Cổ có tồn kho tối đa, hồi chậm theo thời gian thế giới (tính lười, người chơi ngoại tuyến không làm chợ dừng). Hết hàng là không mua được.
- **Giá theo cung cầu**: `giá = giá gốc × clamp(√((nhu cầu + 3) / tồn kho), 0.5, 3)`. Mua làm tồn giảm và nhu cầu tăng nên giá tăng; nhu cầu nguội dần (nửa đời 10 ngày thế giới).
- **Thu mua**: chợ chỉ trả 50% giá mua hiện tại và chỉ nhận Cổ chưa luyện hóa, không phải Bản Mệnh Cổ; mỗi loại có trần tồn kho (gấp đôi tối đa). Mua rồi bán ngay luôn lỗ (có test), nên không kiếm Nguyên Thạch vô hạn bằng mua đi bán lại.

## Giao dịch trực tiếp (`/giaodich`)
- Người bán chọn người mua, Cổ và giá; bot gửi đề nghị kèm nút **Đồng ý** (chỉ người mua bấm được) và **Hủy**, hết hạn sau 2 phút.
- Khi đồng ý, một giao dịch nguyên tử khóa cả hai người và Cổ: kiểm tra lại toàn bộ điều kiện rồi mới chuyển. Hai người cùng đồng ý trên một Cổ, hoặc hai người mua tranh món cuối, chỉ một người thành công (có test chạy đồng thời); Cổ không thể bị nhân bản hoặc mất.
- Phí 5% bị hủy (sink) khỏi người bán, nên mỗi lần giao dịch làm giảm tổng Nguyên Thạch.
- Không giao dịch được: Bản Mệnh Cổ, Cổ đã luyện hóa, khi người bán hoặc người mua đang thăng tiên; người mua giữ tối đa 20 Cổ.

## Chưa có
Đấu giá (`/daugia`), thương đội và giá theo vùng, thu mua theo đơn đặt hàng, giao dịch bí mật, chợ Nguyên Thạch/tài nguyên khác, chợ cho Cổ chưa có dữ liệu gameplay.
