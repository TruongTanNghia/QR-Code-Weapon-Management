"""
User Management View - CRUD interface for system users
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QDialog, QFormLayout, QMessageBox, QHeaderView,
    QFrame, QCheckBox, QGroupBox, QGraphicsDropShadowEffect, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ..models.user import User, UserRole, ROLE_DISPLAY_NAMES
from ..models.unit import Unit


class UserDetailDialog(QDialog):
    """
    [MỚI] Dialog hiển thị chi tiết tài khoản (Giao diện giống Quản lý Loại trang bị)
    """
    def __init__(self, parent=None, user: User = None):
        super().__init__(parent)
        self.user = user
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Chi tiết tài khoản")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        title = QLabel(f"👤 {self.user.username}")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Helper function
        def add_row(layout, label, value, color=None):
            lbl_widget = QLabel(label)
            lbl_widget.setFont(QFont("Segoe UI", 10))
            lbl_widget.setStyleSheet("color: palette(text); opacity: 0.8;")
            
            val_widget = QLabel(str(value) if value else "-")
            val_widget.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            val_widget.setWordWrap(True)
            if color:
                val_widget.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                val_widget.setStyleSheet("color: palette(text);")
                
            layout.addRow(lbl_widget, val_widget)

        # --- Group 1: Thông tin tài khoản ---
        group_account = QGroupBox("Thông tin tài khoản")
        group_account.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        # Style adaptive
        group_account.setStyleSheet("""
            QGroupBox {
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: palette(text);
            }
        """)
        
        account_layout = QFormLayout(group_account)
        account_layout.setSpacing(12)
        account_layout.setContentsMargins(15, 20, 15, 15)
        
        role_text = self.user.get_role_display()
        role_color = "#d35400" if self.user.role == UserRole.ADMIN else None
        
        unit_name = "Không thuộc đơn vị"
        if self.user.unit_id:
            unit = Unit.get_by_id(self.user.unit_id)
            if unit: unit_name = f"{unit.name} ({unit.code})" if unit.code else unit.name

        status_text = "Đang hoạt động" if self.user.is_active else "Đã khóa"
        status_color = "#27ae60" if self.user.is_active else "#c0392b"

        add_row(account_layout, "Vai trò:", role_text, role_color)
        add_row(account_layout, "Đơn vị trực thuộc:", unit_name)
        add_row(account_layout, "Trạng thái:", status_text, status_color)
        add_row(account_layout, "Ngày tạo:", str(self.user.created_at) if self.user.created_at else "-")
        
        layout.addWidget(group_account)
        
        # --- Group 2: Thông tin cá nhân ---
        group_personal = QGroupBox("Thông tin cá nhân")
        group_personal.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        group_personal.setStyleSheet(group_account.styleSheet())
        
        personal_layout = QFormLayout(group_personal)
        personal_layout.setSpacing(12)
        personal_layout.setContentsMargins(15, 20, 15, 15)
        
        add_row(personal_layout, "Họ và tên:", self.user.full_name)
        add_row(personal_layout, "Email:", self.user.email)
        add_row(personal_layout, "Số điện thoại:", self.user.phone)
        add_row(personal_layout, "Đăng nhập lần cuối:", str(self.user.last_login) if self.user.last_login else "Chưa đăng nhập lần nào")
        
        layout.addWidget(group_personal)
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setObjectName("secondaryBtn")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)


class UserDialog(QDialog):
    """Dialog for adding/editing users"""
    
    def __init__(self, parent=None, user: User = None, current_user: User = None):
        super().__init__(parent)
        self.user = user
        self.current_user = current_user
        self.is_edit_mode = user is not None
        self._setup_ui()
        if self.is_edit_mode:
            self._load_user_data()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Sửa tài khoản" if self.is_edit_mode else "Thêm tài khoản mới")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Thông tin tài khoản")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Account info group
        account_group = QGroupBox("Thông tin đăng nhập")
        account_layout = QFormLayout(account_group)
        account_layout.setSpacing(10)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập...")
        if self.is_edit_mode and self.user.role == UserRole.SUPERADMIN:
            self.username_input.setEnabled(False)
        account_layout.addRow("Tên đăng nhập *:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(
            "Để trống nếu không đổi mật khẩu..." if self.is_edit_mode else "Nhập mật khẩu..."
        )
        account_layout.addRow("Mật khẩu *:" if not self.is_edit_mode else "Mật khẩu mới:", self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Xác nhận mật khẩu...")
        account_layout.addRow("Xác nhận:", self.confirm_password_input)
        
        self.role_combo = QComboBox()
        for role, display_name in ROLE_DISPLAY_NAMES.items():
            self.role_combo.addItem(display_name, role)
        
        account_layout.addRow("Vai tr\u00f2 *:", self.role_combo)
        
        self.active_checkbox = QCheckBox("\u0110ang ho\u1ea1t \u0111\u1ed9ng")
        self.active_checkbox.setChecked(True)
        account_layout.addRow("Trạng thái:", self.active_checkbox)
        
        layout.addWidget(account_group)
        
        # Personal info group
        personal_group = QGroupBox("Thông tin cá nhân")
        personal_layout = QFormLayout(personal_group)
        personal_layout.setSpacing(10)
        
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Họ và tên...")
        personal_layout.addRow("Họ tên:", self.fullname_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        personal_layout.addRow("Email:", self.email_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Số điện thoại...")
        personal_layout.addRow("Điện thoại:", self.phone_input)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItem("-- Không thuộc đơn vị --", None)
        self._load_units()
        personal_layout.addRow("Đơn vị:", self.unit_combo)
        
        layout.addWidget(personal_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Lưu" if self.is_edit_mode else "Tạo tài khoản")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_user)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_units(self):
        units = Unit.get_all()
        for unit in units:
            display_text = f"{unit.name} ({unit.code})" if unit.code else unit.name
            self.unit_combo.addItem(display_text, unit.id)
    
    def _load_user_data(self):
        if not self.user: return
        self.username_input.setText(self.user.username)
        self.fullname_input.setText(self.user.full_name)
        self.email_input.setText(self.user.email)
        self.phone_input.setText(self.user.phone)
        self.active_checkbox.setChecked(self.user.is_active)
        index = self.role_combo.findData(self.user.role)
        if index >= 0: self.role_combo.setCurrentIndex(index)
        if self.user.unit_id:
            index = self.unit_combo.findData(self.user.unit_id)
            if index >= 0: self.unit_combo.setCurrentIndex(index)
    
    def _save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập!")
            self.username_input.setFocus()
            return
        if len(username) < 3:
            QMessageBox.warning(self, "Lỗi", "Tên đăng nhập phải có ít nhất 3 ký tự!")
            self.username_input.setFocus()
            return
        if not self.is_edit_mode and not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mật khẩu!")
            self.password_input.setFocus()
            return
        if password and password != confirm_password:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp!")
            self.confirm_password_input.setFocus()
            return
        if password and len(password) < 6:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!")
            self.password_input.setFocus()
            return
        if User.username_exists(username, self.user.id if self.user else None):
            QMessageBox.warning(self, "Lỗi", "Tên đăng nhập đã tồn tại!")
            self.username_input.setFocus()
            return
        
        if not self.user:
            self.user = User()
            if self.current_user:
                self.user.created_by = self.current_user.id
        
        self.user.username = username
        self.user.full_name = self.fullname_input.text().strip()
        self.user.email = self.email_input.text().strip()
        self.user.phone = self.phone_input.text().strip()
        self.user.role = self.role_combo.currentData()
        self.user.unit_id = self.unit_combo.currentData()
        self.user.is_active = self.active_checkbox.isChecked()
        
        if password:
            self.user.set_password(password)
        
        try:
            self.user.save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu tài khoản:\n{str(e)}")


class ChangePasswordDialog(QDialog):
    """Dialog for changing password"""
    
    def __init__(self, parent=None, user: User = None):
        super().__init__(parent)
        self.user = user
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Đổi mật khẩu")
        self.setMinimumWidth(350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        info_label = QLabel(f"Đổi mật khẩu cho: {self.user.username}")
        info_label.setObjectName("subtitle")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("Mật khẩu mới...")
        form_layout.addRow("Mật khẩu mới:", self.new_password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText("Xác nhận mật khẩu...")
        form_layout.addRow("Xác nhận:", self.confirm_password)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Đổi mật khẩu")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._change_password)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _change_password(self):
        new_pass = self.new_password.text()
        confirm = self.confirm_password.text()
        
        if not new_pass:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mật khẩu mới!")
            return
        if len(new_pass) < 6:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu phải có ít nhất 6 ký tự!")
            return
        if new_pass != confirm:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp!")
            return
        
        try:
            self.user.update_password(new_pass)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể đổi mật khẩu:\n{str(e)}")


class UserView(QWidget):
    """Main view for user management"""
    
    user_changed = pyqtSignal()
    
    def __init__(self, parent=None, current_user: User = None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self.refresh_data()
    
    def set_current_user(self, user: User):
        self.current_user = user
    
    def _setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        title_label = QLabel("👥 Quản lý Tài khoản")
        title_label.setObjectName("title")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Thêm tài khoản")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_user)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # --- Filter Card ---
        filter_frame = QGroupBox()
        filter_frame.setTitle("")
        filter_frame.setStyleSheet("""
            QGroupBox {
                border: 1px solid palette(mid);
                border-radius: 8px;
                background-color: palette(window);
                margin-top: 0px;
            }
        """)
        
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm theo tên hoặc username...")
        self.search_input.setMinimumWidth(250)
        self.search_input.setMinimumHeight(45)
        self.search_input.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_input)
        
        self.role_filter = QComboBox()
        self.role_filter.setMinimumHeight(45)
        self.role_filter.addItem("--- Tất cả vai trò ---", None)
        for role, display_name in ROLE_DISPLAY_NAMES.items():
            self.role_filter.addItem(display_name, role)
        self.role_filter.currentIndexChanged.connect(self.refresh_data)
        self.role_filter.setFixedWidth(200)
        filter_layout.addWidget(self.role_filter)
        
        filter_layout.addStretch()
        
        self.show_inactive = QCheckBox("Hiển thị tài khoản đã khóa")
        self.show_inactive.stateChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.show_inactive)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Làm mới danh sách")
        refresh_btn.setFixedSize(45, 45)
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_frame)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Username", "Họ tên", "Vai trò", "Đơn vị", "Email", "Trạng thái", "Thao tác"
        ])
        
        # [FIX FINAL] Style tối giản để tương thích hoàn hảo Dark Mode
        # self.table.setStyleSheet("""
        #     QTableWidget {
        #         border: 1px solid palette(mid);
        #         border-radius: 8px;
        #         background-color: palette(base);
        #         alternate-background-color: palette(alternate-base); /* Quan trọng cho Dark Mode */
        #         gridline-color: palette(mid);
        #     }
        #     QHeaderView::section {
        #         padding: 8px;
        #         border: none;
        #         border-bottom: 2px solid palette(mid);
        #         background-color: transparent;
        #         font-weight: bold;
        #     }
        #     /* XÓA ĐOẠN QTableWidget::item cũ đi để không bị lỗi nền trắng */
            
        #     /* Chỉ tùy chỉnh trạng thái được chọn */
        #     QTableWidget::item:selected {
        #         background-color: rgba(41, 128, 185, 0.3); /* Xanh trong suốt */
        #         color: palette(text);
        #         border: 1px solid #2980b9;
        #     }
        # """)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 210)
        
        self.table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setObjectName("subtitle")
        self.stats_label.setStyleSheet("font-size: 12px; opacity: 0.7;")
        layout.addWidget(self.stats_label)
    
    def refresh_data(self):
        """Refresh user list"""
        include_inactive = self.show_inactive.isChecked()
        role_filter = self.role_filter.currentData()
        
        if role_filter:
            users = User.get_by_role(role_filter)
        else:
            users = User.get_all(include_inactive=include_inactive)
        
        self._populate_table(users)
        
        total = User.count(include_inactive=True)
        active = User.count(include_inactive=False)
        self.stats_label.setText(f"Tổng cộng: {total} tài khoản ({active} đang hoạt động)")
    
    def _populate_table(self, users):
        """Populate table with user data"""
        self.table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.table.setRowHeight(row, 50)
            
            # ID
            id_item = QTableWidgetItem(str(user.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Username
            username_item = QTableWidgetItem(user.username)
            if user.role == UserRole.ADMIN:
                username_item.setForeground(QColor("#c0392b"))
                username_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(row, 1, username_item)
            
            # Full name
            self.table.setItem(row, 2, QTableWidgetItem(user.full_name or "-"))
            
            # Role
            role_item = QTableWidgetItem(user.get_role_display())
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, role_item)
            
            # Unit
            unit_name = "-"
            if user.unit_id:
                unit = Unit.get_by_id(user.unit_id)
                if unit:
                    unit_name = unit.name
            self.table.setItem(row, 4, QTableWidgetItem(unit_name))
            
            # Email
            self.table.setItem(row, 5, QTableWidgetItem(user.email or "-"))
            
            # Status
            status_text = "Đang hoạt động" if user.is_active else "Đã khóa"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if user.is_active:
                status_item.setForeground(QColor("#27ae60"))
            else:
                status_item.setForeground(QColor("#7f8c8d"))
            self.table.setItem(row, 6, status_item)
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setSpacing(5)
            
            # Xem
            view_btn = QPushButton("Xem")
            view_btn.setToolTip("Xem chi tiết")
            view_btn.setFixedSize(40, 28)
            view_btn.setObjectName("tableBtnView") 
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda checked, u=user: self._view_user_detail(u))
            action_layout.addWidget(view_btn)
            
            # Sửa
            edit_btn = QPushButton("Sửa")
            edit_btn.setToolTip("Sửa thông tin")
            edit_btn.setFixedSize(40, 28)
            edit_btn.setObjectName("tableBtn")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, u=user: self._edit_user(u))
            action_layout.addWidget(edit_btn)
            
            # MK
            pwd_btn = QPushButton("MK")
            pwd_btn.setToolTip("Đổi mật khẩu")
            pwd_btn.setFixedSize(35, 28)
            pwd_btn.setObjectName("tableBtn")
            pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pwd_btn.clicked.connect(lambda checked, u=user: self._change_password(u))
            action_layout.addWidget(pwd_btn)
            
            # Xóa
            delete_btn = QPushButton("Xóa")
            delete_btn.setToolTip("Khóa tài khoản")
            delete_btn.setFixedSize(40, 28)
            delete_btn.setObjectName("tableBtnDanger")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, u=user: self._delete_user(u))
            
            action_layout.addWidget(delete_btn)
            
            action_layout.addStretch()
            self.table.setCellWidget(row, 7, action_widget)
    
    def _on_search(self, text):
        if text.strip():
            users = User.search(text.strip())
        else:
            include_inactive = self.show_inactive.isChecked()
            users = User.get_all(include_inactive=include_inactive)
        self._populate_table(users)
    
    def _add_user(self):
        dialog = UserDialog(self, current_user=self.current_user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.user_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã tạo tài khoản mới!")
            
    def _view_user_detail(self, user: User):
        """[MỚI] Xem chi tiết tài khoản"""
        fresh_user = User.get_by_id(user.id)
        if fresh_user:
            dialog = UserDetailDialog(self, fresh_user)
            dialog.exec()
    
    def _edit_user(self, user: User):
        dialog = UserDialog(self, user=user, current_user=self.current_user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.user_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin tài khoản!")
    
    def _change_password(self, user: User):
        dialog = ChangePasswordDialog(self, user=user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Thành công", "Đã đổi mật khẩu thành công!")
    
    def _delete_user(self, user: User):
        if user.role == UserRole.SUPERADMIN:
            QMessageBox.warning(self, "Không thể xóa", "Không thể xóa tài khoản Quản trị viên cao cấp!")
            return
        
        reply = QMessageBox.question(
            self, "Xác nhận khóa",
            f"Bạn có chắc muốn khóa tài khoản '{user.username}'?\n(Tài khoản sẽ không bị xóa hoàn toàn)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            user.delete()
            self.refresh_data()
            self.user_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã khóa tài khoản!")
            
    def _on_row_double_click(self, index):
        """Handle double click on row"""
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            user_id = int(id_item.text())
            user = User.get_by_id(user_id)
            if user:
                self._view_user_detail(user)