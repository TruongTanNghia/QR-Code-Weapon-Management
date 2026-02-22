"""
Main Window - Application main window with sidebar navigation
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction

from .styles import StyleSheet
from .dashboard_view import DashboardView
from .equipment_view import EquipmentView
from .scan_view import ScanView
from .unit_view import UnitView
from .user_view import UserView
from .category_view import CategoryView
from .maintenance_type_view import MaintenanceTypeView
from .audit_view import AuditView # [MỚI] Import Giao diện Nhật ký
from ..models.user import User, UserRole
from ..config import APP_NAME, APP_VERSION, DEFAULT_THEME


class MainWindow(QMainWindow):
    """
    Main application window with sidebar navigation
    """
    
    def __init__(self, current_user: User = None):
        super().__init__()
        self.current_user = current_user
        self.current_theme = DEFAULT_THEME
        self.stylesheet = StyleSheet(self.current_theme)
        self.logout_requested = False
        
        self.nav_buttons = []
        self.admin_nav_buttons = []
        self.manager_nav_buttons = []
        
        self._setup_ui()
        self._apply_styles()
        self._update_ui_for_permissions()
    
    def set_current_user(self, user: User):
        """Set current logged in user"""
        self.current_user = user
        self._update_ui_for_permissions()
        if hasattr(self, 'user_view'):
            self.user_view.set_current_user(user)
    
    def _setup_ui(self):
        """Setup the main UI structure"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        from .maintenance_view import MaintenanceListView
        
        # Khởi tạo các View
        self.dashboard_view = DashboardView(self)
        self.equipment_view = EquipmentView(self)
        self.maintenance_view = MaintenanceListView(self)
        self.scan_view = ScanView(self)
        self.category_view = CategoryView(self)
        self.maintenance_type_view = MaintenanceTypeView(self)
        self.unit_view = UnitView(self)
        self.user_view = UserView(self, current_user=self.current_user)
        self.audit_view = AuditView(self) # [MỚI] Khởi tạo Audit View
        
        # Thêm vào Stack
        self.content_stack.addWidget(self.dashboard_view)   # 0
        self.content_stack.addWidget(self.equipment_view)   # 1
        self.content_stack.addWidget(self.maintenance_view) # 2
        self.content_stack.addWidget(self.scan_view)        # 3
        self.content_stack.addWidget(self.category_view)    # 4
        self.content_stack.addWidget(self.maintenance_type_view) # 5
        self.content_stack.addWidget(self.unit_view)        # 6
        self.content_stack.addWidget(self.user_view)        # 7
        self.content_stack.addWidget(self.audit_view)       # 8 [MỚI]
        
        self._setup_menu()
        
        self._switch_view(0)
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
    
    def _create_sidebar(self) -> QFrame:
        """Create the sidebar navigation"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)
        
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setObjectName("userInfo")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setWordWrap(True)
        layout.addWidget(self.user_info_label)
        
        layout.addSpacing(20)
        
        # [MỚI] Thêm tab Nhật ký hệ thống vào vị trí số 8
        nav_items = [
            ("🏠  Tổng quan", 0, True, False),
            ("📦  Quản lý Trang bị", 1, True, False),
            ("🛠️  Bảo dưỡng", 2, True, False),
            ("📷  Quét mã QR", 3, True, False),
            ("📋  Loại Trang bị", 4, True, False),
            ("🔧  Loại Công việc", 5, True, False),
            ("🏢  Quản lý Đơn vị", 6, True, False),
            ("👥  Quản lý Tài khoản", 7, False, True),
            ("📜  Nhật ký Hệ thống", 8, False, True), # Chỉ Admin thấy
        ]
        
        for text, index, is_manager, is_admin in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._on_nav_click(i))
            layout.addWidget(btn)
            
            self.nav_buttons.append(btn)
            
            if is_admin:
                self.admin_nav_buttons.append(btn)
            elif is_manager:
                self.manager_nav_buttons.append(btn)
        
        layout.addStretch()
        
        # self.theme_btn = QPushButton("🌙  Đổi giao diện")
        # self.theme_btn.setObjectName("sidebarBtn")
        # self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # self.theme_btn.clicked.connect(self._toggle_theme)
        # layout.addWidget(self.theme_btn)
        
        self.logout_btn = QPushButton("🚪  Đăng xuất")
        self.logout_btn.setObjectName("sidebarBtn")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.clicked.connect(self._on_logout)
        layout.addWidget(self.logout_btn)
        
        version_label = QLabel(f"Phiên bản {APP_VERSION}")
        version_label.setObjectName("subtitle")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        return sidebar
    
    def _setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Tệp")
        export_action = QAction("Xuất danh sách PDF", self)
        export_action.triggered.connect(self._on_export_list)
        file_menu.addAction(export_action)
        
        export_qr_action = QAction("Xuất bảng mã QR", self)
        export_qr_action.triggered.connect(self._on_export_qr_sheet)
        file_menu.addAction(export_qr_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Thoát", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu("Xem")
        self.admin_actions = []
        
        self.category_action = QAction("Quản lý LTB", self)
        self.category_action.triggered.connect(lambda: self._on_nav_click(4))
        view_menu.addAction(self.category_action)
        self.admin_actions.append(self.category_action)
        
        self.mtype_action = QAction("Quản lý LCV", self)
        self.mtype_action.triggered.connect(lambda: self._on_nav_click(5))
        view_menu.addAction(self.mtype_action)
        self.admin_actions.append(self.mtype_action)
        
        self.unit_action = QAction("Quản lý ĐV", self)
        self.unit_action.triggered.connect(lambda: self._on_nav_click(6))
        view_menu.addAction(self.unit_action)
        self.admin_actions.append(self.unit_action)
        
        self.user_action = QAction("Quản lý TK", self)
        self.user_action.triggered.connect(lambda: self._on_nav_click(7))
        view_menu.addAction(self.user_action)
        self.admin_actions.append(self.user_action)
        
        help_menu = menubar.addMenu("Trợ giúp")
        about_action = QAction("Giới thiệu", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _update_ui_for_permissions(self):
        if not self.current_user:
            return
        
        role_display = self.current_user.get_role_display()
        self.user_info_label.setText(
            f"👤 {self.current_user.full_name or self.current_user.username}\n"
            f"({role_display})"
        )
        
        role = self.current_user.role
        
        if role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            for btn in self.nav_buttons:
                btn.setVisible(True)
            for action in self.admin_actions:
                action.setVisible(True)
                
        elif role == UserRole.MANAGER:
            for btn in self.nav_buttons:
                if btn in self.admin_nav_buttons:
                    btn.setVisible(False)
                else:
                    btn.setVisible(True)
            
            self.user_action.setVisible(False)
            self.category_action.setVisible(True)
            self.mtype_action.setVisible(True)
            self.unit_action.setVisible(True)
            
        else:
            for btn in self.nav_buttons:
                btn.setVisible(False)
            
            if len(self.nav_buttons) > 3:
                self.nav_buttons[3].setVisible(True)
                
            for action in self.admin_actions:
                action.setVisible(False)
            
            self._switch_view(3)
            self.nav_buttons[3].setChecked(True)
    
    def _on_nav_click(self, index: int):
        if not self.current_user:
            return
        role = self.current_user.role
        if role == UserRole.VIEWER and index != 3:
            QMessageBox.warning(self, "Không có quyền", "Bạn chỉ có quyền quét mã QR!")
            return
        if role == UserRole.MANAGER and index in [7, 8]: # [MỚI] Manager không được xem Nhật ký
            QMessageBox.warning(self, "Không có quyền", "Chức năng này chỉ dành cho Quản trị viên!")
            return
        
        self._switch_view(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def _switch_view(self, index: int):
        self.content_stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard_view.refresh_data()
        elif index == 1:
            self.equipment_view.refresh_data()
        elif index == 4:
            self.category_view.refresh_data()
        elif index == 5:
            self.maintenance_type_view.refresh_data()
        elif index == 6:
            self.unit_view.refresh_data()
        elif index == 7:
            self.user_view.refresh_data()
        elif index == 8: # [MỚI]
            self.audit_view.refresh_data()
    
    def _toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
            #self.theme_btn.setText("🌙  Chế độ tối")
        else:
            self.current_theme = "dark"
            #self.theme_btn.setText("☀️  Chế độ sáng")
        self._apply_styles()
    
    def _apply_styles(self):
        self.stylesheet.set_theme(self.current_theme)
        self.setStyleSheet(self.stylesheet.get_main_stylesheet())
        if hasattr(self, 'scan_view'):
            self.scan_view.update_styles(self.stylesheet)
    
    def _on_export_list(self):
        self.equipment_view.export_equipment_list()
    
    def _on_export_qr_sheet(self):
        self.equipment_view.export_qr_sheet()
    
    def _on_logout(self):
        reply = QMessageBox.question(
            self,
            "Xác nhận đăng xuất",
            "Bạn có chắc muốn đăng xuất?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'scan_view'):
                self.scan_view.stop_camera()
            self.logout_requested = True
            self.close()
    
    def _show_about(self):
        user_info = ""
        if self.current_user:
            user_info = f"<p><b>Đăng nhập:</b> {self.current_user.username} ({self.current_user.get_role_display()})</p>"
        
        QMessageBox.about(
            self,
            "Giới thiệu",
            f"""<h2>{APP_NAME}</h2>
            <p>Phiên bản: {APP_VERSION}</p>
            {user_info}
            <p>Phần mềm quản lý vũ khí trang bị kỹ thuật thông qua mã QR.</p>
            <p>© 2026 - Tên cá nhân</p>
            """
        )
    
    def navigate_to_equipment_detail(self, equipment_id: int):
        self._on_nav_click(1)
        self.equipment_view.show_equipment_detail(equipment_id)
    
    def closeEvent(self, event):
        if hasattr(self, 'scan_view'):
            self.scan_view.stop_camera()
        event.accept()