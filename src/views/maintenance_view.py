"""
Maintenance History View - Display and manage maintenance logs for equipment
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QDialog, QMessageBox, QHeaderView, QFrame, QAbstractItemView,
    QDateEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog, MAINTENANCE_STATUS
from ..controllers.maintenance_controller import MaintenanceController
from .maintenance_dialog import MaintenanceDialog
from ..controllers.user_controller import UserController 
from ..models.user import UserRole


class MaintenanceHistoryView(QWidget):
    """
    Widget showing maintenance history for a specific equipment (Inside Detail View)
    """
    
    log_updated = pyqtSignal()
    
    def __init__(self, parent=None, equipment: Equipment = None):
        super().__init__(parent)
        self.equipment = equipment
        self.controller = MaintenanceController()
        self._setup_ui()
        if equipment:
            self.refresh_data()
    
    def set_equipment(self, equipment: Equipment):
        self.equipment = equipment
        self.refresh_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📋 Lịch sử bảo dưỡng")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả trạng thái", None)
        for status in MAINTENANCE_STATUS:
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self.refresh_data)
        header_layout.addWidget(self.status_filter)
        
        # Kiểm tra quyền: Chỉ hiện nút Thêm nếu KHÔNG PHẢI là Viewer
        self.add_btn = QPushButton("+ Thêm")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_maintenance)
        
        current_user = UserController.get_current_user()
        if current_user and current_user.role == UserRole.VIEWER:
            self.add_btn.hide()
        
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Date filter row
        date_filter_layout = QHBoxLayout()
        
        self.date_filter_check = QCheckBox("Lọc theo ngày:")
        self.date_filter_check.toggled.connect(self._on_date_filter_toggle)
        date_filter_layout.addWidget(self.date_filter_check)
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.setDate(QDate.currentDate())
        self.from_date.setEnabled(False)
        self.from_date.dateChanged.connect(self.refresh_data)
        date_filter_layout.addWidget(QLabel("Từ:"))
        date_filter_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setEnabled(False)
        self.to_date.dateChanged.connect(self.refresh_data)
        date_filter_layout.addWidget(QLabel("Đến:"))
        date_filter_layout.addWidget(self.to_date)
        
        date_filter_layout.addStretch()
        layout.addLayout(date_filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Loại công việc", "Ngày bắt đầu", "Ngày kết thúc",
            "KTV", "Trạng thái", "Thao tác"
        ])
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)   # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)   # Loại CV
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   # Ngày BĐ
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)   # Ngày KT
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # KTV (Giãn phần còn lại)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Trạng thái
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)   # Thao tác
        
        # [FIX] Cập nhật lại độ rộng cột chuẩn hơn
        self.table.setColumnWidth(0, 40)  # ID
        self.table.setColumnWidth(1,220) # Công việc (Giảm chút để nhường chỗ)
        self.table.setColumnWidth(2, 110) # [FIX] Ngày BĐ: Tăng lên 110px
        self.table.setColumnWidth(3, 110) # [FIX] Ngày KT: Tăng lên 110px
        # Cột 4 (KTV) tự giãn
        self.table.setColumnWidth(5, 110) # Trạng thái
        self.table.setColumnWidth(6, 160) # Thao tác
        
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
        
        self.stats_label = QLabel()
        self.stats_label.setObjectName("subtitle")
        layout.addWidget(self.stats_label)
    
    def _on_date_filter_toggle(self, checked):
        self.from_date.setEnabled(checked)
        self.to_date.setEnabled(checked)
        self.refresh_data()

    def refresh_data(self):
        if not self.equipment:
            self.table.setRowCount(0)
            self.stats_label.setText("Chưa chọn thiết bị")
            return
        
        if self.date_filter_check.isChecked():
            from_dt = self.from_date.date().toPyDate()
            to_dt = self.to_date.date().toPyDate()
            from_datetime = datetime.combine(from_dt, datetime.min.time())
            to_datetime = datetime.combine(to_dt, datetime.max.time())
            logs = MaintenanceLog.get_by_equipment_and_date(self.equipment.id, from_datetime, to_datetime)
        else:
            logs = MaintenanceLog.get_by_equipment(self.equipment.id)
        
        status_filter = self.status_filter.currentData()
        if status_filter:
            logs = [l for l in logs if l.status == status_filter]
        
        self._populate_table(logs)
        
        total = len(logs)
        active = len([l for l in logs if l.status == "Đang thực hiện"])
        self.stats_label.setText(f"Tổng: {total} | Đang thực hiện: {active}")
    
    def _format_date_val(self, date_val):
        if not date_val:
            return "-"
        if hasattr(date_val, 'strftime'):
            return date_val.strftime("%d/%m/%Y")
        s_date = str(date_val)[:10]
        try:
            if "-" in s_date:
                parts = s_date.split("-")
                if len(parts) == 3:
                    return f"{parts[2]}/{parts[1]}/{parts[0]}"
        except:
            pass
        return s_date

    def _populate_table(self, logs: list):
        self.table.setRowCount(len(logs))
        
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        for row, log in enumerate(logs):
            self.table.setRowHeight(row, 45)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))
            
            type_item = QTableWidgetItem(log.maintenance_type)
            type_item.setToolTip(log.maintenance_type)
            self.table.setItem(row, 1, type_item)
            
            start_str = self._format_date_val(log.start_date)
            self.table.setItem(row, 2, QTableWidgetItem(start_str))
            
            end_str = self._format_date_val(log.end_date)
            self.table.setItem(row, 3, QTableWidgetItem(end_str))
            
            # KTV - Cho phép xuống dòng nếu tên quá dài
            ktv_item = QTableWidgetItem(log.technician_name or "-")
            self.table.setItem(row, 4, ktv_item)
            
            status_item = QTableWidgetItem(log.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if log.status == "Hoàn thành":
                status_item.setForeground(QColor("#4CAF50"))
            elif log.status == "Đang thực hiện":
                status_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row, 5, status_item)
            
            # Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            
            is_completed = (log.status == "Hoàn thành")
            
            if is_completed or not is_viewer:
                if is_completed:
                    view_btn = QPushButton("Xem") 
                    view_btn.setToolTip("Xem chi tiết")
                    view_btn.setFixedSize(60, 28)
                    view_btn.setObjectName("tableBtnView")
                    view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    view_btn.clicked.connect(lambda checked, l=log: self._edit_log(l))
                    action_layout.addWidget(view_btn)
                elif not is_viewer:
                    edit_btn = QPushButton("Sửa")
                    edit_btn.setFixedSize(50, 28)
                    edit_btn.setObjectName("tableBtn")
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.clicked.connect(lambda checked, l=log: self._edit_log(l))
                    action_layout.addWidget(edit_btn)
                    
                    complete_btn = QPushButton("✓")
                    complete_btn.setFixedSize(30, 28)
                    complete_btn.setObjectName("tableBtn")
                    complete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    complete_btn.clicked.connect(lambda checked, l=log: self._quick_complete(l))
                    action_layout.addWidget(complete_btn)
            
            if not is_viewer:
                delete_btn = QPushButton("Xóa")
                delete_btn.setFixedSize(50, 28)
                delete_btn.setObjectName("tableBtnDanger")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.clicked.connect(lambda checked, l=log: self._delete_log(l))
                action_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, action_widget)

    def _on_double_click(self, index):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            log_id = int(id_item.text())
            log = MaintenanceLog.get_by_id(log_id)
            if is_viewer and log and log.status != "Hoàn thành":
                return
            if log: self._edit_log(log)
            
    def _add_maintenance(self):
        if not self.equipment:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn thiết bị!")
            return
        active_log = MaintenanceLog.get_active_by_equipment(self.equipment.id)
        if active_log:
            reply = QMessageBox.question(self, "Thông báo", f"Đang có công việc '{active_log.maintenance_type}'. Cập nhật nó?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._edit_log(active_log)
                return
        dialog = MaintenanceDialog(self, self.equipment)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success, msg, _ = self.controller.create_maintenance_log(self.equipment.id, dialog.get_data_as_dict(), dialog.get_new_equipment_status())
            if success:
                self.refresh_data()
                self.log_updated.emit()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def _edit_log(self, log):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        log = MaintenanceLog.get_by_id(log.id)
        if not log: return
        dialog = MaintenanceDialog(self, self.equipment, log)
        
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            if is_viewer:
                QMessageBox.warning(self, "Không có quyền", "Bạn chỉ có quyền xem!")
                return
            
            new_equip_status = dialog.get_new_equipment_status()
            
            success, msg = self.controller.update_maintenance_log(
                log.id, 
                dialog.get_data_as_dict(),
                new_equip_status
            )
            
            if success:
                self.refresh_data()
                self.log_updated.emit()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)
        elif result == 2:
            if is_viewer:
                return
            self.refresh_data()
            self.log_updated.emit()

    def _quick_complete(self, log):
        reply = QMessageBox.question(self, "Xác nhận", f"Hoàn thành: {log.maintenance_type}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.complete_maintenance(log.id)
            if success: 
                self.refresh_data()
                self.log_updated.emit()

    def _delete_log(self, log):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.delete_maintenance_log(log.id)
            if success: 
                self.refresh_data()
                self.log_updated.emit()


class MaintenanceListView(QWidget):
    """
    Full page view for all maintenance logs
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = MaintenanceController()
        self.all_logs = []
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self._setup_ui()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # [FIX] Thêm Style riêng cho nút phân trang
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
        
        header_layout = QHBoxLayout()
        title = QLabel("🔧 Quản lý Bảo dưỡng")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("↻ Làm mới")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)
        
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm...")
        self.search_input.textChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.search_input)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả", None)
        for status in MAINTENANCE_STATUS:
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.status_filter)
        layout.addLayout(filter_layout)
        
        date_filter_layout = QHBoxLayout()
        self.date_filter_check = QCheckBox("Lọc theo ngày:")
        self.date_filter_check.toggled.connect(self._on_date_filter_toggle)
        date_filter_layout.addWidget(self.date_filter_check)
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setEnabled(False)
        self.from_date.dateChanged.connect(self.refresh_data)
        date_filter_layout.addWidget(QLabel("Từ:"))
        date_filter_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setEnabled(False)
        self.to_date.dateChanged.connect(self.refresh_data)
        date_filter_layout.addWidget(QLabel("Đến:"))
        date_filter_layout.addWidget(self.to_date)
        
        date_filter_layout.addStretch()
        layout.addLayout(date_filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Thiết bị", "Số hiệu", "Loại công việc", 
            "Ngày BĐ", "Ngày KT", "KTV", "Trạng thái", "Thao tác"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch) # KTV
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 220)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(7, 110)
        self.table.setColumnWidth(8, 165)
        
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
        
        # Pagination bar
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        
        self.stats_label = QLabel()
        self.stats_label.setObjectName("subtitle")
        pagination_layout.addWidget(self.stats_label)
        
        pagination_layout.addStretch()
        
        # [FIX] Đặt ID "pagingBtn" cho các nút phân trang
        self.first_page_btn = QPushButton("<<")
        self.first_page_btn.setObjectName("pagingBtn")
        self.first_page_btn.setFixedSize(36, 30)
        self.first_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.first_page_btn.clicked.connect(self._first_page)
        pagination_layout.addWidget(self.first_page_btn)
        
        self.prev_page_btn = QPushButton("<")
        self.prev_page_btn.setObjectName("pagingBtn")
        self.prev_page_btn.setFixedSize(36, 30)
        self.prev_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_page_btn.clicked.connect(self._prev_page)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel("1 / 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(80)
        pagination_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton(">")
        self.next_page_btn.setObjectName("pagingBtn")
        self.next_page_btn.setFixedSize(36, 30)
        self.next_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_page_btn.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.next_page_btn)
        
        self.last_page_btn = QPushButton(">>")
        self.last_page_btn.setObjectName("pagingBtn")
        self.last_page_btn.setFixedSize(36, 30)
        self.last_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.last_page_btn.clicked.connect(self._last_page)
        pagination_layout.addWidget(self.last_page_btn)
        
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
    
    def _on_date_filter_toggle(self, checked):
        self.from_date.setEnabled(checked)
        self.to_date.setEnabled(checked)
        self.refresh_data()

    def refresh_data(self):
        if self.date_filter_check.isChecked():
            from_dt = self.from_date.date().toPyDate()
            to_dt = self.to_date.date().toPyDate()
            from_datetime = datetime.combine(from_dt, datetime.min.time())
            to_datetime = datetime.combine(to_dt, datetime.max.time())
            logs = MaintenanceLog.get_by_date_range(from_datetime, to_datetime)
        else:
            logs = MaintenanceLog.get_all(limit=500)
        
        status_filter = self.status_filter.currentData()
        if status_filter:
            logs = [l for l in logs if l.status == status_filter]
        search = self.search_input.text().strip().lower()
        if search:
            logs = [l for l in logs if search in l.equipment_name.lower() or search in l.equipment_serial.lower()]
        
        self.all_logs = logs
        self.current_page = 1
        self._update_pagination()
        total = len(logs)
        active = len([l for l in logs if l.status == "Đang thực hiện"])
        self.stats_label.setText(f"Tổng: {total} | Đang thực hiện: {active}")

    # [FIX] Helper format date
    def _format_date_val(self, date_val):
        if not date_val: return "-"
        if hasattr(date_val, 'strftime'): return date_val.strftime("%d/%m/%Y")
        s = str(date_val)[:10]
        try:
            if "-" in s:
                p = s.split("-")
                return f"{p[2]}/{p[1]}/{p[0]}"
        except: pass
        return s

    def _populate_table(self, logs: list):
        self.table.setRowCount(len(logs))
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        for row, log in enumerate(logs):
            self.table.setRowHeight(row, 50)
            self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))
            self.table.setItem(row, 1, QTableWidgetItem(log.equipment_name))
            self.table.setItem(row, 2, QTableWidgetItem(log.equipment_serial))
            type_item = QTableWidgetItem(log.maintenance_type)
            type_item.setToolTip(log.maintenance_type)
            self.table.setItem(row, 3, type_item)
            self.table.setItem(row, 4, QTableWidgetItem(self._format_date_val(log.start_date)))
            self.table.setItem(row, 5, QTableWidgetItem(self._format_date_val(log.end_date)))
            self.table.setItem(row, 6, QTableWidgetItem(log.technician_name or "-"))
            status_item = QTableWidgetItem(log.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if log.status == "Hoàn thành": status_item.setForeground(QColor("#4CAF50"))
            elif log.status == "Đang thực hiện": status_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row, 7, status_item)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            is_completed = (log.status == "Hoàn thành")
            
            if is_completed or not is_viewer:
                if is_completed:
                    view_btn = QPushButton("Xem") 
                    view_btn.setFixedSize(60, 28)
                    view_btn.setObjectName("tableBtnView")
                    view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    view_btn.clicked.connect(lambda checked, l=log: self._edit_log(l))
                    action_layout.addWidget(view_btn)
                elif not is_viewer:
                    edit_btn = QPushButton("Sửa")
                    edit_btn.setFixedSize(50, 28)
                    edit_btn.setObjectName("tableBtn")
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.clicked.connect(lambda checked, l=log: self._edit_log(l))
                    action_layout.addWidget(edit_btn)
                    complete_btn = QPushButton("✓")
                    complete_btn.setFixedSize(30, 28)
                    complete_btn.setObjectName("tableBtn")
                    complete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    complete_btn.clicked.connect(lambda checked, l=log: self._quick_complete(l))
                    action_layout.addWidget(complete_btn)
            if not is_viewer:
                delete_btn = QPushButton("Xóa")
                delete_btn.setFixedSize(50, 28)
                delete_btn.setObjectName("tableBtnDanger")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.clicked.connect(lambda checked, l=log: self._delete_log(l))
                action_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 8, action_widget)

    def _update_pagination(self):
        total = len(self.all_logs)
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.all_logs[start:end]
        
        self._populate_table(page_data)
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

    def _edit_log(self, log):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        equipment = Equipment.get_by_id(log.equipment_id)
        full_log = MaintenanceLog.get_by_id(log.id)
        if not equipment or not full_log: return
        dialog = MaintenanceDialog(self, equipment, full_log)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            if is_viewer:
                QMessageBox.warning(self, "Không có quyền", "Bạn chỉ có quyền xem!")
                return
            new_equip_status = dialog.get_new_equipment_status()
            success, msg = self.controller.update_maintenance_log(full_log.id, dialog.get_data_as_dict(), new_equip_status)
            if success: 
                self.refresh_data()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)
        elif result == 2:
            if is_viewer: return
            self.refresh_data()

    def _quick_complete(self, log):
        reply = QMessageBox.question(self, "Xác nhận", f"Hoàn thành: {log.maintenance_type}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.complete_maintenance(log.id)
            if success: self.refresh_data()

    def _delete_log(self, log):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.delete_maintenance_log(log.id)
            if success: self.refresh_data()
    
    def _on_double_click(self, index):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            log_id = int(id_item.text())
            log = MaintenanceLog.get_by_id(log_id)
            if is_viewer and log and log.status != "Hoàn thành": return
            if log: self._edit_log(log)