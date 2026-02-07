"""
Configuration settings for VKTBKT Management System
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

# Database configuration
DATABASE_PATH = DATA_DIR / "vktbkt.db"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

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
