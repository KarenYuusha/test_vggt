# Kiểm chứng held-out — giả thuyết ghi trước khi chạy (2026-11-06)

Dữ liệu: mỗi cảnh 7-Scenes một chuỗi chưa dùng khi chọn cấu hình — chuỗi test thứ hai
(chess seq-05, fire seq-04, office seq-06, pumpkin seq-07, redkitchen seq-04, stairs seq-04);
heads chỉ có một chuỗi test nên dùng chuỗi train đầu tiên (seq-02). Phương pháp không train nên
chuỗi train cũng là dữ liệu chưa thấy. Mọi tham số (r, alpha=1, quy tắc chọn r) giữ nguyên như đã chốt.

Kernel: `ho-short` (N=25, 50: B1 E1-all E2-all E1-all-r2 E2-all-r2 Ref-flash),
`ho-long` (N=100, 200: B1 E1-all E2-all Ref-flash). Kaggle T4, fp16.

Giả thuyết (đúng/sai được đánh giá trên trung bình 7 chuỗi và số chuỗi thắng):

- **H1** — N ≤ 50: E2-all-r2 có AUC@30 trung bình cao hơn E2-all (r=3), và thắng ở ≥ 5/7 chuỗi.
- **H2** — N ≥ 100: E2-all (bù khối lượng) có AUC@30 trung bình cao hơn E1-all.
- **H3** — N ≥ 100: E2-all có `fid_pose` cao hơn E1-all ở ≥ 6/7 chuỗi.
- **H4** — N = 200: AUC@30 của E2-all cách B1 không quá 1.0 điểm.
- **H5** — Chamfer của mọi cấu hình nén không tệ hơn B1 quá 10%.

## Kết quả (Kaggle `ho-short`, `ho-long`; 7 chuỗi held-out)

AUC@30 trung bình 7 chuỗi (thời gian so với B1):

| N | B1 | E1-all (r=3) | E2-all (r=3, bù) | E1-all-r2 | E2-all-r2 | Ref FlashVGGT |
|---|---|---|---|---|---|---|
| 25 | 83.3 | 77.3 (1.5×) | 77.2 (1.4×) | 81.3 (1.4×) | 80.6 (1.3×) | 82.2 (1.6×) |
| 50 | 83.0 | 78.2 (2.0×) | 80.7 (1.8×) | 81.7 (1.7×) | 82.2 (1.5×) | 82.7 (2.1×) |
| 100 | 82.7 | 79.5 (2.9×) | 82.2 (2.5×) | — | — | 82.5 (3.3×) |
| 200 | 82.3 | 79.9 (4.4×) | 79.8 (3.5×) | — | — | 82.5 (5.4×) |

| Giả thuyết | Kết quả |
|---|---|
| H1 — r=2 > r=3 khi N ≤ 50 | N=25: **đúng** (80.6 vs 77.2, 6/7). N=50: trung bình đúng (82.2 vs 80.7) nhưng chỉ 4/7 chuỗi → **đúng một phần** |
| H2 — E2 > E1 về AUC khi N ≥ 100 | N=100: **đúng** (82.2 vs 79.5, 5/7). N=200: **sai** (79.8 vs 79.9, 4/7) |
| H3 — E2 > E1 về `fid_pose` ở ≥ 6/7 chuỗi | **đúng** ở cả N=100 (6/7) và N=200 (6/7) |
| H4 — E2 cách B1 ≤ 1.0 ở N=200 | **sai** (79.8 vs 82.3) |
| H5 — Chamfer nén ≤ B1 + 10% | E1: đúng mọi N. E2: **sai** ở N=25 (0.064 vs 0.042) và N=200 (0.047 vs 0.041) |

Nguyên nhân chung của các giả thuyết sai: chuỗi **office seq-06**. Mọi cấu hình không train đều kém trên chuỗi này, còn bù
khối lượng thì dao động không đơn điệu theo N: AUC 44.0 (N=25) → 60.2 (50) → 71.3 (100) → 56.4 (200), so với B1 ~73.
FlashVGGT đã fine-tune giữ ổn định (72.5–75.2). Bỏ office ra (chỉ để chẩn đoán, không phải kết quả báo cáo), ở N=200
E2 đạt 83.7, so với B1 83.9 và E1 82.5.
