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
        
        # [FIX] Khởi tạo các list chứa button để tránh lỗi AttributeError
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
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Import views
        from .maintenance_view import MaintenanceListView
        
        # Create views
        self.dashboard_view = DashboardView(self)
        self.equipment_view = EquipmentView(self)
        self.maintenance_view = MaintenanceListView(self)
        self.scan_view = ScanView(self)
        self.category_view = CategoryView(self)
        self.maintenance_type_view = MaintenanceTypeView(self)
        self.unit_view = UnitView(self)
        self.user_view = UserView(self, current_user=self.current_user)
        
        # Add views to stack
        self.content_stack.addWidget(self.dashboard_view)   # 0
        self.content_stack.addWidget(self.equipment_view)   # 1
        self.content_stack.addWidget(self.maintenance_view) # 2
        self.content_stack.addWidget(self.scan_view)        # 3
        self.content_stack.addWidget(self.category_view)    # 4
        self.content_stack.addWidget(self.maintenance_type_view) # 5
        self.content_stack.addWidget(self.unit_view)        # 6
        self.content_stack.addWidget(self.user_view)        # 7
        
        # Setup menu bar
        self._setup_menu()
        
        # Set initial view
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
        
        # App title
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # User info
        self.user_info_label = QLabel("")
        self.user_info_label.setObjectName("userInfo")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setWordWrap(True)
        layout.addWidget(self.user_info_label)
        
        layout.addSpacing(20)
        
        # [FIX] Định nghĩa các nút và quyền truy cập
        # Format: (Text, View_Index, Is_Manager_Access, Is_Admin_Access_Only)
        nav_items = [
            ("🏠  Tổng quan", 0, True, False),
            ("📦  Quản lý Trang bị", 1, True, False),
            ("🛠️  Bảo dưỡng", 2, True, False),
            ("📷  Quét mã QR", 3, True, False), # Ai cũng quét được
            ("📋  Loại Trang bị", 4, True, False),
            ("🔧  Loại Công việc", 5, True, False),
            ("🏢  Quản lý Đơn vị", 6, True, False),
            ("👥  Quản lý Tài khoản", 7, False, True), # Chỉ Admin/Superadmin
        ]
        
        for text, index, is_manager, is_admin in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._on_nav_click(i))
            layout.addWidget(btn)
            
            self.nav_buttons.append(btn)
            
            # Phân loại nút vào danh sách để quản lý ẩn/hiện
            if is_admin:
                self.admin_nav_buttons.append(btn)
            elif is_manager:
                self.manager_nav_buttons.append(btn)
        
        layout.addStretch()
        
        # Theme toggle
        self.theme_btn = QPushButton("🌙  Đổi giao diện")
        self.theme_btn.setObjectName("sidebarBtn")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)
        
        # Logout button
        self.logout_btn = QPushButton("🚪  Đăng xuất")
        self.logout_btn.setObjectName("sidebarBtn")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.clicked.connect(self._on_logout)
        layout.addWidget(self.logout_btn)
        
        # Version label
        version_label = QLabel(f"Phiên bản {APP_VERSION}")
        version_label.setObjectName("subtitle")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        return sidebar
    
    def _setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
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
        
        # View menu
        view_menu = menubar.addMenu("Xem")
        
        # Admin/Manager menu items
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
        
        # Help menu
        help_menu = menubar.addMenu("Trợ giúp")
        about_action = QAction("Giới thiệu", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _update_ui_for_permissions(self):
        """Update UI based on user permissions"""
        if not self.current_user:
            return
        
        # Update user info
        role_display = self.current_user.get_role_display()
        self.user_info_label.setText(
            f"👤 {self.current_user.full_name or self.current_user.username}\n"
            f"({role_display})"
        )
        
        role = self.current_user.role
        
        # [FIX] Logic quyền hạn:
        # SUPERADMIN & ADMIN: Thấy tất cả
        if role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            for btn in self.nav_buttons:
                btn.setVisible(True)
            for action in self.admin_actions:
                action.setVisible(True)
                
        # MANAGER: Thấy Manager Buttons + Scan, Ẩn Admin Buttons
        elif role == UserRole.MANAGER:
            for btn in self.nav_buttons:
                if btn in self.admin_nav_buttons:
                    btn.setVisible(False)
                else:
                    btn.setVisible(True)
            
            # Menu actions
            self.user_action.setVisible(False)
            self.category_action.setVisible(True)
            self.mtype_action.setVisible(True)
            self.unit_action.setVisible(True)
            
        # VIEWER: Chỉ thấy Scan
        else:
            for btn in self.nav_buttons:
                btn.setVisible(False)
            
            # Nút Scan luôn ở index 3
            if len(self.nav_buttons) > 3:
                self.nav_buttons[3].setVisible(True)
                
            # Hide all admin menu actions
            for action in self.admin_actions:
                action.setVisible(False)
            
            # Switch to scan view
            self._switch_view(3)
            self.nav_buttons[3].setChecked(True)
    
    def _on_nav_click(self, index: int):
        """Handle navigation button click"""
        if not self.current_user:
            return
        
        role = self.current_user.role
        
        # Permission check
        # Viewer only Scan (3)
        if role == UserRole.VIEWER and index != 3:
            QMessageBox.warning(self, "Không có quyền", "Bạn chỉ có quyền quét mã QR!")
            return
            
        # Manager restricted from User Management (7)
        if role == UserRole.MANAGER and index == 7:
            QMessageBox.warning(self, "Không có quyền", "Chức năng này chỉ dành cho Quản trị viên!")
            return
        
        self._switch_view(index)
        
        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def _switch_view(self, index: int):
        """Switch to a specific view"""
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
    
    def _toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.theme_btn.setText("🌙  Chế độ tối")
        else:
            self.current_theme = "dark"
            self.theme_btn.setText("☀️  Chế độ sáng")
        
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