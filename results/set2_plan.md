# Bộ thứ ba (set 2) — giả thuyết ghi trước khi chạy (2026-11-06)

## Bối cảnh

Trên bộ held-out, chuỗi office seq-06 làm hỏng các cấu hình không train. Chẩn đoán cục bộ bằng
`analysis/diag_office.py` (kết quả trong `results/diag/`) cho thấy:

- **Lỗi không do `dedup`.** E1 ≈ E1d và E2n ≈ E2.
- **Lỗi nằm ở các frame quay 105–151° so với frame 0.** Frame 0 là keyframe duy nhất giữ đủ độ phân giải, và các
  frame này không có vùng nhìn chung với nó.
- **Bù khối lượng có rủi ro đuôi.** Trên office ở N=25, nó gây sụp kể cả khi r=2 (góc lệch tối đa 124°). Trên chess
  thì nó lại tốt nhất.
- **Thêm keyframe đủ độ phân giải bằng k-means sửa được lỗi phủ.** FlashVGGT có sẵn cơ chế này, không cần train:
  chia các frame thành S // 10 cụm theo token DINO trung bình, và lấy thêm frame 0.

Cấu hình mới **K-r2k10** (r=2, keyframe mỗi 10 frame, không bù) được chọn sau khi xem office seq-06 và chess seq-05
của bộ held-out. Vì thế nó cần được kiểm chứng trên dữ liệu chưa thấy. Cấu hình **K-r3k10** là bản rẻ hơn.

## Dữ liệu

Set 2 là chuỗi thứ ba của mỗi cảnh theo thứ tự test rồi train, chưa dùng ở bất kỳ bước nào trước đây. Heads không
còn chuỗi nào nên chỉ có 6 chuỗi.

## Kernel

Cấu hình chạy: B1, E1-all, E1-all-r2, E2-all, E2-all-r2, K-r2k10, K-r3k10, Ref-flash. Số frame N = 25, 50, 100, 200.
Chạy trên Kaggle T4, fp16.

## Giả thuyết

Đánh giá trên trung bình 6 chuỗi, ở từng N:

| | Giả thuyết |
|---|---|
| H6 | K-r2k10 có AUC@30 ≥ E1-all-r2. Keyframe không làm hại. |
| H7 | K-r3k10 có AUC@30 > E1-all. |
| H8 | Mức tụt AUC tệ nhất so với B1, trên một chuỗi, của K-r2k10 nhỏ hơn của E2-all và E2-all-r2. Tức là ổn định hơn bù khối lượng. |
| H9 | K-r2k10 cách B1 không quá 1.5 điểm AUC@30 ở mọi N. |
| H10 | Chamfer của K-r2k10 không tệ hơn B1 quá 10%. |

## Kết quả set 2 (6 chuỗi: chess seq-01, fire seq-01, office seq-07, pumpkin seq-02, redkitchen seq-06, stairs seq-02)

N=25/50/100 chạy trên máy (RTX 4060, bf16). N=200 và Ref-flash chạy trên Kaggle T4 (fp16), trên các tài khoản tvtrong,
phngkhai và hpthai. Hai môi trường cho B1 lệch nhau ≤ 0.3 AUC trên cả 18 cặp chuỗi×N, nên độ chính xác so sánh được với
nhau. Thời gian trên máy bị nhiễu do một job khác dùng chung GPU, nên chỉ thời gian N=200 trên T4 là dùng được.

AUC@30 trung bình 6 chuỗi:

| N | B1 | E1-all | E1-all-r2 | E2-all | E2-all-r2 | K-r2k10 | K-r3k10 | Ref FlashVGGT |
|---|---|---|---|---|---|---|---|---|
| 25 | 80.6 | 77.0 | 79.5 | 75.1 | 80.4 | 79.8 | 78.4 | 80.9 |
| 50 | 79.8 | 77.2 | 78.9 | 79.8 | 79.7 | 79.2 | 78.2 | 80.7 |
| 100 | 79.5 | 77.5 | 78.9 | 79.5 | 79.4 | 79.1 | 78.4 | 80.6 |
| 200 | 78.8 | 77.2 | 78.6 | 78.6 | 78.7 | 78.8 | 78.4 | 80.5 |

Thời gian ở N=200 trên T4:

| Cấu hình | Thời gian | So với B1 |
|---|---|---|
| B1 | 456 s | 1× |
| E1-all | 103 s | 4.4× |
| E1-all-r2 | 154 s | 3.0× |
| E2-all | 128 s | 3.6× |
| E2-all-r2 | 208 s | 2.2× |
| K-r2k10 | 193 s | 2.4× |
| K-r3k10 | 139 s | 3.3× |
| Ref FlashVGGT | 82 s | 5.6× |

Mức tụt AUC tệ nhất so với B1 trên một chuỗi, theo N = 25 / 50 / 100 / 200:

| Cấu hình | Mức tụt tệ nhất |
|---|---|
| K-r2k10 | 2.3 / 2.7 / 1.5 / 1.1 |
| E2-all | 24.8 / 4.0 / 1.0 / 1.8 |
| E2-all-r2 | 1.0 / 0.6 / 2.8 / 1.9 |

Đánh giá các giả thuyết:

| Giả thuyết | Kết quả |
|---|---|
| H6 — K-r2k10 ≥ E1-all-r2 | **Đúng** ở mọi N, nhưng chênh lệch nhỏ (+0.2 đến +0.3), thắng 4–5/6 chuỗi |
| H7 — K-r3k10 > E1-all | **Đúng** ở mọi N (+1.0 đến +1.4), thắng 5–6/6 chuỗi |
| H8 — mức tụt tệ nhất của K-r2k10 < E2-all và E2-all-r2 | **Đúng một phần.** Đúng với cả hai chỉ ở N=200. So với E2-all: đúng ở N=25, 50, 200, sai ở N=100 (1.5 so với 1.0). So với E2-all-r2: đúng ở N=100, 200 |
| H9 — K-r2k10 cách B1 ≤ 1.5 | **Đúng:** 0.8 / 0.6 / 0.4 / 0.0 |
| H10 — Chamfer của K-r2k10 ≤ B1 + 10% | **Đúng:** 0.044–0.046 so với 0.046–0.047 của B1 |

Set 2 không có chuỗi nào hỏng nặng như office seq-06, nên không kiểm được tác dụng chính của keyframe. Phép thử đó nằm ở
kernel `kf-heldout`, chạy K-r2k10 và K-r3k10 trên bộ held-out.
