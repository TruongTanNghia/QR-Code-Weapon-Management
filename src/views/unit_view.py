"""
Unit Management View - CRUD interface for military units with tree structure
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QComboBox,
    QDialog, QFormLayout, QTextEdit, QMessageBox, QHeaderView,
    QFrame, QSpacerItem, QSizePolicy, QCheckBox, QAbstractItemView,
    QGroupBox, QGraphicsDropShadowEffect, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QIcon

from ..models.unit import Unit, UNIT_LEVELS, get_level_name


class UnitDetailDialog(QDialog):
    """
    Dialog hiển thị chi tiết đơn vị (Read-only)
    """
    def __init__(self, parent=None, unit: Unit = None):
        super().__init__(parent)
        self.unit = unit
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Chi tiết đơn vị")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        title = QLabel(f"🏢 {self.unit.name}")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content Group
        group = QGroupBox("Thông tin chung")
        group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        # Style adaptive
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: palette(text);
            }
        """)
        
        form_layout = QFormLayout(group)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(15, 20, 15, 15)
        
        # Helper to add rows
        def add_row(label, value):
            lbl_widget = QLabel(label)
            lbl_widget.setFont(QFont("Segoe UI", 10))
            lbl_widget.setStyleSheet("color: palette(text); opacity: 0.8;")
            
            val_widget = QLabel(str(value) if value else "-")
            val_widget.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            val_widget.setWordWrap(True)
            val_widget.setStyleSheet("color: palette(text);")
            form_layout.addRow(lbl_widget, val_widget)
        
        # Resolve parent name
        parent_name = "-"
        if self.unit.parent_id:
            parent = Unit.get_by_id(self.unit.parent_id)
            if parent:
                parent_name = parent.name
        elif self.unit.level == 0:
            parent_name = "Cấp cao nhất (Không có cấp trên)"
            
        add_row("Mã đơn vị:", self.unit.code)
        add_row("Cấp độ:", get_level_name(self.unit.level))
        add_row("Đơn vị cấp trên:", parent_name)
        add_row("Chỉ huy:", self.unit.commander)
        add_row("Điện thoại:", self.unit.phone)
        add_row("Địa chỉ:", self.unit.address)
        
        status_text = "Đang hoạt động" if self.unit.is_active else "Ngừng hoạt động"
        status_lbl = QLabel(status_text)
        status_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        status_lbl.setStyleSheet("color: #27ae60;" if self.unit.is_active else "color: #c0392b;")
        form_layout.addRow(QLabel("Trạng thái:"), status_lbl)
        
        layout.addWidget(group)
        
        # Description Group
        desc_group = QGroupBox("Mô tả")
        desc_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        desc_group.setStyleSheet(group.styleSheet())
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(self.unit.description or "Không có mô tả")
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setObjectName("secondaryBtn")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)


class UnitDialog(QDialog):
    """Dialog for adding/editing units"""
    
    def __init__(self, parent=None, unit: Unit = None):
        super().__init__(parent)
        self.unit = unit
        self.is_edit_mode = unit is not None
        self._setup_ui()
        if self.is_edit_mode:
            self._load_unit_data()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Sửa đơn vị" if self.is_edit_mode else "Thêm đơn vị mới")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("Thông tin đơn vị")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Unit name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên đơn vị...")
        form_layout.addRow("Tên đơn vị *:", self.name_input)
        
        # Unit code
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("VD: E1-D2-C3")
        form_layout.addRow("Mã đơn vị:", self.code_input)
        
        # Unit level - connect to update parent options
        self.level_combo = QComboBox()
        for level, name in UNIT_LEVELS.items():
            self.level_combo.addItem(name, level)
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        form_layout.addRow("Cấp đơn vị:", self.level_combo)
        
        # Parent unit - will be populated based on level
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("-- Không có cấp trên --", None)
        form_layout.addRow("Đơn vị cấp trên:", self.parent_combo)
        
        # Commander
        self.commander_input = QLineEdit()
        self.commander_input.setPlaceholderText("Họ tên chỉ huy...")
        form_layout.addRow("Chỉ huy:", self.commander_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Số điện thoại...")
        form_layout.addRow("Điện thoại:", self.phone_input)
        
        # Address
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Địa chỉ đơn vị...")
        form_layout.addRow("Địa chỉ:", self.address_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Mô tả thêm...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Mô tả:", self.description_input)
        
        # Active status
        self.active_checkbox = QCheckBox("Đang hoạt động")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("Trạng thái:", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Lưu" if self.is_edit_mode else "Thêm mới")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_unit)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Initialize parent combo based on default level
        self._on_level_changed()
    
    def _on_level_changed(self):
        """Handle level change - update parent unit options"""
        current_level = self.level_combo.currentData()
        self.parent_combo.clear()
        
        if current_level == 0:
            self.parent_combo.addItem("-- Cấp cao nhất, không có cấp trên --", None)
            self.parent_combo.setEnabled(False)
        else:
            self.parent_combo.setEnabled(True)
            self.parent_combo.addItem("-- Chọn đơn vị cấp trên --", None)
            
            parent_level = current_level - 1
            parent_units = Unit.get_by_level(parent_level)
            if self.unit:
                parent_units = [u for u in parent_units if u.id != self.unit.id]
            
            if parent_units:
                for unit in parent_units:
                    level_name = get_level_name(unit.level)
                    display_text = f"{unit.name} ({level_name})"
                    if unit.code:
                        display_text = f"{unit.name} - {unit.code} ({level_name})"
                    self.parent_combo.addItem(display_text, unit.id)
            else:
                parent_level_name = get_level_name(parent_level)
                self.parent_combo.addItem(f"-- Chưa có đơn vị {parent_level_name} --", None)
    
    def _load_unit_data(self):
        if not self.unit: return
        self.name_input.setText(self.unit.name)
        self.code_input.setText(self.unit.code or "")
        index = self.level_combo.findData(self.unit.level)
        if index >= 0: self.level_combo.setCurrentIndex(index)
        if self.unit.parent_id:
            index = self.parent_combo.findData(self.unit.parent_id)
            if index >= 0: self.parent_combo.setCurrentIndex(index)
        self.commander_input.setText(self.unit.commander or "")
        self.phone_input.setText(self.unit.phone or "")
        self.address_input.setText(self.unit.address or "")
        self.description_input.setPlainText(self.unit.description or "")
        self.active_checkbox.setChecked(self.unit.is_active)
    
    def _save_unit(self):
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        level = self.level_combo.currentData()
        parent_id = self.parent_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đơn vị!")
            self.name_input.setFocus()
            return
        
        if code and Unit.code_exists(code, self.unit.id if self.unit else None):
            QMessageBox.warning(self, "Lỗi", "Mã đơn vị đã tồn tại!")
            self.code_input.setFocus()
            return
        
        if level > 0 and not parent_id:
            level_name = get_level_name(level)
            parent_level_name = get_level_name(level - 1)
            QMessageBox.warning(self, "Lỗi", f"Đơn vị {level_name} cần phải chọn đơn vị cấp trên ({parent_level_name})!")
            self.parent_combo.setFocus()
            return
        
        if not self.unit: self.unit = Unit()
        self.unit.name = name
        self.unit.code = code
        self.unit.level = level
        self.unit.parent_id = parent_id
        self.unit.commander = self.commander_input.text().strip()
        self.unit.phone = self.phone_input.text().strip()
        self.unit.address = self.address_input.text().strip()
        self.unit.description = self.description_input.toPlainText().strip()
        self.unit.is_active = self.active_checkbox.isChecked()
        
        try:
            self.unit.save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu đơn vị:\n{str(e)}")


class UnitView(QWidget):
    """Main view for unit management with tree structure"""
    
    unit_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()
    
    def _setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # --- HEADER SECTION ---
        header_layout = QHBoxLayout()
        title_label = QLabel("🏢 Quản lý Đơn vị")
        title_label.setObjectName("title")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Add button
        add_btn = QPushButton("➕ Thêm đơn vị")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_unit)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # --- CONTROL CARD (Filter & Actions) ---
        control_frame = QGroupBox()
        control_frame.setTitle("") 
        control_frame.setStyleSheet("""
            QGroupBox {
                border: 1px solid palette(mid);
                border-radius: 8px;
                background-color: palette(window);
                margin-top: 0px; 
            }
        """)
        
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(15)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm theo tên hoặc mã đơn vị...")
        self.search_input.setMinimumWidth(300)
        self.search_input.setMinimumHeight(45)
        self.search_input.textChanged.connect(self._on_search)
        control_layout.addWidget(self.search_input)
        
        # Expand/Collapse Buttons
        expand_btn = QPushButton("📂 Mở rộng")
        expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        expand_btn.setObjectName("secondary")
        expand_btn.setMinimumHeight(45)
        expand_btn.clicked.connect(lambda: self.tree.expandAll())
        control_layout.addWidget(expand_btn)
        
        collapse_btn = QPushButton("📁 Thu gọn")
        collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        collapse_btn.setObjectName("secondary")
        collapse_btn.setMinimumHeight(45)
        collapse_btn.clicked.connect(lambda: self.tree.collapseAll())
        control_layout.addWidget(collapse_btn)
        
        control_layout.addStretch()
        
        # Checkbox
        self.show_inactive = QCheckBox("Hiển thị đơn vị ngừng hoạt động")
        self.show_inactive.stateChanged.connect(self.refresh_data)
        control_layout.addWidget(self.show_inactive)
        
        layout.addWidget(control_frame)
        
        # --- TREE WIDGET ---
        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels([
            "Tên đơn vị", "Mã", "Cấp", "Chỉ huy", "Trạng thái", "Thao tác"
        ])
        
        # [FIX FINAL] Style tối giản cho TreeWidget
        # self.tree.setStyleSheet("""
        #     QTreeWidget {
        #         border: 1px solid palette(mid);
        #         border-radius: 8px;
        #         background-color: palette(base);
        #         alternate-background-color: palette(alternate-base);
        #     }
        #     QHeaderView::section {
        #         padding: 8px;
        #         border: none;
        #         border-bottom: 2px solid palette(mid);
        #         background-color: transparent;
        #         font-weight: bold;
        #     }
        #     /* Xóa QTreeWidget::item border-bottom để tránh lỗi background */
            
        #     QTreeWidget::item:selected {
        #         background-color: rgba(41, 128, 185, 0.3);
        #         color: palette(text);
        #         border: 1px solid #2980b9;
        #     }
        # """)
        
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(30)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Column widths
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.tree.setColumnWidth(1, 100) # Mã
        self.tree.setColumnWidth(2, 100) # Cấp
        self.tree.setColumnWidth(4, 120) # Trạng thái
        self.tree.setColumnWidth(5, 185) # Thao tác
        
        layout.addWidget(self.tree)
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setObjectName("subtitle")
        self.stats_label.setStyleSheet("font-size: 12px; opacity: 0.7;") 
        layout.addWidget(self.stats_label)
    
    def refresh_data(self):
        """Refresh unit list with tree structure"""
        self.tree.clear()
        include_inactive = self.show_inactive.isChecked()
        
        # Get level 0 units (root)
        level0_units = Unit.get_by_level(0)
        if not include_inactive:
            level0_units = [u for u in level0_units if u.is_active]
        
        for unit in level0_units:
            item = self._create_tree_item(unit)
            self.tree.addTopLevelItem(item)
            self._set_item_actions(item, unit)
            self._add_children(item, unit.id, include_inactive)
        
        self.tree.expandToDepth(0)
        
        total = Unit.count(include_inactive=include_inactive)
        active = Unit.count(include_inactive=False)
        self.stats_label.setText(f"Tổng cộng: {total} đơn vị ({active} đang hoạt động)")
    
    def _add_children(self, parent_item: QTreeWidgetItem, parent_id: int, include_inactive: bool):
        children = Unit.get_children(parent_id)
        if not include_inactive:
            children = [u for u in children if u.is_active]
        
        for child in children:
            child_item = self._create_tree_item(child)
            parent_item.addChild(child_item)
            self._set_item_actions(child_item, child)
            self._add_children(child_item, child.id, include_inactive)
    
    def _set_item_actions(self, item: QTreeWidgetItem, unit: Unit):
        """Set action buttons for tree item"""
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 4, 5, 4)
        action_layout.setSpacing(5)
        
        # Xem
        view_btn = QPushButton("Xem")
        view_btn.setFixedSize(50, 28)
        view_btn.setObjectName("tableBtnView") 
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.clicked.connect(lambda checked, uid=unit.id: self._view_unit_detail(uid))
        action_layout.addWidget(view_btn)
        
        # Sửa
        edit_btn = QPushButton("Sửa")
        edit_btn.setFixedSize(50, 28)
        edit_btn.setObjectName("tableBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda checked, uid=unit.id: self._edit_unit_by_id(uid))
        action_layout.addWidget(edit_btn)
        
        # Xóa
        delete_btn = QPushButton("Xóa")
        delete_btn.setFixedSize(50, 28)
        delete_btn.setObjectName("tableBtnDanger")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda checked, uid=unit.id: self._delete_unit_by_id(uid))
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        self.tree.setItemWidget(item, 5, action_widget)
    
    def _create_tree_item(self, unit: Unit) -> QTreeWidgetItem:
        """Create tree item for a unit"""
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, unit.id)
        
        item.setText(0, unit.name)
        item.setText(1, unit.code or "-")
        item.setText(2, get_level_name(unit.level))
        item.setText(3, unit.commander or "-")
        
        status = "Hoạt động" if unit.is_active else "Ngừng"
        item.setText(4, status)
        
        if not unit.is_active:
            item.setForeground(4, QColor("#e74c3c")) # Red
        else:
            item.setForeground(4, QColor("#27ae60")) # Green
        
        # Bold the unit name
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        item.setFont(0, font)
        
        return item
    
    def _on_search(self, text):
        if text.strip():
            units = Unit.search(text.strip())
            self.tree.clear()
            for unit in units:
                item = self._create_tree_item(unit)
                self.tree.addTopLevelItem(item)
                self._set_item_actions(item, unit)
        else:
            self.refresh_data()
    
    def _add_unit(self):
        dialog = UnitDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.unit_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã thêm đơn vị mới!")
    
    def _view_unit_detail(self, unit_id: int):
        unit = Unit.get_by_id(unit_id)
        if unit:
            dialog = UnitDetailDialog(self, unit)
            dialog.exec()
            
    def _edit_unit_by_id(self, unit_id: int):
        unit = Unit.get_by_id(unit_id)
        if unit:
            self._edit_unit(unit)
    
    def _edit_unit(self, unit: Unit):
        dialog = UnitDialog(self, unit)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.unit_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin đơn vị!")
    
    def _delete_unit_by_id(self, unit_id: int):
        unit = Unit.get_by_id(unit_id)
        if unit:
            self._delete_unit(unit)
    
    def _delete_unit(self, unit: Unit):
        children = Unit.get_children(unit.id)
        if children:
            QMessageBox.warning(
                self, "Không thể xóa",
                f"Đơn vị '{unit.name}' còn có {len(children)} đơn vị cấp dưới.\nVui lòng xóa các đơn vị cấp dưới trước!"
            )
            return
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa đơn vị '{unit.name}'?\n(Đơn vị sẽ được đánh dấu ngừng hoạt động)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            unit.delete()
            self.refresh_data()
            self.unit_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã xóa đơn vị!")