"""
Audit Log View - Interface to view system activity logs
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QFrame,
    QAbstractItemView, QDateEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

from ..controllers.audit_controller import AuditController

# Bản dịch hành động
ACTION_TRANSLATION = {
    "CREATE": "Thêm mới",
    "UPDATE": "Cập nhật",
    "DELETE": "Xóa"
    # "LOGIN": "Đăng nhập",
    # "EXPORT": "Xuất file"
}

# [MỚI] Bản dịch đối tượng
TARGET_TRANSLATION = {
    "Equipment": "Trang bị",
    "Maintenance": "Bảo dưỡng",
    "Loan": "Cho mượn",
    "User": "Người dùng",
    "Unit": "Đơn vị",
    "Category": "Loại trang bị",
    "MaintenanceType": "Loại công việc"
}

class AuditView(QWidget):
    """
    View displaying system audit logs for Admins
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = AuditController()
        self.all_logs = []
        self.current_page = 1
        self.page_size = 15 # Hiển thị nhiều log hơn trên 1 trang
        self.total_pages = 1
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        self.setStyleSheet(self.styleSheet() + """
            QPushButton#pagingBtn {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                color: palette(text);
                font-weight: bold;
                min-width: 30px;
            }
            QPushButton#pagingBtn:hover {
                background-color: palette(midlight);
                border: 1px solid palette(highlight);
            }
            QPushButton#pagingBtn:disabled {
                background-color: palette(window);
                color: palette(mid);
                border: 1px solid palette(midlight);
            }
        """)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📜 Nhật ký hệ thống (Audit Log)")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)) 
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Filters
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        filter_layout = QVBoxLayout(filter_frame)
        
        row1_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm người dùng, chi tiết...")
        self.search_input.textChanged.connect(self.refresh_data)
        self.search_input.setMinimumWidth(300)
        row1_layout.addWidget(self.search_input)
        
        row1_layout.addWidget(QLabel("Thao tác:"))
        self.action_filter = QComboBox()
        self.action_filter.addItem("Tất cả", None)
        for eng, vn in ACTION_TRANSLATION.items():
            self.action_filter.addItem(vn, eng)
        self.action_filter.currentIndexChanged.connect(self.refresh_data)
        row1_layout.addWidget(self.action_filter)
        
        row1_layout.addStretch()
        filter_layout.addLayout(row1_layout)
        
        row2_layout = QHBoxLayout()
        self.date_filter_check = QCheckBox("Lọc theo thời gian:")
        self.date_filter_check.toggled.connect(self._on_date_filter_toggle)
        row2_layout.addWidget(self.date_filter_check)
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.setDate(QDate.currentDate().addDays(-7))
        self.from_date.setEnabled(False)
        self.from_date.dateChanged.connect(self.refresh_data)
        row2_layout.addWidget(QLabel("Từ:"))
        row2_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setEnabled(False)
        self.to_date.dateChanged.connect(self.refresh_data)
        row2_layout.addWidget(QLabel("Đến:"))
        row2_layout.addWidget(self.to_date)
        
        row2_layout.addStretch()
        
        refresh_btn = QPushButton("⟳ Làm mới")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        row2_layout.addWidget(refresh_btn)
        
        filter_layout.addLayout(row2_layout)
        layout.addWidget(filter_frame)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Thời gian", "Người dùng", "Thao tác", "Đối tượng", "Chi tiết"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120) # [FIX] Nới rộng một chút cho chữ tiếng Việt
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        
        layout.addWidget(self.table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        self.count_label = QLabel("Tổng: 0 bản ghi")
        self.count_label.setObjectName("subtitle")
        pagination_layout.addWidget(self.count_label)
        pagination_layout.addStretch()
        
        self.first_page_btn = QPushButton("<<")
        self.first_page_btn.setObjectName("pagingBtn")
        self.first_page_btn.clicked.connect(self._first_page)
        pagination_layout.addWidget(self.first_page_btn)
        
        self.prev_page_btn = QPushButton("<")
        self.prev_page_btn.setObjectName("pagingBtn")
        self.prev_page_btn.clicked.connect(self._prev_page)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel("1 / 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(80)
        pagination_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton(">")
        self.next_page_btn.setObjectName("pagingBtn")
        self.next_page_btn.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.next_page_btn)
        
        self.last_page_btn = QPushButton(">>")
        self.last_page_btn.setObjectName("pagingBtn")
        self.last_page_btn.clicked.connect(self._last_page)
        pagination_layout.addWidget(self.last_page_btn)
        
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

    def _on_date_filter_toggle(self, checked):
        self.from_date.setEnabled(checked)
        self.to_date.setEnabled(checked)
        self.refresh_data()

    def refresh_data(self):
        keyword = self.search_input.text().strip()
        action = self.action_filter.currentData()
        
        from_dt = None
        to_dt = None
        if self.date_filter_check.isChecked():
            from_dt = self.from_date.date().toPyDate()
            to_dt = self.to_date.date().toPyDate()
            
        self.all_logs = self.controller.get_logs(keyword, action, from_dt, to_dt)
        self.current_page = 1
        self._update_pagination()
        
    def _populate_table(self, logs: list):
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.table.setRowHeight(row, 40)
            
            id_item = QTableWidgetItem(str(log.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Format date
            date_str = "-"
            if log.created_at:
                try:
                    if isinstance(log.created_at, str):
                        dt = datetime.strptime(log.created_at, "%Y-%m-%d %H:%M:%S")
                        date_str = dt.strftime("%d/%m/%Y %H:%M")
                    else:
                        date_str = log.created_at.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = str(log.created_at)[:16]
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            self.table.setItem(row, 2, QTableWidgetItem(log.username or "-"))
            
            # Format Action Color
            action_vn = ACTION_TRANSLATION.get(log.action, log.action)
            action_item = QTableWidgetItem(action_vn)
            action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if log.action == "CREATE": action_item.setForeground(QColor("#4CAF50"))
            elif log.action == "UPDATE": action_item.setForeground(QColor("#FF9800"))
            elif log.action == "DELETE": action_item.setForeground(QColor("#F44336"))
            self.table.setItem(row, 3, action_item)
            
            # [FIX] Format Target Type to Vietnamese
            target_vn = TARGET_TRANSLATION.get(log.target_type, log.target_type)
            self.table.setItem(row, 4, QTableWidgetItem(target_vn))
            
            details_item = QTableWidgetItem(log.details)
            details_item.setToolTip(log.details) # Hover to see full
            self.table.setItem(row, 5, details_item)

    def _update_pagination(self):
        total = len(self.all_logs)
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.all_logs[start:end]
        
        self._populate_table(page_data)
        self.count_label.setText(f"Tổng: {total} bản ghi")
        self.page_label.setText(f"{self.current_page} / {self.total_pages}")
        
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        self.last_page_btn.setEnabled(self.current_page < self.total_pages)
    
    def _first_page(self):
        self.current_page = 1
        self._update_pagination()
    
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._update_pagination()
    
    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_pagination()
    
    def _last_page(self):
        self.current_page = self.total_pages
        self._update_pagination()