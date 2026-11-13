# TUM RGB-D — bộ dữ liệu thứ hai, giả thuyết ghi trước khi chạy (2026-11-08)

## Dữ liệu

6 chuỗi TUM RGB-D, được chuyển sang bố cục 7-Scenes bằng `src/tfvggt/datasets/tum.py`. Mỗi ảnh RGB được ghép với depth và
pose gần nhất (lệch ≤ 20 ms). Tiêu cự lấy theo camera Freiburg, không khử méo.

| Chuỗi | Số frame | Đặc điểm |
|---|---|---|
| fr1_desk | 596 | |
| fr1_room | 1362 | |
| fr1_360 | 756 | Camera quay 360° |
| fr3_long_office | 2486 | Đi vòng |
| fr3_walking_xyz | 826 | Có người di chuyển |
| fr3_str_tex_far | 904 | |

**Đã nhìn trước khi ghi giả thuyết** (chạy trên máy, N=50, để kiểm tra phần chuyển đổi):

| Chuỗi | B1 | AV-s4 | AVE-s4e36 |
|---|---|---|---|
| fr1_desk | 93.2 | 92.3 | 92.6 |
| fr1_360 | 60.2 | 49.0 | 47.1 |

Trên fr1_360, cả hai phương pháp không train đều tụt mạnh (−11 và −13). Vì đã nhìn thấy, kết quả trên chuỗi này được báo
cáo riêng và không tính là kiểm chứng sạch.

## Kernel (Kaggle T4, forward ít bộ nhớ, trừ K-r2k10 tự dùng forward chuẩn)

| Cấu hình | N |
|---|---|
| B1, K-r2k10 | 50, 100, 200 |
| AV-s4, AVE-s4e36, AVEK-s4e36k10 | 50, 100, 200, 400 |

## Giả thuyết

| | Giả thuyết |
|---|---|
| H26 | AVE-s4e36 có AUC@30 trung bình ≥ AV-s4 trên 6 chuỗi, ở mọi N. Đây là lần lặp lại kết quả chính trên bộ dữ liệu khác. |
| H27 | AVE-s4e36 cách B1 không quá 1.0 AUC@30 trung bình trên 6 chuỗi, ở N=100 và N=200. |
| H28 | Trên 5 chuỗi khác fr1_360, AVE-s4e36 cách B1 không quá 2.0 AUC@30 trên từng chuỗi, ở N=100 và N=200. |
| H29 | Thăm dò, trên fr1_360 (đã nhìn): các cấu hình có keyframe (AVEK-s4e36k10, K-r2k10) tụt so với B1 ít hơn AVE-s4e36, ở N=100 và N=200. |

## Kết quả (Kaggle T4; bảng đầy đủ trong `results/aggregate_tum.md`)

AUC@30 trung bình trên 6 chuỗi (thời gian trung bình trong ngoặc):

| N | B1 | K-r2k10 | AV-s4 | AVE-s4e36 | AVEK-s4e36k10 |
|---|---|---|---|---|---|
| 50 | 86.7 (41 s) | 82.9 | 82.3 (22 s) | 83.0 (24 s) | **84.1** (25 s) |
| 100 | 87.4 (128 s) | 84.9 (63 s) | 84.0 (52 s) | 83.9 (55 s) | **85.6** (62 s) |
| 200 | 86.4 (454 s) | 84.6 (192 s) | 83.6 (133 s) | 84.2 (141 s) | **85.1** (170 s) |
| 400 | — | — | 83.5 (387 s) | 83.5 (414 s) | **84.4** (537 s) |

| Giả thuyết | Kết quả |
|---|---|
| H26 — AVE ≥ AV-s4 ở mọi N | **Sai.** Lệch trung bình +0.67 / −0.03 / +0.69 / −0.01, nhưng AVE chỉ thắng 2/6 chuỗi ở mỗi N. Mức dương đến từ riêng fr1_room. Kết quả chính của 7-Scenes không lặp lại trên TUM. |
| H27 — AVE cách B1 ≤ 1.0 ở N=100, 200 | **Sai:** −3.46 và −2.11. AV-s4 cũng tụt tương tự (−3.4 và −2.8). |
| H28 — AVE trong 2 điểm trên từng chuỗi khác fr1_360 | **Sai** ở N=100 (fr1_room −6.0); đúng ở N=200. |
| H29 — keyframe giảm mức tụt trên fr1_360 | **Đúng** (thăm dò): ở N=100, AVEK −5.7, K-r2k10 −7.3, AVE −9.3; ở N=200, AVEK −3.9, K-r2k10 −5.4, AVE −7.1. |

Phân tích sau khi xem kết quả (không phải giả thuyết ghi trước):

- **AVEK-s4e36k10 thắng AV-s4 trên 23/24 cặp (chuỗi, N)**, hơn +1.79 / +1.60 / +1.54 / +0.90.
  - Nó cũng tốt hơn K-r2k10 về AUC (85.6 so với 84.9 ở N=100; 85.1 so với 84.6 ở N=200) và nhanh hơn ở N=200 (170 s
    so với 192 s).
  - Trên 11 chuỗi 7-Scenes mới (`results/fresh_plan.md`), AVEK thắng AV-s4 trên 28/33 cặp. Gộp lại là 51/57 cặp, trên
    17 chuỗi chưa từng dùng để chọn cấu hình.
  - Riêng fr1_360 có 3 cấu hình đã được nhìn ở N=50 trước khi ghi giả thuyết, nhưng AVEK thì chưa.
- **TUM khó hơn hẳn 7-Scenes với mọi cách nén K/V không train.** Mức tụt tập trung ở fr1_360 (camera quay 360°) và
  fr1_room (quay nhanh, cầm tay). Keyframe đủ độ phân giải là thứ duy nhất giảm được mức tụt này, nhưng vẫn cách B1 1.3–3
  điểm.
- **Đánh đổi:** AVEK chậm hơn AVGGT khoảng 20–40%. Ở N=200, nó nhanh hơn VGGT 2.7× (TUM) và 2.9× (7-Scenes), so với
  3.4–3.8× của AVGGT.
