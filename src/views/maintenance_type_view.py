"""
Maintenance Type Management View - CRUD interface for maintenance work types
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QDialog, QFormLayout, QTextEdit, QMessageBox, QHeaderView,
    QFrame, QSpacerItem, QSizePolicy, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..models.maintenance_type import MaintenanceType


class MaintenanceTypeDetailDialog(QDialog):
    """
    Dialog hiển thị chi tiết loại công việc (Read-only)
    """
    def __init__(self, parent=None, mtype: MaintenanceType = None):
        super().__init__(parent)
        self.mtype = mtype
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Chi tiết loại công việc")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        title = QLabel(f"🔧 {self.mtype.name}")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Content Group
        group = QGroupBox("Thông tin chung")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(12)
        
        # Helper function
        def add_row(label, value):
            val_label = QLabel(str(value) if value else "-")
            val_label.setStyleSheet("font-weight: bold; color: #333;")
            val_label.setWordWrap(True)
            form_layout.addRow(label, val_label)
        
        add_row("Mã loại:", self.mtype.code)
        
        # Status logic
        status_text = "Đang sử dụng" if self.mtype.is_active else "Ngừng sử dụng"
        add_row("Trạng thái:", status_text)
        
        # Get count stats
        maintenance_count = self.mtype.get_maintenance_count()
        add_row("Số lượng bản ghi:", f"{maintenance_count} bản ghi bảo dưỡng")
        
        layout.addWidget(group)
        
        # Description Group
        desc_group = QGroupBox("Mô tả")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(self.mtype.description or "Không có mô tả")
        desc_label.setWordWrap(True)
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("secondary")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)


class MaintenanceTypeDialog(QDialog):
    """Dialog for adding/editing maintenance types"""
    
    def __init__(self, parent=None, mtype: MaintenanceType = None):
        super().__init__(parent)
        self.mtype = mtype
        self.is_edit_mode = mtype is not None
        self._setup_ui()
        if self.is_edit_mode:
            self._load_type_data()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Sửa loại công việc" if self.is_edit_mode else "Thêm loại công việc mới")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Type name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên loại công việc...")
        form_layout.addRow("Tên loại *:", self.name_input)
        
        # Type code
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("VD: BD-DK, SC-01")
        form_layout.addRow("Mã loại:", self.code_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Mô tả thêm về loại công việc...")
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Mô tả:", self.description_input)
        
        # Active status
        self.active_checkbox = QCheckBox("Đang sử dụng")
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
        save_btn.clicked.connect(self._save_type)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_type_data(self):
        """Load type data into form"""
        if not self.mtype:
            return
        
        self.name_input.setText(self.mtype.name)
        self.code_input.setText(self.mtype.code or "")
        self.description_input.setPlainText(self.mtype.description or "")
        self.active_checkbox.setChecked(self.mtype.is_active)
    
    def _save_type(self):
        """Save maintenance type to database"""
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        
        # Validation
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên loại công việc!")
            self.name_input.setFocus()
            return
        
        # Check duplicate name
        if MaintenanceType.name_exists(name, self.mtype.id if self.mtype else None):
            QMessageBox.warning(self, "Lỗi", "Tên loại công việc đã tồn tại!")
            self.name_input.setFocus()
            return
        
        # Check duplicate code
        if code and MaintenanceType.code_exists(code, self.mtype.id if self.mtype else None):
            QMessageBox.warning(self, "Lỗi", "Mã loại công việc đã tồn tại!")
            self.code_input.setFocus()
            return
        
        # Create or update type
        if not self.mtype:
            self.mtype = MaintenanceType()
        
        self.mtype.name = name
        self.mtype.code = code if code else None
        self.mtype.description = self.description_input.toPlainText().strip()
        self.mtype.is_active = self.active_checkbox.isChecked()
        
        try:
            self.mtype.save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu loại công việc:\n{str(e)}")


class MaintenanceTypeView(QWidget):
    """Main view for maintenance type management"""
    
    type_changed = pyqtSignal()  # Signal when type list changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_types = []
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self._setup_ui()
        self.refresh_data()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
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
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔧 Quản lý Loại công việc")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add button
        add_btn = QPushButton("➕ Thêm mới")
        add_btn.setObjectName("primaryBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Filter row
        filter_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm theo tên, mã...")
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addSpacing(20)
        
        # Status filter
        filter_layout.addWidget(QLabel("Trạng thái:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả", None)
        self.status_filter.addItem("Đang sử dụng", True)
        self.status_filter.addItem("Ngừng sử dụng", False)
        self.status_filter.currentIndexChanged.connect(self._on_filter_change)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setObjectName("secondary") # Thêm style
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tên loại công việc", "Mã", "Mô tả", "Trạng thái", "Thao tác"
        ])
        
        # Table styling
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 185)
        
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
        
        # Pagination bar
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        
        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setObjectName("subtitle")
        pagination_layout.addWidget(self.stats_label)
        
        pagination_layout.addStretch()
        
        # [FIX] Đặt ID "pagingBtn"
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
    
    def refresh_data(self):
        """Refresh table data"""
        # Get filter status
        status_filter = self.status_filter.currentData()
        include_inactive = status_filter is None
        
        # Get all types
        if include_inactive:
            types = MaintenanceType.get_all(include_inactive=True)
        else:
            types = [t for t in MaintenanceType.get_all(include_inactive=True) 
                    if t.is_active == status_filter]
        
        # Apply search filter
        search_text = self.search_input.text().lower().strip()
        if search_text:
            types = [t for t in types if 
                    search_text in t.name.lower() or
                    (t.code and search_text in t.code.lower()) or
                    (t.description and search_text in t.description.lower())]
        
        self._update_pagination_data(types)
        
        # Update stats
        total = len(types)
        active = len([t for t in types if t.is_active])
        self.stats_label.setText(f"Tổng: {total} loại công việc | Đang sử dụng: {active}")
    
    def _update_pagination_data(self, types_list):
        """Store data and update pagination"""
        self.all_types = types_list
        self.current_page = 1
        self._update_pagination()
    
    def _update_pagination(self):
        """Update pagination state and display current page"""
        total = len(self.all_types)
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.all_types[start:end]
        
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
    
    def _populate_table(self, types: list):
        """Populate table with maintenance type data"""
        self.table.setRowCount(len(types))
        
        for row, mtype in enumerate(types):
            self.table.setRowHeight(row, 45)
            
            # ID
            id_item = QTableWidgetItem(str(mtype.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(mtype.name))
            
            # Code
            code_item = QTableWidgetItem(mtype.code or "-")
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, code_item)
            
            # Description
            desc = mtype.description[:50] + "..." if mtype.description and len(mtype.description) > 50 else (mtype.description or "-")
            self.table.setItem(row, 3, QTableWidgetItem(desc))
            
            # Status
            status_item = QTableWidgetItem("✅ Đang sử dụng" if mtype.is_active else "⛔ Ngừng sử dụng")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, status_item)
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setSpacing(5)
            
            # Nút Xem - Màu Teal
            view_btn = QPushButton("Xem")
            view_btn.setToolTip("Xem chi tiết")
            view_btn.setFixedSize(50, 28)
            view_btn.setObjectName("tableBtnView") 
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda checked, t=mtype: self._on_view(t))
            action_layout.addWidget(view_btn)
            
            # Nút Sửa - Màu Xanh
            edit_btn = QPushButton("Sửa")
            edit_btn.setToolTip("Chỉnh sửa")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setObjectName("tableBtn")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, t=mtype: self._on_edit(t))
            action_layout.addWidget(edit_btn)
            
            # Nút Xóa - Màu Đỏ
            delete_btn = QPushButton("Xóa")
            delete_btn.setToolTip("Xóa")
            delete_btn.setFixedSize(50, 28)
            delete_btn.setObjectName("tableBtnDanger")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, t=mtype: self._on_delete(t))
            action_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 5, action_widget)
            
            # Thêm stretch vào cuối để nút căn trái
            action_layout.addStretch()
    
    def _on_search(self, text):
        """Handle search input change"""
        self.refresh_data()
    
    def _on_filter_change(self, index):
        """Handle filter change"""
        self.refresh_data()
    
    def _on_add(self):
        """Handle add button click"""
        dialog = MaintenanceTypeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.type_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã thêm loại công việc mới!")
    
    def _on_view(self, mtype: MaintenanceType):
        """View type details"""
        dialog = MaintenanceTypeDetailDialog(self, mtype)
        dialog.exec()
    
    def _on_edit(self, mtype: MaintenanceType):
        """Edit a maintenance type"""
        dialog = MaintenanceTypeDialog(self, mtype)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.type_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã cập nhật loại công việc!")
    
    def _on_delete(self, mtype: MaintenanceType):
        """Delete a maintenance type"""
        # Check if has maintenance logs
        count = mtype.get_maintenance_count()
        
        if count > 0:
            # Has logs - offer to deactivate instead
            reply = QMessageBox.question(
                self, "Không thể xóa",
                f"Loại công việc '{mtype.name}' đang có {count} bản ghi bảo dưỡng sử dụng.\n\n"
                "Bạn có muốn chuyển sang trạng thái 'Ngừng sử dụng' thay vì xóa?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                mtype.is_active = False
                mtype.save()
                self.refresh_data()
                self.type_changed.emit()
                QMessageBox.information(self, "Thành công", "Đã chuyển loại công việc sang trạng thái ngừng sử dụng!")
        else:
            # No logs - can delete
            reply = QMessageBox.question(
                self, "Xác nhận xóa",
                f"Bạn có chắc chắn muốn xóa loại công việc '{mtype.name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                mtype.hard_delete()
                self.refresh_data()
                self.type_changed.emit()
                QMessageBox.information(self, "Thành công", "Đã xóa loại công việc!")
    
    def _on_double_click(self, index):
        """Handle double click on table row"""
        row = index.row()
        type_id = int(self.table.item(row, 0).text())
        mtype = MaintenanceType.get_by_id(type_id)
        if mtype:
            self._on_view(mtype)