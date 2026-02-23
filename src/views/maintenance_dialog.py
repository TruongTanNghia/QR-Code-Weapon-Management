"""
Maintenance Dialog - Form for adding/editing maintenance logs
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
from ..models.maintenance_log import MaintenanceLog, MAINTENANCE_STATUS
from ..models.maintenance_type import get_maintenance_type_names
from ..config import EQUIPMENT_STATUS, DATA_DIR 

# --- CLASS HỖ TRỢ CLICK VÀO ẢNH GIỐNG TRANG CHI TIẾT ---
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


class MaintenanceDialog(QDialog):
    def __init__(self, parent=None, equipment: Equipment = None, log: MaintenanceLog = None):
        super().__init__(parent)
        self.equipment = equipment
        self.log = log
        self.is_edit_mode = log is not None
        
        self.is_read_only = False
        if self.is_edit_mode and self.log.status == "Hoàn thành":
            self.is_read_only = True

        self.images_data = {
            'before': {'new': [], 'deleted': [], 'current': self.log.images_before if self.is_edit_mode else []},
            'after': {'new': [], 'deleted': [], 'current': self.log.images_after if self.is_edit_mode else []}
        }

        self._setup_ui()
        if self.is_edit_mode: self._load_log_data()
        if self.is_read_only: self._set_read_only_mode()
    
    def _setup_ui(self):
        if self.is_read_only:
            title = "Chi tiết bảo dưỡng (Đã hoàn thành)"
            header_text = "👁️ Chi tiết công việc bảo dưỡng"
        elif self.is_edit_mode:
            title = "Cập nhật bảo dưỡng"
            header_text = "✏️ Cập nhật công việc bảo dưỡng"
        else:
            title = "Ghi nhật ký bảo dưỡng"
            header_text = "📝 Ghi nhật ký bảo dưỡng/sửa chữa"

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
            equip_info = QLabel(f"<b>Thiết bị:</b> {self.equipment.name} | <b>Số hiệu:</b> {self.equipment.serial_number} | <b>Tình trạng:</b> {self.equipment.status}")
            equip_layout.addWidget(equip_info)
            layout.addWidget(equip_frame)
        
        form_group = QGroupBox("Thông tin chi tiết")
        form_layout = QFormLayout(form_group)
        
        self.type_combo = QComboBox()
        for mtype in get_maintenance_type_names(): self.type_combo.addItem(mtype)
        form_layout.addRow("Loại công việc *:", self.type_combo)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addRow("Mô tả:", self.description_input)
        
        self.technician_input = QLineEdit()
        form_layout.addRow("Kỹ thuật viên:", self.technician_input)
        
        self.start_date = QDateTimeEdit()
        self.start_date.setDateTime(QDateTime.currentDateTime())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày bắt đầu:", self.start_date)
        
        self.end_date = QDateTimeEdit()
        self.end_date.setDateTime(QDateTime.currentDateTime())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)
        self.end_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Ngày kết thúc:", self.end_date)
        
        self.status_combo = QComboBox()
        for status in MAINTENANCE_STATUS: self.status_combo.addItem(status)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        form_layout.addRow("Trạng thái:", self.status_combo)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(50)
        form_layout.addRow("Ghi chú:", self.notes_input)
        layout.addWidget(form_group)
        
        # --- KHU VỰC 2 GALLERY ẢNH TRƯỚC/SAU ---
        images_container = QHBoxLayout()
        images_container.setSpacing(15)
        
        self.group_before, self.layout_before, self.btn_before = self._create_gallery_ui("before", "Ảnh TRƯỚC bảo dưỡng")
        images_container.addWidget(self.group_before)
        
        self.group_after, self.layout_after, self.btn_after = self._create_gallery_ui("after", "Ảnh SAU bảo dưỡng")
        images_container.addWidget(self.group_after)
        
        layout.addLayout(images_container)
        self._render_all_images()
        # ----------------------------------------

        self.status_group = QGroupBox("Cập nhật tình trạng thiết bị")
        status_layout = QHBoxLayout(self.status_group)
        self.update_status_check = QCheckBox("Cập nhật tình trạng thiết bị thành:")
        status_layout.addWidget(self.update_status_check)
        self.new_status_combo = QComboBox()
        for status in EQUIPMENT_STATUS: self.new_status_combo.addItem(status)
        self.new_status_combo.setEnabled(False)
        status_layout.addWidget(self.new_status_combo)
        self.update_status_check.toggled.connect(self.new_status_combo.setEnabled)
        
        layout.addWidget(self.status_group)
        
        button_layout = QHBoxLayout()
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
        
        if not self.is_read_only:
            save_text = "💾 Cập nhật" if self.is_edit_mode else "💾 Lưu"
            self.save_btn = QPushButton(save_text)
            self.save_btn.clicked.connect(self.accept)
            button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

    # --- CÁC HÀM XỬ LÝ UI 2 GALLERY ---
    def _create_gallery_ui(self, category: str, title: str):
        group = QGroupBox(f"{title} (0/5)")
        group.setMinimumHeight(110) # [FIX] Khóa cứng chiều cao tối thiểu để viền không bị vỡ
        
        layout = QHBoxLayout(group)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(10, 15, 10, 10)
        
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(5)
        layout.addLayout(preview_layout)
        
        add_btn = QPushButton("➕ Thêm")
        add_btn.setFixedSize(60, 60)
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
        self._render_gallery("before", self.group_before, self.layout_before, self.btn_before, "Ảnh TRƯỚC bảo dưỡng")
        self._render_gallery("after", self.group_after, self.layout_after, self.btn_after, "Ảnh SAU bảo dưỡng")

    def _render_gallery(self, category, group_box, preview_layout, add_btn, title_prefix):
        # [FIX] Dọn dẹp Layout an toàn: Gán ra biến 'widget' trước khi xóa
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
        
        # [LOGIC] Chỉ được tải ảnh SAU khi đã chọn trạng thái Hoàn thành
        can_add = total < 5 and not self.is_read_only
        if category == "after" and self.status_combo.currentText() != "Hoàn thành":
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
        
        # Load và hiển thị ảnh
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
        self.type_combo.setEnabled(False)
        self.description_input.setReadOnly(True)
        self.technician_input.setReadOnly(True)
        self.start_date.setReadOnly(True)
        self.end_date.setReadOnly(True)
        self.status_combo.setEnabled(False)
        self.notes_input.setReadOnly(True)
        self.status_group.setEnabled(False)
        self.cancel_btn.setText("Đóng")

    def _on_status_changed(self, status: str):
        is_completed = status == "Hoàn thành"
        self.end_date.setEnabled(is_completed)
        if is_completed: self.end_date.setDateTime(QDateTime.currentDateTime())
        
        # Cập nhật lại UI ảnh khi đổi trạng thái (Để ẩn/hiện nút Thêm ảnh SAU)
        self._render_all_images()
    
    def _load_log_data(self):
        if not self.log: return
        
        idx = self.type_combo.findText(self.log.maintenance_type)
        if idx >= 0: self.type_combo.setCurrentIndex(idx)
        
        self.description_input.setPlainText(self.log.description or "")
        self.technician_input.setText(self.log.technician_name or "")
        
        # Xử lý an toàn kiểu dữ liệu thời gian (String -> Datetime)
        if self.log.start_date:
            dt = self.log.start_date
            if isinstance(dt, str):
                try: 
                    clean_str = dt.split('.')[0].replace('Z', '')
                    dt = datetime.fromisoformat(clean_str)
                except ValueError:
                    try: dt = datetime.strptime(dt.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except: pass
            if isinstance(dt, datetime):
                self.start_date.setDateTime(QDateTime(dt))
        
        if self.log.end_date:
            dt = self.log.end_date
            if isinstance(dt, str):
                try: 
                    clean_str = dt.split('.')[0].replace('Z', '')
                    dt = datetime.fromisoformat(clean_str)
                except ValueError:
                    try: dt = datetime.strptime(dt.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except: pass
            if isinstance(dt, datetime):
                self.end_date.setDateTime(QDateTime(dt))
        
        idx = self.status_combo.findText(self.log.status)
        if idx >= 0: self.status_combo.setCurrentIndex(idx)
        
        self.notes_input.setPlainText(self.log.notes or "")
    
    def _delete_log(self):
        reply = QMessageBox.question(self, "Xác nhận xóa", "Bạn có chắc muốn xóa bản ghi bảo dưỡng này?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.log and self.log.delete(): self.done(2)
            else: QMessageBox.warning(self, "Lỗi", "Không thể xóa bản ghi!")
    
    def get_data_as_dict(self) -> dict:
        status = self.status_combo.currentText()
        end_date = None
        if status == "Hoàn thành":
            if self.is_edit_mode and self.log and self.log.status != "Hoàn thành": end_date = datetime.now()
            else: end_date = self.end_date.dateTime().toPyDateTime()

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
        if self.update_status_check.isChecked(): return self.new_status_combo.currentText()
        return None