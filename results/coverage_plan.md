# So sánh với AVGGT và cải tiến lớp đầu — giả thuyết ghi trước khi chạy (2026-11-07)

## Bối cảnh

AVGGT (Sun et al., CVPR 2026, arXiv 2512.02541) là phương pháp tăng tốc VGGT không cần train mạnh nhất đã công bố. Nó có
hai bước:

- Đổi global attention ở các lớp 0–8 thành frame attention.
- Ở các lớp còn lại, lấy mẫu K/V theo lưới: giữ patch đầu tiên của mỗi ô sh×sw, giữ nguyên frame 0, giữ đường chéo, và
  thêm một cặp K/V trung bình.

Cấu hình K-r2k10 trước đây của mình (nén K/V cộng keyframe k-means) gần như trùng với ý tưởng này. Bù khối lượng cũng đã
có trong GPA-VGGT. Vì vậy cần một đóng góp khác.

### Kết quả trên 2 chuỗi phát triển (office seq-06, chess seq-05), chạy trên máy, bf16

AUC@30 trên office seq-06, chuỗi khó, có các frame quay 105–151° so với frame 0:

| Cấu hình | N=100 | N=50 |
|---|---|---|
| B1 (VGGT full) | 72.8 | 72.9 |
| AV-s4 (dựng lại AVGGT, σ=4) | 68.1 | 67.6 |
| AV-s9 (AVGGT, σ=9) | 68.3 | 64.9 |
| AV-s4-g0 (AVGGT nhưng mọi lớp global) | 71.5 | 69.9 |
| AVK-s9k10 (AVGGT + keyframe) | 69.7 | 69.1 |
| AVE-s4e36 (lớp 0–8 global trên lưới 6×6) | 72.1 | 70.2 |
| AVEK-s9e36k10 (lưới 6×6 ở lớp đầu, σ=9 + keyframe ở lớp sau) | 72.3 | 71.8 |
| NB-s9m4 (lân cận đủ độ phân giải, có chính frame) | 52.1 | 32.7 |
| NBx-s9m3 (lân cận, không có chính frame) | 58.4 | 43.2 |

Nhận xét:

1. **Lỗi phủ cũng có ở AVGGT,** tụt 4.7–5.3 điểm. Phần lớn mức tụt đến từ bước đổi lớp 0–8 thành frame attention:
   giữ các lớp đó ở dạng global (AV-s4-g0) lấy lại 2.3–3.4 điểm. Điều này trái với nhận định của AVGGT rằng các lớp
   global đầu không quan trọng. Các lớp này có thể không tạo tương ứng, nhưng chúng vẫn truyền thông tin giữa các frame,
   và các frame không chung vùng nhìn với frame 0 cần thông tin đó.
2. **Không cần độ phân giải cao ở lớp đầu.** Lưới 6×6, khoảng 30 token mỗi frame (≈ 3% số key), đủ để hồi phục, thậm chí
   tốt hơn cả khi giữ đủ độ phân giải.
3. **Tập key riêng cho từng query làm hỏng mô hình.** Cho mỗi frame xem đủ độ phân giải các frame giống nó nhất làm AUC
   sụp. Khi các frame không cùng thấy một tập key, chúng mất hệ quy chiếu chung. Keyframe dùng chung cho mọi query thì
   không gặp vấn đề này. Đây là một kết quả âm.

Bổ sung ở N=25, ghi trước khi có kết quả Kaggle. Số liệu N=25 chạy lần đầu bị sai do lỗi kiểu dữ liệu: ở nhánh không
chia khối (dưới 32768 token), q/k ra fp32 còn v ra bf16, và kernel aten gọi trực tiếp không ép kiểu như SDPA dưới
autocast. Lỗi đã được sửa. Nhánh này chỉ dùng khi N ≤ 31, nên các kernel Kaggle (N ≥ 50) không bị ảnh hưởng.

| Cấu hình | office seq-06 | chess seq-05 |
|---|---|---|
| B1 | 74.6 | 89.7 |
| AV-s4 | 70.0 | 89.5 |
| AV-s9 | 61.9 | 87.9 |
| AVE-s4e36 | 73.6 | 89.4 |
| AVE-s9e36 | 65.0 | 87.8 |
| AVEK-s9e36k10 | 66.8 | 88.0 |

Ở N=25, lưới σ=9 quá thô, và keyframe chỉ có 2 cụm nên không bù được. Cấu hình nên dùng ở N nhỏ là AVE-s4e36.

Cấu hình được chọn sau khi xem 2 chuỗi trên:

- **AVE-s4e36**: AVGGT với σ=4, nhưng các lớp 0–8 vẫn global trên lưới 6×6. Cấu hình này tách riêng tác dụng của lớp đầu.
- **AVEK-s9e36k10**: cấu hình đề xuất. Lớp 0–8 global trên lưới 6×6, các lớp 9–23 dùng lưới 3×3 (σ=9) cộng keyframe
  k-means đủ độ phân giải (S//10 cụm, cộng frame 0), giữ đường chéo và cặp trung bình.

## Kiểm chứng

- **Dữ liệu:** 18 chuỗi không dùng để chọn cấu hình, gồm bộ A (7 chuỗi), bộ B trừ office seq-06 và chess seq-05 (5
  chuỗi), và bộ C (6 chuỗi). Hai chuỗi phát triển cũng chạy, nhưng báo cáo riêng.
- **N:** 50, 100, 200.
- **Môi trường:** Kaggle T4, fp16.
- **Cấu hình:** B1, AV-s4, AV-s9, AVE-s4e36, AVEK-s9e36k10. Số của K-r2k10 lấy từ các lần chạy trước, cũng trên T4.

## Giả thuyết

Đánh giá trên 18 chuỗi, ở từng N:

| | Giả thuyết |
|---|---|
| H11 | AVE-s4e36 có AUC@30 trung bình ≥ AV-s4, và mức tụt tệ nhất so với B1 nhỏ hơn hoặc bằng. Lớp đầu global không làm hại. |
| H12 | AVEK-s9e36k10 cách B1 trung bình ≤ 1.0 điểm ở N=100 và N=200, và mọi chuỗi cách B1 ≤ 2.0 điểm. |
| H13 | Mức tụt tệ nhất của AVEK-s9e36k10 nhỏ hơn của AV-s4 và AV-s9 ở mọi N. |
| H14 | Ở N=200 trên T4, AVEK-s9e36k10 không chậm hơn AV-s4 quá 10%, và nhanh hơn K-r2k10 (189 s). |
| H15 | fid_pose trung bình của AVEK-s9e36k10 ≥ AV-s4 ở mọi N. |

Nếu H11 sai, kết luận "lớp đầu cần global" chỉ đúng với chuỗi có lỗi phủ, và sẽ báo cáo như vậy.

## Kết quả kiểm chứng (Kaggle T4, fp16; bảng đầy đủ trong `results/aggregate_av.md`)

Trung bình trên 18 chuỗi kiểm chứng ở N=200:

| Cấu hình | AUC@30 | Δ so với B1 | Tụt tệ nhất | Số chuỗi trong 2 điểm | fid_pose | Thời gian | Nhanh hơn B1 |
|---|---|---|---|---|---|---|---|
| B1 | 80.8 | — | — | — | — | 455 s | 1× |
| AV-s4 (AVGGT) | 80.2 | −0.6 | −2.7 | 16/18 | 95.2 | 124 s | 3.7× |
| AV-s9 (AVGGT) | 78.8 | −1.9 | −5.1 | 11/18 | 92.1 | 94 s | 4.8× |
| AVE-s4e36 | 80.5 | −0.3 | −2.2 | 17/18 | 95.6 | 130 s | 3.5× |
| AVEK-s9e36k10 | 80.1 | −0.6 | −3.0 | 15/18 | 95.3 | 133 s | 3.4× |
| K-r2k10 (cũ) | 80.6 | −0.2 | −1.1 | 18/18 | 96.7 | 189 s | 2.4× |
| Ref FlashVGGT (fine-tune) | 81.3 | +0.5 | −5.8 | 15/18 | 89.4 | 82 s | 5.6× |

Kiểm định cặp trên 18 chuỗi, AVE-s4e36 trừ AV-s4:

| N | Trung bình | Số chuỗi thắng | Wilcoxon p |
|---|---|---|---|
| 50 | +0.21 | 12/18 | 0.11 |
| 100 | +0.39 | 13/18 | 0.02 |
| 200 | +0.34 | 13/18 | 0.07 |

So với K-r2k10, AVE-s4e36 có AUC trung bình ngang nhau (median 0.00), nhưng mức tụt tệ nhất lớn hơn.

Đánh giá các giả thuyết:

| Giả thuyết | Kết quả |
|---|---|
| H11 — AVE-s4e36 ≥ AV-s4, tụt tệ nhất nhỏ hơn hoặc bằng | **Đúng** ở cả 3 N. Mức tăng nhỏ (+0.2 đến +0.4 AUC); chỉ có ý nghĩa thống kê (p < 0.05) ở N=100. Tốn thêm khoảng 5% thời gian. |
| H12 — AVEK cách B1 ≤ 1.0 và mọi chuỗi trong 2 điểm | **Sai.** Trung bình đạt (−1.0 / −0.6) nhưng chỉ có 16/18 và 15/18 chuỗi trong 2 điểm. |
| H13 — tụt tệ nhất của AVEK nhỏ hơn AV-s4 và AV-s9 | **Sai** ở N=50 (−6.4 so với −4.7) và N=200 (−3.0 so với −2.7). |
| H14 — AVEK ≤ 1.1 × thời gian AV-s4 ở N=200, và nhanh hơn K-r2k10 | **Đúng:** 133 s so với 124 s (1.07×), và so với 189 s. |
| H15 — fid_pose của AVEK ≥ AV-s4 | **Sai** ở N=50 và 100. |

Kết luận trung thực:

- **Cấu hình đề xuất AVEK-s9e36k10 không tốt hơn AVGGT.** Nó khớp quá mức với chuỗi office seq-06. Lưới σ=9 hại trên stairs và heads, còn keyframe tốn gần bằng phần tiết kiệm được.
- **Phát hiện về các lớp đầu đúng nhưng tác dụng nhỏ.** Trên chuỗi thường, giữ các lớp đầu ở dạng global trên lưới thô chỉ tăng +0.2 đến +0.4 AUC. Trên chuỗi phát triển có lỗi phủ, mức tăng lớn: N=100 là −0.6 so với −2.5; N=200 là −0.9 so với −2.2.
- **Các chuỗi khó nhất với mọi phương pháp lưới là stairs và heads** (tụt 1.5–5 điểm). K-r2k10 ít bị hơn, nhưng chậm hơn 1.45×.
