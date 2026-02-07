"""
Maintenance Dialog - Form for adding/editing maintenance logs
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QPushButton, QFrame, QGroupBox, QDateTimeEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont
from datetime import datetime

from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog, MAINTENANCE_STATUS
from ..models.maintenance_type import get_maintenance_type_names
from ..config import EQUIPMENT_STATUS


class MaintenanceDialog(QDialog):
    """
    Dialog for adding/editing maintenance log entry
    """
    
    def __init__(self, parent=None, equipment: Equipment = None, log: MaintenanceLog = None):
        super().__init__(parent)
        self.equipment = equipment
        self.log = log
        self.is_edit_mode = log is not None
        
        # Kiểm tra xem có phải chế độ "Chỉ xem" (Read-only) không
        # Logic: Nếu đã có log và trạng thái là "Hoàn thành" -> Chỉ xem
        self.is_read_only = False
        if self.is_edit_mode and self.log.status == "Hoàn thành":
            self.is_read_only = True

        self._setup_ui()
        
        if self.is_edit_mode:
            self._load_log_data()
            
        # Áp dụng chế độ chỉ xem nếu cần
        if self.is_read_only:
            self._set_read_only_mode()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        # Tiêu đề thay đổi tùy theo chế độ
        if self.is_read_only:
            title = "Chi tiết bảo dưỡng (Đã hoàn thành)"
            icon = "👁️"
            header_text = f"{icon} Chi tiết công việc bảo dưỡng"
        elif self.is_edit_mode:
            title = "Cập nhật bảo dưỡng"
            icon = "✏️"
            header_text = f"{icon} Cập nhật công việc bảo dưỡng"
        else:
            title = "Ghi nhật ký bảo dưỡng"
            icon = "📝"
            header_text = f"{icon} Ghi nhật ký bảo dưỡng/sửa chữa"

        self.setWindowTitle(title)
        self.setMinimumWidth(550)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(header_text)
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Equipment info frame
        if self.equipment:
            equip_frame = QFrame()
            equip_frame.setObjectName("card")
            equip_layout = QHBoxLayout(equip_frame)
            equip_layout.setContentsMargins(15, 15, 15, 15)
            
            equip_info = QLabel(
                f"<b>Thiết bị:</b> {self.equipment.name}<br>"
                f"<b>Số hiệu:</b> {self.equipment.serial_number}<br>"
                f"<b>Tình trạng:</b> {self.equipment.status}"
            )
            equip_layout.addWidget(equip_info)
            layout.addWidget(equip_frame)
        
        # Form
        form_group = QGroupBox("Thông tin chi tiết")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(15)
        
        # Maintenance type - dynamic from database
        self.type_combo = QComboBox()
        for mtype in get_maintenance_type_names():
            self.type_combo.addItem(mtype)
        form_layout.addRow("Loại công việc *:", self.type_combo)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Mô tả công việc thực hiện...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Mô tả:", self.description_input)
        
        # Technician
        self.technician_input = QLineEdit()
        self.technician_input.setPlaceholderText("Tên kỹ thuật viên...")
        form_layout.addRow("Kỹ thuật viên:", self.technician_input)
        
        # Start date
        self.start_date = QDateTimeEdit()
        self.start_date.setDateTime(QDateTime.currentDateTime())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày bắt đầu:", self.start_date)
        
        # End date
        self.end_date = QDateTimeEdit()
        self.end_date.setDateTime(QDateTime.currentDateTime())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.end_date.setEnabled(False) # Default disabled
        form_layout.addRow("Ngày kết thúc:", self.end_date)
        
        # Status
        self.status_combo = QComboBox()
        for status in MAINTENANCE_STATUS:
            self.status_combo.addItem(status)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        form_layout.addRow("Trạng thái:", self.status_combo)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Ghi chú thêm...")
        self.notes_input.setMaximumHeight(60)
        form_layout.addRow("Ghi chú:", self.notes_input)
        
        layout.addWidget(form_group)
        
        # Update equipment status option
        self.status_group = QGroupBox("Cập nhật tình trạng thiết bị")
        status_layout = QHBoxLayout(self.status_group)
        
        self.update_status_check = QCheckBox("Cập nhật tình trạng thiết bị thành:")
        status_layout.addWidget(self.update_status_check)
        
        self.new_status_combo = QComboBox()
        for status in EQUIPMENT_STATUS:
            self.new_status_combo.addItem(status)
        self.new_status_combo.setEnabled(False)
        status_layout.addWidget(self.new_status_combo)
        
        self.update_status_check.toggled.connect(self.new_status_combo.setEnabled)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        
        layout.addWidget(self.status_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Nút xóa (Chỉ hiện khi Edit và KHÔNG phải Read-only)
        if self.is_edit_mode and not self.is_read_only:
            self.delete_btn = QPushButton("🗑️ Xóa")
            self.delete_btn.setObjectName("danger")
            self.delete_btn.clicked.connect(self._delete_log)
            button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # Nút Lưu/Cập nhật
        if not self.is_read_only:
            save_text = "💾 Cập nhật" if self.is_edit_mode else "💾 Lưu"
            self.save_btn = QPushButton(save_text)
            self.save_btn.clicked.connect(self.accept)
            button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)

    def _set_read_only_mode(self):
        """Disable all inputs for read-only mode"""
        self.type_combo.setEnabled(False)
        self.description_input.setReadOnly(True)
        self.technician_input.setReadOnly(True)
        self.start_date.setReadOnly(True)
        self.end_date.setReadOnly(True)
        self.status_combo.setEnabled(False)
        self.notes_input.setReadOnly(True)
        
        # Disable status update group
        self.status_group.setEnabled(False)
        
        # Change Cancel button to "Close"
        self.cancel_btn.setText("Đóng")

    def _on_status_changed(self, status: str):
        is_completed = status == "Hoàn thành"
        self.end_date.setEnabled(is_completed)
        if is_completed:
            self.end_date.setDateTime(QDateTime.currentDateTime())
    
    def _on_type_changed(self, mtype: str):
        if mtype == "Bảo dưỡng định kỳ":
            idx = self.new_status_combo.findText("Đang bảo dưỡng")
            if idx >= 0: self.new_status_combo.setCurrentIndex(idx)
        elif mtype == "Sửa chữa":
            idx = self.new_status_combo.findText("Đang bảo dưỡng")
            if idx >= 0: self.new_status_combo.setCurrentIndex(idx)
    
    def _load_log_data(self):
        if not self.log: return
        
        idx = self.type_combo.findText(self.log.maintenance_type)
        if idx >= 0: self.type_combo.setCurrentIndex(idx)
        
        self.description_input.setPlainText(self.log.description or "")
        self.technician_input.setText(self.log.technician_name or "")
        
        if self.log.start_date:
            dt = self.log.start_date
            if isinstance(dt, str):
                try: dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except: pass
            if isinstance(dt, datetime):
                self.start_date.setDateTime(QDateTime(dt))
        
        if self.log.end_date:
            dt = self.log.end_date
            if isinstance(dt, str):
                try: dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except: pass
            if isinstance(dt, datetime):
                self.end_date.setDateTime(QDateTime(dt))
        
        idx = self.status_combo.findText(self.log.status)
        if idx >= 0: self.status_combo.setCurrentIndex(idx)
        
        self.notes_input.setPlainText(self.log.notes or "")
    
    def _delete_log(self):
        reply = QMessageBox.question(
            self, "Xác nhận xóa", "Bạn có chắc muốn xóa bản ghi bảo dưỡng này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.log and self.log.delete():
                self.done(2)
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể xóa bản ghi!")
    
    def get_data_as_dict(self) -> dict:
        status = self.status_combo.currentText()
        end_date = None
        
        if status == "Hoàn thành":
            if self.is_edit_mode and self.log and self.log.status != "Hoàn thành":
                end_date = datetime.now()
            else:
                end_date = self.end_date.dateTime().toPyDateTime()

        return {
            'maintenance_type': self.type_combo.currentText(),
            'description': self.description_input.toPlainText().strip(),
            'technician': self.technician_input.text().strip(),
            'status': status,
            'start_date': self.start_date.dateTime().toPyDateTime(),
            'end_date': end_date,
            'notes': self.notes_input.toPlainText().strip()
        }

    def get_new_equipment_status(self) -> str:
        if self.update_status_check.isChecked():
            return self.new_status_combo.currentText()
        return None