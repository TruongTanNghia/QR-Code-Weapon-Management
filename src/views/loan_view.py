"""
Loan History View - Display and manage loan logs for equipment
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
from ..models.loan_log import LoanLog, LOAN_STATUS
from ..controllers.loan_controller import LoanController
from .loan_dialog import LoanDialog
from ..controllers.user_controller import UserController 
from ..models.user import UserRole


class LoanHistoryView(QWidget):
    """
    Widget showing loan history for a specific equipment (Inside Detail View)
    """
    
    log_updated = pyqtSignal()
    
    def __init__(self, parent=None, equipment: Equipment = None):
        super().__init__(parent)
        self.equipment = equipment
        self.controller = LoanController()
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
        title = QLabel("📋 Lịch sử cho mượn")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả trạng thái", None)
        for status in LOAN_STATUS:
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self.refresh_data)
        header_layout.addWidget(self.status_filter)
        
        # [PHÂN QUYỀN] Nút Thêm
        self.add_btn = QPushButton("+ Cho mượn")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_loan)
        
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
            "ID", "Đơn vị mượn", "Ngày mượn", "Dự kiến trả",
            "Ngày trả", "Trạng thái", "Thao tác"
        ])
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)   # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Đơn vị mượn
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   # Ngày mượn
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)   # Dự kiến trả
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)   # Ngày trả
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Trạng thái
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)   # Thao tác
        
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 95)
        self.table.setColumnWidth(3, 95)
        self.table.setColumnWidth(4, 95)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 160)
        
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
            logs = LoanLog.get_by_equipment_and_date(self.equipment.id, from_datetime, to_datetime)
        else:
            logs = LoanLog.get_by_equipment(self.equipment.id)
        
        status_filter = self.status_filter.currentData()
        if status_filter:
            logs = [l for l in logs if l.status == status_filter]
        
        self._populate_table(logs)
        
        total = len(logs)
        active = len([l for l in logs if l.status == "Đang mượn"])
        self.stats_label.setText(f"Tổng: {total} | Đang mượn: {active}")
    
    def _populate_table(self, logs: list):
        self.table.setRowCount(len(logs))
        
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        for row, log in enumerate(logs):
            self.table.setRowHeight(row, 45)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))
            self.table.setItem(row, 1, QTableWidgetItem(log.borrower_unit))
            
            loan_str = log.loan_date.strftime("%d/%m/%Y") if hasattr(log.loan_date, 'strftime') else str(log.loan_date)[:10]
            self.table.setItem(row, 2, QTableWidgetItem(loan_str))
            
            expected_str = "-"
            if log.expected_return_date:
                expected_str = log.expected_return_date.strftime("%d/%m/%Y") if hasattr(log.expected_return_date, 'strftime') else str(log.expected_return_date)[:10]
            self.table.setItem(row, 3, QTableWidgetItem(expected_str))
            
            return_str = "-"
            if log.return_date:
                return_str = log.return_date.strftime("%d/%m/%Y") if hasattr(log.return_date, 'strftime') else str(log.return_date)[:10]
            self.table.setItem(row, 4, QTableWidgetItem(return_str))
            
            status_item = QTableWidgetItem(log.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if log.status == "Đã trả":
                status_item.setForeground(QColor("#4CAF50"))
            elif log.status == "Đang mượn":
                status_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row, 5, status_item)
            
            # [PHÂN QUYỀN] Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            
            is_returned = (log.status == "Đã trả")
            
            # Logic tương tự Maintenance: Viewer thấy nút Xem nếu Đã trả
            if is_returned or not is_viewer:
                if is_returned:
                    view_btn = QPushButton("Xem") 
                    view_btn.setFixedSize(60, 28)
                    view_btn.setObjectName("tableBtnView")
                    view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    view_btn.clicked.connect(lambda checked, l=log: self._edit_loan(l))
                    action_layout.addWidget(view_btn)
                elif not is_viewer: # Chưa trả, ko phải Viewer -> Sửa/Trả
                    edit_btn = QPushButton("Sửa")
                    edit_btn.setFixedSize(50, 28)
                    edit_btn.setObjectName("tableBtn")
                    edit_btn.clicked.connect(lambda checked, l=log: self._edit_loan(l))
                    action_layout.addWidget(edit_btn)
                    
                    return_btn = QPushButton("✓ Trả")
                    return_btn.setFixedSize(50, 28)
                    return_btn.setObjectName("tableBtn")
                    return_btn.clicked.connect(lambda checked, l=log: self._quick_return(l))
                    action_layout.addWidget(return_btn)
                
            if not is_viewer:
                delete_btn = QPushButton("Xóa")
                delete_btn.setFixedSize(50, 28)
                delete_btn.setObjectName("tableBtnDanger")
                delete_btn.clicked.connect(lambda checked, l=log: self._delete_loan(l))
                action_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, action_widget)

    def _on_double_click(self, index):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            loan_id = int(id_item.text())
            loan = LoanLog.get_by_id(loan_id)
            if is_viewer and loan and loan.status != "Đã trả":
                return
            if loan: self._edit_loan(loan)
            
    def _add_loan(self):
        if not self.equipment:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn thiết bị!")
            return
        
        if self.equipment.loan_status == "Đã cho mượn":
            active_loan = LoanLog.get_active_by_equipment(self.equipment.id)
            if active_loan:
                reply = QMessageBox.question(
                    self, "Thông báo", 
                    f"Thiết bị đang được mượn bởi '{active_loan.borrower_unit}'.\nBạn có muốn xem thông tin phiếu mượn không?", 
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._edit_loan(active_loan)
                return
            else:
                QMessageBox.warning(self, "Lỗi", "Thiết bị đang ở trạng thái cho mượn!")
                return
        
        dialog = LoanDialog(self, self.equipment)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            valid, error_msg = dialog.validate()
            if not valid:
                QMessageBox.warning(self, "Lỗi", error_msg)
                return
            
            success, msg, _ = self.controller.create_loan(
                self.equipment.id, 
                dialog.get_loan_data()
            )
            if success:
                self.equipment = Equipment.get_by_id(self.equipment.id)
                self.refresh_data()
                self.log_updated.emit()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def _edit_loan(self, loan):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        loan = LoanLog.get_by_id(loan.id)
        if not loan: return
        dialog = LoanDialog(self, self.equipment, loan)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Chặn lưu nếu là Viewer
            if is_viewer:
                QMessageBox.warning(self, "Không có quyền", "Bạn chỉ có quyền xem, không thể chỉnh sửa!")
                return
                
            data = dialog.get_loan_data()
            
            if data.get('status') == "Đã trả" and loan.status != "Đã trả":
                success, msg = self.controller.return_equipment(
                    loan.id, 
                    data.get('notes', ''),
                    data.get('return_date')
                )
            else:
                success, msg = self.controller.update_loan(loan.id, data)
            
            if success:
                self.equipment = Equipment.get_by_id(self.equipment.id)
                self.refresh_data()
                self.log_updated.emit()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)
        elif result == 2:  # Delete
            if is_viewer:
                QMessageBox.warning(self, "Không có quyền", "Bạn không có quyền xóa!")
                return
            success, msg = self.controller.delete_loan(loan.id)
            if success:
                self.equipment = Equipment.get_by_id(self.equipment.id)
                self.refresh_data()
                self.log_updated.emit()

    def _quick_return(self, loan):
        reply = QMessageBox.question(
            self, "Xác nhận", 
            f"Ghi nhận trả thiết bị từ '{loan.borrower_unit}'?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.return_equipment(loan.id)
            if success: 
                self.equipment = Equipment.get_by_id(self.equipment.id)
                self.refresh_data()
                self.log_updated.emit()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def _delete_loan(self, loan):
        reply = QMessageBox.question(
            self, "Xác nhận", 
            "Bạn có chắc muốn xóa bản ghi cho mượn này?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.delete_loan(loan.id)
            if success: 
                self.equipment = Equipment.get_by_id(self.equipment.id)
                self.refresh_data()
                self.log_updated.emit()


# --- CLASS LIST VIEW (Phần bị thiếu đã được thêm lại) ---
class LoanListView(QWidget):
    """
    Full page view for all loan logs
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = LoanController()
        self._setup_ui()
        self.refresh_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("📋 Quản lý cho mượn thiết bị")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm theo đơn vị mượn hoặc số hiệu...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả trạng thái", None)
        for status in LOAN_STATUS:
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self.refresh_data)
        header_layout.addWidget(self.status_filter)
        
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Date filter row
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Thiết bị", "Số hiệu", "Đơn vị mượn",
            "Ngày mượn", "Ngày trả", "Trạng thái", "Thao tác"
        ])
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 150)
        
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
        if hasattr(self, 'date_filter_check') and self.date_filter_check.isChecked():
            start_date = self.from_date.date().toPyDate()
            end_date = self.to_date.date().toPyDate()
            logs = LoanLog.get_by_date_range(start_date, end_date)
        else:
            logs = LoanLog.get_all(limit=500)
        
        status_filter = self.status_filter.currentData()
        if status_filter:
            logs = [l for l in logs if l.status == status_filter]
        
        search_text = self.search_input.text().lower().strip()
        if search_text:
            logs = [l for l in logs if 
                    search_text in l.borrower_unit.lower() or
                    search_text in l.equipment_serial.lower() or
                    search_text in l.equipment_name.lower()]
        
        self._populate_table(logs)
        total = len(logs)
        active = len([l for l in logs if l.status == "Đang mượn"])
        self.stats_label.setText(f"Tổng: {total} bản ghi | Đang mượn: {active}")
    
    def _on_search(self, text):
        self.refresh_data()
    
    def _populate_table(self, logs: list):
        self.table.setRowCount(len(logs))
        
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        for row, log in enumerate(logs):
            self.table.setRowHeight(row, 45)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))
            self.table.setItem(row, 1, QTableWidgetItem(log.equipment_name))
            self.table.setItem(row, 2, QTableWidgetItem(log.equipment_serial))
            self.table.setItem(row, 3, QTableWidgetItem(log.borrower_unit))
            
            loan_str = log.loan_date.strftime("%d/%m/%Y") if hasattr(log.loan_date, 'strftime') else str(log.loan_date)[:10]
            self.table.setItem(row, 4, QTableWidgetItem(loan_str))
            
            return_str = "-"
            if log.return_date:
                return_str = log.return_date.strftime("%d/%m/%Y") if hasattr(log.return_date, 'strftime') else str(log.return_date)[:10]
            self.table.setItem(row, 5, QTableWidgetItem(return_str))
            
            status_item = QTableWidgetItem(log.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if log.status == "Đã trả":
                status_item.setForeground(QColor("#4CAF50"))
            elif log.status == "Đang mượn":
                status_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row, 6, status_item)
            
            # Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            
            is_returned = (log.status == "Đã trả")
            
            # [PHÂN QUYỀN]
            if is_returned or not is_viewer:
                if is_returned:
                    view_btn = QPushButton("Xem")
                    view_btn.setFixedSize(60, 28)
                    view_btn.setObjectName("tableBtnView")
                    view_btn.clicked.connect(lambda checked, l=log: self._view_loan(l))
                    action_layout.addWidget(view_btn)
                elif not is_viewer:
                    return_btn = QPushButton("✓ Trả")
                    return_btn.setFixedSize(60, 28)
                    return_btn.setObjectName("tableBtn")
                    return_btn.clicked.connect(lambda checked, l=log: self._quick_return(l))
                    action_layout.addWidget(return_btn)
            
            if not is_viewer:
                delete_btn = QPushButton("Xóa")
                delete_btn.setFixedSize(50, 28)
                delete_btn.setObjectName("tableBtnDanger")
                delete_btn.clicked.connect(lambda checked, l=log: self._delete_loan(l))
                action_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 7, action_widget)
    
    def _on_double_click(self, index):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            loan_id = int(id_item.text())
            loan = LoanLog.get_by_id(loan_id)
            if is_viewer and loan and loan.status != "Đã trả":
                return
            if loan: self._view_loan(loan)
    
    def _view_loan(self, loan):
        current_user = UserController.get_current_user()
        is_viewer = current_user and current_user.role == UserRole.VIEWER
        
        equipment = Equipment.get_by_id(loan.equipment_id)
        loan = LoanLog.get_by_id(loan.id)
        if not loan: return
            
        dialog = LoanDialog(self, equipment, loan)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            if is_viewer:
                QMessageBox.warning(self, "Không có quyền", "Bạn chỉ có quyền xem!")
                return
                
            data = dialog.get_loan_data()
            if data.get('status') == "Đã trả" and loan.status != "Đã trả":
                success, msg = self.controller.return_equipment(loan.id, data.get('notes', ''), data.get('return_date'))
            else:
                success, msg = self.controller.update_loan(loan.id, data)
            
            if success:
                self.refresh_data()
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)
        elif result == 2:  # Delete
            if is_viewer:
                QMessageBox.warning(self, "Không có quyền", "Bạn không có quyền xóa!")
                return
            success, msg = self.controller.delete_loan(loan.id)
            if success:
                self.refresh_data()
    
    def _quick_return(self, loan):
        reply = QMessageBox.question(self, "Xác nhận", f"Ghi nhận trả thiết bị '{loan.equipment_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.return_equipment(loan.id)
            if success:
                self.refresh_data()
    
    def _delete_loan(self, loan):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.controller.delete_loan(loan.id)
            if success:
                self.refresh_data()