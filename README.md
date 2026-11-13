# tfvggt — Tăng tốc VGGT không cần huấn luyện

`tfvggt` tăng tốc suy luận của [VGGT](https://github.com/facebookresearch/vggt) trên chuỗi ảnh dài mà **không huấn luyện
lại**.

- Dùng nguyên trọng số VGGT-1B gốc.
- Chỉ thay cách tính global attention lúc chạy: nén key/value theo lưới, giữ nguyên một số keyframe, và giữ attention
  đầy đủ ở vài lớp.
- Có thêm một forward ít bộ nhớ, để chạy được tới 800 frame trên GPU 16 GB.

Mã nguồn dựng trên code mô hình của [FlashVGGT](https://github.com/wzpscott/flashvggt). Code đó chỉ được dùng, không bị
sửa.

## Kết quả chính

AUC@30 của pose camera trên GPU T4. "Nhanh hơn" là tỉ lệ thời gian so với VGGT gốc.

| cấu hình | N=200, 6 chuỗi TUM | nhanh hơn | N=800, 8 chuỗi TUM | nhanh hơn |
|---|---|---|---|---|
| VGGT gốc (`B1`) | 86.6 | 1× | 86.1 | 1× |
| `AVE-s4e36` | — | 3.6× | 85.1 | **5.0×** |
| `AVU-c40` | — | — | 85.9 | 4.2× |
| `AVEK-s4e36k10` | 84.8 | 2.9× | 86.2 | 3.6× |
| `AVEKB-f16n3` | 85.7 | 2.4× | 86.9 | 2.8× |
| `AVU-u5` | 85.5 | 2.4× | 86.3 | 2.8× |
| `AVEKBU-f16u10` | **86.0** | 2.1× | **87.1** | 2.3× |

Ghi chú:

- Mọi giả thuyết được ghi trước khi chạy và kiểm trên dữ liệu chưa dùng, kể cả các kết quả âm.
- Cột N=200 lấy từ [results/combo_plan.md](results/combo_plan.md); tốc độ của `AVE-s4e36` ở N=200 lấy từ vòng
  7-Scenes trước đó. Cột N=800 lấy từ [results/longkf_plan.md](results/longkf_plan.md).
- Ở N=800, chính VGGT gốc tụt trên 3/8 chuỗi, nên các so sánh với VGGT ở N=800 có phương sai lớn.
- Toàn bộ quá trình nghiên cứu ở [docs/research.md](docs/research.md).

## Chạy trên Kaggle: một ô notebook

1. Tạo notebook mới. Trong Settings, chọn **Accelerator: GPU T4 x1** và **Internet: On**.
2. Dán ô code trong [notebooks/kaggle.ipynb](notebooks/kaggle.ipynb), hoặc import cả file đó.
3. Sửa dòng `ARGS` nếu cần, rồi chạy.

```python
ARGS = "--dataset tum:fr1_xyz --frames 50 100 --configs recommended"
```

Ô đó tự làm các việc sau:

- tìm mã nguồn theo thứ tự: bản đang mở trên máy, bản gắn vào dưới dạng dataset Kaggle, hoặc `git clone` từ `REPO`;
- `pip install`;
- tải FlashVGGT (đã ghim commit), trọng số VGGT-1B và dữ liệu;
- chạy và ghi kết quả vào `/kaggle/working/results/run.jsonl`.

Trước khi repo có trên GitHub, đưa mã nguồn lên dưới dạng dataset rồi gắn vào notebook:
```bash
python tools/kaggle/kaggle_tool.py upload-code --user <tài-khoản-kaggle>
```

## Chạy trên máy local

Cần GPU CUDA và PyTorch đúng bản CUDA của máy. Cài PyTorch trước theo hướng dẫn ở pytorch.org.

```bash
pip install -e .
tfvggt run --dataset tum:fr1_xyz --frames 50 100 --configs recommended
tfvggt run --dataset 7scenes:office/seq-06 --frames 400 800 --configs B1 AVE-s4e36 AVU-c40 --lowmem
tfvggt summary results/run.jsonl
```

**Lưu ý trên Windows:** khi đường dẫn thư mục có ký tự ngoài bảng mã của hệ thống (ví dụ `CĐ-CL`), `pip install -e .`
có thể lỗi. Lỗi này đã gặp với Python 3.10: setuptools không ghi được file `.pth`. Khi đó, dùng `pip install .` và cài
lại sau mỗi lần sửa code. Notebook luôn dùng cách cài này.

Không cần sửa gì giữa Kaggle và local, vì các đường dẫn được chọn tự động:

| | Kaggle | local | đổi bằng |
|---|---|---|---|
| dữ liệu | `/tmp/tfvggt/data` | `./data` | `TFVGGT_DATA` |
| kết quả | `/kaggle/working/results` | `./results` | `--out` hoặc `TFVGGT_OUT` |
| cache (bản FlashVGGT) | `/tmp/tfvggt/cache` | `~/.cache/tfvggt` | `TFVGGT_CACHE` |

Cũng có thể mở `notebooks/kaggle.ipynb` trên máy và chạy y nguyên ô đó: nó nhận ra bản mã nguồn đang mở.

**FlashVGGT và trọng số** được tìm theo thứ tự sau:

1. Bản `flashvggt` đã cài sẵn, hoặc thư mục ở `$FLASHVGGT_ROOT`.
2. Nếu không có, tự tải bản ghim vào cache.
3. Trọng số VGGT-1B tìm trong `<FlashVGGT>/ckpts/vggt_1b.pt` hoặc `$TFVGGT_CKPT_DIR`. Nếu không có, tải từ Hugging Face
   (`facebook/VGGT-1B`).

## Dữ liệu

| `--dataset` | nguồn |
|---|---|
| `tum:<tên>` | [TUM RGB-D](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) (CC BY 4.0), tải và đổi sang bố cục 7-Scenes. Ví dụ `tum:fr3_sitting_xyz`; chuỗi bất kỳ: `tum:fr<camera>_<tên TUM>` |
| `7scenes:<cảnh>/<chuỗi>` | [7-Scenes](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/) của Microsoft, chỉ dùng cho nghiên cứu phi thương mại. Được tải trên máy chạy, dự án không phát hành lại |
| `--data <thư mục>` | dữ liệu có sẵn theo bố cục `<cảnh>/<chuỗi>/` (frame `*.color.png`, `*.depth.png`, `*.pose.txt`, file `done`) |

- Một chuỗi đã có trong `/kaggle/input` (dataset gắn vào notebook) được dùng luôn, không tải lại.
- Các dataset rút gọn dùng trong thí nghiệm chỉ chứa ảnh cho đúng các N đã chạy.

N frame được lấy đều theo thời gian trên toàn chuỗi.

## Chọn cấu hình

`tfvggt configs` liệt kê đủ 76 cấu hình đã chạy trong thí nghiệm. Các bản khuyến nghị (`--configs recommended`):

| trường hợp | cấu hình |
|---|---|
| tham chiếu: VGGT gốc, chỉ thêm các tối ưu chính xác | `B1` |
| nhanh nhất, nhất là N ≥ 400 | `AVE-s4e36` |
| cân bằng ở N = 400–800, bộ nhớ thấp | `AVU-c40` |
| mặc định bền ở N ≤ 200 | `AVEK-s4e36k10` |
| sát VGGT, cùng chi phí, không cần k-means | `AVU-u5` (N ≤ 400) |
| sát VGGT nhất | `AVEKB-f16n3`, `AVEKBU-f16u10` |

Vài lưu ý:

- **`--lowmem`:** bật khi N ≥ 250 trên GPU 16 GB, hoặc N ≥ 150 trên GPU 8 GB. Kết quả giống forward thường.
- **Bộ nhớ của k-means ở N=800:** các cấu hình có k-means (`AVEK*`) cần khoảng 13.6 GB GPU.
- **Dùng trong code:**
  ```python
  from tfvggt.core import build_model, configure
  from tfvggt.configs import CONFIGS
  model = build_model("vggt")
  configure(model, **CONFIGS["AVU-c40"][1])
  ```

## Kết quả đầu ra

Mỗi dòng của `<out>/<tag>.jsonl` ứng với một bộ (cấu hình, chuỗi, N), gồm các trường:

- **pose:** `auc30`, `rra`, `rta`, `ate`;
- **depth:** `absrel`, `d125`;
- **point cloud:** `acc`, `comp`, `chamfer`;
- **chi phí:** `time`, `peak_gb`;
- **so với `B1` cùng lượt chạy:** `fid_pose`, `fid_depth`.

Chạy lại cùng lệnh thì bỏ qua các dòng đã có.

## Cấu trúc

```
src/tfvggt/
  core.py          build_model, configure: attention nén, keyframe, các tối ưu chính xác
  longseq.py       forward ít bộ nhớ cho chuỗi dài (--lowmem)
  evaluation.py    nạp chuỗi, dự đoán, metric pose / depth / point cloud
  configs.py       76 cấu hình có tên
  runner.py, cli.py
  datasets/        TUM RGB-D, 7-Scenes
  paths.py, _flash.py   đường dẫn Kaggle/local, tìm hoặc tải FlashVGGT và trọng số
notebooks/kaggle.ipynb  một ô, chạy được cả trên Kaggle lẫn local
analysis/          script tổng hợp và kiểm giả thuyết của từng vòng (đọc results/)
results/           kế hoạch ghi trước (*_plan.md), bảng tổng hợp, kết quả thô (*.jsonl)
tools/kaggle/      chạy notebook thành kernel Kaggle từ dòng lệnh, nhiều tài khoản
tests/             pytest; test_configs.py giữ 76 cấu hình đúng như lúc tạo ra results/
docs/research.md   nhật ký nghiên cứu đầy đủ
```

## Kiểm tra

```bash
pip install -e ".[dev]"
pytest
```

## Giấy phép

Chưa chọn giấy phép cho mã nguồn của dự án. Repo không chứa trọng số hay dữ liệu. Mỗi thành phần ngoài có điều khoản
riêng, cần đọc trước khi dùng:

- trọng số VGGT-1B: trang Hugging Face `facebook/VGGT-1B`;
- FlashVGGT;
- TUM RGB-D: CC BY 4.0;
- 7-Scenes: chỉ dùng cho nghiên cứu phi thương mại.
