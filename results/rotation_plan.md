# Khoảng cách tới VGGT trên chuỗi quay nhiều: chẩn đoán (ghi trước khi chạy, 2026-11-09)

Sau [narrow_plan.md](narrow_plan.md), AVEKB-f16n3 đã ngang VGGT trên 11 chuỗi kiểm chứng, nhưng trên các chuỗi TUM quay
nhiều vẫn cách VGGT 1.5–1.8 điểm AUC@30. Vòng này là chẩn đoán: chưa có phương pháp mới, chỉ đo xem lỗi nằm ở đâu.

## Dữ liệu và cấu hình

- **Chuỗi:** fr1_360, fr1_room, fr1_rpy, fr1_plant, fr1_teddy, fr2_360_hemisphere (đều đã dùng trước đây, nên ở đây
  là dữ liệu phát triển). N=100 và 200.
- **Cấu hình:**

  | tên | mô tả |
  |---|---|
  | B1 | VGGT đầy đủ |
  | AV-s4 | AVGGT dựng lại |
  | AVEK-s4e36k10 | AVEK |
  | AVEKB-f16n3 | bản khuyến nghị hiện tại |
  | ABL-e36-Lfull | lớp 0–8 lưới 6×6, lớp 9–23 đầy đủ: cận trên khi chỉ nén lớp đầu |
  | ABL-Efull-s4k10 | lớp 0–8 đầy đủ, lớp 9–23 như AVEK: cận trên khi chỉ nén lớp sau |

- **Lưu thêm:** tư thế dự đoán của từng frame (`--save-poses`), để phân tích cục bộ.

## Câu hỏi và cách đo

| | câu hỏi | cách đo |
|---|---|---|
| D1 | Lỗi đến từ lớp đầu (lưới 6×6) hay từ lớp sau? | khoảng cách tới B1 của ABL-e36-Lfull so với ABL-Efull-s4k10 |
| D2 | Lỗi tập trung ở cặp frame có góc nhìn khác nhau nhiều không? | sai số cặp (max của sai số quay và sai số hướng dịch chuyển, như AUC@30), chia theo góc quay GT giữa hai frame: < 30°, 30–90°, > 90° |
| D3 | Lỗi nằm ở vài frame hỏng hay là trôi đều? | sai số quay của từng frame so với GT sau khi căn theo frame 0. Đo phần mất mát AUC đến từ 10% frame tệ nhất (bỏ các cặp có frame đó rồi tính lại) |
| D4 | Frame hỏng có liên quan tới keyframe không? | khoảng cách từ frame hỏng tới keyframe k-means gần nhất, so với frame bình thường |

Kết quả chẩn đoán sẽ quyết định hướng sửa. Mọi hướng sửa sau đó phải có giả thuyết ghi trước, và được kiểm chứng trên
chuỗi chưa dùng.

## Bổ sung (ghi trước khi chạy): thí nghiệm oracle

Chẩn đoán sơ bộ trên 5 chuỗi (fr1_360, fr1_room, fr1_rpy, fr1_plant, rồi fr1_teddy và fr2_360_hemisphere khi có) cho
thấy lỗi tập trung:

- Với các cấu hình nén, 74–82% mức mất AUC so với B1 nằm ở các cặp chạm tới 10% frame tệ nhất. Nếu xáo trộn mức mất
  giữa các cặp thì con số này chỉ khoảng 32%.
- Các frame hỏng gần như trùng nhau giữa những cấu hình dùng cùng tập keyframe k-means (Jaccard 0.5–1.0, ngẫu nhiên chỉ
  khoảng 0.05). Với AVGGT, vốn không có keyframe, thì trùng ít hơn trên fr1_360 và fr1_room.
- Mức hỏng tương quan yếu với góc quay tới keyframe gần nhất (Spearman khoảng +0.15). Nó gần như không tương quan với
  độ khó của frame đối với B1, hay với tốc độ quay.

Câu hỏi: nếu biết đúng frame nào sẽ hỏng và giữ nguyên (không nén) các frame đó như keyframe, thì sửa được bao nhiêu?
Nếu oracle cũng không sửa được, hướng "phát hiện rồi sửa" bị loại mà không cần tìm cách phát hiện.

- **AVEK-oracle:** keyframe của AVEK, cộng thêm S/10 frame có mức mất lớn nhất dưới AVEK (chọn bằng ground truth, bỏ
  các frame đã là keyframe).
- **AVEK-rand:** keyframe của AVEK, cộng thêm S/10 frame ngẫu nhiên (seed 0, cũng bỏ keyframe). Đây là đối chứng cho việc
  chỉ đơn giản tăng số keyframe.
- **Dữ liệu:** 6 chuỗi ở trên, N=100 và 200. Danh sách frame nằm trong `scripts/oracle_keyframes.json`, tạo bằng
  `analysis/make_oracle.py`.

| | nội dung | ngưỡng |
|---|---|---|
| O1 | oracle sửa được phần lớn lỗi | trên các ô mà AVEK mất ít nhất 1 điểm so với B1, AVEK-oracle lấy lại trung bình ít nhất 50% phần mất |
| O2 | chọn đúng frame quan trọng hơn chỉ tăng số keyframe | trung bình AVEK-oracle − AVEK-rand ≥ +1.0 trên các ô đó |

- O1 và O2 cùng đúng: bước tiếp theo là tìm cách phát hiện frame hỏng không cần ground truth.
- O1 sai: dừng hướng giữ nguyên frame hỏng.
- O1 đúng nhưng O2 sai: chỉ cần nhiều keyframe hơn, nhưng k5 trước đây đã không hơn k10, nên cần xem lại.

## Kết quả

`python analysis/diag_rotation.py`, bảng đầy đủ ở [diag_rotation.md](diag_rotation.md). Có 6 chuỗi × N=100, 200, tổng
12 ô. AUC tính lại từ tư thế đã lưu khớp với AUC của kernel ở cả 72/72 ô.

**D1: lỗi đến từ lớp nào.** Mức tụt AUC@30 so với B1, trung bình 12 ô:

| AVGGT | AVEK | AVEKB-f16n3 | chỉ nén lớp 0–8 | chỉ nén lớp 9–23 (có keyframe) |
|---|---|---|---|---|
| −5.0 | −3.1 | −2.0 | −1.1 | −2.7 |

Phần lớn lỗi đến từ việc nén lớp 9–23. Lưới 6×6 ở lớp 0–8 chỉ tốn khoảng 1 điểm.

**D2: lỗi theo góc nhìn.** Mức mất của mỗi cặp frame tăng theo góc quay GT giữa hai frame. Với AVEK, cặp lệch dưới 30°
mất +1.9, cặp lệch 30–90° mất +2.3, cặp lệch trên 90° mất +4.7. Riêng khi chỉ nén lớp 0–8 thì mức mất phẳng, khoảng
+1.0, không phụ thuộc góc.

**D3: lỗi tập trung ở vài frame.** 59–75% mức mất nằm ở các cặp chạm tới 10% frame tệ nhất. Nếu xáo trộn mức mất giữa
các cặp thì con số này chỉ 28–32%. Frame hỏng đi thành từng đoạn liền nhau, và gần như trùng nhau giữa các cấu hình dùng
chung tập keyframe.

**D4 và D3b: tương quan đều yếu.** Mức hỏng của frame có Spearman khoảng +0.1 với góc quay tới keyframe gần nhất, và
khoảng 0 với độ khó của frame đối với B1 hay với tốc độ quay. Keyframe ở đây được tính lại trên máy cục bộ (chỉ chạy
patch embedding, fp16), nên có thể lệch nhẹ so với keyframe trên T4.

**Oracle (O1, O2): cả hai sai.** Xét 11 ô mà AVEK mất ít nhất 1 điểm:

- Thêm đúng 10% frame hỏng nhất làm keyframe chỉ lấy lại trung bình 35% phần mất.
- Thêm 10% frame ngẫu nhiên cho kết quả tương đương (oracle − ngẫu nhiên = −0.09).
- **Kết luận theo quy tắc ghi trước:** dừng hướng "phát hiện frame hỏng rồi giữ nguyên frame đó".

**Quan sát ngoài dự kiến (chưa kiểm chứng, sinh ra từ dữ liệu phát triển).**

- Thêm 10% frame ngẫu nhiên làm keyframe giúp trung bình +1.1 điểm so với AVEK trên 12 ô (−2.1 so với −3.1, tính theo
  mức tụt so với B1). Mức này ngang AVEKB-f16n3 (−2.0), với chi phí tương tự (khoảng +25 s ở N=200).
- Trước đây, gấp đôi số keyframe k-means (k5) không giúp. Trên fr1_360 và fr1_room, k5 kém tập "k10 + ngẫu nhiên"
  khoảng 1.5 điểm.
- Giả thuyết cho vòng sau: keyframe k-means (frame gần tâm cụm) thiếu đa dạng, nên thêm frame trải đều theo thời gian
  sẽ giúp. Thêm nữa, cách này có thể cộng dồn với dải 16–18.
