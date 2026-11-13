# tfvggt — Tăng tốc VGGT không cần huấn luyện (training-free)

Giữ nguyên trọng số VGGT-1B, chỉ thay đổi cách tính ở giai đoạn inference. Code FlashVGGT (`../flashvggt`) chỉ được
import, không sửa.

**Tóm tắt (cập nhật 2026-11-09).** Phần 0 là giai đoạn 2. Các phần 1–7 là giai đoạn 1, giữ lại làm lịch sử.

- **Đối chứng mạnh nhất đã công bố.** AVGGT (CVPR 2026) đã làm nén K/V không train; bù khối lượng đã có trong GPA-VGGT.
  Vì vậy cấu hình K-r2k10 của giai đoạn 1 không còn là đóng góp mới. Mình dựng lại AVGGT để làm đối chứng.
- **Đóng góp 1 — lớp đầu global trên lưới thô (AVE-s4e36).** AVGGT đổi các lớp global 0–8 thành frame attention. Mình
  giữ chúng là global, nhưng chỉ trên lưới 6×6 (khoảng 3% key).
  - So với AVGGT trên 7-Scenes (không lặp lại trên TUM, xem dưới): +0.2 đến +0.4 AUC@30 trên 18 chuỗi kiểm chứng,
    +0.5 đến +0.8 trên 11 chuỗi chưa từng nhìn
    (p = 0.005 ở N=200), +1.2 ở N=400 và +1.0 ở N=800.
  - Chi phí: chậm hơn khoảng 5–7%.
- **Đóng góp 2 — forward ít bộ nhớ.** Phép tính cho từng token giữ nguyên. Nén attention không giảm bộ nhớ đỉnh, nên
  trước đây mọi phương pháp dừng ở khoảng N=250 trên T4.
  - Forward streaming đưa VGGT lên **800 frame trên Tesla T4 16 GB**: đỉnh 7.4 GB với AVE, 9.7 GB với VGGT full.
  - Ở N=400, forward chuẩn hết bộ nhớ, còn bản này chỉ cần 5.3 GB. Ngay cả GPU 8 GB cũng chạy được 400 frame.
  - Kết quả lệch so với forward chuẩn: 0.00 AUC.
- **Bộ dữ liệu thứ hai (TUM RGB-D, 6 chuỗi): lợi thế của AVE không lặp lại.**
  - So với AVGGT, AVE chỉ thắng 2/6 chuỗi ở mỗi N.
  - Cấu hình có thêm keyframe k-means đủ độ phân giải (**AVEK-s4e36k10**) thắng AVGGT trên 23/24 cặp (chuỗi, N) của
    TUM, hơn +0.9 đến +1.8 AUC. Trên 11 chuỗi 7-Scenes mới, nó thắng 28/33 cặp.
  - Đổi lại, AVEK chậm hơn AVGGT 20–40%.
  - TUM khó hơn hẳn với mọi cách nén K/V không train: trên fr1_360 (quay 360°) và fr1_room, mọi cấu hình nén đều tụt
    3–9 điểm so với VGGT.
- **Đóng góp 3 — chỗ nén K/V gây hại nằm ở các lớp global giữa (14–18).**
  - Ablation trên chuỗi phát triển cho thấy:
    - nén lưới 6×6 ở lớp 0–8 gần như không tốn gì;
    - phần lớn mất mát đến từ lưới 2×2 ở lớp 9–23;
    - riêng dải 14–18 chiếm khoảng 75% phần mất mát đó.
  - Cấu hình **AVEKB-s4e36k10f14** = AVEK + attention đầy đủ ở lớp 14–18. Kiểm chứng trên 6 chuỗi TUM chưa dùng:
    - hơn AVEK +1.5 / +0.8 AUC@30 ở N=100 / 200, thắng 5/6 chuỗi;
    - lấy lại khoảng 47–63% khoảng cách từ AVGGT đến VGGT;
    - đổi lại chỉ nhanh hơn VGGT 2.0× ở N=200 (AVGGT 3.4×).
  - Hai trên bốn giả thuyết ghi trước sai, và n=6 nên không có ý nghĩa thống kê (xem 0.4b).
  - **Bản rẻ hơn: AVEKB-f16n3**, chỉ giữ lớp 16–18 đầy đủ. Bản này được chọn trên dữ liệu phát triển theo quy tắc ghi
    trước, rồi kiểm chứng trên 7 chuỗi 7-Scenes và 4 chuỗi TUM chưa dùng:
    - ngang VGGT ở N=200 (79.0 so với 78.2 trên 7-Scenes, 84.9 so với 85.1 trên TUM);
    - nhanh hơn VGGT 2.4×;
    - hơn AVEK trên 10/11 chuỗi, p = 0.0015.
  - Gộp 17 chuỗi chưa dùng, AVEKB hơn AVEK +0.57 ở N=200, p = 0.013. Cả 7 giả thuyết của vòng này đều đúng (xem 0.4c).
  - Trên các chuỗi TUM quay nhiều, khoảng cách tới VGGT vẫn còn 1.5–1.8 điểm.
  - **Keyframe trải đều theo thời gian (AVU-u5)**, thay cho k-means: frame 0 và S/5 frame trải đều được giữ nguyên.
    Kiểm chứng trên 6 chuỗi TUM mới:
    - hơn AVEK +1.3 điểm (N=200: thắng 5/6 chuỗi, p = 0.031);
    - ngang AVEKB-f16n3 (+0.16) với cùng chi phí (2.4× so với VGGT), nhưng đơn giản hơn;
    - cả 3 giả thuyết ghi trước đều đúng (xem 0.4e).
    - Vòng sau kiểm lại trên 4 chuỗi 7-Scenes mới: vẫn ngang f16n3 (+0.30).
  - **Bản chính xác nhất: AVEKBU-f16u10** = f16n3 cộng S/10 frame trải đều. Kiểm chứng riêng trên 6 chuỗi TUM và 4
    chuỗi 7-Scenes mới (xem 0.4f):
    - hơn f16n3 +0.8 ở N=100 (thắng 6/6 chuỗi TUM), nhưng chỉ +0.2 đến +0.3 ở N=200, không có ý nghĩa thống kê;
    - nhanh hơn VGGT 2.1×.
    - Sau hiệu chỉnh Holm, không kiểm định nào của hai vòng keyframe trải đều còn dưới 0.05.
- **Tốc độ ở chuỗi dài.** AVE nhanh hơn VGGT full 4.4× ở N=400 và 4.9–5.0× ở N=800 trên T4, chưa đạt mức 8× mà mình
  đặt ra trước. Kết quả này lặp lại trên 8 chuỗi TUM dài mới (xem 0.4g).
- **Chuỗi dài N=400/800 với keyframe trải đều** (0.4g):
  - Keyframe trải đều giúp ở N=400 (+0.75 so với AVEK) nhưng gần như hết tác dụng ở N=800 (+0.10).
  - AVU-u5 và f16u10 mất lợi thế tốc độ, chỉ còn 2.8× và 2.3× so với VGGT.
  - 6/9 giả thuyết ghi trước sai.
  - VGGT gốc tự tụt ở N=800 trên 3/8 chuỗi, trong khi các bản nén ổn định.
  - Bản AVU-c40 (40 keyframe trải đều cố định) hơn AVE +1.07 với 4.2× so với VGGT, nhưng trượt ngưỡng chi phí ghi trước.
- **Kết quả âm.** Đã thử và loại các ý sau, xem phần 0.4:
  - độ phân giải theo lân cận cho từng query;
  - lưới lệch pha theo frame;
  - giảm số query;
  - keyframe kết hợp lưới thô σ=9;
  - chọn keyframe theo độ phủ (FPS);
  - lưới thích ứng theo nội dung.
  - giữ nguyên các frame bị nén làm hỏng (oracle, chọn bằng ground truth).

## 0. Giai đoạn 2 — so với AVGGT, và chuỗi dài trên GPU 16 GB

Mọi số liệu dưới đây chạy trên Kaggle T4, fp16. Giả thuyết được ghi trước khi chạy, và các giả thuyết sai cũng được
giữ lại. Chi tiết trong [results/coverage_plan.md](../results/coverage_plan.md), [results/fresh_plan.md](../results/fresh_plan.md)
và [results/longseq_plan.md](../results/longseq_plan.md).

### 0.1 Phương pháp

Code ở `_grid_attention` trong [tfvggt/core.py](../src/tfvggt/core.py). Các phần key rời nhau được ghép chính xác thành một
softmax chung qua log-sum-exp. Phép ghép được kiểm tra với softmax tường minh, sai số khoảng 1e-6.

- **AV-s4 — dựng lại AVGGT:**
  - Lớp global 0–8 đổi thành frame attention.
  - Ở lớp 9–23, K/V giữ patch đầu của mỗi ô 2×2; frame 0 giữ nguyên.
  - Thêm đường chéo (key của chính query) và một cặp K/V trung bình của các key bị bỏ.
- **AVE-s4e36 — của mình:** giống AV-s4, nhưng lớp 0–8 vẫn là global, với K/V trên lưới 6×6.
- **Forward ít bộ nhớ** ([tfvggt/longseq.py](../src/tfvggt/longseq.py)):
  - Frame block chạy theo nhóm frame.
  - Global block chạy hai lượt qua các khối token. Lượt 1 chỉ giữ tập K/V đã nén. Lượt 2 tính query, attention,
    residual và MLP ngay trên từng khối.
  - Tầng trung gian của DPT và output nằm trên RAM CPU.
  - Bật bằng `model.lowmem = True`, hoặc `--lowmem` khi chạy script.

### 0.2 So với AVGGT

**Δ AUC@30 của AVE-s4e36 trừ AV-s4**, kiểm định Wilcoxon cặp:

| Bộ chuỗi | N=50 | N=100 | N=200 | N=400 | N=800 |
|---|---|---|---|---|---|
| 18 chuỗi kiểm chứng | +0.21 | +0.39 (p=0.02) | +0.34 | | |
| 11 chuỗi chưa từng nhìn | +0.61 | +0.53 | +0.84 (p=0.005) | | |
| 6 chuỗi dài (bộ 3) | | | | +1.19 | +1.03 |

**Bảng N=200 trên 11 chuỗi mới:**

| Cấu hình | Δ AUC so với VGGT | Tụt tệ nhất | Nhanh hơn VGGT |
|---|---|---|---|
| AV-s4 (AVGGT) | +0.10 | −2.6 | 3.8× |
| AVE-s4e36 | +0.93 | −0.5 | 3.6× |
| K-r2k10 (giai đoạn 1) | +0.74 | −0.4 | 2.5× |

Lợi thế của AVE tập trung ở các chuỗi mà AVGGT tụt mạnh: office seq-06, office seq-09, stairs seq-03.

Theo sai số tư thế từng frame trên office seq-06, giữ lớp đầu global giảm sai số ở mọi nhóm góc so với frame 0. Điều
này trái với nhận định của AVGGT rằng các lớp đầu không quan trọng. Chúng có thể không tạo tương ứng, nhưng vẫn truyền
thông tin giữa các frame.

### 0.3 Chuỗi dài trên T4 16 GB

Bộ 3 gồm 6 chuỗi. Riêng stairs seq-03 chỉ có 500 frame.

| N | Cấu hình | AUC@30 TB | Thời gian TB | Bộ nhớ đỉnh |
|---|---|---|---|---|
| 400 | VGGT full, forward chuẩn | hết bộ nhớ | — | > 15 GB |
| 400 | VGGT full, ít bộ nhớ | 80.2 | 1919 s | 6.46 GB |
| 400 | AV-s4, ít bộ nhớ | 79.2 | 409 s | 5.29 GB |
| 400 | AVE-s4e36, ít bộ nhớ | 80.4 | 437 s | 5.29 GB |
| 800 | VGGT full, ít bộ nhớ (chỉ chess seq-02) | 89.4 | 7183 s | 9.66 GB |
| 800 | AV-s4, ít bộ nhớ | 79.1 | 1289 s | 7.41 GB |
| 800 | AVE-s4e36, ít bộ nhớ | 80.1 | 1377 s | 7.41 GB |

Ở N=200, forward ít bộ nhớ cho AUC khớp forward chuẩn: lệch trung bình 0.00, tối đa 0.02 trên 6 chuỗi. Thời gian chậm
hơn khoảng 5%, bộ nhớ đỉnh giảm từ 11.3 GB xuống 4.3 GB.

### 0.4a TUM RGB-D, bộ dữ liệu thứ hai

6 chuỗi, chuyển sang bố cục 7-Scenes bằng [src/tfvggt/datasets/tum.py](../src/tfvggt/datasets/tum.py). Chi tiết trong
[results/tum_plan.md](../results/tum_plan.md).

AUC@30 trung bình (thời gian trong ngoặc):

| N | VGGT | K-r2k10 | AVGGT (AV-s4) | AVE-s4e36 | AVEK-s4e36k10 |
|---|---|---|---|---|---|
| 50 | 86.7 (41 s) | 82.9 | 82.3 (22 s) | 83.0 (24 s) | **84.1** (25 s) |
| 100 | 87.4 (128 s) | 84.9 (63 s) | 84.0 (52 s) | 83.9 (55 s) | **85.6** (62 s) |
| 200 | 86.4 (454 s) | 84.6 (192 s) | 83.6 (133 s) | 84.2 (141 s) | **85.1** (170 s) |
| 400 | — | — | 83.5 (387 s) | 83.5 (414 s) | **84.4** (537 s) |

Giả thuyết ghi trước:

| | Giả thuyết | Kết quả |
|---|---|---|
| H26 | AVE ≥ AVGGT ở mọi N | **Sai** |
| H27 | AVE cách VGGT ≤ 1 | **Sai** (−3.5 và −2.1) |
| H28 | AVE trong 2 điểm trên từng chuỗi | **Sai** ở N=100 |
| H29 | Keyframe giảm mức tụt trên fr1_360 (thăm dò) | **Đúng** |

Trên cả hai bộ dữ liệu, cấu hình bền nhất so với AVGGT là AVEK-s4e36k10: thắng 51/57 cặp (chuỗi, N) trên 17 chuỗi chưa
từng dùng để chọn cấu hình. Đây là phân tích sau khi xem kết quả, không phải giả thuyết ghi trước.

### 0.4b Nén gây hại ở lớp nào? Dải lớp đầy đủ (2026-11-09)

Chi tiết trong [results/ablation_plan.md](../results/ablation_plan.md) (phát triển, đã nhìn) và
[results/band_plan.md](../results/band_plan.md) (kiểm chứng, giả thuyết ghi trước).

**Ablation** trên fr1_360 và fr1_room, N=100/200. R là tổng AUC lấy lại so với AVE trên 4 ô:

| Giữ attention đầy đủ ở | R | Thời gian ở N=200 |
|---|---|---|
| (không, = AVE) | 0 | 141 s |
| lớp 0–8 | +7.1 | — |
| lớp 9–23 | +16.1 | 340 s |
| lớp 9–13 | −1.9 | 212 s |
| **lớp 14–18** | **+12.1** | 214 s |
| lớp 19–23 | +3.4 | 214 s |

**Kiểm chứng** trên 6 chuỗi TUM chưa từng chạy: fr1_rpy, fr1_plant, fr1_teddy, fr2_360_hemisphere, fr2_desk,
fr3_sitting_halfsphere. AUC@30 trung bình (thời gian):

| N | VGGT | AVGGT | AVE | AVEK | AVEB (AVE + 14–18) | AVEKB (AVEK + 14–18) |
|---|---|---|---|---|---|---|
| 100 | 80.3 (133 s) | 76.8 (53 s) | 75.8 (56 s) | 77.4 (64 s) | 78.0 (70 s) | **79.0** (76 s) |
| 200 | 79.8 (467 s) | 76.6 (136 s) | 75.8 (145 s) | 77.4 (175 s) | 77.1 (206 s) | **78.1** (230 s) |

| | Giả thuyết | Kết quả |
|---|---|---|
| H30 | AVEB ≥ AVE + 1 | **Đúng** (+2.2 / +1.3) |
| H31 | AVEB ≥ AVEK | **Sai** ở N=200 (−0.3) |
| H32 | AVEKB ≥ AVEK + 0.5 | **Đúng** (+1.5 / +0.8) |
| H33 | AVEKB thu hẹp ≥ 50% khoảng cách AVEK–VGGT trên chuỗi quay nhiều | **Sai** ở N=200 (24%) |

Cần lưu ý:

- Chỉ có 6 chuỗi, nên p = 0.09–1.0.
- fr1_rpy (chỉ quay) là ngoại lệ: thêm dải đầy đủ làm AUC giảm 1–4 điểm.
- AVE thua AVGGT 0.8–1.0 điểm trên bộ này.
- Chưa chạy trên 7-Scenes.

### 0.4c Dải rẻ hơn, kiểm chứng trên 7-Scenes và 4 chuỗi TUM mới (2026-11-09)

Giả thuyết ghi trước và kết quả nằm ở [results/narrow_plan.md](../results/narrow_plan.md). Bảng đầy đủ ở
[results/aggregate_narrow.md](../results/aggregate_narrow.md).

**Chọn trên dữ liệu phát triển** (6 chuỗi TUM của 0.4b). Quy tắc: chọn bản rẻ nhất mà vẫn giữ ít nhất 70% mức cải
thiện của AVEKB so với AVEK.

| biến thể | gain so với AVEK | thời gian N=200 |
|---|---|---|
| AVEKB (14–18 đầy đủ) | +1.15 | 230 s |
| 15–17 đầy đủ | +0.48 | 199 s |
| 14–16 đầy đủ | +0.36 | 200 s |
| **16–18 đầy đủ (V\*)** | **+1.01** | 199 s |
| 14–18 trên lưới 1×2 | +0.68 | 184 s |

**Kiểm chứng.** AUC@30 trung bình ở N=100 / N=200, tốc độ so với VGGT ở N=200:

| bộ | VGGT | AVGGT | AVEK | AVEKB | AVEKB-f16n3 |
|---|---|---|---|---|---|
| 7-Scenes, 7 chuỗi mới | 79.1 / 78.2 | 78.2 / 77.5 (3.7×) | 78.9 / 78.4 (2.9×) | 79.4 / 78.7 (2.1×) | **79.4 / 79.0 (2.4×)** |
| TUM, 4 chuỗi mới | 85.3 / 85.1 | 85.0 / 84.2 (3.9×) | 84.3 / 84.0 (3.0×) | 85.9 / 84.9 (2.2×) | 85.5 / 84.9 (2.5×) |
| TUM, 6 chuỗi của 0.4b (dữ liệu chọn) | 80.3 / 79.8 | 76.8 / 76.6 | 77.4 / 77.4 | 79.0 / 78.1 | 78.8 / 78.1 |

| | Giả thuyết | Kết quả |
|---|---|---|
| H34 | AVEKB ≥ AVEK trên 7-Scenes | **Đúng** (+0.5 / +0.3) |
| H35 | AVEKB ≥ AVGGT + 0.5 trên 7-Scenes | **Đúng** (+1.2 / +1.2) |
| H36 | V\* giữ ≥ 70% mức cải thiện của AVEKB và nhanh ≥ 2.2× | **Đúng** (137%, 2.38×) |
| H37 | AVEKB > AVEK, 13 chuỗi, N=200 | **Đúng, sát ngưỡng** (p = 0.040) |
| H38 | trên 4 chuỗi TUM mới: AVEKB ≥ AVEK + 0.5, V\* giữ ≥ 70% | **Đúng** (+1.2; 83%) |
| H39 | gộp: AVEKB trên 17 chuỗi, V\* trên 11 chuỗi không dùng để chọn | **Đúng** (p = 0.013; p = 0.0015) |

Cần lưu ý:

- **Lỗi tổng hợp đã sửa.** Script tổng hợp ban đầu lấy khóa theo tên cảnh, làm hai cặp chuỗi cùng cảnh đè lên nhau.
  Với bản lỗi, H37 ra Sai; sau khi sửa thì ra Đúng. Vì vậy H37 nên đọc là sát ngưỡng.
- **Trên 7-Scenes, chênh lệch giữa các cấu hình phần lớn dưới 0.5 điểm.** Việc V\* hơn AVEKB ở đây có thể chỉ là nhiễu.
- **Dải đầy đủ có ích chủ yếu ở cảnh khó:** fr1_floor, office seq-04, các chuỗi quay nhiều. Trên các chuỗi này, khoảng
  cách tới VGGT vẫn còn.

### 0.4d Chẩn đoán khoảng cách trên chuỗi quay nhiều (2026-11-09)

Chi tiết ở [results/rotation_plan.md](../results/rotation_plan.md) và [results/diag_rotation.md](../results/diag_rotation.md).
Dữ liệu là 6 chuỗi TUM phát triển ở N=100 và 200. Tư thế từng frame được lưu bằng `--save-poses`, rồi phân tích bằng
[analysis/diag_rotation.py](../analysis/diag_rotation.py).

- **Lỗi chủ yếu đến từ nén lớp 9–23.** Chỉ nén lớp 9–23 thì mất −2.7 điểm, chỉ nén lớp 0–8 thì mất −1.1 điểm.
- **Mức mất tăng theo góc nhìn giữa hai frame.** Với AVEK, cặp lệch trên 90° mất 4.7 điểm, cặp lệch dưới 30° mất 1.9
  điểm.
- **Lỗi tập trung ở khoảng 10% frame**, đi thành đoạn liền nhau: 59–75% mức mất nằm ở các cặp chạm tới các frame này,
  so với 28–32% sau khi xáo trộn. Mức hỏng hầu như không tương quan với độ khó đối với VGGT, tốc độ quay hay góc tới
  keyframe gần nhất.
- **Oracle (kết quả âm).** Giữ nguyên đúng các frame hỏng, chọn bằng ground truth, chỉ lấy lại 35% phần mất. Thêm cùng
  số frame ngẫu nhiên cho kết quả tương đương. Vì vậy hướng "phát hiện rồi sửa frame hỏng" bị loại.
- **Quan sát mới.** Thêm 10% frame ngẫu nhiên làm keyframe giúp khoảng +1.1 điểm so với AVEK, ngang AVEKB-f16n3 với
  cùng chi phí. Trong khi đó, gấp đôi keyframe k-means thì không giúp. Quan sát này được kiểm chứng ở 0.4e.

### 0.4e Keyframe trải đều theo thời gian (2026-11-09)

Chi tiết ở [results/kfx_plan.md](../results/kfx_plan.md) và [results/aggregate_kfx.md](../results/aggregate_kfx.md). Code nằm ở
`keyframe_unif` / `kmeans` trong `configure`. Hàm `uniform_extra` chọn frame ở tâm m đoạn đều nhau, theo cách xác định.

- **Bước 1, chọn trên 6 chuỗi phát triển:**
  - AVEKU-u10 (AVEK + S/10 frame trải đều) được +0.75, AVU-u5 (bỏ k-means, S/5 frame trải đều) được +0.78. Chọn
    C\* = AVU-u5.
  - Bản kết hợp f16n3 + u10 chỉ hơn f16n3 +0.43, dưới ngưỡng +0.5, nên bị loại.
- **Bước 2, kiểm chứng trên 6 chuỗi TUM chưa dùng:** fr2_rpy, fr2_360_kidnap, fr2_pioneer_360, fr3_sitting_rpy,
  fr3_walking_halfsphere, cùng fr2_xyz làm đối chứng dễ.

  | N | VGGT | AVEK | AVEKB-f16n3 | **AVU-u5** | f16n3 + u10 (tham khảo) |
  |---|---|---|---|---|---|
  | 100 | 77.2 | 72.5 | 73.8 | **73.9** | 75.1 |
  | 200 | 75.6 (489 s) | 71.7 (169 s) | 72.7 (205 s) | **72.9** (201 s) | 73.5 (234 s) |

  - H40 đúng: AVU-u5 hơn AVEK +1.31.
  - H40w đúng: p = 0.031 ở N=200 trên 6 chuỗi.
  - H41 đúng: ngang f16n3 (+0.16) với cùng thời gian.
- **Đọc kết quả:**
  - Cùng S/5 frame giữ nguyên: chọn bằng k-means thì không giúp (mục 0.4), còn trải đều theo thời gian thì giúp.
  - AVU-u5 không chính xác hơn f16n3, chỉ đơn giản hơn.
  - Bản kết hợp f16n3 + u10 hơn f16n3 +1.06 trên 6 chuỗi mới (thắng 10/12 ô). Nhưng nó đã bị loại ở bước 1, nên đây
    chưa phải kết quả đã kiểm chứng.
  - Khoảng cách tới VGGT trên chuỗi quay nhiều vẫn còn khoảng 2.6–3.7 điểm.

### 0.4f Kiểm chứng riêng f16n3 + keyframe trải đều (2026-11-10)

Chi tiết ở [results/combo_plan.md](../results/combo_plan.md) và [results/aggregate_combo.md](../results/aggregate_combo.md).
Dữ liệu là 6 chuỗi TUM và 4 chuỗi 7-Scenes chưa từng chạy:

- TUM: fr3_walking_rpy, fr2_pioneer_slam, fr2_large_with_loop, fr3_nostr_tex_near_loop, fr3_teddy,
  fr2_desk_with_person;
- 7-Scenes: office seq-05/08, redkitchen seq-05/07.

| bộ | N | VGGT | AVEK | f16n3 | AVU-u5 | f16u10 |
|---|---|---|---|---|---|---|
| 6 TUM | 100 | 87.2 | 84.6 | 85.6 | 85.8 | **86.4** |
| 6 TUM | 200 | 86.6 (470 s) | 84.8 (164 s) | 85.7 (198 s) | 85.5 (196 s) | **86.0** (227 s) |
| 4 7-Scenes | 100 | 68.8 | 67.9 | 67.8 | 68.0 | **68.5** |
| 4 7-Scenes | 200 | 66.3 | 66.8 | 67.0 | **67.5** | 67.1 |

**Giả thuyết:**

- **H43 đúng, vừa đủ:** f16u10 − f16n3 = +0.54 trên TUM, thắng 11/12 ô.
- **H43w sai:** ở N=200, p = 0.11.
- **H44 đúng:** f16u10 không làm tệ đi trên 7-Scenes (+0.34).
- **H45 đúng:** AVU-u5 ngang f16n3 trên 7-Scenes (+0.30).
- **H46 sai:** gộp 10 chuỗi ở N=200 được +0.16, p = 0.12.

**Đọc kết quả:**

- f16u10 hơn f16n3 khoảng +0.8 ở N=100, nhưng gần như không hơn ở N=200, và chậm hơn khoảng 15%.
- AVU-u5 ngang f16n3 qua 3 lần đo độc lập.
- Ở N=200 trên 7-Scenes, VGGT thua mọi cấu hình nén. Nguyên nhân là riêng redkitchen seq-07, nơi VGGT chỉ được 61.5.

### 0.4g Chuỗi dài N=400 và 800 với keyframe trải đều (2026-11-10)

Chi tiết ở [results/longkf_plan.md](../results/longkf_plan.md) và [results/aggregate_longkf.md](../results/aggregate_longkf.md).

- **Dữ liệu:** 8 chuỗi TUM dài chưa từng chạy: fr3_sitting_xyz, fr3_structure_texture_near, fr3_large_cabinet,
  fr2_pioneer_slam2/3, fr2_flowerbouquet, fr2_coke, fr2_dishes.
- **Cách chạy:** Kaggle T4, `--lowmem`, 16 kernel trên 8 tài khoản.
- **Cấu hình mới AVU-c40:** frame 0 + 40 frame trải đều cố định với mọi N. Nó được thêm vì S/5 keyframe tăng theo N.

| N | VGGT | AVE | AVEK | f16n3 | AVU-u5 | f16u10 | AVU-c40 |
|---|---|---|---|---|---|---|---|
| 400 | 88.1 (1856 s) | 85.9 (4.3×) | 87.2 (3.3×) | 87.8 (2.6×) | 87.9 (2.7×) | **88.2** (2.2×) | 87.2 (3.3×) |
| 800 | 86.1 (7244 s) | 85.1 (5.0×) | 86.2 (3.6×) | 86.9 (2.8×) | 86.3 (2.8×) | **87.1** (2.3×) | 85.9 (4.2×) |

Các tỉ số trong ngoặc là tốc độ so với VGGT.

**Giả thuyết đúng:**

- **H49:** f16u10 không thua VGGT (+0.56), một phần nhờ VGGT tụt ở N=800.
- **H50a:** AVE nhanh hơn VGGT 4.98× ở N=800.

**Giả thuyết sai:**

- **H47 và H47w:** AVU-u5 − AVEK = +0.42 (+0.75 ở N=400, +0.10 ở N=800); p = 0.37.
- **H48:** f16u10 − f16n3 = +0.25.
- **H50b và H50c (đã dự đoán sai từ trước):** AVU-u5 chỉ 2.78×, f16u10 chỉ 2.32×.
- **H51:** AVU-c40 nhanh hơn AVU-u5 (0.66× thời gian) nhưng kém −0.60.
- **H52:** AVU-c40 hơn AVE +1.07, thắng 15/16 ô, nhưng tốn 1.19× thời gian, quá ngưỡng 1.15×.

**Đọc kết quả:**

- **VGGT gốc tụt ở N=800** trên fr2_dishes (94.6 → 89.3), fr2_pioneer_slam3 (74.9 → 63.0) và fr2_coke. Các bản nén giữ
  ổn định trên các chuỗi này.
  - Ngược lại, trên fr2_pioneer_slam2, VGGT tăng lên 72.8, còn mọi bản nén ở 61–65.
  - Vì vậy, các so sánh với VGGT ở N=800 có phương sai lớn.
  - Theo quy tắc ghi trước, bản chọn cho chuỗi dài là AVE (AVE − VGGT = −0.995), nhưng nó chỉ vừa lọt ngưỡng nhờ VGGT
    tụt.
- **Đổi tốc độ lấy độ chính xác theo một đường đều:** AVE (5.0×) → AVU-c40 (4.2×) → AVEK (3.6×) → f16n3 (2.8×) →
  f16u10 (2.3×). Không cấu hình nào nằm hẳn phía trên đường này.
- **k-means đẩy bộ nhớ đỉnh lên 13.64 GB ở N=800**, so với 7.4–7.8 GB khi không dùng k-means. T4 chỉ có khoảng 15 GB.
  Bước `select_keyframes` giải thích được khoảng 3.9 GB trong mức chênh này.

### 0.4 Hướng đã thử và loại

Tất cả trên dữ liệu phát triển, office seq-06 ở N=100, trừ khi ghi khác.

- **Độ phân giải theo lân cận cho từng query** (mỗi frame xem đủ độ phân giải các frame giống nó nhất): AUC sụp từ 72
  xuống 33–58. Khi các frame nhìn những tập key khác nhau, chúng mất hệ quy chiếu chung. Keyframe dùng chung cho mọi query
  thì không gặp vấn đề này.
- **Keyframe k-means:** giúp trên stairs và heads ở dữ liệu phát triển (+0.7 đến +1.7). Nhưng trên 11 chuỗi mới, nó không
  hơn AVE mà chậm hơn khoảng 25%. Bản kết hợp với lưới σ=9 (AVEK-s9e36k10) khớp quá mức với office seq-06.
- **Lưới lệch pha theo frame** (không tốn thêm token): +2.7 trên office seq-06, không giúp trên stairs và heads.
- **Giảm query** (global attention chỉ tính trên lưới query thưa, token khác dùng lại kết quả trong ô 2×2): AUC sụp
  xuống 22–43, kể cả khi đường chéo được tính riêng cho từng token. Chỉ 7 lớp cuối chịu được, nên tăng tốc không đáng kể.
- **Nén mạnh hơn ở các lớp cuối 17–23**, trên 4 chuỗi phát triển ở N=100, chạy trên máy với forward ít bộ nhớ:

  | Biến thể | office-06 | chess-05 | stairs-01 | heads-01 | Thời gian |
  |---|---|---|---|---|---|
  | AVE-s4e36 | 72.0 | 89.5 | 85.2 | 91.7 | 33–34 s |
  | Lưới 4×4 ở lớp 17–23 | 72.8 | 87.9 | 84.0 | 89.1 | 30–31 s |
  | Lưới 6×6 ở lớp 17–23 | 73.2 | 86.6 | 82.1 | 87.8 | 30 s |
  | Lưới 4×4 từ lớp 13 | 72.5 | 87.5 | 79.6 | 87.2 | 29–30 s |
  | Lớp 17–23 thành frame attention | 56.4 | 76.0 | 50.8 | 79.2 | 29 s |

  Chỉ nhanh hơn khoảng 10%, nhưng tụt 1–5 điểm trên 3/4 chuỗi; bỏ hẳn global ở các lớp cuối thì sụp. Các lớp cuối vẫn
  cần thông tin giữa các frame ở độ phân giải đủ. Hướng này không được đưa đi kiểm chứng.

- **Chọn keyframe theo độ phủ** (farthest-point trên đặc trưng DINO): độ phủ góc nhìn đo bằng ground truth không tốt hơn
  k-means; tệ hơn trên fr3_long_office. Gấp đôi số keyframe (S//5) cũng không giúp. Dừng mà không tốn GPU. Về sau,
  S//5 keyframe trải đều theo thời gian thì lại giúp (0.4e).
- **Lưới thích ứng theo nội dung** (mỗi ô 2×2 giữ patch được token camera chú ý nhiều nhất, hoặc patch có key mạnh nhất,
  thay vì patch góc): kém hơn lưới cố định 3–5 điểm trên fr1_360 và fr1_room. Kernel dừng sớm.

### 0.5 Giới hạn

- Chỉ có dữ liệu trong nhà (7-Scenes, TUM). Chuỗi dài chạy trên 6 chuỗi 7-Scenes và 8 chuỗi TUM. VGGT full ở N=800 chạy
  trên 9 chuỗi, mỗi chuỗi khoảng 2 giờ T4, và tự nó không ổn định ở N=800 (0.4g).
- Mức tăng tốc trên T4 (không có FlashAttention) thấp hơn số AVGGT báo trên A100.
- Lợi thế của AVE so với AVGGT nhỏ trên chuỗi thường (+0.2 đến +0.5). Nó lớn hơn chủ yếu trên vài chuỗi khó.
- Ở N=800, các tầng trung gian chiếm khoảng 13.6 GB RAM CPU. Kaggle đủ, nhưng máy 16 GB RAM thì không.

## 1. Phương pháp (giai đoạn 1)

**Tối ưu chính xác** — đầu ra giống hệt hoặc sai khác ~1e-4. Code ở [tfvggt/core.py](../src/tfvggt/core.py).

| Tối ưu | Tác dụng |
|---|---|
| DPT head chạy theo khối 2 frame (gốc: 8) | Bỏ được một nút thắt mà trước đó chưa ai để ý: ở 50 frame, depth head chiếm 36% thời gian |
| Lưu output trung gian 4 lớp ở bf16 (gốc: fp32) | Giảm khoảng 15 MB mỗi frame |
| Tạo q/k/v theo từng khúc, ghi thẳng vào buffer fp16 | Không còn tensor fp32 tạm của LayerNorm/RoPE cho toàn bộ token. Ở N=100, bộ nhớ đỉnh giảm từ 8.52 GB xuống 7.47 GB |
| MLP và DINO chạy theo khúc | Giảm bộ nhớ tạm trong mỗi block |

**Global attention xấp xỉ**, áp dụng cho mọi lớp global:

- **Nén K/V theo frame.** Query giữ đủ độ phân giải. K/V của mỗi frame được lấy mẫu nearest với hệ số r, nên r=2 giữ
  252/1036 patch và r=3 giữ 108/1036 patch. Các token camera và register được giữ nguyên.
- **Keyframe đủ độ phân giải.** Đây là cơ chế có sẵn của FlashVGGT, nhưng trong bài gốc nó chỉ được dùng kèm fine-tune.
  - **Cách chọn:** chia các frame thành S // 10 cụm bằng k-means trên token DINO trung bình của mỗi frame. Frame gần tâm
    mỗi cụm, cùng với frame 0, được giữ K/V đủ độ phân giải.
  - **Vì sao cần:** chẩn đoán ở mục 3.3 cho thấy đây là thứ còn thiếu khi không fine-tune.
- **Bù khối lượng** (đã thử và loại bỏ, xem mục 3.4).
  - **Ý tưởng:** cộng `log(số token mà key nén đại diện)` vào logit của key đó, để phần attention mỗi frame nhận được
    khớp với full attention.
  - **Cách cài:** bias được nhét vào một chiều phụ của head, nên vẫn dùng được kernel memory-efficient.

Tên cấu hình:

| Tên | Ý nghĩa |
|---|---|
| `B1` | VGGT full + tối ưu chính xác |
| `E1-all` | Nén r=3 |
| `E1-all-r2` | Nén r=2 |
| `E2-*` | Nén + bù khối lượng |
| `K-r2k10`, `K-r3k10` | Nén r=2 hoặc r=3 + keyframe k-means |
| `Ref-flash` | FlashVGGT đã fine-tune: mốc tham chiếu, cần 4×H800 khoảng 16 giờ để train |

## 2. Thiết lập

- **Dữ liệu:** 7-Scenes, chia thành ba bộ chuỗi không trùng nhau, tổng 20 chuỗi. Với mỗi chuỗi, lấy N frame cách đều
  trên toàn chuỗi, ảnh 518×392.

  | Bộ | Chuỗi |
  |---|---|
  | A | Chuỗi test đầu tiên của mỗi cảnh (7) |
  | B | Chuỗi held-out: chuỗi test thứ hai, riêng heads lấy chuỗi train seq-02 (7) |
  | C | Chuỗi tiếp theo chưa dùng; heads đã hết chuỗi (6) |

- **Metric:**
  - pose AUC@30 trên các cặp frame tương đối;
  - ATE sau căn chỉnh Sim3;
  - depth AbsRel sau chuẩn hóa median;
  - Chamfer sau Sim3, đơn vị mét;
  - `fid_pose`: AUC@30 khi lấy chính output của VGGT full làm "ground truth", để đo mức bám sát mô hình gốc.
- **Phần cứng:**
  - Kaggle Tesla T4 16 GB, fp16. Mọi số thời gian đều lấy từ đây.
  - Bộ C ở N ≤ 100 chạy trên RTX 4060 8 GB, bf16. B1 ở hai môi trường lệch nhau ≤ 0.3 AUC trên cả 18 cặp chuỗi×N đã so.
- **Giả thuyết ghi trước khi chạy:** [results/heldout_plan.md](../results/heldout_plan.md) và
  [results/set2_plan.md](../results/set2_plan.md).

## 3. Kết quả

### 3.1 Bảng chính — 20 chuỗi

Δ là AUC@30 của cấu hình trừ AUC@30 của B1 trên cùng chuỗi. Cột "≤2" là số chuỗi cách B1 không quá 2 điểm. Tốc độ là
thời gian của B1 chia cho thời gian của cấu hình, đo trên T4.

| N | Cấu hình | AUC@30 | Δ trung bình | Δ tệ nhất | ≤2 | Tốc độ |
|---|---|---|---|---|---|---|
| 25 | B1 | 82.1 | — | — | — | 14 s |
| | E1-all-r2 | 80.5 | −1.6 | −6.0 | 16/20 | 1.4× |
| | **K-r2k10** | 80.8 | −1.3 | −8.6 | 15/20 | 1.4× |
| | E2-all (bù) | 77.0 | −5.1 | **−30.5** | 10/20 | 1.4× |
| | Ref FlashVGGT | 81.4 | −0.7 | −13.0 | 15/20 | 1.6× |
| 50 | B1 | 81.7 | — | — | — | 40 s |
| | E1-all-r2 | 80.4 | −1.2 | −5.8 | 16/20 | 1.7× |
| | **K-r2k10** | 80.9 | −0.8 | −3.7 | 17/20 | 1.7× |
| | E2-all-r2 (bù) | 81.0 | −0.7 | −5.1 | 18/20 | 1.5× |
| | Ref FlashVGGT | 81.5 | −0.2 | −8.9 | 17/20 | 2.2× |
| 100 | B1 | 81.3 | — | — | — | 137 s |
| | E1-all | 78.9 | −2.4 | −12.8 | 9/20 | 3.1× |
| | **K-r2k10** | 80.9 | −0.4 | **−1.8** | **20/20** | 2.2× |
| | K-r3k10 | 80.4 | −0.9 | −2.9 | 15/20 | 2.7× |
| | E2-all (bù) | 80.8 | −0.5 | −4.2 | 18/20 | 2.7× |
| | Ref FlashVGGT | 81.4 | +0.0 | −9.3 | 17/20 | 3.5× |
| 200 | B1 | 80.8 | — | — | — | 453 s |
| | E1-all | 79.1 | −1.7 | −8.6 | 10/20 | 4.4× |
| | **K-r2k10** | 80.6 | −0.2 | **−1.1** | **20/20** | 2.4× |
| | K-r3k10 | 80.3 | −0.5 | −3.1 | 17/20 | 3.3× |
| | E2-all (bù) | 79.9 | −0.9 | **−16.3** | 18/20 | 3.5× |
| | Ref FlashVGGT | 81.4 | +0.6 | −5.8 | 17/20 | 5.5× |

- **Chamfer:** mọi cấu hình K có Chamfer 0.041–0.042, còn B1 là 0.043–0.044. Nén không làm hỏng tái tạo 3D.
- **Bám sát VGGT gốc:** `fid_pose` của K-r2k10 đạt 95–97, còn Ref FlashVGGT chỉ khoảng 89. Bản fine-tune cho kết quả
  khác hẳn VGGT gốc, dù AUC so với ground truth tương đương.
- **Bảng đầy đủ:** chạy `python analysis/aggregate.py`, kết quả đã lưu ở [results/aggregate20.md](../results/aggregate20.md).

### 3.2 Phần nào được kiểm chứng sạch

Cấu hình K-r2k10 được chọn sau khi chạy thử trên hai chuỗi của bộ B (office seq-06 và chess seq-05), ở N=25 và 50. Các
dữ liệu không được nhìn tới khi chọn cấu hình là bộ A, toàn bộ bộ C, và bộ B ở N=100 và N=200. Bảng dưới chỉ tính 13 chuỗi
của bộ A và bộ C:

| N | Δ trung bình | Δ tệ nhất | ≤2 |
|---|---|---|---|
| 25 | −0.9 | −3.4 | 10/13 |
| 50 | −0.8 | −3.7 | 11/13 |
| 100 | −0.4 | −1.5 | 13/13 |
| 200 | −0.2 | −1.1 | 13/13 |

### 3.3 Chẩn đoán: vì sao nén không train lại hỏng

Có một chuỗi mà mọi cấu hình nén đều hỏng: office seq-06 trong bộ B. Script chẩn đoán là
[analysis/diag_office.py](../analysis/diag_office.py), kết quả lưu ở `results/diag/`. Ba phát hiện:

- **Cờ `dedup` không phải nguyên nhân.** Bật hay tắt `dedup` cho kết quả gần như nhau.
- **Các frame hỏng đều quay 105–151° so với frame 0.** Camera đi vòng rồi nhìn ngược lại, nên các frame này không có vùng
  chung với frame 0, trong khi frame 0 là keyframe đủ độ phân giải duy nhất. Chúng chỉ có thể định vị qua các frame lân
  cận, mà các frame đó đều đã bị nén. Đây là lỗi phủ, không phải lỗi của attention nói chung.
- **Thêm keyframe theo cụm hình ảnh sửa được lỗi này.** Keyframe k-means tự rơi vào đoạn camera quay ngược lại.

Kết quả trên office seq-06 theo N = 25 / 50 / 100 / 200:

| Cấu hình | AUC@30 |
|---|---|
| B1 | 74.6 / 72.7 / 72.9 / 72.7 |
| E1-all | 53.7 / 54.1 / 60.1 / 64.1 |
| E2-all | 44.0 / 60.2 / 71.3 / 56.4 |
| **K-r2k10** | 66.0 / 69.6 / 71.2 / 71.8 |

### 3.4 Kết quả âm: bù khối lượng

- **Trên các chuỗi dễ, phép bù giúp ích.** Nó tăng `fid_pose` trung bình và có lúc cứu được một chuỗi.
- **Nhưng nó có rủi ro đuôi nặng.** Trên office seq-06, AUC dao động không đơn điệu theo N, sụp còn 44.0 ở N=25 và 56.4
  ở N=200. Với r=2 thì vẫn có lúc sụp: góc lệch lớn nhất lên tới 124°.
- **Nó cũng có hại** khi r=4, khi áp lên checkpoint FlashVGGT đã fine-tune, và khi dùng layout của FlashVGGT.
- **Chi phí:** chậm hơn nén thường 5–25%.
- **Giả thuyết về nguyên nhân** (chưa kiểm chứng): với nearest sampling, mỗi key nén chỉ là một token thật. Nhân trọng
  số của nó lên r² lần có thể khuếch đại những match sai ở các head khớp theo vị trí.

### 3.5 Tối ưu chính xác trên RTX 4060 Laptop 8 GB

Đo với VGGT full, cảnh garden ở độ phân giải 518×336.

| N | Gốc | Sau tối ưu | Sai khác đầu ra |
|---|---|---|---|
| 50 | 23.4 s, 5.64 GB | 16.6 s, 4.97 GB | depth 7e-5 |
| 75 | 171 s (tràn VRAM sang RAM) | 31.7 s, 6.14 GB | depth 7e-5 |

Khi đã tối ưu, máy 8 GB chạy được 100 frame 7-Scenes. Trên T4, N=200 trước đây bị OOM, giờ chạy với 11.3 GB.

## 4. Khuyến nghị (không train)

**Cập nhật giai đoạn 2.**

| Trường hợp | Dùng | Ghi chú |
|---|---|---|
| Cần sát VGGT, chấp nhận chậm hơn AVEK | `AVEKB-f16n3` | Trên 11 chuỗi kiểm chứng (7-Scenes và TUM), ngang VGGT ở N=200, nhanh hơn VGGT 2.4×. Trên các chuỗi TUM quay nhiều, vẫn cách VGGT khoảng 1.7 điểm. |
| Cần sát VGGT nhất, nhất là N ≤ 100 | `AVEKBU-f16u10` | Hơn `AVEKB-f16n3` +0.8 ở N=100, thắng 6/6 chuỗi TUM mới. Ở N=200 chỉ hơn +0.2 đến +0.3, không có ý nghĩa thống kê. Nhanh hơn VGGT 2.1×. |
| Giống `AVEKB-f16n3`, đơn giản hơn (không k-means, không dải) | `AVU-u5` | Ngang `AVEKB-f16n3` qua 3 lần đo: 2 bộ TUM mới và 7-Scenes, chênh từ −0.01 đến +0.30. Nhanh hơn VGGT 2.4×. |
| Giống trên, dải rộng hơn | `AVEKB-s4e36k10f14` | Chính xác tương đương `AVEKB-f16n3` nhưng chậm hơn, nhanh hơn VGGT chỉ 2.1×. |
| Mặc định, cần bền trên nhiều loại cảnh | `AVEK-s4e36k10` | Thắng AVGGT trên 51/57 cặp (chuỗi, N) của 7-Scenes và TUM. Nhanh hơn VGGT 2.7–2.9× ở N=200. |
| Cảnh kiểu 7-Scenes, cần nhanh hơn | `AVE-s4e36` | Nhanh hơn VGGT 1.9× ở N=50, 2.5× ở N=100, 3.6× ở N=200 và 4.4–4.9× ở N=400–800. Trên TUM không hơn AVGGT. |
| N ≥ 250 trên T4, hoặc N ≥ 150 trên GPU 8 GB | Thêm `--lowmem` | Kết quả như forward chuẩn. |
| N = 400–800, cần nhanh nhất | `AVE-s4e36` | 4.3× ở N=400, 5.0× ở N=800. Kém VGGT 2.2 điểm ở N=400 và 1.0 ở N=800, nhưng thua tới 11.8 điểm trên một chuỗi robot (8 chuỗi TUM). |
| N = 400–800, cân bằng | `AVU-c40` | Hơn AVE +1.07, thắng 15/16 ô, ở 3.3–4.2×. Ngang AVEK mà nhanh hơn và tốn bằng nửa bộ nhớ GPU. Chưa qua ngưỡng chi phí ghi trước (1.19× so với 1.15× thời gian AVE). |
| N = 400–800, cần sát VGGT nhất | `AVEKBU-f16u10` hoặc `AVEKB-f16n3` | Ngang hoặc hơn VGGT trung bình, 2.2–2.8×. Cần khoảng 13.6 GB GPU ở N=800 vì k-means. |
| Cần bền nhất ở N ≤ 200, chấp nhận chậm hơn | `K-r2k10` | Tụt tệ nhất nhỏ nhất, nhưng chậm hơn AVE khoảng 1.45×. |
| N ≤ 25 | `AVE-s4e36` | Chưa kiểm chứng trên Kaggle; trên dữ liệu phát triển cách VGGT ≤ 1 điểm. |

Bảng dưới đây là khuyến nghị của giai đoạn 1, giữ lại để đối chiếu.

| N | Dùng | Tốc độ trên T4 | AUC so với VGGT full |
|---|---|---|---|
| ≤ 25 | `E1-all-r2` hoặc `K-r2k10` | 1.4× | −1.3 đến −1.6 trung bình |
| 50 | `K-r2k10` | 1.7× | −0.8 trung bình, tệ nhất −3.7 |
| 100 | `K-r2k10` | 2.2× | −0.4 trung bình, 20/20 chuỗi trong 2 điểm |
| 200 | `K-r2k10` | 2.4× | −0.2 trung bình, 20/20 chuỗi trong 2 điểm |
| 200, cần nhanh hơn | `K-r3k10` | 3.3× | −0.5 trung bình, tệ nhất −3.1 |

- **Chuỗi ngắn (N ≤ 25):** tốc độ chỉ tăng 1.4×, và cả hai cấu hình đều có chuỗi tụt 6–9 điểm.
- **Khi được fine-tune:** FlashVGGT vẫn nhanh nhất (5.5× ở N=200). Đổi lại, nó cho kết quả khác VGGT gốc, `fid_pose`
  chỉ khoảng 89, và có chuỗi tụt tới 9 điểm.

## 5. Giới hạn

- Chỉ có 20 chuỗi, tất cả từ một bộ dữ liệu trong nhà. Chưa kiểm tra trên CO3D, ScanNet hay cảnh ngoài trời.
- Chỉ kiểm tra `keyframe_every=10`. Các giá trị khác chưa được quét, để tránh lại thành chỉnh tham số trên chính dữ liệu đánh giá.
- Ở N=100 và N=200, `E1-all-r2` và `E2-all-r2` chỉ có số liệu trên bộ C (6 chuỗi).
- Trên Windows, PyTorch không có FlashAttention, nên tốc độ trên GPU cục bộ khác với T4.

## 6. Chạy lại và cấu trúc mã nguồn

Cách cài đặt, chạy trên Kaggle hoặc máy local, và cấu trúc thư mục: xem [README.md](../README.md).
Bảng tổng hợp và kiểm tra giả thuyết của từng vòng: các script trong [analysis/](../analysis/), kết quả thô trong [results/](../results/).
