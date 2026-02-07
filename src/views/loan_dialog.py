"""
Loan Dialog - Form for adding/editing equipment loans
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
from ..models.loan_log import LoanLog, LOAN_STATUS


class LoanDialog(QDialog):
    """
    Dialog for adding/editing loan log entry
    """
    
    def __init__(self, parent=None, equipment: Equipment = None, loan: LoanLog = None):
        super().__init__(parent)
        self.equipment = equipment
        self.loan = loan
        self.is_edit_mode = loan is not None
        
        # Chế độ chỉ xem nếu đã trả
        self.is_read_only = False
        if self.is_edit_mode and self.loan.status == "Đã trả":
            self.is_read_only = True

        self._setup_ui()
        
        if self.is_edit_mode:
            self._load_loan_data()
            
        if self.is_read_only:
            self._set_read_only_mode()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        if self.is_read_only:
            title = "Chi tiết cho mượn (Đã trả)"
            icon = "👁️"
            header_text = f"{icon} Chi tiết phiếu cho mượn"
        elif self.is_edit_mode:
            title = "Cập nhật phiếu cho mượn"
            icon = "✏️"
            header_text = f"{icon} Cập nhật thông tin cho mượn"
        else:
            title = "Tạo phiếu cho mượn"
            icon = "📝"
            header_text = f"{icon} Tạo phiếu cho mượn thiết bị"

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
            
            loan_status_text = self.equipment.loan_status or "Đang ở kho"
            equip_info = QLabel(
                f"<b>Thiết bị:</b> {self.equipment.name}<br>"
                f"<b>Số hiệu:</b> {self.equipment.serial_number}<br>"
                f"<b>Trạng thái cho mượn:</b> {loan_status_text}"
            )
            equip_layout.addWidget(equip_info)
            layout.addWidget(equip_frame)
        
        # Form
        form_group = QGroupBox("Thông tin cho mượn")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(15)
        
        # Borrower unit
        self.borrower_input = QLineEdit()
        self.borrower_input.setPlaceholderText("Nhập tên đơn vị mượn...")
        form_layout.addRow("Đơn vị mượn *:", self.borrower_input)
        
        # Loan date
        self.loan_date = QDateTimeEdit()
        self.loan_date.setDateTime(QDateTime.currentDateTime())
        self.loan_date.setCalendarPopup(True)
        self.loan_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày cho mượn:", self.loan_date)
        
        # Expected return date
        self.expected_return_date = QDateTimeEdit()
        self.expected_return_date.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.expected_return_date.setCalendarPopup(True)
        self.expected_return_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày dự kiến trả:", self.expected_return_date)
        
        # Return date (for edit mode)
        self.return_date = QDateTimeEdit()
        self.return_date.setDateTime(QDateTime.currentDateTime())
        self.return_date.setCalendarPopup(True)
        self.return_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.return_date.setEnabled(False)  # Default disabled
        form_layout.addRow("Ngày trả:", self.return_date)
        
        # Status
        self.status_combo = QComboBox()
        for status in LOAN_STATUS:
            self.status_combo.addItem(status)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        if not self.is_edit_mode:
            self.status_combo.setEnabled(False)  # Status is always "Đang mượn" when creating
        form_layout.addRow("Trạng thái:", self.status_combo)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Ghi chú thêm (mục đích mượn, điều kiện, ...)...")
        self.notes_input.setMaximumHeight(80)
        form_layout.addRow("Ghi chú:", self.notes_input)
        
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Nút xóa (Chỉ hiện khi Edit và KHÔNG phải Read-only)
        if self.is_edit_mode and not self.is_read_only:
            self.delete_btn = QPushButton("🗑️ Xóa")
            self.delete_btn.setObjectName("danger")
            self.delete_btn.clicked.connect(self._delete_loan)
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
        self.borrower_input.setReadOnly(True)
        self.loan_date.setReadOnly(True)
        self.expected_return_date.setReadOnly(True)
        self.return_date.setReadOnly(True)
        self.status_combo.setEnabled(False)
        self.notes_input.setReadOnly(True)
        
        # Change Cancel button to "Close"
        self.cancel_btn.setText("Đóng")

    def _on_status_changed(self, status: str):
        """Handle status change - enable return date if returned"""
        if status == "Đã trả":
            self.return_date.setEnabled(True)
        else:
            self.return_date.setEnabled(False)
    
    def _load_loan_data(self):
        """Load existing loan data into form"""
        if not self.loan:
            return
        
        self.borrower_input.setText(self.loan.borrower_unit)
        
        if self.loan.loan_date:
            try:
                if isinstance(self.loan.loan_date, str):
                    dt = datetime.fromisoformat(self.loan.loan_date.replace('Z', '+00:00'))
                else:
                    dt = self.loan.loan_date
                self.loan_date.setDateTime(QDateTime(
                    dt.year, dt.month, dt.day, dt.hour, dt.minute
                ))
            except:
                pass
        
        if self.loan.expected_return_date:
            try:
                if isinstance(self.loan.expected_return_date, str):
                    dt = datetime.fromisoformat(self.loan.expected_return_date.replace('Z', '+00:00'))
                else:
                    dt = self.loan.expected_return_date
                self.expected_return_date.setDateTime(QDateTime(
                    dt.year, dt.month, dt.day, dt.hour, dt.minute
                ))
            except:
                pass
        
        if self.loan.return_date:
            try:
                if isinstance(self.loan.return_date, str):
                    dt = datetime.fromisoformat(self.loan.return_date.replace('Z', '+00:00'))
                else:
                    dt = self.loan.return_date
                self.return_date.setDateTime(QDateTime(
                    dt.year, dt.month, dt.day, dt.hour, dt.minute
                ))
                self.return_date.setEnabled(True)
            except:
                pass
        
        # Set status
        idx = self.status_combo.findText(self.loan.status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        
        self.notes_input.setPlainText(self.loan.notes or "")
    
    def _delete_loan(self):
        """Delete loan record"""
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            "Bạn có chắc muốn xóa bản ghi cho mượn này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.done(2)  # Custom return code for delete
    
    def get_loan_data(self) -> dict:
        """Get form data as dictionary"""
        data = {
            'borrower_unit': self.borrower_input.text().strip(),
            'loan_date': self.loan_date.dateTime().toPyDateTime(),
            'expected_return_date': self.expected_return_date.dateTime().toPyDateTime(),
            'notes': self.notes_input.toPlainText().strip(),
        }
        
        # Include status and return_date for edit mode
        if self.is_edit_mode:
            data['status'] = self.status_combo.currentText()
            if data['status'] == "Đã trả":
                data['return_date'] = self.return_date.dateTime().toPyDateTime()
        
        return data
    
    def validate(self) -> tuple:
        """Validate form data"""
        data = self.get_loan_data()
        
        if not data.get('borrower_unit'):
            return False, "Vui lòng nhập đơn vị mượn!"
        
        return True, ""
