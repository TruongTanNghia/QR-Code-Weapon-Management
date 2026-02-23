"""
Equipment Input Dialog - Form for adding/editing equipment
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QPushButton, QFrame, QMessageBox, QDateEdit, QGroupBox, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QPixmap
from datetime import datetime
from pathlib import Path

from ..models.equipment import Equipment
from ..models.unit import Unit, UNIT_LEVELS, get_level_name
from ..models.category import Category
from ..config import EQUIPMENT_STATUS, DATA_DIR


class EquipmentInputDialog(QDialog):
    """
    Dialog for adding or editing equipment
    """
    
    def __init__(self, parent=None, equipment: Equipment = None):
        super().__init__(parent)
        self.equipment = equipment
        self.is_edit_mode = equipment is not None
        
        # Biến quản lý hình ảnh
        self.new_images = [] # Đường dẫn ảnh mới thêm (trên máy người dùng)
        self.deleted_images = [] # Đường dẫn ảnh cũ muốn xóa (trong DB)
        self.current_images = self.equipment.images if self.is_edit_mode else []
        
        self._setup_ui()
        
        if self.is_edit_mode:
            self._populate_form()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        title = "Sửa thông tin thiết bị" if self.is_edit_mode else "Thêm thiết bị mới"
        self.setWindowTitle(title)
        self.setMinimumWidth(550)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f"📦 {title}")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Form
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Các trường nhập liệu (Giữ nguyên như cũ)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên thiết bị...")
        form_layout.addRow("Tên thiết bị *:", self.name_input)
        
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Nhập số hiệu duy nhất...")
        form_layout.addRow("Số hiệu *:", self.serial_input)
        
        self.category_combo = QComboBox()
        self._load_categories()
        form_layout.addRow("Loại *:", self.category_combo)
        
        self.manufacturer_input = QLineEdit()
        form_layout.addRow("Nhà sản xuất:", self.manufacturer_input)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2100)
        self.year_spin.setValue(2020)
        self.year_spin.setSpecialValueText("-")
        form_layout.addRow("Năm sản xuất:", self.year_spin)
        
        self.receive_date_edit = QDateEdit()
        self.receive_date_edit.setCalendarPopup(True)
        self.receive_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.receive_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Ngày cấp phát:", self.receive_date_edit)
        
        self.status_combo = QComboBox()
        for status in EQUIPMENT_STATUS:
            self.status_combo.addItem(status)
        form_layout.addRow("Tình trạng:", self.status_combo)
        
        # Unit - Chọn theo cấu trúc phân cấp
        unit_layout = QHBoxLayout()
        self.unit_level0_combo = QComboBox()
        self.unit_level0_combo.addItem("-- Chọn cấp 0 --", None)
        self.unit_level0_combo.currentIndexChanged.connect(self._on_unit_level0_changed)
        unit_layout.addWidget(self.unit_level0_combo)
        
        self.unit_level1_combo = QComboBox()
        self.unit_level1_combo.addItem("-- Chọn cấp 1 --", None)
        self.unit_level1_combo.currentIndexChanged.connect(self._on_unit_level1_changed)
        self.unit_level1_combo.setEnabled(False)
        unit_layout.addWidget(self.unit_level1_combo)
        
        self.unit_level2_combo = QComboBox()
        self.unit_level2_combo.addItem("-- Chọn cấp 2+ --", None)
        self.unit_level2_combo.setEnabled(False)
        unit_layout.addWidget(self.unit_level2_combo)
        
        self._load_units_level0()
        form_layout.addRow("Đơn vị:", unit_layout)
        
        self.location_input = QLineEdit()
        form_layout.addRow("Vị trí:", self.location_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addRow("Mô tả:", self.description_input)
        
        layout.addWidget(form_frame)
        
        # --- [MỚI] KHU VỰC HÌNH ẢNH MINH CHỨNG ---
        self.image_group = QGroupBox("Hình ảnh thiết bị (0/5)")
        self.image_layout = QHBoxLayout(self.image_group)
        
        # Layout chứa các ảnh nhỏ (thumbnail)
        self.image_preview_layout = QHBoxLayout()
        self.image_layout.addLayout(self.image_preview_layout)
        
        # Nút thêm ảnh
        self.add_image_btn = QPushButton("➕ Thêm")
        self.add_image_btn.setFixedSize(100, 50)
        self.add_image_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_image_btn.clicked.connect(self._choose_images)
        self.image_layout.addWidget(self.add_image_btn)
        self.image_layout.addStretch()
        
        layout.addWidget(self.image_group)
        self._render_images() # Hiển thị ảnh hiện có (nếu sửa)
        # ----------------------------------------
        
        # Note
        note_label = QLabel("* Các trường bắt buộc")
        note_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(note_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Lưu" if self.is_edit_mode else "➕ Thêm")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    # --- CÁC HÀM XỬ LÝ ẢNH [MỚI] ---
    def _choose_images(self):
        """Mở hộp thoại chọn ảnh"""
        total_current = len(self.current_images) - len(self.deleted_images) + len(self.new_images)
        if total_current >= 5:
            QMessageBox.warning(self, "Giới hạn", "Chỉ được phép tải lên tối đa 5 ảnh!")
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg)"
        )
        for f in files:
            if total_current < 5:
                self.new_images.append(f)
                total_current += 1
        self._render_images()

    def _render_images(self):
        """Vẽ lại danh sách ảnh thumbnail lên giao diện"""
        # Xóa các widget cũ
        while self.image_preview_layout.count():
            item = self.image_preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Hiển thị ảnh đã có trong DB (chưa bị đánh dấu xóa)
        for img_path in self.current_images:
            if img_path not in self.deleted_images:
                self._add_thumbnail(img_path, is_existing=True)
        
        # Hiển thị ảnh mới chọn
        for img_path in self.new_images:
            self._add_thumbnail(img_path, is_existing=False)
            
        # Cập nhật số lượng
        total = len(self.current_images) - len(self.deleted_images) + len(self.new_images)
        self.image_group.setTitle(f"Hình ảnh thiết bị ({total}/5)")
        self.add_image_btn.setVisible(total < 5)

    def _add_thumbnail(self, img_path: str, is_existing: bool):
        """Tạo widget cho 1 thumbnail ảnh"""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 5, 0)
        vbox.setSpacing(2)
        
        lbl = QLabel()
        lbl.setFixedSize(80, 80)
        lbl.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        
        # Lấy đường dẫn tuyệt đối để hiển thị
        if is_existing:
            full_path = str(DATA_DIR / img_path)
        else:
            full_path = img_path
            
        pixmap = QPixmap(full_path).scaled(
            80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        lbl.setPixmap(pixmap)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        del_btn = QPushButton("Xóa")
        del_btn.setStyleSheet("color: red; padding: 2px; font-size: 11px;")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda _, p=img_path, ext=is_existing: self._remove_image(p, ext))
        
        vbox.addWidget(lbl)
        vbox.addWidget(del_btn)
        self.image_preview_layout.addWidget(container)

    def _remove_image(self, img_path: str, is_existing: bool):
        """Xử lý khi bấm nút Xóa ảnh"""
        if is_existing:
            self.deleted_images.append(img_path)
        else:
            self.new_images.remove(img_path)
        self._render_images()

    def get_image_data(self):
        """Trả về dữ liệu ảnh để Controller xử lý"""
        return self.new_images, self.deleted_images
    # --------------------------------
    
    # ... (Các hàm _load_categories, _load_units_level0, _on_unit_level0_changed, _on_unit_level1_changed, _get_selected_unit_id, _set_unit_hierarchy giữ nguyên) ...
    def _load_categories(self):
        categories = Category.get_all(include_inactive=False)
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)
    
    def _load_units_level0(self):
        units = Unit.get_by_level(0)
        for unit in units:
            display = f"{unit.name}" + (f" ({unit.code})" if unit.code else "")
            self.unit_level0_combo.addItem(display, unit.id)
            
    def _on_unit_level0_changed(self):
        self.unit_level1_combo.clear()
        self.unit_level1_combo.addItem("-- Chọn cấp 1 --", None)
        self.unit_level2_combo.clear()
        self.unit_level2_combo.addItem("-- Chọn cấp 2+ --", None)
        self.unit_level2_combo.setEnabled(False)
        
        parent_id = self.unit_level0_combo.currentData()
        if parent_id:
            self.unit_level1_combo.setEnabled(True)
            units = Unit.get_children(parent_id)
            for unit in units:
                display = f"{unit.name}" + (f" ({unit.code})" if unit.code else "")
                self.unit_level1_combo.addItem(display, unit.id)
        else:
            self.unit_level1_combo.setEnabled(False)
            
    def _on_unit_level1_changed(self):
        self.unit_level2_combo.clear()
        self.unit_level2_combo.addItem("-- Chọn cấp 2+ --", None)
        
        parent_id = self.unit_level1_combo.currentData()
        if parent_id:
            self.unit_level2_combo.setEnabled(True)
            units = Unit.get_children(parent_id)
            for unit in units:
                level_name = get_level_name(unit.level)
                display = f"{unit.name} ({level_name})" + (f" - {unit.code}" if unit.code else "")
                self.unit_level2_combo.addItem(display, unit.id)
        else:
            self.unit_level2_combo.setEnabled(False)
            
    def _get_selected_unit_id(self):
        if self.unit_level2_combo.currentData(): return self.unit_level2_combo.currentData()
        if self.unit_level1_combo.currentData(): return self.unit_level1_combo.currentData()
        if self.unit_level0_combo.currentData(): return self.unit_level0_combo.currentData()
        return None

    def _populate_form(self):
        if not self.equipment: return
        self.name_input.setText(self.equipment.name)
        self.serial_input.setText(self.equipment.serial_number)
        
        idx = self.category_combo.findText(self.equipment.category)
        if idx >= 0: self.category_combo.setCurrentIndex(idx)
        self.manufacturer_input.setText(self.equipment.manufacturer or "")
        
        if self.equipment.manufacture_year:
            self.year_spin.setValue(self.equipment.manufacture_year)
            
        if self.equipment.receive_date:
            try:
                if isinstance(self.equipment.receive_date, str):
                    dt = datetime.fromisoformat(self.equipment.receive_date.replace('Z', '+00:00'))
                else:
                    dt = self.equipment.receive_date
                self.receive_date_edit.setDate(QDate(dt.year, dt.month, dt.day))
            except: pass
            
        idx = self.status_combo.findText(self.equipment.status)
        if idx >= 0: self.status_combo.setCurrentIndex(idx)
        
        if self.equipment.unit_id:
            self._set_unit_hierarchy(self.equipment.unit_id)
            
        self.location_input.setText(self.equipment.location or "")
        self.description_input.setPlainText(self.equipment.description or "")

    def _set_unit_hierarchy(self, unit_id: int):
        unit = Unit.get_by_id(unit_id)
        if not unit: return
        hierarchy = []
        current = unit
        while current:
            hierarchy.insert(0, current)
            if current.parent_id:
                current = Unit.get_by_id(current.parent_id)
            else:
                current = None
        if len(hierarchy) >= 1:
            idx = self.unit_level0_combo.findData(hierarchy[0].id)
            if idx >= 0: self.unit_level0_combo.setCurrentIndex(idx)
        if len(hierarchy) >= 2:
            idx = self.unit_level1_combo.findData(hierarchy[1].id)
            if idx >= 0: self.unit_level1_combo.setCurrentIndex(idx)
        if len(hierarchy) >= 3:
            idx = self.unit_level2_combo.findData(hierarchy[-1].id)
            if idx >= 0: self.unit_level2_combo.setCurrentIndex(idx)

    def _on_save(self):
        name = self.name_input.text().strip()
        serial = self.serial_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên thiết bị!")
            self.name_input.setFocus()
            return
        if not serial:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số hiệu!")
            self.serial_input.setFocus()
            return
            
        exclude_id = self.equipment.id if self.is_edit_mode else None
        if Equipment.serial_exists(serial, exclude_id):
            QMessageBox.warning(self, "Lỗi", f"Số hiệu '{serial}' đã tồn tại trong hệ thống!")
            self.serial_input.setFocus()
            return
            
        self.accept()
    
    def get_equipment(self) -> Equipment:
        equipment = Equipment()
        equipment.name = self.name_input.text().strip()
        equipment.serial_number = self.serial_input.text().strip()
        equipment.category = self.category_combo.currentText()
        equipment.manufacturer = self.manufacturer_input.text().strip()
        equipment.manufacture_year = self.year_spin.value() if self.year_spin.value() > 1900 else None
        equipment.receive_date = self.receive_date_edit.date().toPyDate()
        equipment.status = self.status_combo.currentText()
        equipment.unit_id = self._get_selected_unit_id()
        equipment.location = self.location_input.text().strip()
        equipment.description = self.description_input.toPlainText().strip()
        return equipment