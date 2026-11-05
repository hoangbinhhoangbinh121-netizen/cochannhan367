# GU_WORM_DATABASE

> File sinh tự động bởi `tools/gen_gu_doc.py` từ `data/gu_worms/gu_seed.json` (nhập từ Cotrung (1).xlsx) và `gu_gameplay.json`. Không sửa tay.

- Tổng số Cổ Trùng nhập từ file Excel: **74** (đã gộp bản trùng *Thủy Toản Cổ*).
- Dùng được trong gameplay (đã có rank, thức ăn, chu kỳ nuôi): **5**, toàn bộ là số liệu **thiết kế tạm** (`provisional`), chưa đối chiếu nguyên tác.
- Chưa dùng được (thiếu rank/thức ăn/cổ phương, chưa xác minh): **69**.

Lưu ý chất lượng dữ liệu nguồn: tên *Cổ Định Vận* có Hán tự 定运蛊 (Hán-Việt chuẩn là *Định Vận Cổ*); mục *Thư Trùng* trong file chỉ ghi "quý hiếm" nên chưa có công dụng cụ thể; một số mô tả trong file ghi rõ "theo năng lực cổ trùng" mà chưa có cơ chế.

## Dùng được trong gameplay (tạm)

| gu_id | Tên | Rank | Loại | Thức ăn | Chu kỳ (ngày TG) | Hiệu ứng cơ chế |
|---|---|---|---|---|---|---|
| `gu_tuu_trung` | Tửu Trùng | 1 | support | nguyen_thach x3 | 20 | {"refine_efficiency_bonus": 0.1} |
| `gu_nguyet_quang_co` | Nguyệt Quang Cổ | 1 | attack | nguyen_thach x2 | 12 | chưa có (chờ hệ thống chiến đấu) |
| `gu_hung_luc_co` | Hùng Lực Cổ | 1 | buff | nguyen_thach x2 | 12 | chưa có (chờ hệ thống chiến đấu) |
| `gu_bach_tru_co` | Bạch Trư Cổ | 1 | permanent_buff | nguyen_thach x2 | 16 | chưa có (chờ hệ thống chiến đấu) |
| `gu_hac_tru_co` | Hắc Trư Cổ | 1 | permanent_buff | nguyen_thach x2 | 16 | chưa có (chờ hệ thống chiến đấu) |

## Chưa dùng được (chờ nghiên cứu)

| gu_id | Tên | Hán tự | Công dụng theo file |
|---|---|---|---|
| `gu_xuan_thu_thien` | Xuân Thu Thiền | 春秋蝉 | Đưa ý thức của người sử dụng quay về một thời điểm trong quá khứ thông qua Quang Âm Trường Hà; việc kích hoạt có rủi ro lớn. |
| `gu_dinh_tien_du` | Định Tiên Du | 定仙游 | Dịch chuyển tức thời đến địa điểm đã được định vị bằng khí tức/ấn ký phù hợp. |
| `gu_tri_tue_co` | Trí Tuệ Cổ | 智慧蛊 | Phát ra ánh sáng trí tuệ, hỗ trợ suy diễn và tư duy; việc sử dụng có thể tiêu hao tuổi thọ. |
| `gu_menh_co` | Mệnh Cổ | 命蛊 | Đại diện cho sự an bài của vận mệnh; là nền tảng quyền lực quan trọng của Thiên Đình trong phần lớn cốt truyện. |
| `gu_tinh_co` | Tình Cổ | 情蛊 | Cổ trùng đặc biệt gắn với tình yêu; sức mạnh khó kiểm soát và không vận hành như cổ trùng thông thường. |
| `gu_kien_tri_co` | Kiên Trì Cổ | 坚持蛊 | Tượng trưng cho sự kiên trì; năng lực gắn với ý chí và sức bền tinh thần. |
| `gu_hy_vong_co` | Hy Vọng Cổ | 希望蛊 | Xuất hiện trong truyền thuyết Nhân Tổ, tượng trưng cho hy vọng. |
| `gu_chi_ton_tien_thai_co` | Chí Tôn Tiên Thai Cổ | 至尊仙胎蛊 | Tạo ra cơ thể Chí Tôn Tiên Thai, có khiếu huyệt đặc biệt và khả năng kiêm tu nhiều đạo. |
| `gu_nhan_nhu_co_co` | Nhân Như Cố Cổ | 人如故 | Khôi phục người hoặc sinh vật về trạng thái trước đó theo năng lực của cổ trùng. |
| `gu_son_nhu_co_co` | Sơn Như Cố Cổ | 山如故 | Khôi phục núi sông hoặc cảnh vật về trạng thái trước đó theo năng lực của cổ trùng. |
| `gu_nien_luu_nhu_thuy_co` | Niên Lưu Như Thủy Cổ | 年流如水蛊 | Sản sinh Niên Cổ; đồng thời có thể thu hút niên thú, nên tiềm ẩn rủi ro. |
| `gu_thien_nguyen_bao_lien_co` | Thiên Nguyên Bảo Liên Cổ | 天元宝莲蛊 | Sản sinh chân nguyên hoàng hạnh; là cổ trùng tiêu biểu gắn với Nguyên Liên Tiên Tôn. |
| `gu_huyet_lo_co` | Huyết Lô Cổ | 血颅蛊 | Hấp thu máu hậu duệ để tăng tư chất khiếu huyệt theo cách thức tàn nhẫn của cổ trùng. |
| `gu_doc_the_co` | Độc Thệ Cổ | 毒誓蛊 | Tạo lời thề ràng buộc; người vi phạm có thể chịu hậu quả nghiêm trọng. |
| `gu_co_dinh_van` | Cổ Định Vận | 定运蛊 | Hỗ trợ cố định vận khí trong những thủ đoạn vận đạo nhất định. |
| `gu_lien_van_co` | Liên Vận Cổ | 连运蛊 | Liên kết vận khí giữa các mục tiêu. |
| `gu_doan_van_co` | Đoạn Vận Cổ | 断运蛊 | Phá vỡ liên kết vận khí do Liên Vận Cổ tạo ra. |
| `gu_nghich_van_co` | Nghịch Vận Cổ | 逆运蛊 | Chuyển vận rủi thành vận may theo năng lực của cổ trùng. |
| `gu_van_khi_co` | Vận Khí Cổ | 运气蛊 | Quan sát hoặc tác động đến vận khí tùy loại cổ và cách sử dụng. |
| `gu_than_niem_co` | Thần Niệm Cổ | 神念蛊 | Tạo hoặc tăng cường thần niệm để dò xét, giao tiếp và xử lý thông tin. |
| `gu_cuong_luyen_co` | Cường Luyện Cổ | 强炼蛊 | Hỗ trợ luyện hóa cổ trùng của người khác; là cổ trùng quan trọng trong thủ đoạn luyện đạo. |
| `gu_quang_giap_co` | Quang Giáp Cổ | 光甲蛊 | Tạo áo giáp ánh sáng để phòng thủ. |
| `gu_thoi_cham_co` | Thời Châm Cổ | 时针蛊 | Phóng ra kim châm dùng để công kích theo thủ đoạn thời đạo. |
| `gu_dao_duc_co` | Đao Dực Cổ | 刀翼蛊 | Tạo hoặc sử dụng cánh lưỡi đao để chiến đấu. |
| `gu_tu_ky_co` | Tử Kỳ Cổ | 死期蛊 | Đặt thời điểm tử vong cho mục tiêu; khi đến hạn, mục tiêu có thể chết nếu thủ đoạn không bị phá giải. |
| `gu_thu_diep_co` | Thư Điệp Cổ | 信蝶蛊 | Dùng để truyền tin hoặc gửi thư. |
| `gu_ghi_anh_co` | Ghi Ảnh Cổ | 留影蛊 | Ghi lại hình ảnh hoặc sự việc để xem lại. |
| `gu_cot_mau_co` | Cốt Mâu Cổ | 骨矛蛊 | Tạo mâu xương để tấn công. |
| `gu_bach_ngoc_co` | Bạch Ngọc Cổ | 白玉蛊 | Cường hóa thân thể và tăng khả năng phòng ngự theo hiệu ứng bạch ngọc. |
| `gu_thien_bong_co` | Thiên Bồng Cổ | 天蓬蛊 | Tạo lớp bảo hộ quanh người dùng để giảm sát thương. |
| `gu_bang_tinh_co` | Băng Tinh Cổ | 冰晶蛊 | Tạo trạng thái hoặc sức mạnh băng tinh, tăng năng lực phòng ngự và công kích liên quan đến băng. |
| `gu_thuy_toan_co` | Thủy Toản Cổ | 水钻蛊 | Tạo mũi khoan nước để công kích hoặc xuyên phá. |
| `gu_lam_dieu_bang_quan_co` | Lam Điểu Băng Quan Cổ | 蓝鸟冰棺蛊 | Tạo chim băng xanh có thể va chạm, phát nổ và đóng băng mục tiêu. |
| `gu_han_co` | Hận Cổ | 恨蛊 | Liên quan đến hận ý; có thể nhận biết hoặc tác động theo hận ý trong những điều kiện nhất định. |
| `gu_van_nga_tien_co` | Vạn Ngã Tiên Cổ | 万我仙蛊 | Là hạt nhân của thủ đoạn Vạn Ngã, tạo ra số lượng lớn phân thân/biến thể chiến đấu. |
| `gu_mong_diep_tien_co` | Mộng Điệp Tiên Cổ | 梦蝶仙蛊 | Hỗ trợ dò xét và khám phá cảnh giới mộng. |
| `gu_mong_tao_co` | Mộng Tạo Cổ | 造梦蛊 | Liên quan đến việc tạo mộng cảnh; công dụng cụ thể phụ thuộc thủ đoạn phối hợp. |
| `gu_dao_sinh_co` | Đạo Sinh Cổ | 盗生蛊 | Đánh cắp tuổi thọ của mục tiêu theo năng lực cổ trùng. |
| `gu_toan_luc_co` | Toàn Lực Cổ |  | Phát huy hư ảnh sức mạnh mãnh thú để tăng lực công kích |
| `gu_thu_trung` | Thư Trùng |  | Cổ Trùng quý hiếm, có giá trị đặc biệt. |
| `gu_cuu_nhan_tuu_trung` | Cửu Nhãn Tửu Trùng |  | Tinh luyện chân nguyên, nâng cao phẩm chất chân nguyên. |
| `gu_an_tuc_co` | Ẩn Tức Cổ |  | Che giấu khí tức và tu vi. |
| `gu_cot_duc_co` | Cốt Dực Cổ |  | Tạo cánh xương hỗ trợ di chuyển và chiến đấu. |
| `gu_huyet_nguyet_co` | Huyết Nguyệt Cổ |  | Phóng nguyệt nhận huyết sắc để tấn công. |
| `gu_huyet_cam_co` | Huyết Cảm Cổ |  | Cảm nhận huyết mạch có liên quan. |
| `gu_huyet_bo_co` | Huyết Bộ Cổ |  | Hỗ trợ di chuyển bằng thủ đoạn thuộc huyết đạo. |
| `gu_tay_thuy_co` | Tẩy Thủy Cổ |  | Thanh tẩy những ảnh hưởng bất lợi trong khiếu. |
| `gu_thanh_tam_co` | Thanh Tâm Cổ |  | Hỗ trợ duy trì sự tỉnh táo. |
| `gu_thanh_phong_luan_co` | Thanh Phong Luân Cổ |  | Hỗ trợ di chuyển bằng sức gió. |
| `gu_tru_nhiet_co` | Trừ Nhiệt Cổ |  | Hỗ trợ loại bỏ nhiệt độc. |
| `gu_truy_phong_co` | Truy Phong Cổ |  | Tăng tốc độ di chuyển. |
| `gu_tang_khi_co` | Tàng Khí Cổ |  | Che giấu khí tức. |
| `gu_lien_tam_co` | Liên Tâm Cổ |  | Kết nối tâm trí giữa những người sử dụng. |
| `gu_thong_thien_co` | Thông Thiên Cổ |  | Kết nối với Bảo Hoàng Thiên. |
| `gu_nguyet_nha_co` | Nguyệt Nha Cổ |  | Tạo nguyệt nhận để tấn công. |
| `gu_ca_sau_luc_co` | Cá Sấu Lực Cổ |  | Gia tăng sức mạnh cá sấu. |
| `gu_loi_minh_co` | Lôi Minh Cổ |  | Tạo công kích thuộc lôi đạo. |
| `gu_thiet_can_co` | Thiết Cân Cổ |  | Cường hóa gân cốt. |
| `gu_cho_no_co` | Chó Nô Cổ |  | Nô dịch chó và các loài thú họ chó. |
| `gu_hac_no_co` | Hạc Nô Cổ |  | Nô dịch loài hạc. |
| `gu_loc_no_co` | Lộc Nô Cổ |  | Nô dịch loài hươu. |
| `gu_giay_hac_co` | Giấy Hạc Cổ |  | Dùng để truyền tải thông tin. |
| `gu_tam_am_co` | Tâm Âm Cổ |  | Truyền tải âm thanh hoặc thông tin. |
| `gu_huong_thao_tam_bo_co` | Hương Thảo Tam Bộ Cổ |  | Hỗ trợ tăng tốc độ chạy. |
| `gu_hoa_nu_co` | Hoa Nụ Cổ |  | Liên quan đến sinh trưởng thực vật. |
| `gu_cu_luc_co` | Cự Lực Cổ |  | Gia tăng sức mạnh. |
| `gu_khuu_khi_co` | Khứu Khí Cổ |  | Tạo ra khí có mùi khó chịu. |
| `gu_su_tu_hong_co` | Sư Tử Hống Cổ |  | Tạo tiếng gầm có sức công kích. |
| `gu_phi_cot_thuan_co` | Phi Cốt Thuẫn Cổ |  | Tạo khiên xương bay để phòng thủ. |
