# Dải đầy đủ rẻ hơn và kiểm chứng AVEKB trên 7-Scenes chưa dùng (ghi trước khi chạy, 2026-11-09)

Tiếp nối [band_plan.md](band_plan.md). AVEKB (AVEK + attention đầy đủ ở lớp global 14–18) lấy lại được khoảng một nửa
khoảng cách tới VGGT trên 6 chuỗi TUM mới, nhưng chỉ nhanh hơn VGGT 2.0× ở N=200, trong khi AVGGT nhanh hơn 3.4×. Vòng này
có hai câu hỏi:

1. Có bản dải nào rẻ hơn mà vẫn giữ phần lớn mức cải thiện không?
2. AVEKB có đứng vững trên 7-Scenes chưa dùng không? Đây là cảnh dễ hơn, nên cần kiểm tra AVEKB không làm tệ đi, đồng
   thời có thêm số chuỗi để kiểm định thống kê.

## Biến thể (đều là AVEK cộng một dải, cùng code `full_layers` / `band_sub` trong `src/tfvggt/core.py`)

| tên | dải |
|---|---|
| AVEKB-f15n3 | đầy đủ ở lớp 15–17 |
| AVEKB-f14n3 | đầy đủ ở lớp 14–16 |
| AVEKB-f16n3 | đầy đủ ở lớp 16–18 |
| AVEKB-g12 | lớp 14–18 dùng lưới 1×2 (giữ nửa số patch key) thay cho đầy đủ |

## Bước 1: chọn biến thể trên dữ liệu phát triển

- **Dữ liệu:** 6 chuỗi TUM trong `vald`/`vale`/`valf` (fr1_rpy, fr2_desk, fr1_plant, fr3_sitting_halfsphere, fr1_teddy,
  fr2_360_hemisphere), ở N=100 và 200, tổng cộng 12 ô. AVEK và AVEKB dùng lại kết quả đã có của các chuỗi này.
- **gain(V):** trung bình trên 12 ô của AUC@30(V) − AUC@30(AVEK).
- **cost(V):** thời gian trung bình ở N=200 của V trừ đi của AVEK.
- **Quy tắc chọn:** V\* là biến thể có cost nhỏ nhất trong số các biến thể thỏa gain(V) ≥ 0.7 · gain(AVEKB). Nếu
  hòa, lấy biến thể có gain lớn hơn. Nếu không biến thể nào đạt ngưỡng, không có V\*: kết quả là âm, và AVEKB vẫn là bản
  khuyến nghị.

## Bước 2: kiểm chứng trên 7 chuỗi 7-Scenes chưa từng chạy

- **Dữ liệu:** set5 (chess seq-06, office seq-03, pumpkin seq-08, redkitchen seq-01, stairs seq-06) và set6 (office
  seq-04, redkitchen seq-02).
- **Cấu hình:** B1, AV-s4, AVEK, AVEKB và cả 4 biến thể, ở N=100 và 200. Cả 4 biến thể được chạy luôn để tiết kiệm một
  vòng GPU, nhưng việc chọn V\* chỉ dựa trên bước 1. Kết quả 7-Scenes của các biến thể không phải V\* chỉ ghi để tham
  khảo, không dùng để chọn.

## Giả thuyết

| | nội dung | ngưỡng |
|---|---|---|
| H34 | AVEKB không làm tệ đi trên 7-Scenes | trung bình AVEKB − AVEK ≥ 0 ở cả N=100 và N=200 |
| H35 | AVEKB hơn AVGGT trên 7-Scenes | trung bình AVEKB − AV-s4 ≥ +0.5 ở cả hai N |
| H36 | V\* giữ được mức cải thiện trên 7-Scenes và đủ nhanh | gain(V\*) ≥ 0.7 · gain(AVEKB), tính gộp cả hai N, và V\* nhanh hơn B1 ít nhất 2.2× ở N=200 |
| H37 | gộp 13 chuỗi chưa dùng (6 TUM mới và 7 chuỗi 7-Scenes), N=200 | AVEKB > AVEK với Wilcoxon một phía p < 0.05 |

H36 chỉ áp dụng khi có V\*. Nếu gain(AVEKB) trên 7-Scenes ≤ 0 thì tỉ lệ ở H36 không có nghĩa, và sẽ được báo như vậy.

## Lưu ý trước

7-Scenes gần bão hòa: AUC@30 thường trên 85, nên chênh lệch giữa các cấu hình sẽ nhỏ. H34 vì vậy chủ yếu kiểm tra việc
không làm tệ đi.

## Kết quả bước 1 (ghi trước khi có đủ kết quả 7-Scenes)

`python analysis/aggregate_narrow.py`, dữ liệu phát triển gồm 6 chuỗi TUM × 2 giá trị N, tổng 12 ô:

| cấu hình | gain so với AVEK | thời gian N=200 | cost so với AVEK |
|---|---|---|---|
| AVEKB (14–18 đầy đủ) | +1.15 | 230 s | +55 s |
| AVEKB-f15n3 | +0.48 | 199 s | +24 s |
| AVEKB-f14n3 | +0.36 | 200 s | +25 s |
| **AVEKB-f16n3** | **+1.01** | 199 s | +24 s |
| AVEKB-g12 | +0.68 | 184 s | +9 s |

- Ngưỡng là 0.7 × 1.15 = 0.80. Chỉ f16n3 vượt ngưỡng, nên **V\* = AVEKB-f16n3**. Nó giữ 88% mức cải thiện với chưa
  tới một nửa chi phí dải.
- Phần lớn tác dụng nằm ở các lớp 16–18. Hai dải 3 lớp lệch về phía 14 thì kém hẳn.
- Khi quy tắc được áp dụng, tôi đã thấy vài dòng 7-Scenes đầu tiên (chess, pumpkin ở N=100) trong log. Quy tắc chọn
  hoàn toàn cơ học và chỉ dùng dữ liệu phát triển, nên những dòng đó không ảnh hưởng tới việc chọn.

## Bổ sung (ghi trước khi chạy): 4 chuỗi TUM mới

Hai tài khoản rảnh sau bước 1 được dùng để chạy thêm 4 chuỗi TUM chưa từng chạy: fr1_desk2 và fr1_floor (split `tumg`),
fr1_xyz và fr3_cabinet (split `tumh`). Mỗi chuỗi chạy B1, AV-s4, AVEK, AVEKB và V\* = AVEKB-f16n3, ở N=100 và 200.

| | nội dung | ngưỡng |
|---|---|---|
| H38a | AVEKB hơn AVEK trên 4 chuỗi này | trung bình AVEKB − AVEK ≥ +0.5, gộp cả hai N |
| H38b | V\* giữ được mức cải thiện trên 4 chuỗi này | gain(V\*) ≥ 0.7 · gain(AVEKB), gộp cả hai N |
| H39 | gộp tất cả chuỗi chưa dùng (6 TUM vòng trước, 7 chuỗi 7-Scenes, 4 TUM này), N=200 | AVEKB > AVEK và V\* > AVEK, mỗi cặp Wilcoxon một phía p < 0.05 |

H37 vẫn giữ nguyên như đã ghi (13 chuỗi). H39 là kiểm định thêm, không thay thế H37.

## Kết quả bước 2 và phần bổ sung

`python analysis/aggregate_narrow.py`, bảng đầy đủ ở [aggregate_narrow.md](aggregate_narrow.md).

**Lỗi tổng hợp đã sửa trước khi đọc kết quả.** Bản đầu của script lấy khóa theo tên cảnh. Vì vậy office seq-03/seq-04
và redkitchen seq-01/seq-02 đè lên nhau: chỉ còn 5 trong 7 chuỗi, và H37 lúc đó ra Sai (p = 0.051 trên 11 chuỗi). Đã
sửa sang khóa `cảnh/chuỗi`. Mọi số dưới đây dùng đủ 7 chuỗi như đã ghi trước. Kết luận của H37 đổi theo lần sửa này,
nên H37 cần được đọc là sát ngưỡng.

**7-Scenes, 7 chuỗi chưa dùng.** AUC@30 trung bình (thời gian):

| N | VGGT | AVGGT | AVEK | AVEKB | **V\* = AVEKB-f16n3** |
|---|---|---|---|---|---|
| 100 | 79.1 (128 s) | 78.2 (49 s) | 78.9 (58 s) | 79.4 (71 s) | **79.4** (65 s) |
| 200 | 78.2 (472 s) | 77.5 (126 s) | 78.4 (164 s) | 78.7 (222 s) | **79.0** (199 s) |

**4 chuỗi TUM mới** (fr1_desk2, fr1_floor, fr1_xyz, fr3_cabinet):

| N | VGGT | AVGGT | AVEK | AVEKB | V\* |
|---|---|---|---|---|---|
| 100 | 85.3 (133 s) | 85.0 (51 s) | 84.3 (60 s) | 85.9 (74 s) | 85.5 (69 s) |
| 200 | 85.1 (514 s) | 84.2 (132 s) | 84.0 (171 s) | 84.9 (236 s) | 84.9 (209 s) |

| | kết quả |
|---|---|
| H34 | **Đúng.** AVEKB − AVEK = +0.53 / +0.27, thắng 6/7 và 5/7 chuỗi |
| H35 | **Đúng.** AVEKB − AVGGT = +1.16 / +1.18, p = 0.031 / 0.047 |
| H36 | **Đúng.** V\* lấy được +0.55 so với +0.40 của AVEKB (137%), nhanh hơn VGGT 2.38× ở N=200 |
| H37 | **Đúng, sát ngưỡng.** 13 chuỗi, N=200: +0.49, thắng 10/13, p = 0.040 |
| H38a | **Đúng.** AVEKB − AVEK = +1.21 trên 8 ô |
| H38b | **Đúng.** V\* giữ 83% (+1.01 so với +1.21) |
| H39 | **Đúng.** AVEKB trên 17 chuỗi, N=200: +0.57, thắng 13/17, p = 0.013. V\* trên 11 chuỗi không dùng để chọn nó: +0.69, thắng 10/11, p = 0.0015 |

### Đọc kết quả

- **V\* = AVEKB-f16n3 là điểm cân bằng tốt hơn AVEKB.**
  - Trên 11 chuỗi không dùng để chọn nó, V\* ngang VGGT ở N=200: 79.0 so với 78.2 trên 7-Scenes, 84.9 so với 85.1 trên
    TUM. Tốc độ nhanh hơn VGGT 2.4×, so với 2.1× của AVEKB.
  - Trên 6 chuỗi TUM khó dùng để chọn nó, V\* vẫn cách VGGT 1.5–1.8 điểm (78.8 / 78.1 so với 80.3 / 79.8). Khoảng
    cách này gần như bằng AVEKB.
- **Kết quả V\* hơn AVEKB trên 7-Scenes (137%) không nên coi là thật.** Chênh lệch từng chuỗi phần lớn dưới 0.5 điểm.
  Riêng office seq-04 kéo V\* lên 1.8 điểm ở N=200. Kết luận an toàn hơn là V\* giữ được gần trọn mức cải thiện với
  khoảng một nửa chi phí dải.
- **Trên 7-Scenes, nén gần như không mất gì so với VGGT.** AVEK đã ngang VGGT ở N=200. Dải đầy đủ chủ yếu có ích ở
  cảnh khó: fr1_floor +2.1 đến +4.9 điểm, office seq-04, và các chuỗi TUM quay nhiều.
- **Kiểm định nhiều lần.** Vòng này kiểm 7 giả thuyết mà không hiệu chỉnh. Với 3 kiểm định gộp (H37, hai phần của
  H39), theo Holm thì cả ba vẫn qua: 0.0015 < 0.017, 0.013 < 0.025, 0.040 < 0.05. Với Bonferroni chặt hơn, H37
  (0.040 × 3 = 0.12) không qua. Hai kết quả H39 là bằng chứng vững hơn.
- **Lớp 16–18 quan trọng hơn 14–15.** f14n3 hầu như không giúp gì, trên cả dữ liệu phát triển (+0.36) và 7-Scenes
  (−0.1).
