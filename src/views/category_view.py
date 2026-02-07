"""
Category Management View - CRUD interface for equipment categories
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QDialog, QFormLayout, QTextEdit, QMessageBox, QHeaderView,
    QFrame, QSpacerItem, QSizePolicy, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..models.category import Category


class CategoryDetailDialog(QDialog):
    """
    [MỚI] Dialog hiển thị chi tiết loại trang bị (Read-only)
    """
    def __init__(self, parent=None, category: Category = None):
        super().__init__(parent)
        self.category = category
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Chi tiết loại trang bị")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        title = QLabel(f"📦 {self.category.name}")
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
        
        add_row("Mã loại:", self.category.code)
        
        # Status logic
        status_text = "Đang sử dụng" if self.category.is_active else "Ngừng sử dụng"
        add_row("Trạng thái:", status_text)
        
        # Get count stats
        equip_count = self.category.get_equipment_count()
        add_row("Số lượng thiết bị:", f"{equip_count} thiết bị")
        
        layout.addWidget(group)
        
        # Description Group
        desc_group = QGroupBox("Mô tả")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(self.category.description or "Không có mô tả")
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


class CategoryDialog(QDialog):
    """Dialog for adding/editing categories"""
    
    def __init__(self, parent=None, category: Category = None):
        super().__init__(parent)
        self.category = category
        self.is_edit_mode = category is not None
        self._setup_ui()
        if self.is_edit_mode:
            self._load_category_data()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Sửa loại trang bị" if self.is_edit_mode else "Thêm loại trang bị mới")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Category name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập tên loại trang bị...")
        form_layout.addRow("Tên loại *:", self.name_input)
        
        # Category code
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("VD: VK-01, TB-02")
        form_layout.addRow("Mã loại:", self.code_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Mô tả thêm về loại trang bị...")
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
        save_btn.clicked.connect(self._save_category)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_category_data(self):
        """Load category data into form"""
        if not self.category:
            return
        
        self.name_input.setText(self.category.name)
        self.code_input.setText(self.category.code or "")
        self.description_input.setPlainText(self.category.description or "")
        self.active_checkbox.setChecked(self.category.is_active)
    
    def _save_category(self):
        """Save category to database"""
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        
        # Validation
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên loại trang bị!")
            self.name_input.setFocus()
            return
        
        # Check duplicate name
        if Category.name_exists(name, self.category.id if self.category else None):
            QMessageBox.warning(self, "Lỗi", "Tên loại trang bị đã tồn tại!")
            self.name_input.setFocus()
            return
        
        # Check duplicate code
        if code and Category.code_exists(code, self.category.id if self.category else None):
            QMessageBox.warning(self, "Lỗi", "Mã loại trang bị đã tồn tại!")
            self.code_input.setFocus()
            return
        
        # Create or update category
        if not self.category:
            self.category = Category()
        
        self.category.name = name
        self.category.code = code if code else None
        self.category.description = self.description_input.toPlainText().strip()
        self.category.is_active = self.active_checkbox.isChecked()
        
        try:
            self.category.save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu loại trang bị:\n{str(e)}")


class CategoryView(QWidget):
    """Main view for category management"""
    
    category_changed = pyqtSignal()  # Signal when category list changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_categories = []
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self._setup_ui()
        self.refresh_data()
    
    def _setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
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
        
        title_label = QLabel("📋  Quản lý Loại Trang bị")
        title_label.setObjectName("title")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button  
        refresh_btn = QPushButton("Làm mới")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        # Add button
        add_btn = QPushButton("➕  Thêm loại")
        add_btn.setObjectName("primaryBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_category)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Tìm kiếm theo tên hoặc mã loại...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        self.show_inactive = QCheckBox("Hiển thị loại không sử dụng")
        self.show_inactive.stateChanged.connect(self.refresh_data)
        search_layout.addWidget(self.show_inactive)
        
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tên loại", "Mã", "Trạng thái", "Thao tác"
        ])
        
        # Table settings
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 185)
        
        layout.addWidget(self.table)
        
        # Pagination bar
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        
        # Stats
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
        """Refresh category list"""
        include_inactive = self.show_inactive.isChecked()
        categories = Category.get_all(include_inactive=include_inactive)
        self.all_categories = categories
        self.current_page = 1
        self._update_pagination()
        
        total = Category.count(include_inactive=True)
        active = Category.count(include_inactive=False)
        self.stats_label.setText(f"Tổng cộng: {total} loại trang bị ({active} đang sử dụng)")
    
    def _update_pagination(self):
        """Update pagination state and display current page"""
        total = len(self.all_categories)
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.all_categories[start:end]
        
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
    
    def _populate_table(self, categories):
        """Populate table with category data"""
        self.table.setRowCount(len(categories))
        
        for row, category in enumerate(categories):
            self.table.setRowHeight(row, 50)
            
            # ID
            id_item = QTableWidgetItem(str(category.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(category.name))
            
            # Code
            self.table.setItem(row, 2, QTableWidgetItem(category.code or "-"))
            
            # Status
            status = "✅ Đang dùng" if category.is_active else "❌ Ngừng dùng"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, status_item)
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(5)
            
            # [MỚI] Nút Xem (Xanh Teal)
            view_btn = QPushButton("Xem")
            view_btn.setToolTip("Xem chi tiết")
            view_btn.setFixedSize(50, 28)
            view_btn.setObjectName("tableBtnView") 
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda checked, c=category: self._view_category_detail(c))
            action_layout.addWidget(view_btn)
            
            # Nút Sửa
            edit_btn = QPushButton("Sửa")
            edit_btn.setToolTip("Sửa thông tin")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setObjectName("tableBtn")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, c=category: self._edit_category(c))
            action_layout.addWidget(edit_btn)
            
            # Nút Xóa
            delete_btn = QPushButton("Xóa")
            delete_btn.setToolTip("Xóa loại trang bị")
            delete_btn.setFixedSize(50, 28)
            delete_btn.setObjectName("tableBtnDanger")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, c=category: self._delete_category(c))
            action_layout.addWidget(delete_btn)
            
            action_layout.addStretch()
            self.table.setCellWidget(row, 4, action_widget)
    
    def _on_search(self, text):
        """Handle search input"""
        if text.strip():
            categories = Category.search(text.strip())
        else:
            include_inactive = self.show_inactive.isChecked()
            categories = Category.get_all(include_inactive=include_inactive)
        self.all_categories = categories
        self.current_page = 1
        self._update_pagination()
    
    def _add_category(self):
        """Show dialog to add new category"""
        dialog = CategoryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.category_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã thêm loại trang bị mới!")
    
    def _view_category_detail(self, category: Category):
        """[MỚI] Show detail dialog"""
        dialog = CategoryDetailDialog(self, category)
        dialog.exec()

    def _edit_category(self, category: Category):
        """Show dialog to edit category"""
        dialog = CategoryDialog(self, category)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            self.category_changed.emit()
            QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin loại trang bị!")
    
    def _delete_category(self, category: Category):
        """Delete category"""
        count = category.get_equipment_count()
        if count > 0:
            reply = QMessageBox.question(
                self,
                "Xác nhận",
                f"Loại trang bị '{category.name}' đang được sử dụng bởi {count} trang bị.\n"
                f"Bạn có muốn đánh dấu ngừng sử dụng không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                category.delete()
                self.refresh_data()
                self.category_changed.emit()
                QMessageBox.information(self, "Thành công", "Đã đánh dấu ngừng sử dụng!")
        else:
            reply = QMessageBox.question(
                self,
                "Xác nhận xóa",
                f"Bạn có chắc muốn xóa loại trang bị '{category.name}'?\n"
                f"(Loại sẽ được đánh dấu ngừng sử dụng)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                category.delete()
                self.refresh_data()
                self.category_changed.emit()
                QMessageBox.information(self, "Thành công", "Đã xóa loại trang bị!")