# Kiểm chứng "dải lớp đầy đủ" trên TUM chưa dùng — giả thuyết ghi trước khi chạy (2026-11-09)

## Nguồn gốc

Ablation trên các chuỗi phát triển (`results/ablation_plan.md`, đã nhìn) cho thấy hai điều:

- phần lớn mất mát nằm ở lưới 2×2 của các lớp global 9–23;
- giữ riêng dải 14–18 ở attention đầy đủ lấy lại 12.1 trên 16.1 điểm mà cả 9–23 đầy đủ lấy lại được. Dải 9–13 và
  19–23 lấy lại ít hơn nhiều.

Cấu hình mới:

- **AVEB-s4e36f14** = AVE-s4e36 + attention đầy đủ ở lớp 14–18.
- **AVEKB-s4e36k10f14** = AVEK-s4e36k10 + attention đầy đủ ở lớp 14–18.

## Dữ liệu: 6 chuỗi TUM chưa từng chạy

Các chuỗi được chọn theo mô tả chuyển động của TUM, trước mọi lần chạy:

| Nhóm | Chuỗi |
|---|---|
| Quay nhiều | fr1_rpy, fr1_plant, fr1_teddy, fr2_360_hemisphere |
| Dễ hơn | fr2_desk, fr3_sitting_halfsphere |

Chạy trên Kaggle T4 với `--lowmem`, N = 100 và 200. Cấu hình: B1, AV-s4, AVE-s4e36, AVEK-s4e36k10, AVEB-s4e36f14,
AVEKB-s4e36k10f14.

## Giả thuyết

Tất cả tính bằng AUC@30 trung bình trên 6 chuỗi, trừ khi ghi khác.

| | Giả thuyết |
|---|---|
| H30 | AVEB ≥ AVE + 1.0, ở cả N=100 và N=200. |
| H31 | AVEB ≥ AVEK, ở cả hai N. Thời gian được báo cáo riêng, vì AVEB dự kiến chậm hơn AVEK. |
| H32 | AVEKB ≥ AVEK + 0.5, ở cả hai N. |
| H33 | Trên 4 chuỗi quay nhiều, AVEKB thu hẹp ít nhất 50% khoảng cách từ AVEK đến B1 (trung bình 4 chuỗi), ở cả hai N. |

Các chỉ số khác (Chamfer, thời gian, bộ nhớ) chỉ báo cáo, không kiểm định.

## Kết quả (Kaggle T4; bảng đầy đủ trong `results/aggregate_band.md`)

AUC@30 trung bình trên 6 chuỗi (thời gian trung bình trong ngoặc):

| N | B1 | AV-s4 | AVE | AVEK | AVEB | AVEKB |
|---|---|---|---|---|---|---|
| 100 | 80.3 (133 s) | 76.8 (53 s) | 75.8 (56 s) | 77.4 (64 s) | 78.0 (70 s) | **79.0** (76 s) |
| 200 | 79.8 (467 s) | 76.6 (136 s) | 75.8 (145 s) | 77.4 (175 s) | 77.1 (206 s) | **78.1** (230 s) |

| Giả thuyết | Kết quả |
|---|---|
| H30 — AVEB ≥ AVE + 1.0 | **Đúng:** +2.23 / +1.32, thắng 5/6 chuỗi ở mỗi N. |
| H31 — AVEB ≥ AVEK | **Sai:** +0.60 ở N=100 nhưng −0.29 ở N=200. |
| H32 — AVEKB ≥ AVEK + 0.5 | **Đúng:** +1.54 / +0.75, thắng 5/6 chuỗi ở mỗi N. |
| H33 — AVEKB thu hẹp ≥ 50% khoảng cách AVEK–B1 trên 4 chuỗi quay nhiều | **Sai:** 53% ở N=100 nhưng chỉ 24% ở N=200. |

Với 6 chuỗi, không cặp so sánh nào có ý nghĩa thống kê (Wilcoxon p = 0.09–1.0). Đây là mức hiệu ứng trên một bộ chuỗi
nhỏ, không phải kết luận chắc chắn.

Ghi chú:

- **fr1_rpy** (chỉ quay tại chỗ, nhanh) là ngoại lệ. Trên chuỗi này, mọi cấu hình kể cả B1 chỉ đạt 39–46. Thêm dải đầy
  đủ còn làm *giảm* AUC: AVEB 41.5 / 38.9 so với AVE 42.7 / 42.7. Đây là chuỗi duy nhất mà AVEKB thua AVEK.
- **fr2_360_hemisphere:** AVEKB lấy lại nhiều nhất (+5.6 / +2.6 so với AVEK), nhưng vẫn cách B1 2.4 / 3.6.
- **AVE thua AVGGT** trên bộ TUM mới này (−1.0 / −0.8), chủ yếu do fr2_360_hemisphere (44.5 so với 48.8). Kết quả này
  khớp với H26 sai ở vòng TUM trước: lớp đầu trên lưới 6×6 không giúp trên TUM.
- **Chi phí:** ở N=200, AVEKB nhanh hơn B1 2.0×. Con số này là 2.7× với AVEK và 3.4× với AVGGT. AVEKB lấy lại khoảng
  một nửa khoảng cách từ AVGGT đến VGGT: 63% ở N=100 và 47% ở N=200.
- **Chưa kiểm chứng trên 7-Scenes.** Thêm attention đầy đủ khó làm kết quả tệ đi, nhưng mình chưa chạy.
