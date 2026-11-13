# Kiểm chứng riêng bản kết hợp dải 16–18 + keyframe trải đều (ghi trước khi chạy, 2026-11-09)

Tiếp nối [kfx_plan.md](kfx_plan.md).

**Bối cảnh.** Bản kết hợp AVEKBU-f16u10 (AVEKB-f16n3 + S/10 frame trải đều theo thời gian) bị loại ở bước 1 vòng trước.
Lý do là trên dữ liệu phát triển nó chỉ hơn f16n3 +0.43, dưới ngưỡng +0.5. Tuy vậy, trên 6 chuỗi kiểm chứng của vòng
trước, nó hơn f16n3 +1.06 và thắng 10/12 ô. Các chuỗi đó vì vậy giờ đã "dùng rồi" đối với bản này: chúng là lý do mở vòng
này, nên không được dùng làm bằng chứng nữa.

Vòng này kiểm chứng f16u10 **đúng như đã định nghĩa**, không đổi tham số, trên dữ liệu hoàn toàn mới. Đồng thời, vòng
này cho AVU-u5 chạy lần đầu trên 7-Scenes.

## Dữ liệu (chưa từng chạy)

**6 chuỗi TUM**, chọn theo mô tả chuyển động của TUM trước khi chạy:

| chuỗi | chuyển động |
|---|---|
| fr3_walking_rpy | quay tại chỗ, có người đi lại |
| fr2_pioneer_slam | robot, nhiều vòng quay |
| fr2_large_with_loop | cầm tay, vòng lớn |
| fr3_nostructure_texture_near_withloop | vòng gần mặt phẳng có texture |
| fr3_teddy | đi vòng quanh vật |
| fr2_desk_with_person | đối chứng dễ hơn |

Các chuỗi này nằm ở split `tuml`, `tumm`, `tumn`.

**4 chuỗi 7-Scenes**, là các chuỗi tiếp theo theo thứ tự test-rồi-train, chỉ office và redkitchen còn chuỗi chưa dùng:

- set7: office và redkitchen ở vị trí thứ 8;
- set8: office và redkitchen ở vị trí thứ 9.

Các chuỗi này nằm ở split `s7a`, `s7b` (private).

**Số frame:** N=100 và 200.

## Cấu hình

B1, AVEK-s4e36k10, AVEKB-f16n3, AVU-u5, AVEKBU-f16u10. Định nghĩa không đổi so với
[src/tfvggt/configs.py](../src/tfvggt/configs.py).

## Giả thuyết

| | nội dung | ngưỡng |
|---|---|---|
| H43 | f16u10 hơn f16n3 trên TUM mới | trung bình f16u10 − f16n3 ≥ +0.5 trên 12 ô TUM |
| H43w | như trên, kiểm định | N=200, 6 chuỗi TUM, Wilcoxon một phía p < 0.05 |
| H44 | f16u10 không làm tệ đi trên 7-Scenes | trung bình f16u10 − f16n3 ≥ −0.3 trên 8 ô 7-Scenes |
| H45 | AVU-u5 vẫn ngang f16n3 trên 7-Scenes | trung bình AVU-u5 − f16n3 ≥ −0.5 trên 8 ô 7-Scenes |
| H46 | gộp 10 chuỗi mới, N=200 | f16u10 > f16n3, Wilcoxon một phía p < 0.05 |

**Quyết định theo kết quả:**

- H43 và H44 cùng đúng: f16u10 trở thành bản khuyến nghị khi cần sát VGGT. Chi phí phải được báo kèm (vòng trước đo
  được 2.1× so với VGGT, f16n3 là 2.4×).
- H43 sai: báo kết quả âm. Mức +1.06 của vòng trước được xem là ăn may hoặc do chọn dữ liệu.
- H45 sai: AVU-u5 chỉ được khuyến nghị cho chuỗi quay nhiều.

H43w, H46 và H40w (vòng trước) không được hiệu chỉnh kiểm định nhiều lần; số liệu sẽ được báo kèm hiệu chỉnh Holm.

## Kết quả

Lệnh: `python analysis/aggregate_combo.py`. Bảng đầy đủ ở [aggregate_combo.md](aggregate_combo.md).

**Ghi chú dữ liệu.** fr2_large_with_loop chỉ có ground truth cho 1268/5182 frame, vì hệ mocap mất dấu ở vòng lớn. Các
frame được lấy mẫu vì vậy có khoảng trống thời gian.

AUC@30 trung bình, kèm thời gian ở N=200:

| bộ | N | VGGT | AVEK | f16n3 | AVU-u5 | f16u10 |
|---|---|---|---|---|---|---|
| 6 TUM mới | 100 | 87.2 | 84.6 | 85.6 | 85.8 | **86.4** |
| 6 TUM mới | 200 | 86.6 (470 s) | 84.8 (164 s) | 85.7 (198 s) | 85.5 (196 s) | **86.0** (227 s) |
| 4 7-Scenes mới | 100 | 68.8 | 67.9 | 67.8 | 68.0 | **68.5** |
| 4 7-Scenes mới | 200 | 66.3 (496 s) | 66.8 (168 s) | 67.0 (205 s) | **67.5** (202 s) | 67.1 (235 s) |

Tốc độ so với VGGT ở N=200:

| bộ | AVEK | f16n3 | AVU-u5 | f16u10 |
|---|---|---|---|---|
| TUM | 2.87× | 2.37× | 2.40× | 2.07× |
| 7-Scenes | 2.96× | 2.42× | 2.46× | 2.11× |

| | kết quả |
|---|---|
| H43 | **Đúng, vừa đủ.** f16u10 − f16n3 = +0.54 trên 12 ô TUM, thắng 11/12. Mức này gồm +0.81 ở N=100 và +0.27 ở N=200 |
| H43w | **Sai.** N=200: +0.1, +0.3, +0.7, −0.3, +0.3, +0.5; p = 0.11 |
| H44 | **Đúng.** f16u10 − f16n3 = +0.34 trên 7-Scenes |
| H45 | **Đúng.** AVU-u5 − f16n3 = +0.30 trên 7-Scenes |
| H46 | **Sai.** Gộp 10 chuỗi, N=200: +0.16, thắng 8/10, p = 0.12 |

**Hiệu chỉnh Holm** trên 3 kiểm định của hai vòng keyframe trải đều:

| kiểm định | p gốc | p sau Holm |
|---|---|---|
| H40w | 0.031 | 0.094 |
| H43w | 0.11 | 0.22 |
| H46 | 0.12 | 0.22 |

Không kiểm định nào còn dưới 0.05.

### Đọc kết quả

**f16u10.**

- Theo quy tắc ghi trước, H43 và H44 cùng đúng, nên f16u10 trở thành bản khuyến nghị khi cần sát VGGT nhất.
- Mức cải thiện là thật nhưng nhỏ, và chủ yếu ở N=100:
  - N=100: thắng 6/6 chuỗi TUM, +0.8.
  - N=200: chỉ +0.2 đến +0.3, không có ý nghĩa thống kê.
- Đổi lại, nó chậm hơn f16n3 khoảng 15% (2.1× so với 2.4× khi so với VGGT).
- Trên 6 chuỗi TUM mới, f16u10 cách VGGT 0.8 điểm ở N=100 và 0.6 điểm ở N=200.

**AVU-u5 ngang f16n3 ở cả ba lần đo:** TUM vòng trước +0.16, TUM vòng này −0.01, 7-Scenes +0.30. Nó luôn hơn AVEK:
+1.3, +0.9 và +0.35.

- Tốc độ bằng f16n3 nhưng cách làm đơn giản hơn, nên là lựa chọn rẻ tương đương.
- Tuy vậy, sau Holm, mức hơn AVEK chưa có ý nghĩa thống kê. Kết luận an toàn là AVU-u5 ít nhất ngang f16n3.

**7-Scenes.** Ở N=200, mọi cấu hình nén đều hơn VGGT. Lý do là redkitchen seq-07, nơi VGGT chỉ được 61.5 còn các cấu hình
nén được 66–67. Đây không phải dấu hiệu nén tốt hơn nói chung.
