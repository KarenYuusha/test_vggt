# Kiểm chứng trên 11 chuỗi mới — giả thuyết ghi trước khi chạy (2026-11-08)

## Vì sao cần một bộ chuỗi mới

Sau đợt kiểm chứng AVGGT (`results/coverage_plan.md`), tôi đã nhìn cả 20 chuỗi cũ khi tìm nguyên nhân các mức tụt trên
stairs và heads. Vì vậy 20 chuỗi đó giờ là dữ liệu phát triển. Kiểm chứng dưới đây dùng 11 chuỗi 7-Scenes chưa từng chạy:

- **Bộ 3:** chess seq-02, fire seq-02, office seq-09, pumpkin seq-03, redkitchen seq-12, stairs seq-03.
- **Bộ 4:** chess seq-04, office seq-01, pumpkin seq-06, redkitchen seq-14, stairs seq-05.

## Những gì đã thấy trên dữ liệu phát triển

Chạy trên máy, bf16, N=100.

**Ablation trên stairs seq-01 và heads seq-01**, hai chuỗi mà mọi phương pháp lưới đều tụt mạnh nhất. Các thành phần sau
đều chỉ làm AUC thay đổi dưới 1 điểm:

- lấy mẫu nearest so với lưới;
- đường chéo và cặp trung bình;
- độ phân giải ở các lớp đầu (lưới 6×6 so với σ4).

Thứ duy nhất tạo khác biệt lớn là **keyframe đủ độ phân giải** (k-means, S//10 cụm, cộng frame 0): +1.7 trên stairs và
+0.7 trên heads.

**Lưới lệch pha theo frame** (mỗi frame giữ một pha khác nhau trong ô sh×sw, không tốn thêm token): kết quả lẫn lộn.
Giúp +2.7 trên office seq-06, không giúp trên stairs và heads. Không đưa vào cấu hình đề xuất.

**So sánh trên 3 chuỗi khó** (AUC@30):

| Cấu hình | stairs-01 | heads-01 | office-06 | Δ trung bình so với B1 |
|---|---|---|---|---|
| B1 | 87.6 | 93.3 | 72.8 | — |
| AV-s4 (AVGGT) | 84.4 | 90.8 | 68.1 | −3.5 |
| AVE-s4e36 | 85.2 | 91.7 | 72.1 | −1.6 |
| AVS-s4 (lệch pha) | 84.2 | 90.8 | 70.8 | −2.6 |
| AVK-s4k10 (AVGGT + keyframe) | 85.6 | 91.5 | 69.8 | −2.3 |
| AVEK-s4e36k10 | 86.5 | 92.3 | 73.4 | −0.5 |

Hai thành phần bổ trợ nhau. Lớp đầu global trên lưới thô sửa lỗi phủ (office seq-06). Keyframe đủ độ phân giải sửa các
cảnh lặp lại hoặc ít kết cấu (stairs, heads).

## Cấu hình

| Tên | Mô tả | Vai trò |
|---|---|---|
| B1 | VGGT full | Tham chiếu |
| AV-s4 | AVGGT σ=4 | Đối chứng chính |
| K-r2k10 | Cấu hình cũ của mình | Đối chứng |
| AVE-s4e36 | Lặp lại kiểm chứng H11 | Đối chứng phụ |
| **AVEK-s4e36k10** | Lớp 0–8 global trên lưới 6×6; lớp 9–23 lưới σ=4 + đường chéo + cặp trung bình; keyframe k-means đủ độ phân giải (S//10 cụm, cộng frame 0) ở mọi lớp global | **Cấu hình đề xuất** |
| AVEK-s4e36k20 | Như trên nhưng keyframe mỗi 20 frame, rẻ hơn | Thăm dò; chưa chạy trên dữ liệu phát triển |

Số frame N = 50, 100, 200. Chạy trên Kaggle T4, fp16.

## Giả thuyết

Đánh giá trên 11 chuỗi mới:

| | Giả thuyết |
|---|---|
| H16 | AVEK-s4e36k10 có AUC@30 trung bình ≥ AV-s4 ở mọi N, và mức tụt tệ nhất so với B1 nhỏ hơn ở mọi N. |
| H17 | AVEK-s4e36k10 cách B1 không quá 2 điểm AUC@30 trên cả 11 chuỗi, ở N=100 và N=200. |
| H18 | AVEK-s4e36k10 cách B1 trung bình không quá 0.5 điểm ở N=100 và N=200. |
| H19 | AVE-s4e36 có AUC@30 trung bình ≥ AV-s4 ở mọi N (lặp lại H11). |
| H20 | Ở N=200, AVEK-s4e36k10 nhanh hơn K-r2k10 ít nhất 10%, và AUC trung bình ≥ K-r2k10 − 0.2. |

Kết quả sẽ được báo cáo đầy đủ, kể cả các giả thuyết sai. Kiểm định cặp bằng Wilcoxon trên 11 chuỗi.

## Kết quả (Kaggle T4, fp16; bảng đầy đủ trong `results/aggregate_fresh.md`)

| Giả thuyết | Kết quả |
|---|---|
| H16 — AVEK ≥ AV-s4 và tụt tệ nhất nhỏ hơn ở mọi N | **Sai.** Trung bình đạt ở cả 3 N (+0.43 / +0.33 / +0.69). Nhưng ở N=100, mức tụt tệ nhất là −4.3 so với −3.3 (office seq-09). |
| H17 — mọi chuỗi trong 2 điểm ở N=100 và 200 | **Sai** ở N=100 (10/11), đúng ở N=200 (11/11). |
| H18 — trung bình cách B1 ≤ 0.5 | **Đúng:** −0.09 và +0.79. |
| H19 — AVE-s4e36 ≥ AV-s4 ở mọi N | **Đúng:** +0.61 / +0.53 / +0.84, thắng 9/11 chuỗi ở mỗi N, Wilcoxon p = 0.08 / 0.05 / 0.005. |
| H20 — AVEK nhanh hơn K-r2k10 ≥ 10%, AUC ≥ K-r2k10 − 0.2 | **Đúng:** nhanh hơn 1.19×, AUC +0.05. |

Kết luận:

- **Kết quả lặp lại ổn định nhất là AVE-s4e36:** giữ các lớp 0–8 ở dạng global trên lưới 6×6 thay vì đổi thành frame
  attention.
  - Hơn AVGGT trên cả 18 chuỗi kiểm chứng cũ (+0.2 đến +0.4) và 11 chuỗi mới (+0.5 đến +0.8).
  - Chỉ tốn thêm 4–5% thời gian.
- **Keyframe không đáng chi phí trên dữ liệu mới.** AVEK không hơn AVE mà chậm hơn khoảng 25%. Lợi ích của keyframe trên
  stairs/heads ở dữ liệu phát triển không lặp lại được trên trung bình.
- **Mức tụt tệ nhất là chung cho mọi phương pháp:** office seq-09 ở N=100 tụt −3 đến −4 với cả K-r2k10, AV-s4, AVE và
  AVEK.
- **Ở N=200, các bản nén có AUC trung bình cao hơn chính VGGT full** (+0.1 đến +0.9), chủ yếu do stairs seq-05, nơi VGGT
  full kém hơn bản nén 4–8 điểm.

## Hướng thử thêm (sau khi xem 11 chuỗi; chạy trên máy, office seq-06, N=100)

**Giảm query** (chỉ tính global attention trên lưới query thưa, các token khác dùng lại kết quả của token neo trong ô):

| Biến thể | AUC@30 (B1 = 72.8, AVE-s4e36 = 72.1) |
|---|---|
| Ô 2×2, mọi lớp, sao chép output | 35.5 |
| Như trên, giữ đủ query cho frame 0 | 37.1 |
| Ô 2×2 từ lớp 13 | 22.0 |
| Ô 2×2 chỉ ở lớp 17–23 | 72.0 |
| Ô 2×2, chỉ dùng chung phần key thô kèm log-sum-exp; đường chéo và cặp trung bình tính riêng cho từng token | 38.7 |
| Như trên, từ lớp 9 | 42.7 |

Kết quả âm: các lớp giữa không chịu được việc dùng chung kết quả attention giữa các frame, kể cả trong ô 2×2. Chỉ 7 lớp
cuối chịu được, nên phần tăng tốc nhỏ.

**Bộ nhớ:** đo theo từng giai đoạn cho thấy B1 và AVE-s4e36 có bộ nhớ đỉnh giống hệt nhau (5.14 GB ở N=100 trên máy).
Bộ nhớ nằm ở trọng số, các tầng trung gian lưu cho DPT head, và các tensor tạm trong mỗi block. Nén attention không giảm
bộ nhớ, nên trên T4 16 GB mọi phương pháp chỉ chạy được tới khoảng N=250.
