"""
Login Dialog - User authentication interface
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QCheckBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from ..models.user import User
from ..config import APP_NAME, ASSETS_DIR


class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    login_successful = pyqtSignal(User)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logged_in_user = None
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Đăng nhập hệ thống")
        # [FIX] Tăng chiều cao lên 580 để chứa logo đẹp hơn
        self.setFixedSize(400, 580)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Load logo từ thư mục assets
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        
        # [MỚI] Hiển thị Logo thay vì Text tiêu đề đơn thuần
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if logo_path.exists():
            # Load ảnh và resize về kích thước phù hợp (ví dụ 100x100)
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaled(
                110, 110,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback nếu chưa có file ảnh
            logo_label.setText("🛡️") 
            font = QFont()
            font.setPointSize(50)
            logo_label.setFont(font)
            
        layout.addWidget(logo_label)
        
        # App Name
        app_label = QLabel(APP_NAME)
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        app_label.setFont(app_font)
        app_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(app_label)
        
        # Subtitle
        sub_label = QLabel("ĐĂNG NHẬP HỆ THỐNG")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_font = QFont("Segoe UI", 10)
        sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        sub_label.setFont(sub_font)
        sub_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(sub_label)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        self.username_input.setMinimumHeight(45)
        self.username_input.returnPressed.connect(self._focus_password)
        layout.addWidget(self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.returnPressed.connect(self._login)
        layout.addWidget(self.password_input)
        
        # Remember me
        self.remember_checkbox = QCheckBox("Ghi nhớ đăng nhập")
        self.remember_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.remember_checkbox)
        
        # Error Label
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        layout.addSpacing(5)
        
        # Login button
        self.login_btn = QPushButton("ĐĂNG NHẬP")
        self.login_btn.setObjectName("primaryBtn")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._login)
        
        # Thêm hiệu ứng đổ bóng cho nút
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.login_btn.setGraphicsEffect(shadow)
        
        layout.addWidget(self.login_btn)
        
        layout.addStretch()
        
        # Footer text
        footer = QLabel("© 2026 Quản lý VKTBKT")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #bdc3c7; font-size: 11px;")
        layout.addWidget(footer)
        
        # Set focus
        self.username_input.setFocus()
    
    def _apply_styles(self):
        """Apply modern styles to dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLineEdit {
                padding: 0 15px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font-size: 14px;
                background-color: #fafafa;
                selection-background-color: #3498db;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: white;
            }
            QCheckBox {
                font-size: 13px;
                color: #555;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                /* image: url(assets/check.png); */ 
            }
            QPushButton#primaryBtn {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 25px; /* Rounded pill shape */
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton#primaryBtn:hover {
                background-color: #3498db;
            }
            QPushButton#primaryBtn:pressed {
                background-color: #21618c;
                margin-top: 2px; /* Press effect */
            }
            QLabel#errorLabel {
                color: #e74c3c;
                font-size: 13px;
                background-color: #fcebe9;
                padding: 8px;
                border-radius: 6px;
                margin-top: 5px;
            }
        """)
    
    def _focus_password(self):
        """Focus on password input"""
        self.password_input.setFocus()
    
    def _login(self):
        """Handle login attempt"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validation
        if not username:
            self._show_error("Vui lòng nhập tên đăng nhập!")
            self.username_input.setFocus()
            return
        
        if not password:
            self._show_error("Vui lòng nhập mật khẩu!")
            self.password_input.setFocus()
            return
        
        # Hide error
        self.error_label.hide()
        
        # Attempt authentication
        user = User.authenticate(username, password)
        
        if user:
            self.logged_in_user = user
            self.login_successful.emit(user)
            self.accept()
        else:
            self._show_error("Tên đăng nhập hoặc mật khẩu không đúng!")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def _show_error(self, message: str):
        """Show error message"""
        self.error_label.setText(f"⚠️ {message}")
        self.error_label.show()
    
    def get_user(self) -> User:
        """Get logged in user"""
        return self.logged_in_user