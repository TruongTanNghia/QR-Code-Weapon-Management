"""
Equipment Input Dialog - Form for adding/editing equipment
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QPushButton, QFrame, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime

from ..models.equipment import Equipment
from ..models.unit import Unit, UNIT_LEVELS, get_level_name
from ..models.category import Category
from ..config import EQUIPMENT_STATUS


class EquipmentInputDialog(QDialog):
    """
    Dialog for adding or editing equipment
    """
    
    def __init__(self, parent=None, equipment: Equipment = None):
        super().__init__(parent)
        self.equipment = equipment
        self.is_edit_mode = equipment is not None
        self._setup_ui()
        
        if self.is_edit_mode:
            self._populate_form()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        title = "Sửa thông tin thiết bị" if self.is_edit_mode else "Thêm thiết bị mới"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f"📦 {title}")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Form
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Equipment name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên thiết bị...")
        form_layout.addRow("Tên thiết bị *:", self.name_input)
        
        # Serial number
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Nhập số hiệu duy nhất...")
        form_layout.addRow("Số hiệu *:", self.serial_input)
        
        # Category - load từ database
        self.category_combo = QComboBox()
        self._load_categories()
        form_layout.addRow("Loại *:", self.category_combo)
        
        # Manufacturer
        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText("Nhập tên nhà sản xuất...")
        form_layout.addRow("Nhà sản xuất:", self.manufacturer_input)
        
        # Manufacture year
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2100)
        self.year_spin.setValue(2020)
        self.year_spin.setSpecialValueText("-")
        form_layout.addRow("Năm sản xuất:", self.year_spin)
        
        # Receive date (Ngày cấp phát/nhập kho)
        self.receive_date_edit = QDateEdit()
        self.receive_date_edit.setCalendarPopup(True)
        self.receive_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.receive_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Ngày cấp phát:", self.receive_date_edit)
        
        # Status
        self.status_combo = QComboBox()
        for status in EQUIPMENT_STATUS:
            self.status_combo.addItem(status)
        form_layout.addRow("Tình trạng:", self.status_combo)
        
        # Unit - Chọn theo cấu trúc phân cấp
        unit_layout = QHBoxLayout()
        
        # Level 0 combo
        self.unit_level0_combo = QComboBox()
        self.unit_level0_combo.setMinimumWidth(150)
        self.unit_level0_combo.addItem("-- Chọn cấp 0 --", None)
        self.unit_level0_combo.currentIndexChanged.connect(self._on_unit_level0_changed)
        unit_layout.addWidget(self.unit_level0_combo)
        
        # Level 1 combo
        self.unit_level1_combo = QComboBox()
        self.unit_level1_combo.setMinimumWidth(150)
        self.unit_level1_combo.addItem("-- Chọn cấp 1 --", None)
        self.unit_level1_combo.currentIndexChanged.connect(self._on_unit_level1_changed)
        self.unit_level1_combo.setEnabled(False)
        unit_layout.addWidget(self.unit_level1_combo)
        
        # Level 2+ combo
        self.unit_level2_combo = QComboBox()
        self.unit_level2_combo.setMinimumWidth(150)
        self.unit_level2_combo.addItem("-- Chọn cấp 2+ --", None)
        self.unit_level2_combo.setEnabled(False)
        unit_layout.addWidget(self.unit_level2_combo)
        
        self._load_units_level0()
        
        form_layout.addRow("Đơn vị:", unit_layout)
        
        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Vị trí lưu trữ...")
        form_layout.addRow("Vị trí:", self.location_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Mô tả chi tiết về thiết bị...")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Mô tả:", self.description_input)
        
        layout.addWidget(form_frame)
        
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
    
    def _load_categories(self):
        """Load categories from database"""
        categories = Category.get_all(include_inactive=False)
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)
    
    def _load_units_level0(self):
        """Load level 0 units"""
        units = Unit.get_by_level(0)
        for unit in units:
            display = f"{unit.name}" + (f" ({unit.code})" if unit.code else "")
            self.unit_level0_combo.addItem(display, unit.id)
    
    def _on_unit_level0_changed(self):
        """Handle level 0 unit selection change"""
        # Clear and disable lower levels
        self.unit_level1_combo.clear()
        self.unit_level1_combo.addItem("-- Chọn cấp 1 --", None)
        self.unit_level2_combo.clear()
        self.unit_level2_combo.addItem("-- Chọn cấp 2+ --", None)
        self.unit_level2_combo.setEnabled(False)
        
        parent_id = self.unit_level0_combo.currentData()
        if parent_id:
            self.unit_level1_combo.setEnabled(True)
            # Load level 1 units that belong to selected level 0
            units = Unit.get_children(parent_id)
            for unit in units:
                display = f"{unit.name}" + (f" ({unit.code})" if unit.code else "")
                self.unit_level1_combo.addItem(display, unit.id)
        else:
            self.unit_level1_combo.setEnabled(False)
    
    def _on_unit_level1_changed(self):
        """Handle level 1 unit selection change"""
        # Clear level 2
        self.unit_level2_combo.clear()
        self.unit_level2_combo.addItem("-- Chọn cấp 2+ --", None)
        
        parent_id = self.unit_level1_combo.currentData()
        if parent_id:
            self.unit_level2_combo.setEnabled(True)
            # Load level 2+ units that belong to selected level 1
            units = Unit.get_children(parent_id)
            for unit in units:
                level_name = get_level_name(unit.level)
                display = f"{unit.name} ({level_name})" + (f" - {unit.code}" if unit.code else "")
                self.unit_level2_combo.addItem(display, unit.id)
        else:
            self.unit_level2_combo.setEnabled(False)
    
    def _get_selected_unit_id(self):
        """Get the most specific selected unit ID"""
        # Return the most specific (lowest level) selected unit
        if self.unit_level2_combo.currentData():
            return self.unit_level2_combo.currentData()
        if self.unit_level1_combo.currentData():
            return self.unit_level1_combo.currentData()
        if self.unit_level0_combo.currentData():
            return self.unit_level0_combo.currentData()
        return None
    
    def _populate_form(self):
        """Populate form with existing equipment data"""
        if not self.equipment:
            return
        
        self.name_input.setText(self.equipment.name)
        self.serial_input.setText(self.equipment.serial_number)
        
        # Find and set category
        idx = self.category_combo.findText(self.equipment.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        
        self.manufacturer_input.setText(self.equipment.manufacturer or "")
        
        if self.equipment.manufacture_year:
            self.year_spin.setValue(self.equipment.manufacture_year)
        
        # Set receive date
        if self.equipment.receive_date:
            try:
                if isinstance(self.equipment.receive_date, str):
                    dt = datetime.fromisoformat(self.equipment.receive_date.replace('Z', '+00:00'))
                else:
                    dt = self.equipment.receive_date
                self.receive_date_edit.setDate(QDate(dt.year, dt.month, dt.day))
            except:
                pass
        
        # Find and set status
        idx = self.status_combo.findText(self.equipment.status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        
        # Find and set unit hierarchy
        if self.equipment.unit_id:
            self._set_unit_hierarchy(self.equipment.unit_id)
        
        self.location_input.setText(self.equipment.location or "")
        self.description_input.setPlainText(self.equipment.description or "")
    
    def _set_unit_hierarchy(self, unit_id: int):
        """Set unit combo boxes based on unit hierarchy"""
        unit = Unit.get_by_id(unit_id)
        if not unit:
            return
        
        # Build hierarchy from unit to root
        hierarchy = []
        current = unit
        while current:
            hierarchy.insert(0, current)
            if current.parent_id:
                current = Unit.get_by_id(current.parent_id)
            else:
                current = None
        
        # Set level 0
        if len(hierarchy) >= 1:
            idx = self.unit_level0_combo.findData(hierarchy[0].id)
            if idx >= 0:
                self.unit_level0_combo.setCurrentIndex(idx)
        
        # Set level 1
        if len(hierarchy) >= 2:
            idx = self.unit_level1_combo.findData(hierarchy[1].id)
            if idx >= 0:
                self.unit_level1_combo.setCurrentIndex(idx)
        
        # Set level 2+
        if len(hierarchy) >= 3:
            # The last item in hierarchy is the actual selected unit
            idx = self.unit_level2_combo.findData(hierarchy[-1].id)
            if idx >= 0:
                self.unit_level2_combo.setCurrentIndex(idx)
    
    def _on_save(self):
        """Handle save button click"""
        # Validate
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
        
        # Check serial uniqueness
        exclude_id = self.equipment.id if self.is_edit_mode else None
        if Equipment.serial_exists(serial, exclude_id):
            QMessageBox.warning(
                self, "Lỗi",
                f"Số hiệu '{serial}' đã tồn tại trong hệ thống!"
            )
            self.serial_input.setFocus()
            return
        
        self.accept()
    
    def get_equipment(self) -> Equipment:
        """Get equipment object from form data"""
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
