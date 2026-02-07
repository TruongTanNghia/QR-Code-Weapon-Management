"""
Stylesheet definitions for the application
Supports Dark and Light themes
"""

from ..config import THEMES, DEFAULT_THEME


class StyleSheet:
    """
    Application stylesheet manager with Dark/Light theme support
    """
    
    def __init__(self, theme: str = DEFAULT_THEME):
        self.current_theme = theme
        self.colors = THEMES.get(theme, THEMES[DEFAULT_THEME])
    
    def set_theme(self, theme: str):
        """Switch theme"""
        if theme in THEMES:
            self.current_theme = theme
            self.colors = THEMES[theme]
    
    def get_main_stylesheet(self) -> str:
        """Get main application stylesheet"""
        c = self.colors
        return f"""
            /* Main Window */
            QMainWindow {{
                background-color: {c['bg_primary']};
            }}
            
            /* Central Widget */
            QWidget {{
                background-color: {c['bg_primary']};
                color: {c['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }}
            
            /* Sidebar */
            QWidget#sidebar {{
                background-color: {c['bg_secondary']};
                border-right: 1px solid {c['border']};
            }}
            
            /* Sidebar Buttons */
            QPushButton#sidebarBtn {{
                background-color: transparent;
                color: {c['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
            }}
            
            QPushButton#sidebarBtn:hover {{
                background-color: {c['accent']};
                color: white;
            }}
            
            QPushButton#sidebarBtn:checked {{
                background-color: {c['accent']};
                color: white;
            }}
            
            /* Cards */
            QFrame#card {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 16px;
            }}
            
            QFrame#statCard {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 20px;
                min-width: 200px;
            }}
            
            /* Labels */
            QLabel {{
                color: {c['text_primary']};
            }}
            
            QLabel#title {{
                font-size: 24px;
                font-weight: bold;
                color: {c['text_primary']};
            }}
            
            QLabel#subtitle {{
                font-size: 14px;
                color: {c['text_secondary']};
            }}
            
            QLabel#userInfo {{
                font-size: 12px;
                color: {c['text_secondary']};
                padding: 8px;
                background-color: {c['bg_primary']};
                border-radius: 6px;
                margin-top: 5px;
            }}
            
            QLabel#viewTitle {{
                font-size: 18px;
                font-weight: bold;
                color: {c['text_primary']};
            }}
            
            QLabel#statValue {{
                font-size: 32px;
                font-weight: bold;
                color: {c['accent']};
            }}
            
            QLabel#statLabel {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {c['accent']};
            }}
            
            QPushButton:disabled {{
                background-color: {c['border']};
                color: {c['text_secondary']};
            }}
            
            QPushButton#success {{
                background-color: {c['success']};
            }}
            
            QPushButton#success:hover {{
                background-color: #43A047;
            }}
            
            QPushButton#danger {{
                background-color: {c['danger']};
            }}
            
            QPushButton#danger:hover {{
                background-color: #E53935;
            }}
            
            /* Small table action buttons */
            QPushButton#tableBtn {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
                min-width: 30px;
            }}
            
            QPushButton#tableBtn:hover {{
                background-color: {c['accent_hover']};
            }}
            
            QPushButton#tableBtnDanger {{
                background-color: {c['danger']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
                min-width: 30px;
            }}
            
            QPushButton#tableBtnDanger:hover {{
                background-color: #E53935;
            }}

            QPushButton#tableBtnView {{
                background-color: #17a2b8; /* Màu Teal dịu mắt */
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
                min-width: 30px;
            }}

            QPushButton#tableBtnView:hover {{
                background-color: #138496;
            }}
            
            QPushButton#secondary {{
                background-color: transparent;
                color: {c['accent']};
                border: 1px solid {c['accent']};
            }}
            
            QPushButton#secondary:hover {{
                background-color: {c['accent']};
                color: white;
            }}
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 2px solid {c['accent']};
            }}
            
            QLineEdit:disabled {{
                background-color: {c['bg_primary']};
                color: {c['text_secondary']};
            }}
            
            /* ComboBox */
            QComboBox {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                min-width: 150px;
            }}
            
            QComboBox:focus {{
                border: 2px solid {c['accent']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                selection-background-color: {c['bg_primary']};
                selection-color: {c['text_primary']};
            }}
            
            /* SpinBox */
            QSpinBox {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }}
            
            /* --- [SỬA LẠI PHẦN TABLE] --- */
            QTableWidget {{
                background-color: {c['bg_primary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c['border']};
                selection-background-color: transparent; /* Xóa màu xanh mặc định */
            }}
            
            QTableWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {c['border']};
            }}
            
            /* Khi chọn dòng: Giữ nguyên màu chữ, chỉ thêm viền hoặc đổi nền nhẹ */
            QTableWidget::item:selected {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['accent']}; /* Thêm viền để biết đang chọn */
            }}
            
            /* Khi di chuột: Màu nền nhẹ nhàng */
            QTableWidget::item:hover {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
            }}
            
            QHeaderView::section {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                font-weight: bold;
                padding: 12px;
                border: none;
                border-bottom: 2px solid {c['accent']};
            }}
            /* --- [KẾT THÚC SỬA TABLE] --- */
            
            /* ScrollBar */
            QScrollBar:vertical {{
                background-color: {c['bg_primary']};
                width: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {c['border']};
                border-radius: 5px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {c['accent']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {c['bg_primary']};
                height: 10px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {c['border']};
                border-radius: 5px;
                min-width: 30px;
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                background-color: {c['bg_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            
            QTabBar::tab {{
                background-color: {c['bg_secondary']};
                color: {c['text_secondary']};
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {c['accent']};
                color: white;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {c['border']};
            }}
            
            /* GroupBox */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {c['text_primary']};
            }}
            
            /* Dialog */
            QDialog {{
                background-color: {c['bg_primary']};
            }}
            
            /* Message Box */
            QMessageBox {{
                background-color: {c['bg_primary']};
            }}
            
            /* ToolTip */
            QToolTip {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 5px;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {c['bg_secondary']};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {c['accent']};
                border-radius: 4px;
            }}
            
            /* Menu */
            QMenuBar {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
            }}
            
            QMenuBar::item:selected {{
                background-color: {c['accent']};
                color: white;
            }}
            
            QMenu {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
            }}
            
            QMenu::item:selected {{
                background-color: {c['accent']};
                color: white;
            }}
            
            /* Status indicator labels */
            QLabel#statusGood {{
                color: {c['success']};
                font-weight: bold;
            }}
            
            QLabel#statusWarning {{
                color: {c['warning']};
                font-weight: bold;
            }}
            
            QLabel#statusDanger {{
                color: {c['danger']};
                font-weight: bold;
            }}
        """
    
    def get_camera_frame_style(self) -> str:
        """Style for camera preview frame"""
        c = self.colors
        return f"""
            QLabel#cameraFrame {{
                background-color: #000000;
                border: 2px solid {c['accent']};
                border-radius: 8px;
            }}
        """
    
    def get_status_color(self, status: str) -> str:
        """Get color for equipment status (Cấp 1-5)"""
        status_colors = {
            'Cấp 1': self.colors['success'],    # Excellent
            'Cấp 2': self.colors['success'],    # Good
            'Cấp 3': self.colors['warning'],    # Fair
            'Cấp 4': self.colors['warning'],    # Poor
            'Cấp 5': self.colors['danger']      # Critical
        }
        return status_colors.get(status, self.colors['text_secondary'])