# Mức tụt trên TUM đến từ đâu? Ablation trên chuỗi phát triển (2026-11-09)

## Bối cảnh

Trên TUM, mọi cách nén K/V không train đều tụt mạnh ở hai chuỗi:

- fr1_360 (camera quay 360°): AVE-s4e36 tụt −9.3 / −7.1 AUC@30 so với B1 ở N=100 / 200; AVEK tụt −5.7 / −3.9.
- fr1_room (cầm tay, quay nhanh): AVE −6.0 / −0.4; AVEK −2.5 / −0.2.

Các kết quả này đã được nhìn, nên toàn bộ phần dưới là **phát triển, thăm dò**, không phải kiểm chứng.

## Phân tích độ phủ của keyframe (đã làm, không tốn kernel GPU)

`scratchpad/kf_coverage.py` so bốn cách chọn cùng số keyframe:

- k-means (như AVEK);
- farthest-point sampling trên descriptor trung bình của DINO;
- farthest-point sampling trên lưới 2×2;
- chia đều theo thời gian.

Độ phủ đo bằng ground truth: góc giữa trục quang của mỗi frame và trục quang của keyframe gần nhất.

| | N | k-means | FPS-mean | FPS-grid | đều |
|---|---|---|---|---|---|
| fr1_360 | 100 | 19.3° / max 59° | 19.6 / 58 | 20.5 / 55 | 22.0 / 63 |
| fr1_360 | 200 | 11.5 / 38 | 12.1 / 37 | 12.3 / 40 | 11.1 / 34 |
| fr1_room | 100 | 14.7 / 58 | 14.5 / 39 | 15.6 / 42 | 15.0 / 48 |
| fr3_long_office | 100 | 10.3 / 32 | 16.7 / 71 | 12.4 / 45 | 11.7 / 37 |

**Kết luận:** không cách chọn nào phủ góc nhìn tốt hơn k-means; FPS còn tệ hơn rõ trên fr3_long_office. Với cùng số
keyframe, đổi cách chọn không phải là đòn bẩy. Hướng "chọn keyframe theo độ phủ" dừng ở đây, không tốn GPU.

## Ablation (Kaggle T4, `--lowmem`, N = 100 và 200)

| Cấu hình | Global lớp 0–8 | Global lớp 9–23 |
|---|---|---|
| B1 (đã có) | đầy đủ | đầy đủ |
| AVE-s4e36 (đã có) | lưới 6×6 | lưới 2×2 + diag + mean |
| ABL-e36-Lfull | lưới 6×6 | **đầy đủ** |
| ABL-Efull-s4 | **đầy đủ** | lưới 2×2 + diag + mean |
| ABL-Efull-s4k10 | **đầy đủ** | lưới 2×2 + diag + mean + keyframe k-means |
| AVEK-s4e36k5 | như AVEK, gấp đôi số keyframe (S//5) | |

Chuỗi:

- phát triển: fr1_360 và fr1_desk (split tuma), fr1_room và fr3_walking_xyz (split tumb);
- fr1_desk và walking_xyz làm đối chứng "dễ".

### Quy tắc quyết định (ghi trước khi chạy)

"Mức tụt" là khoảng B1 − AVE trên fr1_360 và fr1_room, ở từng N. Một nhóm lớp được coi là **nguồn chính** nếu giữ
nhóm đó đầy đủ lấy lại được ít nhất 2/3 mức tụt, tính trung bình trên hai chuỗi và hai giá trị N.

- **Nguồn chính là các lớp đầu** (ABL-e36-Lfull không lấy lại được, ABL-Efull-s4 lấy lại được): hướng tiếp là lưới
  mịn hơn hoặc thích ứng ở lớp 0–8. Các lớp này rẻ khi dùng lưới 6×6, nên còn dư ngân sách.
- **Nguồn chính là các lớp sau:** hướng tiếp nhắm vào lớp 9–23. Có hai lựa chọn: keyframe riêng cho từng frame truy vấn
  (giữ nguyên các frame giống nó nhất), hoặc lưới mịn hơn chỉ cho các frame giống nhất.
- **Không nhóm nào riêng lẻ lấy lại được:** thiệt hại cộng dồn, và không có cách sửa một nhóm lớp nào đáng theo đuổi.
- **AVEK-s4e36k5:** nếu lấy lại được ít nhất một nửa khoảng cách còn lại của AVEK so với B1, thì số keyframe là đòn
  bẩy. Khi đó bước tiếp là thử số keyframe thích ứng trên chuỗi mới.

## Kết quả ablation (Kaggle T4; `results/kaggle/abla`, `results/kaggle/ablb`)

AUC@30, N=100 / N=200. B1, AVE và AVEK lấy từ lần chạy TUM trước (cùng phần cứng, cùng code).

| Chuỗi | B1 | AVE | AVEK k10 | ABL-e36-Lfull | ABL-Efull-s4 | ABL-Efull-s4k10 | AVEK k5 |
|---|---|---|---|---|---|---|---|
| fr1_360 | 62.5 / 59.7 | 53.2 / 52.6 | 56.7 / 55.7 | **60.2 / 57.0** | 55.3 / 54.9 | 57.1 / 56.3 | 57.1 / 54.9 |
| fr1_room | 83.5 / 82.1 | 77.4 / 81.7 | 81.0 / 81.9 | **82.5** / 81.3 | 79.3 / 82.5 | 81.6 / 82.7 | 80.3 / 82.1 |
| fr1_desk (đối chứng) | 93.4 / 93.0 | 92.7 / 92.5 | 93.1 / 92.6 | **93.7 / 93.3** | 92.3 / 92.1 | 92.8 / 92.5 | 93.0 / 92.7 |
| walking_xyz (đối chứng) | 91.0 / 90.1 | 89.3 / 88.3 | 90.4 / 89.1 | **90.8 / 89.9** | 90.0 / 88.7 | 90.5 / 89.2 | 90.7 / 89.3 |

**Theo đúng chữ của quy tắc ghi trước, kết quả bị suy biến.** Quy tắc lấy trung bình *tỉ lệ* lấy lại được trên 4 ô
(2 chuỗi × 2 N). Ô fr1_room N=200 chỉ tụt 0.4 điểm, nằm trong mức nhiễu, nên tỉ lệ ở ô đó vô nghĩa (−100% và +200%).
Tính đúng chữ thì lớp sau lấy lại 30%, lớp đầu lấy lại 71%, ngược với ba ô còn lại. Ghi nhận thẳng: quy tắc viết chưa
tốt.

Nếu tính theo **tổng điểm tụt** (22.9 điểm trên 4 ô), thì:

- giữ lớp sau đầy đủ lấy lại 16.1 điểm (70%);
- giữ lớp đầu đầy đủ lấy lại 7.1 điểm (31%).

Ở ba ô có mức tụt rõ, tỉ lệ cho lớp sau là 75 / 62 / 84%, cho lớp đầu là 23 / 32 / 31%. Trên hai chuỗi đối chứng, giữ
lớp sau đầy đủ đưa AUC về ngang B1. Giữ lớp đầu đầy đủ thì không giúp gì, thậm chí thấp hơn AVE trên fr1_desk.

**Kết luận** (thăm dò, dữ liệu đã nhìn):

- Phần lớn mất mát đến từ lưới 2×2 ở lớp 9–23.
- Lưới 6×6 ở lớp 0–8 gần như không tốn gì.
- Gấp đôi keyframe (k5) không hơn k10 (fr1_360 57.1 / 54.9 so với 56.7 / 55.7), nên số keyframe không phải đòn bẩy.
- Giữ lớp sau đầy đủ đắt gần bằng B1 (340 s so với 454 s ở N=200), nên cần một cách rẻ hơn.

## Bước 2: lưới thích ứng theo nội dung ở lớp 9–23 (ghi trước khi chạy, 2026-11-09)

**Ý tưởng:** mỗi ô 2×2 vẫn giữ đúng 1 patch, nên số key và độ phủ không gian giống hệt lưới. Khác ở chỗ patch được
chọn là patch có điểm cao nhất, thay vì luôn là góc trên-trái.

- `wsel="pref"`: điểm là tổng khối attention (softmax chính xác trên mọi key) mà token camera/register của mọi frame
  dồn vào patch đó. Token camera là nơi mô hình tổng hợp thông tin để ước lượng pose.
- `wsel="norm"`: điểm là chuẩn của key. Đây là đối chứng rẻ: có phải chỉ cần chọn key "mạnh"?

**Kiểm tra trên máy** (N=16):

- mỗi frame giữ đúng 266 patch, bằng lưới; chỉ 26% patch được chọn trùng góc trên-trái;
- forward ít bộ nhớ khớp forward chuẩn ở 97–99.7% patch được chọn. Phần lệch do làm tròn bf16 làm đổi argmax.

**Cấu hình:** AVEW-pref, AVEW-norm, AVEKW-pref (= AVEK + wsel). Cùng chuỗi phát triển, cùng N=100/200, `--lowmem`.

**Quy tắc** (so với AVE, hoặc AVEK cho AVEKW). AVEW-pref được coi là đáng kiểm chứng trên dữ liệu chưa dùng nếu đạt cả
ba điều kiện:

1. Tổng AUC lấy lại trên 4 ô (fr1_360, fr1_room × 2 N) ≥ +4 điểm, tức trung bình ≥ +1 điểm mỗi ô.
2. Không tụt quá 0.5 điểm ở ô nào của hai chuỗi đối chứng.
3. Thời gian tăng ≤ 15% ở N=200.

Nếu AVEW-norm đạt mức tương đương AVEW-pref thì cách chấm điểm theo token camera không phải là lý do, và sẽ báo cáo như
vậy.

### Kết quả bước 2 (dừng sớm; dòng kết quả lấy từ log, `results/kaggle/wsel{a,b}/rows_from_log.txt`)

| N=100 | AVE | AVEW-pref | AVEW-norm | AVEK | AVEKW-pref |
|---|---|---|---|---|---|
| fr1_360 | 53.2 | 50.1 | 51.6 | 56.7 | 53.5 |
| fr1_room | 77.4 | 72.8 | 77.4 | 81.0 | 78.5 |

(Ô fr1_360 N=200 chạy xong trước khi dừng: AVEW-pref 52.1, AVE 52.6.)

**Không đạt.** Sau hai ô, tổng là −7.7 điểm. Hai ô N=200 không thể bù để đạt +4, vì ở fr1_room N=200 AVE chỉ cách
B1 0.4. Tôi dừng hai kernel để tiết kiệm GPU.

Chọn patch theo nội dung đều kém hơn lưới cố định, cả cách chấm theo token camera lẫn theo chuẩn key. Đây cũng là kết
quả của lưới dịch pha trước đó. Giả thuyết giải thích (chưa kiểm chứng): lưới cố định giữ cùng vị trí ảnh ở mọi frame,
và phần mean-fill giả định các key bị bỏ là "trung bình". Chọn key cực trị làm lệch cả hai điều này.

## Bước 3: dải lớp nào trong 9–23 cần attention đầy đủ? (ghi trước khi chạy)

Ba cấu hình, mỗi cấu hình giữ đầy đủ 5 lớp, các lớp còn lại như AVE: ABL-L9-13full, ABL-L14-18full, ABL-L19-23full.
Cùng chuỗi phát triển, N=100/200, `--lowmem`.

**Quy tắc:** gọi R(dải) là tổng AUC lấy lại so với AVE trên 4 ô (fr1_360, fr1_room × 2 N). Giữ cả 9–23 đầy đủ lấy
lại 16.1 điểm.

- Nếu một dải có R ≥ 8 (≥ 50% của 16.1) và không ô đối chứng nào tụt quá 0.5 so với AVE: cấu hình "AVE + dải đó đầy
  đủ" (có và không có keyframe) sẽ được kiểm chứng trên chuỗi chưa dùng, so với AVEK ở thời gian tương đương.
- Nếu không: mất mát trải đều trên các lớp sau, không có cách sửa rẻ theo lớp. Kết luận dừng ở đó.

### Kết quả bước 3 (`results/kaggle/band{a,b}`)

AUC@30, N=100 / N=200. Cột R là tổng điểm lấy lại so với AVE trên 4 ô của fr1_360 và fr1_room.

| Cấu hình | fr1_360 | fr1_room | fr1_desk | walking_xyz | R |
|---|---|---|---|---|---|
| AVE | 53.2 / 52.6 | 77.4 / 81.7 | 92.7 / 92.5 | 89.3 / 88.3 | 0 |
| L9-13 đầy đủ | 52.7 / 53.3 | 76.9 / 80.1 | 93.4 / 92.9 | 88.9 / 88.4 | −1.9 |
| **L14-18 đầy đủ** | **57.9 / 55.2** | **81.4 / 82.5** | 93.0 / 92.8 | 90.2 / 89.1 | **+12.1** |
| L19-23 đầy đủ | 54.2 / 53.9 | 78.1 / 82.1 | 92.8 / 92.5 | 89.5 / 88.4 | +3.4 |
| 9–23 đầy đủ | 60.2 / 57.0 | 82.5 / 81.3 | 93.7 / 93.3 | 90.8 / 89.9 | +16.1 |

**Đạt quy tắc.** Dải 14–18 có R = 12.1 ≥ 8, và không ô đối chứng nào tụt so với AVE. Riêng dải này chiếm 75% phần
lấy lại được khi giữ cả 9–23 đầy đủ, với một phần ba số lớp. Các lớp giữa (14–18) cần thông tin xuyên frame đầy đủ
nhất; lớp 9–13 và 19–23 chịu nén tốt.

Chi phí ở N=200 (T4, forward ít bộ nhớ): 214 s, so với AVE 141 s, AVEK 170 s và B1 454 s. Kiểm chứng trên chuỗi
chưa dùng: xem `results/band_plan.md`.
