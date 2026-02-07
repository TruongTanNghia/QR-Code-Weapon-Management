"""
Dashboard View - Main overview screen with statistics
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from datetime import datetime

from ..models.database import Database
from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..config import ASSETS_DIR  # [MỚI] Import đường dẫn assets


class DashboardView(QWidget):
    """
    Dashboard view showing statistics and recent activities
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.db = Database()
        self._setup_ui()
        self.refresh_data()
    
    def _setup_ui(self):
        """Setup the dashboard UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # --- HEADER SECTION (Sửa đổi để thêm Logo) ---
        header_layout = QHBoxLayout()
        
        # [MỚI] Thêm Logo vào đầu trang
        logo_label = QLabel()
        logo_path = ASSETS_DIR / "logo.png"
        
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Resize logo vừa phải (khoảng 55x55 px) để cân đối với tiêu đề
            scaled_pixmap = pixmap.scaled(
                55, 55,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
            header_layout.addWidget(logo_label)
            header_layout.addSpacing(15) # Khoảng cách giữa Logo và Tiêu đề
        else:
            # Fallback nếu không thấy logo thì dùng emoji cũ
            header_layout.addWidget(QLabel("📊"))
        
        # Tiêu đề chính
        title = QLabel("TỔNG QUAN HỆ THỐNG QUẢN LÝ VKTBKT")
        title.setObjectName("title")
        # Tăng kích thước font một chút cho cân xứng với logo
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;") # Màu xanh đen đậm đà hơn
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # --- STATISTICS CARDS ---
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(20)
        
        # Create stat cards (will be populated in refresh_data)
        self.stat_cards = {}
        
        card_configs = [
            ("total", "📦 Tổng thiết bị", "0"),
            ("good", "✅ Tốt (Cấp 1-2)", "0"),
            ("maintenance", "⚠️ Cần chú ý (Cấp 4-5)", "0"),
            ("active_logs", "📝 Công việc đang thực hiện", "0")
        ]
        
        for key, label, value in card_configs:
            card = self._create_stat_card(label, value)
            self.stat_cards[key] = card
            self.stats_layout.addWidget(card)
        
        main_layout.addLayout(self.stats_layout)
        
        # --- CONTENT AREA (Two Columns) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left column - Charts/Tables breakdown
        left_column = QVBoxLayout()
        
        # 1. Status Table
        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        
        status_title = QLabel("📈 Phân loại theo tình trạng")
        status_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        status_layout.addWidget(status_title)
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(2)
        self.status_table.setHorizontalHeaderLabels(["Tình trạng", "Số lượng"])
        self.status_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.status_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.status_table.setColumnWidth(1, 100)
        self.status_table.verticalHeader().setVisible(False)
        self.status_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.status_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.status_table.setMaximumHeight(250)
        self.status_table.setAlternatingRowColors(True) # Thêm màu xen kẽ cho đẹp
        status_layout.addWidget(self.status_table)
        
        left_column.addWidget(status_card)
        
        # 2. Category Table
        category_card = QFrame()
        category_card.setObjectName("card")
        category_layout = QVBoxLayout(category_card)
        
        category_title = QLabel("📂 Phân loại theo danh mục")
        category_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        category_layout.addWidget(category_title)
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(2)
        self.category_table.setHorizontalHeaderLabels(["Danh mục", "Số lượng"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.category_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.category_table.setColumnWidth(1, 100)
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.category_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.category_table.setMaximumHeight(250)
        self.category_table.setAlternatingRowColors(True)
        category_layout.addWidget(self.category_table)
        
        left_column.addWidget(category_card)
        
        content_layout.addLayout(left_column)
        
        # Right column - Recent activities & Actions
        right_column = QVBoxLayout()
        
        # 3. Recent Activity
        activity_card = QFrame()
        activity_card.setObjectName("card")
        activity_layout = QVBoxLayout(activity_card)
        
        activity_title = QLabel("🔧 Hoạt động bảo dưỡng trong ngày")
        activity_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        activity_layout.addWidget(activity_title)
        
        # Hiển thị ngày hiện tại
        self.today_label = QLabel(f"Ngày: {datetime.now().strftime('%d/%m/%Y')}")
        self.today_label.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: bold;")
        activity_layout.addWidget(self.today_label)
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Thiết bị", "Loại công việc", "Ngày", "Trạng thái"])
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.activity_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.activity_table.setColumnWidth(2, 100)
        self.activity_table.setColumnWidth(3, 120)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.setAlternatingRowColors(True)
        activity_layout.addWidget(self.activity_table)
        
        right_column.addWidget(activity_card)
        
        # 4. Quick actions
        actions_card = QFrame()
        actions_card.setObjectName("card")
        actions_layout = QVBoxLayout(actions_card)
        
        actions_title = QLabel("⚡ Thao tác nhanh")
        actions_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        actions_layout.addWidget(actions_title)
        
        actions_btn_layout = QHBoxLayout()
        actions_btn_layout.setSpacing(15)
        
        add_btn = QPushButton("➕ Thêm thiết bị")
        add_btn.setObjectName("primaryBtn") # Style nổi bật
        add_btn.setMinimumHeight(40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_equipment)
        actions_btn_layout.addWidget(add_btn)
        
        scan_btn = QPushButton("📷 Quét mã QR")
        scan_btn.setObjectName("primaryBtn")
        scan_btn.setMinimumHeight(40)
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.clicked.connect(self._on_scan)
        actions_btn_layout.addWidget(scan_btn)
        
        export_btn = QPushButton("📄 Xuất báo cáo")
        export_btn.setObjectName("secondaryBtn")
        export_btn.setMinimumHeight(40)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._on_export)
        actions_btn_layout.addWidget(export_btn)
        
        actions_layout.addLayout(actions_btn_layout)
        
        right_column.addWidget(actions_card)
        right_column.addStretch()
        
        content_layout.addLayout(right_column)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
    
    def _create_stat_card(self, label: str, value: str) -> QFrame:
        """Create a statistics card widget"""
        card = QFrame()
        card.setObjectName("statCard")
        # Style cho card thống kê (nếu chưa có trong styles.py thì có thể inline ở đây)
        card.setStyleSheet("""
            #statCard {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 10px;
            }
            #statCard:hover {
                border: 1px solid palette(highlight);
                background-color: palette(midlight);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #2980b9;") # Màu xanh điểm nhấn
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        text_label = QLabel(label)
        text_label.setObjectName("statLabel")
        text_label.setFont(QFont("Segoe UI", 11))
        text_label.setStyleSheet("color: palette(text);")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        stats = self.db.get_statistics()
        
        # Update stat cards
        self.stat_cards["total"].value_label.setText(str(stats['total_equipment']))
        
        # Count equipment with good status (Cấp 1, Cấp 2)
        good_count = stats['by_status'].get('Cấp 1', 0) + stats['by_status'].get('Cấp 2', 0)
        self.stat_cards["good"].value_label.setText(str(good_count))
        
        # Count equipment needing attention (Cấp 4, Cấp 5)
        maintenance_count = stats['by_status'].get('Cấp 4', 0) + stats['by_status'].get('Cấp 5', 0)
        self.stat_cards["maintenance"].value_label.setText(str(maintenance_count))
        
        self.stat_cards["active_logs"].value_label.setText(str(stats['active_maintenance']))
        
        # Update status table
        self.status_table.setRowCount(len(stats['by_status']))
        for row, (status, count) in enumerate(stats['by_status'].items()):
            self.status_table.setItem(row, 0, QTableWidgetItem(status))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_table.setItem(row, 1, count_item)
        
        # Update category table
        self.category_table.setRowCount(len(stats['by_category']))
        for row, (category, count) in enumerate(stats['by_category'].items()):
            self.category_table.setItem(row, 0, QTableWidgetItem(category))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.category_table.setItem(row, 1, count_item)
        
        # Update today's maintenance activities
        self.today_label.setText(f"Ngày: {datetime.now().strftime('%d/%m/%Y')}")
        logs = MaintenanceLog.get_today()
        self.activity_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            self.activity_table.setItem(row, 0, QTableWidgetItem(log.equipment_name))
            self.activity_table.setItem(row, 1, QTableWidgetItem(log.maintenance_type))
            
            date_str = ""
            if log.start_date:
                if isinstance(log.start_date, str):
                    date_str = log.start_date[:10]
                else:
                    date_str = log.start_date.strftime('%d/%m/%Y')
            self.activity_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            status_item = QTableWidgetItem(log.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Tô màu trạng thái
            if log.status == "Hoàn thành":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
                
            self.activity_table.setItem(row, 3, status_item)
    
    def _on_add_equipment(self):
        """Handle add equipment button click"""
        if self.main_window:
            self.main_window._on_nav_click(1)
            self.main_window.equipment_view.show_add_dialog()
    
    def _on_scan(self):
        """Handle scan button click"""
        if self.main_window:
            self.main_window._on_nav_click(3)  # Scan is now at index 3
    
    def _on_export(self):
        """Handle export button click"""
        if self.main_window:
            self.main_window._on_export_list()