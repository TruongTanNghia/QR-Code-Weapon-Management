# Quản lý VKTBKT - Phần mềm Quản lý Vũ khí Trang bị Kỹ thuật thông qua mã QR

## 📋 Mô tả

Phần mềm desktop hỗ trợ quản lý vũ khí, khí tài tại đơn vị quân đội thông qua công nghệ mã QR. Chuyển đổi số công tác quản lý từ sổ sách giấy tờ sang quản lý điện tử.

## ✨ Tính năng chính

- 📦 **Quản lý hồ sơ thiết bị**: Thêm, sửa, xóa thông tin vũ khí/khí tài
- 🏷️ **Sinh mã QR tự động**: Mỗi thiết bị được cấp một mã QR định danh duy nhất
- 📷 **Quét mã tra cứu nhanh**: Sử dụng webcam để quét mã QR và tra cứu thông tin
- 📝 **Nhật ký bảo dưỡng**: Ghi lại lịch sử sửa chữa, bảo dưỡng
- 📄 **Xuất báo cáo PDF**: Xuất danh sách thiết bị và bảng mã QR để in
- 🌙 **Giao diện Dark/Light mode**: Hỗ trợ 2 chế độ hiển thị

## 🛠️ Yêu cầu hệ thống

- **Hệ điều hành**: Windows 10/11
- **Python**: 3.10 trở lên
- **Webcam**: Để sử dụng tính năng quét mã QR
- **RAM**: Tối thiểu 4GB
- **Ổ cứng**: 100MB trống

## 📦 Cài đặt

### 1. Clone hoặc tải xuống dự án

```bash
cd d:\1.PROJECT\QuanLyVKTB
```

### 2. Tạo môi trường ảo (Virtual Environment)

```bash
python -m venv venv
```

### 3. Kích hoạt môi trường ảo

**Windows (Command Prompt):**

```bash
venv\Scripts\activate
```

**Windows (PowerShell):**

```bash
.\venv\Scripts\Activate.ps1
```

### 4. Cài đặt các thư viện

```bash
pip install -r requirements.txt
```

### 5. Cài đặt thêm Visual C++ Redistributable (nếu chưa có)

Thư viện `pyzbar` cần Visual C++ Redistributable. Tải và cài đặt từ:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## 🚀 Chạy ứng dụng

```bash
python main.py
```

## 📁 Cấu trúc dự án

```
QuanLyVKTB/
├── main.py                 # File khởi chạy ứng dụng
├── requirements.txt        # Danh sách thư viện
├── README.md              # Tài liệu hướng dẫn
│
├── data/                  # Dữ liệu
│   ├── vktbkt.db         # Database SQLite
│   ├── qr_codes/         # Ảnh mã QR
│   └── exports/          # File PDF xuất
│
├── assets/               # Tài nguyên
│   ├── icons/           # Biểu tượng
│   ├── images/          # Hình ảnh
│   └── fonts/           # Font chữ
│
└── src/                  # Source code
    ├── __init__.py
    ├── config.py         # Cấu hình ứng dụng
    │
    ├── models/           # Data models (MVC - Model)
    │   ├── __init__.py
    │   ├── database.py   # Kết nối CSDL
    │   ├── equipment.py  # Model thiết bị
    │   └── maintenance_log.py  # Model nhật ký
    │
    ├── views/            # Giao diện (MVC - View)
    │   ├── __init__.py
    │   ├── styles.py     # Stylesheet themes
    │   ├── main_window.py
    │   ├── dashboard_view.py
    │   ├── equipment_view.py
    │   ├── scan_view.py
    │   ├── input_dialog.py
    │   ├── maintenance_dialog.py
    │   ├── equipment_detail_dialog.py
    │   └── qr_dialog.py
    │
    ├── controllers/      # Logic xử lý (MVC - Controller)
    │   ├── __init__.py
    │   ├── equipment_controller.py
    │   └── maintenance_controller.py
    │
    └── services/         # Các dịch vụ
        ├── __init__.py
        ├── qr_service.py      # Tạo/giải mã QR
        ├── camera_service.py  # Xử lý camera (QThread)
        └── export_service.py  # Xuất PDF
```

## 📖 Hướng dẫn sử dụng

### 1. Thêm thiết bị mới

1. Vào mục **"Quản lý TB"** từ menu bên trái
2. Nhấn nút **"➕ Thêm mới"**
3. Điền thông tin thiết bị (Tên, Số hiệu, Loại,...)
4. Nhấn **"Thêm"** để lưu

### 2. In mã QR

1. Trong danh sách thiết bị, nhấn nút **"🏷️"** trên dòng thiết bị
2. Cửa sổ hiển thị mã QR xuất hiện
3. Nhấn **"Lưu ảnh"** hoặc **"In"** để in ra giấy decal

### 3. Quét mã QR tra cứu

1. Vào mục **"📷 Quét mã QR"**
2. Chọn camera và nhấn **"Bắt đầu quét"**
3. Hướng camera về mã QR trên thiết bị
4. Thông tin sẽ tự động hiển thị

### 4. Ghi nhật ký bảo dưỡng

1. Nhấn nút **"📝"** trên dòng thiết bị
2. Chọn loại công việc và điền thông tin
3. Có thể cập nhật tình trạng thiết bị
4. Nhấn **"Lưu"** để ghi nhật ký

### 5. Xuất báo cáo

1. Vào menu **Tệp > Xuất danh sách PDF** hoặc **Xuất bảng mã QR**
2. File PDF sẽ được lưu trong thư mục `data/exports/`

## 🔒 Bảo mật

- Dữ liệu được lưu trữ **cục bộ** trong file SQLite
- **Không kết nối Internet** - đảm bảo an toàn thông tin
- File database có thể sao lưu dễ dàng

## 🔧 Khắc phục sự cố

### Camera không hoạt động

- Kiểm tra kết nối webcam
- Thử chọn camera khác trong dropdown
- Đảm bảo không có ứng dụng khác đang sử dụng camera

### Lỗi import pyzbar

```bash
pip uninstall pyzbar
pip install pyzbar
```

Và cài đặt Visual C++ Redistributable như hướng dẫn ở trên.

### Lỗi font tiếng Việt trong PDF

- Đảm bảo hệ thống có font Arial hoặc Times New Roman

## 📝 License

© 2024 VKTBKT Team. All rights reserved.

## 📧 Liên hệ

Nếu có vấn đề hoặc góp ý, vui lòng liên hệ đội phát triển.
