"""
Configuration settings for VKTBKT Management System
"""
import os
import sys
from pathlib import Path

# --- CẤU HÌNH ĐƯỜNG DẪN THÔNG MINH (CHO CẢ CODE VÀ EXE) ---
if getattr(sys, 'frozen', False):
    # TRƯỜNG HỢP 1: Chạy từ file .exe (Đã build)
    # INTERNAL_DIR: Đường dẫn tạm thời chứa code và assets (đã được giải nén ngầm)
    INTERNAL_DIR = Path(sys._MEIPASS)
    
    # EXTERNAL_DIR: Đường dẫn chứa file .exe đang chạy (Để lưu Database)
    EXTERNAL_DIR = Path(sys.executable).parent
else:
    # TRƯỜNG HỢP 2: Chạy code Python bình thường
    INTERNAL_DIR = Path(__file__).resolve().parent.parent
    EXTERNAL_DIR = INTERNAL_DIR

# Định nghĩa các thư mục dựa trên logic trên
ASSETS_DIR = INTERNAL_DIR / "assets"
DATA_DIR = EXTERNAL_DIR / "data"

# Database configuration
DATABASE_PATH = DATA_DIR / "vktbkt.db"

# Ensure data directory exists (Tạo thư mục data nếu chưa có)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Application settings
APP_NAME = "Quản lý VKTBKT"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Tên tác giả"

# Equipment status options
EQUIPMENT_STATUS = [
    "Cấp 1",
    "Cấp 2",
    "Cấp 3",
    "Cấp 4",
    "Cấp 5"
]

# Equipment loan status options
LOAN_STATUS_OPTIONS = [
    "Đang ở kho",
    "Đã cho mượn"
]

# Equipment categories
EQUIPMENT_CATEGORIES = [
    "Súng ngắn",
    "Súng trường",
    "Súng máy",
    "Súng phóng lựu",
    "Khí tài quang học",
    "Khí tài thông tin",
    "Phương tiện vận tải",
    "Trang bị bảo hộ",
    "Khác"
]

# QR Code settings
QR_BOX_SIZE = 10
QR_BORDER = 4
QR_VERSION = 1

# Camera settings
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Theme settings
THEMES = {
    "light": {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F5F5F5",
        "text_primary": "#212121",
        "text_secondary": "#757575",
        "accent": "#1976D2",
        "accent_hover": "#1565C0",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "danger": "#F44336",
        "border": "#E0E0E0"
    },
    "dark": {
        "bg_primary": "#1E1E1E",
        "bg_secondary": "#252526",
        "text_primary": "#FFFFFF",
        "text_secondary": "#CCCCCC",
        "accent": "#0078D4",
        "accent_hover": "#106EBE",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "danger": "#F44336",
        "border": "#3C3C3C"
    }
}

DEFAULT_THEME = "light"