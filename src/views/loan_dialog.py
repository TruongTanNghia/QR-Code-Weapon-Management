"""
Loan Dialog - Form for adding/editing equipment loans
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QPushButton, QFrame, QGroupBox, QDateTimeEdit, QMessageBox, QWidget, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from datetime import datetime
import os

from ..models.equipment import Equipment
from ..models.loan_log import LoanLog, LOAN_STATUS
from ..config import DATA_DIR

# --- CLASS HỖ TRỢ CLICK VÀO ẢNH ---
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

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
            scaled_pixmap = pixmap.scaled(1200, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Lỗi: Không thể tải hình ảnh.")
            self.image_label.setStyleSheet("color: white;")
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)
        close_btn = QPushButton("Đóng")
        close_btn.setFixedSize(100, 35)
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
# -----------------------------------------------------------


class LoanDialog(QDialog):
    def __init__(self, parent=None, equipment: Equipment = None, loan: LoanLog = None):
        super().__init__(parent)
        self.equipment = equipment
        self.loan = loan
        self.is_edit_mode = loan is not None
        
        self.is_read_only = False
        if self.is_edit_mode and self.loan.status == "Đã trả":
            self.is_read_only = True

        # [MỚI] Tách cấu trúc biến ảnh thành lúc giao / lúc trả
        self.images_data = {
            'before': {'new': [], 'deleted': [], 'current': self.loan.images_before if self.is_edit_mode else []},
            'after': {'new': [], 'deleted': [], 'current': self.loan.images_after if self.is_edit_mode else []}
        }

        self._setup_ui()
        if self.is_edit_mode: self._load_loan_data()
        if self.is_read_only: self._set_read_only_mode()
    
    def _setup_ui(self):
        if self.is_read_only:
            title = "Chi tiết cho mượn (Đã trả)"
            header_text = "👁️ Chi tiết phiếu cho mượn"
        elif self.is_edit_mode:
            title = "Cập nhật phiếu cho mượn"
            header_text = "✏️ Cập nhật thông tin cho mượn"
        else:
            title = "Tạo phiếu cho mượn"
            header_text = "📝 Tạo phiếu cho mượn thiết bị"

        self.setWindowTitle(title)
        self.setMinimumWidth(650)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel(header_text)
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        if self.equipment:
            equip_frame = QFrame()
            equip_frame.setObjectName("card")
            equip_layout = QHBoxLayout(equip_frame)
            loan_status_text = self.equipment.loan_status or "Đang ở kho"
            equip_info = QLabel(f"<b>Thiết bị:</b> {self.equipment.name} | <b>Số hiệu:</b> {self.equipment.serial_number} | <b>Trạng thái:</b> {loan_status_text}")
            equip_layout.addWidget(equip_info)
            layout.addWidget(equip_frame)
        
        form_group = QGroupBox("Thông tin cho mượn")
        form_layout = QFormLayout(form_group)
        
        self.borrower_input = QLineEdit()
        form_layout.addRow("Đơn vị mượn *:", self.borrower_input)
        
        self.loan_date = QDateTimeEdit()
        self.loan_date.setDateTime(QDateTime.currentDateTime())
        self.loan_date.setCalendarPopup(True)
        self.loan_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày cho mượn:", self.loan_date)
        
        self.expected_return_date = QDateTimeEdit()
        self.expected_return_date.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.expected_return_date.setCalendarPopup(True)
        self.expected_return_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày dự kiến trả:", self.expected_return_date)
        
        self.return_date = QDateTimeEdit()
        self.return_date.setDateTime(QDateTime.currentDateTime())
        self.return_date.setCalendarPopup(True)
        self.return_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.return_date.setEnabled(False)
        form_layout.addRow("Ngày trả:", self.return_date)
        
        self.status_combo = QComboBox()
        for status in LOAN_STATUS: self.status_combo.addItem(status)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        if not self.is_edit_mode: self.status_combo.setEnabled(False)
        form_layout.addRow("Trạng thái:", self.status_combo)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        form_layout.addRow("Ghi chú:", self.notes_input)
        
        layout.addWidget(form_group)
        
        # --- [MỚI] KHU VỰC 2 GALLERY ẢNH LÚC GIAO / LÚC TRẢ ---
        images_container = QHBoxLayout()
        images_container.setSpacing(15)
        
        self.group_before, self.layout_before, self.btn_before = self._create_gallery_ui("before", "Ảnh LÚC GIAO")
        images_container.addWidget(self.group_before)
        
        self.group_after, self.layout_after, self.btn_after = self._create_gallery_ui("after", "Ảnh LÚC TRẢ")
        images_container.addWidget(self.group_after)
        
        layout.addLayout(images_container)
        self._render_all_images()
        # ----------------------------------------
        
        button_layout = QHBoxLayout()
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
        
        if not self.is_read_only:
            save_text = "💾 Cập nhật" if self.is_edit_mode else "💾 Lưu"
            self.save_btn = QPushButton(save_text)
            self.save_btn.clicked.connect(self.accept)
            button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

    # --- CÁC HÀM XỬ LÝ UI GALLERY ---
    def _create_gallery_ui(self, category: str, title: str):
        group = QGroupBox(f"{title} (0/5)")
        group.setMinimumHeight(110)
        layout = QHBoxLayout(group)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(10, 15, 10, 10)
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(5)
        layout.addLayout(preview_layout)
        add_btn = QPushButton("➕")
        add_btn.setFixedSize(60, 40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda _, c=category: self._choose_images(c))
        layout.addWidget(add_btn)
        layout.addStretch()
        return group, preview_layout, add_btn

    def _choose_images(self, category: str):
        data = self.images_data[category]
        total_current = len(data['current']) - len(data['deleted']) + len(data['new'])
        if total_current >= 5:
            QMessageBox.warning(self, "Giới hạn", "Chỉ được phép tải lên tối đa 5 ảnh!")
            return
            
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg)")
        for f in files:
            if total_current < 5:
                data['new'].append(f)
                total_current += 1
        self._render_all_images()

    def _render_all_images(self):
        self._render_gallery("before", self.group_before, self.layout_before, self.btn_before, "Ảnh LÚC GIAO")
        self._render_gallery("after", self.group_after, self.layout_after, self.btn_after, "Ảnh LÚC TRẢ")

    def _render_gallery(self, category, group_box, preview_layout, add_btn, title_prefix):
        while preview_layout.count():
            item = preview_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        
        data = self.images_data[category]
        for img_path in data['current']:
            if img_path not in data['deleted']:
                self._add_thumbnail(category, preview_layout, img_path, is_existing=True)
        for img_path in data['new']:
            self._add_thumbnail(category, preview_layout, img_path, is_existing=False)
            
        total = len(data['current']) - len(data['deleted']) + len(data['new'])
        group_box.setTitle(f"{title_prefix} ({total}/5)")
        
        can_add = total < 5 and not self.is_read_only
        # [LOGIC] Ảnh Lúc trả chỉ khả dụng khi chọn "Đã trả"
        if category == "after" and self.status_combo.currentText() != "Đã trả":
            can_add = False
            
        add_btn.setVisible(can_add)

    def _add_thumbnail(self, category, preview_layout, img_path: str, is_existing: bool):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl = ClickableLabel()
        lbl.setFixedSize(60, 60)
        lbl.setStyleSheet("QLabel { border: 1px solid #ccc; background-color: #f9f9f9; } QLabel:hover { border: 1px solid #1976D2; }")
        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        
        full_path = str(DATA_DIR / img_path) if is_existing else img_path
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl.setPixmap(pixmap)
        else:
            lbl.setText("X")
            
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.clicked.connect(lambda p=full_path: self._show_full_image(p))
        vbox.addWidget(lbl)
        
        if not self.is_read_only:
            del_btn = QPushButton("Xóa")
            del_btn.setStyleSheet("color: red; padding: 2px; font-size: 10px;")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, c=category, p=img_path, ext=is_existing: self._remove_image(c, p, ext))
            vbox.addWidget(del_btn)
            
        preview_layout.addWidget(container)

    def _show_full_image(self, image_path):
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file ảnh gốc trên ổ cứng!")
            return
        dialog = ImageViewerDialog(image_path, self)
        dialog.exec()

    def _remove_image(self, category: str, img_path: str, is_existing: bool):
        if is_existing: self.images_data[category]['deleted'].append(img_path)
        else: self.images_data[category]['new'].remove(img_path)
        self._render_all_images()

    def get_image_data(self):
        return (
            self.images_data['before']['new'], self.images_data['before']['deleted'],
            self.images_data['after']['new'], self.images_data['after']['deleted']
        )
    # --------------------------------

    def _set_read_only_mode(self):
        self.borrower_input.setReadOnly(True)
        self.loan_date.setReadOnly(True)
        self.expected_return_date.setReadOnly(True)
        self.return_date.setReadOnly(True)
        self.status_combo.setEnabled(False)
        self.notes_input.setReadOnly(True)
        self.cancel_btn.setText("Đóng")

    def _on_status_changed(self, status: str):
        if status == "Đã trả":
            self.return_date.setEnabled(True)
            self.return_date.setDateTime(QDateTime.currentDateTime())
        else:
            self.return_date.setEnabled(False)
        self._render_all_images()
    
    def _load_loan_data(self):
        if not self.loan: return
        self.borrower_input.setText(self.loan.borrower_unit)
        
        # Xử lý an toàn String to Datetime
        for date_attr, widget in [('loan_date', self.loan_date), 
                                  ('expected_return_date', self.expected_return_date),
                                  ('return_date', self.return_date)]:
            dt = getattr(self.loan, date_attr)
            if dt:
                if isinstance(dt, str):
                    try: dt = datetime.fromisoformat(dt.split('.')[0].replace('Z', ''))
                    except ValueError:
                        try: dt = datetime.strptime(dt.split('.')[0], '%Y-%m-%d %H:%M:%S')
                        except: pass
                if isinstance(dt, datetime):
                    widget.setDateTime(QDateTime(dt))
                    if date_attr == 'return_date': widget.setEnabled(True)

        idx = self.status_combo.findText(self.loan.status)
        if idx >= 0: self.status_combo.setCurrentIndex(idx)
        self.notes_input.setPlainText(self.loan.notes or "")
    
    def _delete_loan(self):
        reply = QMessageBox.question(self, "Xác nhận xóa", "Bạn có chắc muốn xóa bản ghi cho mượn này?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.done(2)
    
    def get_loan_data(self) -> dict:
        data = {
            'borrower_unit': self.borrower_input.text().strip(),
            'loan_date': self.loan_date.dateTime().toPyDateTime(),
            'expected_return_date': self.expected_return_date.dateTime().toPyDateTime(),
            'notes': self.notes_input.toPlainText().strip(),
        }
        if self.is_edit_mode:
            data['status'] = self.status_combo.currentText()
            if data['status'] == "Đã trả":
                data['return_date'] = self.return_date.dateTime().toPyDateTime()
        return data
    
    def validate(self) -> tuple:
        data = self.get_loan_data()
        if not data.get('borrower_unit'): return False, "Vui lòng nhập đơn vị mượn!"
        return True, ""