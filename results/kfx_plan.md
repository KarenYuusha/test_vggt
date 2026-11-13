# Keyframe trải đều theo thời gian (ghi trước khi chạy, 2026-11-09)

Tiếp nối [rotation_plan.md](rotation_plan.md). Thí nghiệm oracle cho một quan sát ngoài dự kiến: thêm 10% frame
**ngẫu nhiên** làm keyframe giúp AVEK khoảng +1.1 điểm AUC@30 trên 6 chuỗi TUM quay nhiều, ngang AVEKB-f16n3. Trước đó,
gấp đôi số keyframe k-means (k5) thì không giúp gì.

**Giả thuyết:** keyframe k-means (frame gần tâm cụm đặc trưng) thiếu đa dạng về thời gian và góc nhìn. Thêm frame trải đều
theo thời gian sẽ giúp, kể cả khi cộng thêm dải đầy đủ 16–18.

Kiểm tra nhanh trên máy (30 frame đầu fr1_360, chỉ để kiểm code, không dùng để chọn): k-means chọn frame 0, 22, 23, 25. Ba
keyframe k-means dồn vào một đoạn ngắn, khớp với giả thuyết.

## Biến thể

Code: `keyframe_unif` / `kmeans` trong `configure` ([src/tfvggt/core.py](../src/tfvggt/core.py)) và hàm `uniform_extra`.

- `uniform_extra` lấy m frame ở tâm của m đoạn đều nhau.
- Nếu một vị trí đã là keyframe, nó dời sang frame trống gần nhất.
- Cách chọn là xác định, không ngẫu nhiên.

| tên | mô tả | số frame giữ nguyên |
|---|---|---|
| AVEKU-u10 | AVEK + S/10 frame trải đều | frame 0 + S/10 k-means + S/10 đều |
| AVU-u5 | bỏ k-means: frame 0 + S/5 frame trải đều | frame 0 + S/5 đều (cùng số lượng với AVEKU-u10) |
| AVEKBU-f16u10 | AVEKB-f16n3 + S/10 frame trải đều | như AVEKU-u10, thêm attention đầy đủ ở lớp 16–18 |

AVU-u5 trả lời câu hỏi phụ: k-means có cần không, hay chỉ cần keyframe trải đều?

## Bước 1: chọn trên dữ liệu phát triển

- **Dữ liệu:** 6 chuỗi của rotation_plan (fr1_360, fr1_room, fr1_rpy, fr1_plant, fr1_teddy, fr2_360_hemisphere), N=100
  và 200, tổng 12 ô.
- **Kết quả đã có:** B1, AVEK, AVEKB-f16n3 (thư mục `rot*`) và AVEK-rand (thư mục `orc*`). Mọi kết quả đều chạy trên
  T4, không dùng `--lowmem`.
- **Lưu ý:** dữ liệu này chính là nơi quan sát "ngẫu nhiên giúp" xuất hiện. Vì vậy bước 1 chỉ dùng để chọn, không phải
  bằng chứng.

**Quy tắc chọn:**

- **C\* (bản rẻ):** trong AVEKU-u10 và AVU-u5, chọn bản có gain so với AVEK lớn hơn, trung bình trên 12 ô. Bản đó phải
  đạt gain ≥ +0.5. Nếu không bản nào đạt, không có C\*.
- **Bản kết hợp:** AVEKBU-f16u10 được giữ nếu gain(f16u10) − gain(f16n3) ≥ +0.5 trên 12 ô. Nếu không, bỏ.

## Bước 2: kiểm chứng trên 6 chuỗi TUM chưa từng chạy

- **Chuỗi:**
  - fr2_rpy, fr2_360_kidnap, fr2_pioneer_360, fr3_sitting_rpy, fr3_walking_halfsphere: quay nhiều theo mô tả của TUM.
  - fr2_xyz: chủ yếu tịnh tiến, dùng làm đối chứng dễ.
- Các chuỗi được chọn theo mô tả chuyển động, trước khi có bất kỳ lần chạy nào. Chúng nằm ở các split `tumi`, `tumj`,
  `tumk`.
- **Cấu hình:** B1, AVEK, AVEKB-f16n3, AVEKU-u10, AVU-u5, AVEKBU-f16u10, ở N=100 và 200. Cả ba biến thể đều được chạy để
  tiết kiệm một vòng GPU, nhưng việc chọn chỉ dựa trên bước 1. Kết quả của bản không được chọn chỉ để tham khảo.

| | nội dung | ngưỡng |
|---|---|---|
| H40 | C\* hơn AVEK | trung bình C\* − AVEK ≥ +0.5 trên 12 ô |
| H40w | như trên, kiểm định | N=200, 6 chuỗi, Wilcoxon một phía p < 0.05 (với 6 chuỗi, p nhỏ nhất có thể đạt là 0.016) |
| H41 | C\* ít nhất ngang bản khuyến nghị hiện tại, với chi phí tương đương | trung bình C\* − f16n3 ≥ 0 trên 12 ô, và thời gian N=200 của C\* ≤ 1.05 × thời gian của f16n3 |
| H42 | keyframe trải đều cộng dồn được với dải 16–18 | chỉ khi giữ bản kết hợp: trung bình f16u10 − f16n3 ≥ +0.5 trên 12 ô |

- H40 hoặc H42 sai: báo kết quả âm, và bản khuyến nghị vẫn là AVEKB-f16n3.
- H42 đúng: f16u10 trở thành bản khuyến nghị cho chuỗi khó, kèm chi phí đo được.
- H41 đúng: C\* là một lựa chọn rẻ tương đương f16n3.

Giữa H40, H41 và H42 không hiệu chỉnh kiểm định nhiều lần. Chỉ H40w là kiểm định thống kê; các giả thuyết còn lại là
ngưỡng hiệu ứng.

## Kết quả bước 1 (ghi trước khi có kết quả kiểm chứng)

Lệnh: `python analysis/aggregate_kfx.py`. Dữ liệu là 6 chuỗi × N=100, 200, tổng 12 ô.

| cấu hình | gain so với AVEK | thời gian N=200 |
|---|---|---|
| AVEKB-f16n3 | +1.12 | 193 s |
| AVEK-rand (đối chứng ngẫu nhiên, seed 0) | +1.03 | 189 s |
| AVEKU-u10 | +0.75 | 200 s |
| **AVU-u5** | **+0.78** | 201 s |
| AVEKBU-f16u10 | +1.55 | 236 s |

- **C\* = AVU-u5.** Nó hơn AVEKU-u10 chỉ 0.03 điểm, nên thực chất hai bản ngang nhau. Bỏ hẳn k-means, chỉ giữ frame
  trải đều, cho kết quả như AVEK + frame trải đều.
- **Bản kết hợp bị loại:** gain(f16u10) − gain(f16n3) = +0.43, dưới ngưỡng +0.5. H42 vì vậy không được kiểm. Kết quả
  kiểm chứng của f16u10 chỉ để tham khảo.
- **Đọc sơ bộ:**
  - Trên dữ liệu phát triển, frame trải đều (+0.75) giúp ít hơn frame ngẫu nhiên (+1.03). Vậy quan sát "ngẫu nhiên giúp"
    không được giải thích hoàn toàn bằng việc trải đều theo thời gian.
  - Một phần chênh lệch có thể là do chọn trên chính dữ liệu đã sinh ra quan sát đó.
  - Lý do để vẫn tiếp tục bước 2: các frame cụ thể của bản ngẫu nhiên không mang sang chuỗi khác được, còn cách trải
    đều thì có thể dùng cho mọi chuỗi.

## Kết quả bước 2: 6 chuỗi TUM chưa dùng

Bảng đầy đủ ở [aggregate_kfx.md](aggregate_kfx.md). Bảng dưới là AUC@30 trung bình trên 6 chuỗi, kèm thời gian chạy.

| N | VGGT | AVEK | AVEKB-f16n3 | AVEKU-u10 | **C\* = AVU-u5** | AVEKBU-f16u10 (tham khảo) |
|---|---|---|---|---|---|---|
| 100 | 77.2 (132 s) | 72.5 (60 s) | 73.8 (68 s) | 74.5 (67 s) | **73.9** (67 s) | 75.1 (74 s) |
| 200 | 75.6 (489 s) | 71.7 (169 s) | 72.7 (205 s) | 72.7 (201 s) | **72.9** (201 s) | 73.5 (234 s) |

Ở N=200, tốc độ so với VGGT như sau:

| AVEK | f16n3 | AVU-u5 | AVEKU-u10 | f16u10 |
|---|---|---|---|---|
| 2.90× | 2.39× | 2.43× | 2.44× | 2.09× |

| | kết quả |
|---|---|
| H40 | **Đúng.** AVU-u5 − AVEK = +1.31 trên 12 ô |
| H40w | **Đúng, sát ngưỡng.** N=200: +1.27, thắng 5/6 chuỗi, p = 0.031 |
| H41 | **Đúng.** AVU-u5 − f16n3 = +0.16, thời gian bằng 0.98× của f16n3 |
| H42 | Không kiểm (bản kết hợp bị loại ở bước 1) |

### Đọc kết quả

**AVU-u5 ngang AVEKB-f16n3, không hơn.**

- So với f16n3, nó hơn +0.16 nhưng chỉ thắng 4/12 ô.
- Mức hơn AVEK ở N=100 chủ yếu nhờ fr2_pioneer_360 (+6.9). Ở N=200, kết quả đều hơn: 5/6 chuỗi, từ +0.4 đến +3.6.
- Điểm mạnh của AVU-u5 là đơn giản hơn: không cần k-means, không cần dải đầy đủ, và cùng chi phí.

**Keyframe trải đều có tác dụng, keyframe k-means thêm thì không.**

- Trước đây, gấp đôi số keyframe k-means (S/5) không giúp (mục 0.4 của README). Cùng số frame đó mà trải đều theo thời
  gian (AVU-u5) thì giúp +1.3.
- Điều này ủng hộ giả thuyết "k-means thiếu đa dạng": k-means có xu hướng chọn các frame gần nhau, như ví dụ 22, 23, 25 ở
  phần mở đầu.

**Bản kết hợp f16u10 có vẻ tốt hơn trên dữ liệu chưa dùng, nhưng không được tính là đã kiểm chứng.**

- Trên 6 chuỗi mới, nó hơn f16n3 +1.06, thắng 10/12 ô. Đây là bản duy nhất rút khoảng cách tới VGGT trên 5 chuỗi quay
  nhiều xuống còn −2.6 điểm (f16n3 −3.9, AVU-u5 −3.7).
- Tuy vậy, theo quy tắc ghi trước, nó đã bị loại ở bước 1 (+0.43 < +0.5). Kết quả ở đây chỉ là tham khảo, và cần một
  vòng kiểm chứng mới có ghi trước trên dữ liệu khác.

**Giới hạn.**

- Chỉ có 6 chuỗi kiểm chứng. p = 0.031 gần mức nhỏ nhất có thể đạt được với n=6.
- Không hiệu chỉnh kiểm định nhiều lần giữa các vòng.
- fr2_xyz (đối chứng dễ): mọi cấu hình nén đều ngang VGGT (97.0–97.3 so với 96.5–96.8), nên không có dấu hiệu làm tệ
  đi.
