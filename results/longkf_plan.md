# Keyframe trải đều trên chuỗi dài N=400 và 800 (ghi trước khi chạy, 2026-11-10)

Tiếp nối [combo_plan.md](combo_plan.md) và [longseq_plan.md](longseq_plan.md).

**Bối cảnh.** Đến nay, keyframe trải đều (AVU-u5, f16u10) chỉ được kiểm ở N ≤ 200. Chuỗi dài lại là nơi tăng tốc có giá
trị nhất. Vòng chuỗi dài trước (7-Scenes, chỉ AV-s4, AVE-s4e36 và B1) đo được AVE nhanh hơn B1 4.39× ở N=400 và 4.89× ở
N=800 (một chuỗi).

**Vấn đề chi phí dự kiến.** AVU-u5 giữ nguyên S/5 frame, nên số frame nguyên tăng theo N.

- Ở N=800, nó giữ 160 frame nguyên, khoảng 167k key, cộng khoảng 206k key của lưới 2×2.
- B1 có khoảng 833k key, nên ở các lớp 9–23, AVU-u5 chỉ nén khoảng 2.2×.
- Dự đoán: tốc độ của AVU-u5 và f16u10 so với B1 ở N=800 thấp hơn rõ so với AVE.

Vì vậy, vòng này thêm một biến thể có số keyframe cố định:

- **AVU-c40:** frame 0 + 40 frame trải đều, với mọi N. Ở N=200, nó trùng với AVU-u5.
- Code: `keyframe_count` trong `configure` ([src/tfvggt/core.py](../src/tfvggt/core.py)).
- Biến thể này được định nghĩa trước khi chạy và không chỉnh theo kết quả.

**Kiểm tra code trên máy** (office seq-06 ở N=50, chỉ kiểm tính đúng, không dùng để chọn): forward ít bộ nhớ khớp forward
chuẩn với AVU-c40 (AUC 72.38 so với 72.41) và f16u10 (74.27 so với 74.21). Độ lệch depth tương đối dưới 1e-3.

## Dữ liệu (chưa từng chạy)

8 chuỗi TUM dài, chọn theo mô tả của TUM, trước mọi lần chạy:

| chuỗi | chuyển động |
|---|---|
| fr3_sitting_xyz | cầm tay, tịnh tiến, có người ngồi |
| fr3_structure_texture_near | cầm tay, gần, nhiều cấu trúc |
| fr3_large_cabinet | đi vòng quanh tủ lớn |
| fr2_pioneer_slam2 | robot, nhiều vòng quay |
| fr2_flowerbouquet | cầm tay, quanh một vật |
| fr2_large_no_loop | cầm tay, quãng đường dài |
| fr2_coke | cầm tay, quanh một vật |
| fr2_dishes | cầm tay, quanh bàn |

- **Dự phòng**, dùng theo thứ tự: fr2_pioneer_slam3, fr3_structure_notexture_near, fr2_metallic_sphere2. Một chuỗi bị thay
  chỉ khi nó có dưới 800 frame khớp ground truth, hoặc không tải được.
- **Số frame:** N=400 và 800, lấy đều theo thời gian như mọi vòng trước. Tổng cộng 8 chuỗi × 2 N = 16 ô.
- **Phần cứng:** Kaggle T4, `--lowmem` cho mọi cấu hình. Forward chuẩn hết bộ nhớ từ N≈250.

**Thay chuỗi theo quy tắc** (ghi sau khi tải, trước mọi lần chạy):

- fr2_large_no_loop chỉ có 654/3359 frame khớp ground truth, nên được thay bằng chuỗi dự phòng đầu tiên là
  fr2_pioneer_slam3 (2248 frame).
- Các chuỗi còn lại có từ 979 đến 3007 frame.

| split | chuỗi | tài khoản |
|---|---|---|
| `tumo` | fr3_sitting_xyz, fr3_str_tex_near | hpthai, ngvtvi |
| `tump` | fr3_large_cabinet, fr2_pioneer_slam2 | tvtrong, phngkhai |
| `tumq` | fr2_flowerbouquet, fr2_pioneer_slam3 | ngantoan, hcttoan |
| `tumr` | fr2_coke, fr2_dishes | liuwinter, ngthhoai |

## Cấu hình

B1, AVE-s4e36, AVEK-s4e36k10, AVEKB-f16n3, AVU-u5, AVEKBU-f16u10, AVU-c40. Định nghĩa nằm trong
[src/tfvggt/configs.py](../src/tfvggt/configs.py).

## Giả thuyết

| | nội dung | ngưỡng |
|---|---|---|
| H47 | keyframe trải đều vẫn giúp ở chuỗi dài | trung bình AVU-u5 − AVEK ≥ +0.5 trên 16 ô |
| H47w | như trên, kiểm định | N=800, 8 chuỗi, Wilcoxon một phía p < 0.05 |
| H48 | bản kết hợp vẫn cộng thêm ở chuỗi dài | trung bình f16u10 − f16n3 ≥ +0.5 trên 16 ô (cùng ngưỡng H43) |
| H49 | f16u10 sát VGGT ở chuỗi dài | trung bình f16u10 − B1 ≥ −1.0 trên 16 ô |
| H50a | tăng tốc của AVE được lặp lại | thời gian B1 / thời gian AVE ≥ 4.5×, trung bình trên 8 chuỗi ở N=800 |
| H50b | AVU-u5 vẫn nhanh ở N=800 | thời gian B1 / AVU-u5 ≥ 3.0× ở N=800 |
| H50c | f16u10 vẫn nhanh ở N=800 | thời gian B1 / f16u10 ≥ 2.5× ở N=800 |
| H51 | số keyframe cố định giữ được độ chính xác mà rẻ hơn | trung bình AVU-c40 − AVU-u5 ≥ −0.3 trên 16 ô, **và** thời gian AVU-c40 ≤ 0.8 × AVU-u5 ở N=800 |
| H52 | AVU-c40 hơn AVE với chi phí gần như nhau | trung bình AVU-c40 − AVE ≥ +0.5 trên 16 ô, **và** thời gian AVU-c40 ≤ 1.15 × AVE ở N=800 |

Các ngưỡng tốc độ được tính bằng thời gian trung bình (trên 8 chuỗi), không phải trung bình của các tỉ lệ.

**Dự đoán của tôi trước khi chạy:**

- H50b và H50c có khả năng sai, vì số frame nguyên tăng theo N.
- H48 có khả năng sai: ở N=200, mức cộng thêm đã giảm còn +0.27.

**Quyết định theo kết quả:**

- Bản khuyến nghị cho N ≥ 400 là cấu hình **nhanh nhất** có AUC@30 trung bình ở N=800 không thấp hơn B1 quá 1.0 điểm. Nếu
  không cấu hình nào đạt, báo cấu hình có AUC cao nhất kèm tốc độ.
- H51 đúng: dùng số keyframe cố định (c40) thay S/5 cho chuỗi dài.
- H47 sai: keyframe trải đều chỉ được khuyến nghị cho N ≤ 200.

**Thống kê.** Wilcoxon chỉ chạy cho H47w. Báo kèm hiệu chỉnh Holm, gộp với ba kiểm định của hai vòng trước (H40w, H43w,
H46). Các giả thuyết còn lại là ngưỡng hiệu ứng.

## Cách chạy

- Mỗi chuỗi chạy trên một tài khoản, gồm hai kernel nối tiếp:
  1. N=400, đủ 7 cấu hình.
  2. N=800, đủ 7 cấu hình.
- Kernel nào bị lỗi hoặc bị khởi động lại thì chạy lại y nguyên.
- Kết quả nằm ở `results/kaggle/lkf*`. Lệnh tổng hợp: `analysis/aggregate_longkf.py`.

## Kết quả

Lệnh: `cd analysis && python aggregate_longkf.py`. Bảng từng chuỗi ở [aggregate_longkf.md](aggregate_longkf.md). Cả 16
kernel chạy hết, không kernel nào phải khởi động lại.

AUC@30 trung bình trên 8 chuỗi:

| N | B1 | AVE | AVEK | f16n3 | AVU-u5 | f16u10 | AVU-c40 |
|---|---|---|---|---|---|---|---|
| 400 | 88.1 | 85.9 | 87.2 | 87.8 | 87.9 | **88.2** | 87.2 |
| 800 | 86.1 | 85.1 | 86.2 | 86.9 | 86.3 | **87.1** | 85.9 |

Thời gian, tốc độ so với B1 và bộ nhớ đỉnh ở N=800 (T4, `--lowmem`):

| | B1 | AVE | AVEK | f16n3 | AVU-u5 | f16u10 | AVU-c40 |
|---|---|---|---|---|---|---|---|
| thời gian | 7244 s | 1455 s | 2007 s | 2596 s | 2603 s | 3124 s | 1726 s |
| tốc độ | 1× | **4.98×** | 3.61× | 2.79× | 2.78× | 2.32× | 4.20× |
| bộ nhớ đỉnh | 9.66 GB | 7.41 GB | 13.64 GB | 13.64 GB | 7.79 GB | 13.64 GB | 7.44 GB |

Ở N=400, tốc độ so với B1 là: AVE 4.34×, AVEK 3.33×, AVU-c40 3.34×, AVU-u5 2.67×, f16n3 2.63×, f16u10 2.24×.

| | kết quả |
|---|---|
| H47 | **Sai.** AVU-u5 − AVEK = +0.42 trên 16 ô, thắng 13/16. Mức này gồm +0.75 ở N=400 và chỉ +0.10 ở N=800 |
| H47w | **Sai.** N=800: −0.0, −0.7, +0.4, +1.0, −1.1, +0.2, +0.6, +0.6; p = 0.37 |
| H48 | **Sai.** f16u10 − f16n3 = +0.25, thắng 13/16 |
| H49 | **Đúng.** f16u10 − B1 = +0.56. Kết quả này nhờ một phần vào việc B1 tụt ở N=800 (xem dưới) |
| H50a | **Đúng.** AVE nhanh hơn B1 4.98× ở N=800, lặp lại mức 4.89× của vòng chuỗi dài trước |
| H50b | **Sai, như dự đoán.** AVU-u5 chỉ 2.78× |
| H50c | **Sai, như dự đoán.** f16u10 chỉ 2.32× |
| H51 | **Sai.** AVU-c40 rẻ hơn AVU-u5 rõ (0.66× thời gian), nhưng kém hơn −0.60 |
| H52 | **Sai về chi phí.** AVU-c40 − AVE = +1.07, thắng 15/16 ô, nhưng thời gian bằng 1.19× AVE (ngưỡng 1.15×) |

**Bản chọn cho chuỗi dài theo quy tắc ghi trước:** AVE-s4e36. Nó là cấu hình nhanh nhất có AUC ở N=800 không thấp hơn B1
quá 1.0, với AVE − B1 = −0.995, tức chỉ vừa lọt ngưỡng. Kết quả này phải đọc kèm hai lưu ý ngay dưới đây.

**Holm** trên 4 kiểm định của ba vòng keyframe trải đều: H40w 0.031 → 0.125, H43w 0.11 → 0.33, H46 0.12 → 0.33,
H47w 0.37 → 0.37. Không kiểm định nào có ý nghĩa.

### Đọc kết quả

**1. VGGT gốc tự tụt ở N=800 trên 3/8 chuỗi, còn các bản nén thì ổn định.**

| chuỗi | B1 N=400 → N=800 | f16u10 N=400 → N=800 |
|---|---|---|
| fr2_dishes | 94.6 → 89.3 | 96.7 → 94.3 |
| fr2_pioneer_slam3 | 74.9 → 63.0 | 75.2 → 72.0 |
| fr2_coke | 94.6 → 92.6 | 95.3 → 94.5 |

- Ngược lại, trên fr2_pioneer_slam2, B1 tăng từ 66.4 lên 72.8, còn mọi bản nén ở 61–65. Ở đây AVE thua B1 tới 11.8 điểm.
- Hệ quả: trung bình của B1 ở N=800 bị kéo xuống, nên các phép so với B1 ở N=800 (H49, quy tắc chọn) có phương sai lớn.
  AVE "lọt ngưỡng" chủ yếu vì B1 tụt trên dishes và pioneer_slam3.
- Trên 5 chuỗi B1 không tụt, AVE thua B1 từ 1.0 đến 11.8 điểm. f16n3 và f16u10 nằm trong khoảng ±1.2 so với B1 trên
  4 chuỗi, nhưng thua khoảng 8 điểm trên pioneer_slam2.
- Quan sát "nén như một dạng điều chuẩn ở chuỗi dài" đã thấy ở vòng trước (office, stairs) nay xuất hiện thêm trên 3 chuỗi
  TUM. Tuy vậy, đây là quan sát sau khi chạy, chưa phải kết luận.

**2. Keyframe trải đều giúp ở N=400 nhưng gần như hết tác dụng ở N=800.**

- AVU-u5 − AVEK: +0.75 ở N=400 (thắng 8/8), +0.10 ở N=800 (thắng 5/8).
- Đồng thời, AVU-u5 mất lợi thế chi phí: 2.78× ở N=800, so với 3.61× của AVEK.
- Với 160 frame nguyên, AVU-u5 vẫn không hơn 80 keyframe k-means. Giả thuyết "thiếu đa dạng thời gian" giải thích được kết
  quả ở N ≤ 400, nhưng không còn đủ ở N=800.

**3. AVU-c40 là điểm giữa đáng chú ý, dù không qua ngưỡng ghi trước.**

- Nó hơn AVE +1.07, thắng 15/16 ô, với 4.2× so với B1 (AVE là 5.0×).
- Nó ngang AVEK về độ chính xác (−0.3 ở N=800) nhưng nhanh hơn 1.16× và tốn bằng nửa bộ nhớ đỉnh.
- H52 trượt ở điều kiện chi phí (1.19× so với ngưỡng 1.15×). Kết quả âm này được giữ nguyên, không nới ngưỡng.

**4. k-means tốn bộ nhớ ở N=800.**

- Mọi cấu hình dùng k-means đạt đỉnh 13.64 GB, so với 7.4–7.8 GB của các bản không dùng, sát giới hạn 15 GB của T4.
- Đo riêng trên máy, bước `select_keyframes` cần thêm khoảng 1.2× bộ đệm token, tức khoảng 3.9 GB ở N=800. Con số này
  giải thích một phần mức chênh 6.2 GB. Phần còn lại chưa tìm ra nguyên nhân.
- Đây là một lý do thực tế để dùng keyframe trải đều (không k-means) cho N ≥ 800.

**5. Về tốc độ.** AVE lặp lại 4.9–5.0× ở N=800. Mức 8× đặt ra từ đầu vẫn chưa đạt. Mọi cách thêm frame nguyên đều đổi
tốc độ lấy độ chính xác theo một đường khá đều:

| cấu hình | tốc độ ở N=800 | AUC ở N=800 |
|---|---|---|
| AVE | 5.0× | 85.1 |
| AVU-c40 | 4.2× | 85.9 |
| AVEK | 3.6× | 86.2 |
| f16n3 | 2.8× | 86.9 |
| f16u10 | 2.3× | 87.1 |

Không cấu hình nào nằm hẳn phía trên đường này.

**Ghi chú phụ.** f16u10 trên fr3_large_cabinet ở N=400 có ATE 0.133, so với khoảng 0.03 của các cấu hình khác, trong khi
AUC vẫn ngang (94.4). Có thể là một ngoại lệ khi căn chỉnh scale. Không ảnh hưởng tới các giả thuyết.
