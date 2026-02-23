"""
Equipment Detail Dialog - Show full equipment details with QR and maintenance history
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QFrame, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea, QWidget,
    QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal # [MỚI] Import pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QColor
import io
import os # [MỚI]

from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..models.loan_log import LoanLog
from ..services.qr_service import QRService
from ..services.export_service import ExportService
from .maintenance_view import MaintenanceHistoryView
from .loan_view import LoanHistoryView
from ..config import DATA_DIR # [MỚI] Import thư mục gốc để lấy ảnh


# --- [MỚI] CLASS HỖ TRỢ CLICK VÀO ẢNH ---
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

# --- [MỚI] HỘP THOẠI XEM ẢNH PHÓNG TO ---
class ImageViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Xem hình ảnh minh chứng")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #333; }")
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #333;")
        
        pixmap = QPixmap(str(image_path))
        if not pixmap.isNull():
            # Scale ảnh cho lớn nhưng không làm méo/vỡ tỉ lệ
            scaled_pixmap = pixmap.scaled(
                1200, 800, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Lỗi: Không thể tải hình ảnh.")
            self.image_label.setStyleSheet("color: white;")
            
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)
        
        close_btn = QPushButton("Đóng")
        close_btn.setFixedSize(100, 35)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)


class EquipmentDetailDialog(QDialog):
    """
    Dialog showing full equipment details with QR code and maintenance history
    """
    
    def __init__(self, parent=None, equipment: Equipment = None, 
                 maintenance_logs: list = None, qr_service: QRService = None):
        super().__init__(parent)
        self.equipment = equipment
        self.maintenance_logs = maintenance_logs or []
        self.qr_service = qr_service or QRService()
        self.export_service = ExportService()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"Chi tiết: {self.equipment.name}")
        self.setMinimumSize(1000, 650) 
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with name and QR
        header_layout = QHBoxLayout()
        
        # Left side - Info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.equipment.name)
        name_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        info_layout.addWidget(name_label)
        
        serial_label = QLabel(f"Số hiệu: {self.equipment.serial_number}")
        serial_label.setFont(QFont("Segoe UI", 14))
        serial_label.setStyleSheet("color: #888;")
        info_layout.addWidget(serial_label)
        
        status_label = QLabel(f"Tình trạng: {self.equipment.status}")
        status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.status_label = status_label
        self._update_status_color()
        info_layout.addWidget(status_label)
        
        # Loan status label
        loan_status = self.equipment.loan_status or "Đang ở kho"
        loan_status_label = QLabel(f"Trạng thái mượn: {loan_status}")
        loan_status_label.setFont(QFont("Segoe UI", 12))
        self.loan_status_label = loan_status_label
        self._update_loan_status_color()
        info_layout.addWidget(loan_status_label)
        
        info_layout.addStretch()
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        # Right side - QR Code
        qr_frame = QFrame()
        qr_frame.setFixedSize(150, 150)
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setContentsMargins(0, 0, 0, 0)
        
        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        qr_img, _ = self.qr_service.generate_equipment_qr(
            self.equipment.id,
            self.equipment.serial_number
        )
        
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        scaled_pixmap = pixmap.scaled(
            130, 130,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        qr_label.setPixmap(scaled_pixmap)
        qr_layout.addWidget(qr_label)
        header_layout.addWidget(qr_frame)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Tab 1: Equipment details
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setContentsMargins(10, 10, 10, 10)
        
        details_group = QGroupBox("Thông tin chi tiết")
        form_layout = QFormLayout(details_group)
        form_layout.setSpacing(12)
        
        details = [
            ("Loại:", self.equipment.category),
            ("Nhà sản xuất:", self.equipment.manufacturer or "-"),
            ("Năm sản xuất:", str(self.equipment.manufacture_year) if self.equipment.manufacture_year else "-"),
            ("Đơn vị:", self.equipment.unit_name or "-"),
            ("Vị trí:", self.equipment.location or "-"),
            ("Ngày cấp phát:", self._format_date(self.equipment.receive_date) if self.equipment.receive_date else "-"),
            ("Mô tả:", self.equipment.description or "-"),
        ]
        
        for label, value in details:
            value_label = QLabel(value)
            value_label.setWordWrap(True)
            value_label.setFont(QFont("Segoe UI", 11))
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            form_layout.addRow(label_widget, value_label)
        
        details_layout.addWidget(details_group)
        
        # --- [MỚI] KHU VỰC HIỂN THỊ HÌNH ẢNH TRONG TAB THÔNG TIN ---
        image_group = QGroupBox("Hình ảnh thiết bị")
        image_layout = QHBoxLayout(image_group)
        image_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        if hasattr(self.equipment, 'images') and self.equipment.images:
            has_valid_image = False
            for img_path in self.equipment.images:
                full_path = DATA_DIR / img_path
                if full_path.exists():
                    has_valid_image = True
                    
                    # Tạo Label có thể click
                    lbl = ClickableLabel()
                    lbl.setFixedSize(120, 120)
                    lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                    lbl.setStyleSheet("""
                        QLabel { border: 2px solid #ddd; border-radius: 4px; background-color: #f9f9f9; }
                        QLabel:hover { border: 2px solid #1976D2; }
                    """)
                    
                    pixmap = QPixmap(str(full_path)).scaled(
                        116, 116, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    lbl.setPixmap(pixmap)
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setToolTip("Click để phóng to ảnh")
                    
                    # Kết nối sự kiện click mở ảnh to
                    lbl.clicked.connect(lambda p=full_path: self._show_full_image(p))
                    
                    image_layout.addWidget(lbl)
            
            if not has_valid_image:
                image_layout.addWidget(QLabel("Các file ảnh không còn tồn tại trên ổ cứng."))
        else:
            no_img_label = QLabel("Chưa có hình ảnh đính kèm.")
            no_img_label.setStyleSheet("color: #888; font-style: italic;")
            image_layout.addWidget(no_img_label)
            
        details_layout.addWidget(image_group)
        # --------------------------------------------------------
        
        details_layout.addStretch()
        tab_widget.addTab(details_tab, "📋 Thông tin")
        
        # Tab 2: Maintenance history
        self.maintenance_view = MaintenanceHistoryView(self, self.equipment)
        self.maintenance_view.log_updated.connect(self._on_maintenance_updated)
        tab_widget.addTab(self.maintenance_view, f"🔧 Bảo dưỡng ({len(self.maintenance_logs)})")
        
        # Tab 3: Loan history
        loan_logs = LoanLog.get_by_equipment(self.equipment.id)
        self.loan_view = LoanHistoryView(self, self.equipment)
        self.loan_view.log_updated.connect(self._on_loan_updated)
        tab_widget.addTab(self.loan_view, f"📝 Cho mượn ({len(loan_logs)})")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("📄 Xuất hồ sơ PDF")
        export_btn.setObjectName("secondary")
        export_btn.clicked.connect(self._export_detail)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    # [MỚI] Hàm mở dialog xem ảnh to
    def _show_full_image(self, image_path):
        dialog = ImageViewerDialog(image_path, self)
        dialog.exec()
    
    def _update_status_color(self):
        if self.equipment.status in ["Cấp 1", "Cấp 2"]:
            self.status_label.setStyleSheet("color: #4CAF50;")
        elif self.equipment.status == "Cấp 3":
            self.status_label.setStyleSheet("color: #FF9800;")
        else:
            self.status_label.setStyleSheet("color: #F44336;")
    
    def _update_loan_status_color(self):
        loan_status = self.equipment.loan_status or "Đang ở kho"
        if loan_status == "Đang ở kho":
            self.loan_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.loan_status_label.setStyleSheet("color: #FF9800;")
    
    def _format_date(self, date_value):
        if date_value is None:
            return "-"
        if hasattr(date_value, 'strftime'):
            return date_value.strftime("%d/%m/%Y")
        try:
            return str(date_value)[:10]
        except:
            return "-"
    
    def _on_maintenance_updated(self):
        self.equipment = Equipment.get_by_id(self.equipment.id)
        self.status_label.setText(f"Tình trạng: {self.equipment.status}")
        self._update_status_color()
        logs = MaintenanceLog.get_by_equipment(self.equipment.id)
        tab_widget = self.findChild(QTabWidget)
        for i in range(tab_widget.count()):
            if "Bảo dưỡng" in tab_widget.tabText(i):
                tab_widget.setTabText(i, f"🔧 Bảo dưỡng ({len(logs)})")
                break
    
    def _on_loan_updated(self):
        self.equipment = Equipment.get_by_id(self.equipment.id)
        loan_status = self.equipment.loan_status or "Đang ở kho"
        self.loan_status_label.setText(f"Trạng thái mượn: {loan_status}")
        self._update_loan_status_color()
        self.loan_view.set_equipment(self.equipment)
        logs = LoanLog.get_by_equipment(self.equipment.id)
        tab_widget = self.findChild(QTabWidget)
        for i in range(tab_widget.count()):
            if "Cho mượn" in tab_widget.tabText(i):
                tab_widget.setTabText(i, f"📝 Cho mượn ({len(logs)})")
                break
    
    def _export_detail(self):
        try:
            maintenance_logs = MaintenanceLog.get_by_equipment(self.equipment.id)
            loan_logs = LoanLog.get_by_equipment(self.equipment.id)
            filepath = self.export_service.export_equipment_detail(
                self.equipment, maintenance_logs, loan_logs
            )
            reply = QMessageBox.information(
                self, "Thành công",
                f"Đã xuất hồ sơ PDF!\n\nĐường dẫn: {filepath}",
                QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok
            )
            if reply == QMessageBox.StandardButton.Open:
                import os
                os.startfile(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {str(e)}")