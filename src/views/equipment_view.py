"""
Equipment View - Equipment management interface
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QFrame,
    QMessageBox, QMenu, QFileDialog, QAbstractItemView,
    QDateEdit, QCheckBox # [MỚI] Import
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QAction, QPixmap, QImage, QColor
from datetime import datetime

from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..models.category import Category
from ..models.database import Database
from ..controllers.maintenance_controller import MaintenanceController
from ..controllers.user_controller import UserController
from ..services.qr_service import QRService
from ..services.export_service import ExportService
from ..config import EQUIPMENT_STATUS
from .input_dialog import EquipmentInputDialog
from .maintenance_dialog import MaintenanceDialog
from .equipment_detail_dialog import EquipmentDetailDialog


class EquipmentView(QWidget):
    """
    Equipment management view with CRUD operations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.qr_service = QRService()
        self.export_service = ExportService()
        self.maintenance_controller = MaintenanceController()
        self.db = Database()
        self.current_equipment_list = []
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the equipment management UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Style cho nút phân trang
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
            QPushButton#pagingBtn:pressed {
                background-color: palette(mid);
            }
            QPushButton#pagingBtn:disabled {
                background-color: palette(window);
                color: palette(mid);
                border: 1px solid palette(midlight);
            }
        """)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📦 Quản lý Vũ khí Trang bị")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)) 
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Add button
        add_btn = QPushButton("➕ Thêm mới")
        add_btn.setObjectName("primaryBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # --- SEARCH AND FILTER BAR (Cải tiến) ---
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        
        # Đổi thành Vertical Layout để chứa 2 dòng
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(10)
        
        # [DÒNG 1] Tìm kiếm, Loại, Tình trạng
        row1_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm theo tên, số hiệu...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setMinimumWidth(250)
        row1_layout.addWidget(self.search_input)
        
        row1_layout.addWidget(QLabel("Loại:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Tất cả", None)
        self.category_filter.currentIndexChanged.connect(self._on_filter_change)
        row1_layout.addWidget(self.category_filter)
        
        row1_layout.addWidget(QLabel("Tình trạng:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả", None)
        for status in EQUIPMENT_STATUS:
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self._on_filter_change)
        row1_layout.addWidget(self.status_filter)
        
        row1_layout.addStretch()
        filter_layout.addLayout(row1_layout)
        
        # [DÒNG 2] Lọc theo ngày, Làm mới
        row2_layout = QHBoxLayout()
        
        self.date_filter_check = QCheckBox("Lọc theo ngày cấp phát:")
        self.date_filter_check.toggled.connect(self._on_date_filter_toggle)
        row2_layout.addWidget(self.date_filter_check)
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.setDate(QDate.currentDate().addDays(-365)) # Mặc định 1 năm trước
        self.from_date.setEnabled(False)
        self.from_date.dateChanged.connect(self.refresh_data)
        row2_layout.addWidget(QLabel("Từ:"))
        row2_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setEnabled(False)
        self.to_date.dateChanged.connect(self.refresh_data)
        row2_layout.addWidget(QLabel("Đến:"))
        row2_layout.addWidget(self.to_date)
        
        row2_layout.addStretch()
        
        refresh_btn = QPushButton("⟳ Làm mới")
        refresh_btn.setToolTip("Làm mới danh sách")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        row2_layout.addWidget(refresh_btn)
        
        filter_layout.addLayout(row2_layout)
        
        layout.addWidget(filter_frame)
        
        # Equipment table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tên thiết bị", "Số hiệu", "Loại", 
            "Năm SX", "Tình trạng", "Ngày cấp", "Thao tác" # [FIX] Đổi "Đơn vị" -> "Ngày cấp"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 120) # [FIX] Cột ngày cấp
        self.table.setColumnWidth(7, 230)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        
        self.table.doubleClicked.connect(self._on_row_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)
        
        # Pagination bar
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        
        self.count_label = QLabel("Tổng: 0 thiết bị")
        self.count_label.setObjectName("subtitle")
        pagination_layout.addWidget(self.count_label)
        
        pagination_layout.addStretch()
        
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
        
        # Export buttons
        export_list_btn = QPushButton("📄 Xuất danh sách")
        export_list_btn.setObjectName("secondary")
        export_list_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_list_btn.clicked.connect(self.export_equipment_list)
        pagination_layout.addWidget(export_list_btn)
        
        export_qr_btn = QPushButton("🏷️ Xuất mã QR")
        export_qr_btn.setObjectName("secondary")
        export_qr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_qr_btn.clicked.connect(self.export_qr_sheet)
        pagination_layout.addWidget(export_qr_btn)
        
        layout.addLayout(pagination_layout)
        
        # Initial load will happen in showEvent
    
    def _on_date_filter_toggle(self, checked):
        """[MỚI] Toggle date filter controls"""
        self.from_date.setEnabled(checked)
        self.to_date.setEnabled(checked)
        self.refresh_data()

    def _load_categories(self):
        """Load danh sách loại trang bị từ Database"""
        current_data = self.category_filter.currentData()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("Tất cả", None)
        
        categories = Category.get_all()
        for cat in categories:
            self.category_filter.addItem(cat.name, cat.name)
            
        if current_data:
            index = self.category_filter.findData(current_data)
            if index >= 0:
                self.category_filter.setCurrentIndex(index)
                
        self.category_filter.blockSignals(False)

    def refresh_data(self):
        """Refresh equipment list from database"""
        keyword = self.search_input.text().strip()
        category = self.category_filter.currentData()
        status = self.status_filter.currentData()
        
        # [MỚI] Logic lọc kết hợp
        if self.date_filter_check.isChecked():
            from_dt = self.from_date.date().toPyDate()
            to_dt = self.to_date.date().toPyDate()
            from_datetime = datetime.combine(from_dt, datetime.min.time())
            to_datetime = datetime.combine(to_dt, datetime.max.time())
            equipment_list = Equipment.get_by_date_range(from_datetime, to_datetime)
        elif keyword:
            equipment_list = Equipment.search(keyword)
        elif category:
            equipment_list = Equipment.get_by_category(category)
        elif status:
            equipment_list = Equipment.get_by_status(status)
        else:
            equipment_list = Equipment.get_all(limit=500)
        
        # Apply secondary filters in memory (Python list filtering)
        # Nếu đã lọc theo ngày, tiếp tục lọc theo các tiêu chí khác nếu có
        if self.date_filter_check.isChecked():
            if keyword:
                k = keyword.lower()
                equipment_list = [e for e in equipment_list if k in e.name.lower() or k in e.serial_number.lower()]
            if category:
                equipment_list = [e for e in equipment_list if e.category == category]
            if status:
                equipment_list = [e for e in equipment_list if e.status == status]
        else:
            # Logic cũ cho các trường hợp khác
            if keyword and category:
                equipment_list = [e for e in equipment_list if e.category == category]
            if keyword and status:
                equipment_list = [e for e in equipment_list if e.status == status]
            if category and status and not keyword:
                equipment_list = [e for e in equipment_list if e.status == status]
        
        self.current_equipment_list = equipment_list
        self.current_page = 1
        self._update_pagination()
    
    # [MỚI] Hàm format ngày hiển thị
    def _format_date(self, date_val):
        if not date_val: return "-"
        if hasattr(date_val, 'strftime'): return date_val.strftime("%d/%m/%Y")
        s = str(date_val)[:10]
        try:
            if "-" in s:
                p = s.split("-")
                return f"{p[2]}/{p[1]}/{p[0]}"
        except: pass
        return s

    def _populate_table(self, equipment_list: list):
        """Populate table with equipment data"""
        self.table.setRowCount(len(equipment_list))
        
        for row, equip in enumerate(equipment_list):
            self.table.setRowHeight(row, 50)
            
            id_item = QTableWidgetItem(str(equip.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(equip.name))
            self.table.setItem(row, 2, QTableWidgetItem(equip.serial_number))
            self.table.setItem(row, 3, QTableWidgetItem(equip.category))
            
            year_text = str(equip.manufacture_year) if equip.manufacture_year else "-"
            year_item = QTableWidgetItem(year_text)
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, year_item)
            
            status_item = QTableWidgetItem(equip.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if equip.status in ["Cấp 1", "Cấp 2"]:
                status_item.setForeground(QColor("#4CAF50"))
            elif equip.status == "Cấp 3":
                status_item.setForeground(QColor("#FF9800"))
            elif equip.status in ["Cấp 4", "Cấp 5"]:
                status_item.setForeground(QColor("#F44336"))
            self.table.setItem(row, 5, status_item)
            
            # [FIX] Hiển thị Ngày cấp phát thay vì Đơn vị
            date_str = self._format_date(equip.receive_date)
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, date_item)
            
            # --- ACTION BUTTONS ---
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(5)
            
            view_btn = QPushButton("Xem")
            view_btn.setToolTip("Xem chi tiết & Lịch sử")
            view_btn.setFixedSize(50, 28)
            view_btn.setObjectName("tableBtnView") 
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda _, eid=equip.id: self.show_equipment_detail(eid))
            action_layout.addWidget(view_btn)
            
            edit_btn = QPushButton("Sửa")
            edit_btn.setToolTip("Sửa thông tin")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setObjectName("tableBtn")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, eid=equip.id: self._edit_equipment(eid))
            action_layout.addWidget(edit_btn)
            
            qr_btn = QPushButton("QR")
            qr_btn.setToolTip("Xem & In mã QR")
            qr_btn.setFixedSize(40, 28)
            qr_btn.setObjectName("tableBtn")
            qr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            qr_btn.clicked.connect(lambda _, e=equip: self._show_qr(e))
            action_layout.addWidget(qr_btn)
            
            del_btn = QPushButton("Xóa")
            del_btn.setToolTip("Xóa thiết bị")
            del_btn.setFixedSize(50, 28)
            del_btn.setObjectName("tableBtnDanger")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, eid=equip.id: self._delete_equipment(eid))
            action_layout.addWidget(del_btn)
            
            action_layout.addStretch()
            self.table.setCellWidget(row, 7, action_widget)
    
    def _update_pagination(self):
        """Update pagination state and display current page"""
        total = len(self.current_equipment_list)
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.current_equipment_list[start:end]
        
        self._populate_table(page_data)
        self.count_label.setText(f"Tổng: {total} thiết bị")
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
    
    def _on_search(self, text: str):
        self.refresh_data()
    
    def _on_filter_change(self):
        self.refresh_data()
    
    def _on_row_double_click(self, index):
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            equipment_id = int(id_item.text())
            self.show_equipment_detail(equipment_id)
    
    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0: return
        
        id_item = self.table.item(row, 0)
        if not id_item: return
        
        equipment_id = int(id_item.text())
        equip = Equipment.get_by_id(equipment_id)
        
        menu = QMenu(self)
        action_view = menu.addAction("👁️ Xem chi tiết")
        action_edit = menu.addAction("✏️ Chỉnh sửa")
        menu.addSeparator()
        action_qr = menu.addAction("🏷️ Xem mã QR")
        action_log = menu.addAction("📝 Thêm nhật ký bảo dưỡng")
        menu.addSeparator()
        action_delete = menu.addAction("🗑️ Xóa")
        
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        
        if action == action_view:
            self.show_equipment_detail(equipment_id)
        elif action == action_edit:
            self._edit_equipment(equipment_id)
        elif action == action_qr:
            self._show_qr(equip)
        elif action == action_log:
            self._add_maintenance_log(equipment_id)
        elif action == action_delete:
            self._delete_equipment(equipment_id)
    
    def _get_current_user_info(self):
        """Lấy thông tin người dùng hiện tại để ghi audit log"""
        user = UserController.get_current_user()
        if user:
            return user.id, user.username
        return None, "Hệ thống"

    def show_add_dialog(self):
        dialog = EquipmentInputDialog(self)
        if dialog.exec():
            equipment = dialog.get_equipment()
            equipment.save()
            qr_img, qr_path = self.qr_service.generate_equipment_qr(equipment.id, equipment.serial_number)
            equipment.qr_code_path = qr_path
            equipment.save()
            
            # Ghi nhật ký hệ thống
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "CREATE", "Equipment", equipment.id,
                f"Thêm mới trang bị: {equipment.name} (Số hiệu: {equipment.serial_number}, Loại: {equipment.category})")
            
            QMessageBox.information(self, "Thành công", f"Đã thêm thiết bị '{equipment.name}' và tạo mã QR!")
            self.refresh_data()
    
    def _edit_equipment(self, equipment_id: int):
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thiết bị!")
            return
        
        old_name = equipment.name
        old_serial = equipment.serial_number
        
        dialog = EquipmentInputDialog(self, equipment)
        if dialog.exec():
            updated = dialog.get_equipment()
            updated.id = equipment_id
            updated.qr_code_path = equipment.qr_code_path
            updated.save()
            
            # Ghi nhật ký hệ thống
            user_id, username = self._get_current_user_info()
            log_details = f"Cập nhật trang bị: {updated.name} (Số hiệu: {updated.serial_number})"
            if updated.serial_number != old_serial:
                log_details += f" [Đổi số hiệu từ {old_serial} sang {updated.serial_number}]"
            self.db.log_action(user_id, username, "UPDATE", "Equipment", equipment_id, log_details)
            
            QMessageBox.information(self, "Thành công", f"Đã cập nhật thiết bị '{updated.name}'!")
            self.refresh_data()
    
    def _delete_equipment(self, equipment_id: int):
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment: return
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa thiết bị '{equipment.name}'?\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            name = equipment.name
            serial = equipment.serial_number
            self.qr_service.delete_qr(equipment.id, equipment.serial_number)
            equipment.delete()
            
            # Ghi nhật ký hệ thống
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "DELETE", "Equipment", equipment_id,
                f"Xóa trang bị: {name} (Số hiệu: {serial})")
            
            QMessageBox.information(self, "Thành công", f"Đã xóa thiết bị '{name}'!")
            self.refresh_data()
    
    def _show_qr(self, equipment: Equipment):
        from .qr_dialog import QRDialog
        dialog = QRDialog(self, equipment, self.qr_service)
        dialog.exec()
    
    def _add_maintenance_log(self, equipment_id: int):
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return
        
        active_log = MaintenanceLog.get_active_by_equipment(equipment_id)
        is_update_existing = False
        
        if active_log:
            reply = QMessageBox.question(
                self, "Công việc đang thực hiện",
                f"Thiết bị này đang có công việc '{active_log.maintenance_type}' chưa hoàn thành.\n"
                f"Bạn có muốn cập nhật công việc này không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog = MaintenanceDialog(self, equipment, active_log)
                is_update_existing = True
            else:
                return
        else:
            dialog = MaintenanceDialog(self, equipment)
        
        if dialog.exec():
            log_data = dialog.get_data_as_dict()
            new_status = dialog.get_new_equipment_status()
            
            if is_update_existing:
                success, message = self.maintenance_controller.update_maintenance_log(
                    active_log.id, log_data
                )
                if success and new_status:
                    equipment.status = new_status
                    equipment.save()
            else:
                success, message, _ = self.maintenance_controller.create_maintenance_log(
                    equipment.id, log_data, update_equipment_status=new_status
                )
            
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Lỗi", message)

    def show_equipment_detail(self, equipment_id: int):
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thiết bị!")
            return
        
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        dialog = EquipmentDetailDialog(self, equipment, logs, self.qr_service)
        dialog.exec()
    
    def export_equipment_list(self):
        """Cho phép người dùng chọn nơi lưu file"""
        if not self.current_equipment_list:
            QMessageBox.warning(self, "Thông báo", "Không có dữ liệu để xuất!")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"danh_sach_thiet_bi_{timestamp}.pdf"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu danh sách thiết bị",
            default_name,
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                filepath = self.export_service.export_equipment_list(
                    self.current_equipment_list,
                    save_path=filename
                )
                reply = QMessageBox.information(
                    self, "Thành công",
                    f"Đã xuất file PDF thành công!\n\nĐường dẫn: {filepath}",
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok
                )
                if reply == QMessageBox.StandardButton.Open:
                    import os
                    os.startfile(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {str(e)}")
    
    def export_qr_sheet(self):
        """Cho phép người dùng chọn nơi lưu file QR"""
        if not self.current_equipment_list:
            QMessageBox.warning(self, "Thông báo", "Không có dữ liệu để xuất!")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"bang_ma_qr_{timestamp}.pdf"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu bảng mã QR",
            default_name,
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                filepath = self.export_service.export_qr_sheet(
                    self.current_equipment_list,
                    save_path=filename
                )
                reply = QMessageBox.information(
                    self, "Thành công",
                    f"Đã xuất bảng mã QR thành công!\n\nĐường dẫn: {filepath}",
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok
                )
                if reply == QMessageBox.StandardButton.Open:
                    import os
                    os.startfile(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {str(e)}")
    
    def showEvent(self, event):
        """Load lại danh mục mỗi khi vào view"""
        super().showEvent(event)
        self._load_categories()
        self.refresh_data()