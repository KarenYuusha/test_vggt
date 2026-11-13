# Chạy trên Kaggle từ dòng lệnh

Phần này không bắt buộc: dán ô trong `notebooks/kaggle.ipynb` vào một notebook Kaggle là đủ. Công cụ ở đây chỉ để chạy
nhiều kernel, trên nhiều tài khoản, mà không phải mở trình duyệt.

```bash
pip install kaggle
# 1. đưa mã nguồn lên dataset <user>/tfvggt-src (chỉ cần khi chưa dùng GitHub)
python tools/kaggle/kaggle_tool.py upload-code --user U --public
# 2. tạo kernel <user>/tfvggt-<tag> từ notebook, thay dòng ARGS bằng --args
python tools/kaggle/kaggle_tool.py push --user U --tag lk1 \
    --args "--dataset tum:fr3_sitting_xyz --frames 400 800 --configs B1 AVE-s4e36 AVU-c40 --lowmem"
# 3. theo dõi; khi kernel xong, tải kết quả về results/kaggle/<tag>/
python tools/kaggle/kaggle_tool.py watch --user U --tag lk1
```

- **Khóa API:** theo cách thông thường của Kaggle CLI (`~/.kaggle/kaggle.json` hoặc `KAGGLE_USERNAME`/`KAGGLE_KEY`).
  - Với nhiều tài khoản, dùng `--accounts <file>` hoặc `$TFVGGT_KAGGLE_ACCOUNTS`. File có mỗi dòng một
    `{"username": ..., "key": ...}`.
  - Khóa chỉ được truyền cho Kaggle CLI qua biến môi trường, không in ra và không ghi vào file.
- **Quy tắc chạy:** mỗi tài khoản chỉ chạy một kernel một lúc.
- **Khi kernel bị treo:** `watch` cảnh báo khi kernel nằm ở QUEUED quá 5 phút, hoặc log im lặng quá 5 phút. Khi đó xóa
  kernel bằng `delete`, rồi `push` lại trên cùng tài khoản.
- **Dữ liệu chuẩn bị sẵn:** gắn thêm bằng `--data owner/dataset`. Ví dụ dataset TUM đã rút gọn, để không phải tải lại
  trong kernel.
