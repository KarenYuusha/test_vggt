# Chuỗi dài trên GPU 16 GB — giả thuyết ghi trước khi chạy (2026-11-08)

## Bối cảnh

Đo bộ nhớ theo từng giai đoạn cho thấy nén attention không giảm bộ nhớ đỉnh: B1 và AVE-s4e36 đều 5.14 GB ở N=100 trên
máy, và 11.3 GB ở N=200 trên T4. Bộ nhớ nằm ở bốn tầng trung gian lưu cho DPT head, các tensor tạm trên toàn bộ token
trong mỗi block, và ảnh cùng output để trên GPU. Vì vậy trên T4, mọi phương pháp không train đều dừng ở khoảng N=250.
AVGGT báo kết quả ở N=800, nhưng trên A100.

`src/tfvggt/longseq.py` thêm một forward ít bộ nhớ. Phép tính cho từng token giữ nguyên, chỉ thay đổi thứ tự thực hiện và
nơi lưu trữ:

- Frame block chạy theo nhóm frame.
- Global block chạy hai lượt streaming qua các khối token. Lượt 1 chỉ giữ tập key/value đã nén. Lượt 2 tính query, chú ý
  vào tập key đó (cộng đường chéo và cặp trung bình), rồi áp dụng residual, MLP và residual ngay trên khối đó.
- Các tầng trung gian chuyển sang RAM CPU. Các head đọc lại theo từng khối frame.
- Ảnh và output nằm trên CPU.

### Đo trên máy (RTX 4060 8 GB, office seq-06, AVE-s4e36)

| N | Forward chuẩn | Ít bộ nhớ | AUC@30 |
|---|---|---|---|
| 50 | 5.37 GB | 3.64 GB | 70.24 so với 70.15 |
| 100 | 7.47 GB (T4) | 3.78 GB | 72.0 |
| 200 | 11.30 GB (T4) | 4.30 GB | 71.4 |
| 400 | không chạy được | 5.29 GB, 272 s | 70.9 |

Ở N=50, B1 chạy bằng hai cách cho AUC trùng khớp (72.85), và depth của AVE lệch trung bình 0.09%.

## Thí nghiệm (Kaggle T4, fp16)

**Chuỗi:** bộ 3, gồm chess seq-02, fire seq-02, office seq-09, pumpkin seq-03, redkitchen seq-12 và stairs seq-03 (chuỗi
này chỉ có 500 frame, nên "N=800" thực chất là 500 frame).

| Kernel | Nội dung |
|---|---|
| a / b / c (mỗi kernel 2 chuỗi) | Forward ít bộ nhớ. B1 ở N=400; AV-s4 ở N=400, 800; AVE-s4e36 ở N=200, 400, 800. |
| d | Forward ít bộ nhớ, B1 ở N=800 trên chess seq-02: tham chiếu tốc độ và độ chính xác. |
| e | Forward chuẩn ở N=400 trên chess seq-02 (B1, AV-s4, AVE-s4e36): kiểm tra hết bộ nhớ. |

## Giả thuyết

| | Giả thuyết |
|---|---|
| H21 | Trên T4 ở N=400, forward chuẩn hết bộ nhớ với cả B1, AV-s4 và AVE-s4e36. Forward ít bộ nhớ chạy được mọi cấu hình ở N=400 và N=800, với bộ nhớ đỉnh ≤ 10 GB. |
| H22 | Ở N=200 trên T4, AVE-s4e36 ít bộ nhớ cách AVE-s4e36 chuẩn (đã chạy trong kernel fresh-set3a/3b) ≤ 0.3 AUC@30 trung bình trên 6 chuỗi. |
| H23 | Ở N=400, AVE-s4e36 nhanh hơn B1 ít nhất 5× (cả hai ít bộ nhớ, trung bình 6 chuỗi). Ở N=800 trên chess seq-02, nhanh hơn ít nhất 8×. |
| H24 | Ở N=400, AVE-s4e36 cách B1 không quá 1.0 AUC@30 trung bình, và có AUC trung bình ≥ AV-s4. |
| H25 | Ở N=800, AVE-s4e36 có AUC@30 trung bình (so với ground truth) ≥ AV-s4 trên 6 chuỗi. |

## Kết quả (Kaggle T4; bảng từng chuỗi trong `results/aggregate_long.md`)

| Giả thuyết | Kết quả |
|---|---|
| H21 — forward chuẩn hết bộ nhớ ở N=400; bản ít bộ nhớ chạy đủ, đỉnh ≤ 10 GB | **Đúng.** Forward chuẩn hết bộ nhớ với cả B1, AV-s4 và AVE-s4e36. Bản ít bộ nhớ có đỉnh 4.30 GB ở N=200, 5.29–6.46 GB ở N=400, 7.41 GB ở N=800, và 9.66 GB với B1 ở N=800. |
| H22 — ở N=200, bản ít bộ nhớ khớp bản chuẩn trong 0.3 AUC | **Đúng.** Chênh lệch trung bình 0.00, tối đa 0.02 trên 6 chuỗi. |
| H23 — AVE nhanh hơn B1 ≥ 5× ở N=400 và ≥ 8× ở N=800 | **Sai.** Chỉ đạt 4.39× (trung bình 6 chuỗi) và 4.89× (chess seq-02). |
| H24 — ở N=400, AVE cách B1 ≤ 1.0 và ≥ AV-s4 | **Đúng.** AVE − B1 = +0.27; AVE − AV-s4 = +1.19. |
| H25 — ở N=800, AVE ≥ AV-s4 | **Đúng.** Trung bình +1.03, thắng 5/6 chuỗi. Theo chuỗi: chess −0.1, fire +0.2, office +2.6, pumpkin +0.5, redkitchen +0.2, stairs +2.7. |

Ghi chú:

- **Vì sao không đạt 8×.** Với σ=4 trên 15 lớp global, chi phí global attention giảm tối đa 24/(15/4) = 6.4×. Phần
  còn lại (frame attention, MLP, DPT, chuyển dữ liệu sang CPU) kéo con số xuống khoảng 4.4–4.9×. AVGGT báo 8–10× ở
  N=800, nhưng trên A100 với FlashAttention-2, một điều kiện khác.
- **Lợi thế của AVE so với AVGGT tăng theo N.** Ở N ≤ 200 là +0.5 đến +0.8. Ở N=400 là +1.19 và ở N=800 là +1.03. Lợi
  thế tập trung ở office seq-09 và stairs seq-03 (+2.6 đến +3.5), hai chuỗi mà AVGGT tụt 1–2.5 điểm so với B1.
- **Ở N=400, AVE còn cao hơn B1** trên office (+1.0) và stairs (+1.8). Dấu hiệu này đã thấy ở N=200 trên stairs seq-05.
  Nén K/V có vẻ đóng vai trò điều chuẩn trên các chuỗi dài, nhưng mới chỉ có trên 2 chuỗi nên chưa phải kết luận.
- **Chi phí GPU của đợt này** là khoảng 14 giờ T4. Trong đó có khoảng 2.3 giờ bị bỏ đi khi khởi động lại 4 kernel để
  thêm dòng tiến độ, theo quy tắc kernel không được im lặng quá 5 phút.
