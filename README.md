# TikTok Human Chrome Bot

Bot tự động lướt TikTok, tương tác và phát hiện cross‑follow (fl chéo) bằng **Chrome profile thật** và **điều khiển chuột/bàn phím giống người**.

## 🛠 Chuẩn bị

### 1. Tìm đường dẫn profile Chrome
- Mở Chrome, gõ `chrome://version/` vào thanh địa chỉ.
- Dòng **Profile Path** ví dụ:  
  `C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Profile 230`
- `user_data_dir` là phần cho đến `User Data`  
  `C:\Users\Admin\AppData\Local\Google\Chrome\User Data`
- `profile_dir` là tên thư mục con `Profile 230`

### 2. Đóng hoàn toàn Chrome
- Kiểm tra Task Manager không còn process `chrome.exe`.  
  Hoặc dùng lệnh: `taskkill /F /IM chrome.exe`

### 3. Cài đặt Python và thư viện
```bash
pip install -r requirements.txt
playwright install chromium   # (cần để dùng CDP)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
python main.py
```