"""
Scan View - QR code scanning interface with camera
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QComboBox, QMessageBox,
    QGroupBox, QFormLayout, QDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QFont

# Import thêm CameraDiscoveryThread
from ..services.camera_service import CameraService, CameraDiscoveryThread
from ..services.qr_service import QRService
from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..models.user import UserRole
from ..controllers.maintenance_controller import MaintenanceController
from .equipment_detail_dialog import EquipmentDetailDialog
from .maintenance_dialog import MaintenanceDialog


class ScanView(QWidget):
    """
    QR code scanning view with live camera feed
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.qr_service = QRService()
        self.camera_service = None
        self.discovery_thread = None # Thread tìm camera
        self.current_equipment = None
        self.maintenance_controller = MaintenanceController()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the scan view UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # --- LEFT PANEL: CAMERA ---
        left_panel = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📷 Quét mã QR")
        title.setObjectName("title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Camera selection
        header_layout.addWidget(QLabel("Camera:"))
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(200)
        # Không gọi _populate_cameras ngay lập tức ở đây để tránh lag khởi động
        header_layout.addWidget(self.camera_combo)
        
        left_panel.addLayout(header_layout)
        
        # Camera frame
        camera_frame = QFrame()
        camera_frame.setObjectName("card")
        camera_layout = QVBoxLayout(camera_frame)
        
        self.camera_label = QLabel()
        self.camera_label.setObjectName("cameraFrame")
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setText("Đang tải danh sách camera...")
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #888;
                font-size: 16px;
                border: 2px dashed #444;
                border-radius: 8px;
            }
        """)
        camera_layout.addWidget(self.camera_label)
        
        # Camera controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)
        
        self.start_btn = QPushButton("▶️ Bắt đầu quét")
        self.start_btn.setMinimumHeight(32)
        self.start_btn.clicked.connect(self.start_camera)
        self.start_btn.setEnabled(False) # Chờ tìm camera xong mới enable
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Dừng")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setMinimumHeight(32)
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        # Status Label
        self.status_label = QLabel("Trạng thái: Đang khởi tạo...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 13px;
                color: #333; 
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 15px;
                padding: 0 20px;
                min-width: 250px;
                max-height: 30px;
            }
        """)
        controls_layout.addWidget(self.status_label)
        
        camera_layout.addLayout(controls_layout)
        left_panel.addWidget(camera_frame)
        
        main_layout.addLayout(left_panel, stretch=2)
        
        # --- RIGHT PANEL: RESULT (Giữ nguyên) ---
        right_panel = QVBoxLayout()
        
        result_title = QLabel("📋 Kết quả quét")
        result_title.setObjectName("title")
        right_panel.addWidget(result_title)
        
        self.result_frame = QFrame()
        self.result_frame.setObjectName("card")
        result_layout = QVBoxLayout(self.result_frame)
        
        self.no_result_label = QLabel(
            "Chưa có kết quả\n\n"
            "Hướng camera về phía mã QR trên thiết bị để quét"
        )
        self.no_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_result_label.setStyleSheet("color: #888; font-size: 14px;")
        result_layout.addWidget(self.no_result_label)
        
        # Equipment info
        self.equipment_info = QWidget()
        equipment_layout = QVBoxLayout(self.equipment_info)
        equipment_layout.setContentsMargins(0, 0, 0, 0)
        
        self.equip_name_label = QLabel()
        self.equip_name_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.equip_name_label.setWordWrap(True)
        equipment_layout.addWidget(self.equip_name_label)
        
        self.equip_serial_label = QLabel()
        self.equip_serial_label.setObjectName("subtitle")
        self.equip_serial_label.setFont(QFont("Segoe UI", 12))
        equipment_layout.addWidget(self.equip_serial_label)
        
        equipment_layout.addSpacing(15)
        
        info_group = QGroupBox("Thông tin chi tiết")
        info_form = QFormLayout(info_group)
        info_form.setSpacing(10)
        
        self.info_labels = {}
        info_fields = [
            ("category", "Loại:"),
            ("manufacturer", "Nhà sản xuất:"),
            ("year", "Năm sản xuất:"),
            ("status", "Tình trạng:"),
            ("unit", "Đơn vị:"),
            ("location", "Vị trí:"),
        ]
        
        for key, label_text in info_fields:
            label = QLabel("-")
            label.setStyleSheet("font-weight: bold; color: #333;")
            self.info_labels[key] = label
            info_form.addRow(label_text, label)
        
        equipment_layout.addWidget(info_group)
        
        desc_group = QGroupBox("Mô tả")
        desc_layout = QVBoxLayout(desc_group)
        self.description_label = QLabel("-")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #333;")
        desc_layout.addWidget(self.description_label)
        equipment_layout.addWidget(desc_group)
        
        equipment_layout.addStretch()
        
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.reset_btn = QPushButton("🔄 Quét tiếp")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.clicked.connect(self._on_reset)
        action_layout.addWidget(self.reset_btn)

        self.detail_btn = QPushButton("👁️ Xem chi tiết")
        self.detail_btn.clicked.connect(self._on_view_detail)
        action_layout.addWidget(self.detail_btn)
        
        self.maintenance_btn = QPushButton("📝 Ghi nhật ký")
        self.maintenance_btn.clicked.connect(self._on_add_maintenance)
        action_layout.addWidget(self.maintenance_btn)
        
        equipment_layout.addLayout(action_layout)
        
        self.equipment_info.hide()
        result_layout.addWidget(self.equipment_info)
        
        right_panel.addWidget(self.result_frame)
        
        # Instructions
        instructions = QFrame()
        instructions.setObjectName("card")
        inst_layout = QVBoxLayout(instructions)
        
        inst_title = QLabel("📖 Hướng dẫn")
        inst_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        inst_layout.addWidget(inst_title)
        
        inst_text = QLabel(
            "1. Chọn camera và nhấn 'Bắt đầu quét'\n"
            "2. Hướng camera về phía mã QR trên thiết bị\n"
            "3. Giữ khoảng cách phù hợp (15-30cm)\n"
            "4. Đợi hệ thống nhận diện mã QR\n"
            "5. Thông tin thiết bị sẽ hiển thị tự động"
        )
        inst_text.setStyleSheet("color: #444; line-height: 1.6; font-size: 13px;")
        inst_layout.addWidget(inst_text)
        
        right_panel.addWidget(instructions)
        right_panel.addStretch()
        
        main_layout.addLayout(right_panel, stretch=1)
    
    def _populate_cameras(self):
        """Start async camera discovery"""
        self.camera_combo.clear()
        self.camera_combo.addItem("⏳ Đang tìm camera...", -1)
        self.camera_combo.setEnabled(False)
        self.start_btn.setEnabled(False)
        
        # Run discovery in background thread to prevent UI freeze
        self.discovery_thread = CameraDiscoveryThread()
        self.discovery_thread.cameras_found.connect(self._on_cameras_found)
        self.discovery_thread.start()

    def _on_cameras_found(self, cameras):
        """Handle discovered cameras"""
        self.camera_combo.clear()
        self.camera_combo.setEnabled(True)
        
        if not cameras:
            self.camera_combo.addItem("❌ Không tìm thấy camera", -1)
            self.status_label.setText("Trạng thái: Không có camera")
            self.camera_label.setText("Không tìm thấy camera nào\nVui lòng kiểm tra kết nối")
        else:
            for idx in cameras:
                self.camera_combo.addItem(f"📷 Camera {idx}", idx)
            self.start_btn.setEnabled(True)
            self.status_label.setText("Trạng thái: Sẵn sàng")
            self.camera_label.setText("Camera đã tắt\n\nNhấn 'Bắt đầu quét' để bật")
            self._update_status_style("default")

    def start_camera(self):
        camera_idx = self.camera_combo.currentData()
        if camera_idx is None or camera_idx < 0:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy camera.")
            return
        
        self.camera_service = CameraService(camera_idx)
        self.camera_service.frame_ready.connect(self._on_frame_ready)
        self.camera_service.qr_detected.connect(self._on_qr_detected)
        self.camera_service.error_occurred.connect(self._on_camera_error)
        self.camera_service.camera_started.connect(self._on_camera_started)
        self.camera_service.camera_stopped.connect(self._on_camera_stopped)
        self.camera_service.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.camera_combo.setEnabled(False)
        self.status_label.setText("Trạng thái: Đang khởi động...")
        self._update_status_style("waiting")

    def stop_camera(self):
        if self.camera_service:
            self.camera_service.stop()
            self.camera_service = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.camera_combo.setEnabled(True)
        self.camera_label.clear()
        self.camera_label.setText("Camera đã tắt\n\nNhấn 'Bắt đầu quét' để bật lại")
        self.status_label.setText("Trạng thái: Đã dừng")
        self._update_status_style("stopped")
    
    def _on_frame_ready(self, qimage: QImage):
        scaled = qimage.scaled(
            self.camera_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_label.setPixmap(QPixmap.fromImage(scaled))
    
    def _on_qr_detected(self, qr_data: str):
        """Handle detected QR code with Security Check"""
        self.status_label.setText(f"Trạng thái: Đã phát hiện mã QR!")
        self._update_status_style("success")
        
        decoded = self.qr_service.decode_qr_data(qr_data)
        
        if decoded['type'] == 'equipment':
            equipment_id = decoded['equipment_id']
            scanned_serial = decoded['serial_number']
            
            equipment = Equipment.get_by_id(equipment_id)
            
            if equipment:
                if equipment.serial_number != scanned_serial:
                    self.stop_camera()
                    QMessageBox.warning(
                        self, 
                        "Cảnh báo dữ liệu", 
                        f"Mã QR không hợp lệ!\n\n"
                        f"- Trong mã QR: {scanned_serial}\n"
                        f"- Trên hệ thống: {equipment.serial_number}"
                    )
                    return

                self._show_equipment_info(equipment)
            else:
                QMessageBox.warning(self, "Không tìm thấy", f"Không tìm thấy thiết bị ID: {equipment_id}")
        else:
            # Tạm dừng xử lý QR này trong 2s để tránh spam, nhưng không chặn hoàn toàn
            pass 
    
    def _show_equipment_info(self, equipment: Equipment):
        self.current_equipment = equipment
        self.no_result_label.hide()
        self.equipment_info.show()
        
        # Hide maintenance button for viewers
        if self.main_window and self.main_window.current_user:
            is_viewer = self.main_window.current_user.role == UserRole.VIEWER
            self.maintenance_btn.setVisible(not is_viewer)
        
        self.equip_name_label.setText(equipment.name)
        self.equip_serial_label.setText(f"Số hiệu: {equipment.serial_number}")
        
        self.info_labels["category"].setText(equipment.category)
        self.info_labels["manufacturer"].setText(equipment.manufacturer or "-")
        self.info_labels["year"].setText(str(equipment.manufacture_year) if equipment.manufacture_year else "-")
        self.info_labels["status"].setText(equipment.status)
        self.info_labels["unit"].setText(equipment.unit_name or "-")
        self.info_labels["location"].setText(equipment.location or "-")
        self.description_label.setText(equipment.description or "Không có mô tả")
        
        status = equipment.status
        style = "font-weight: bold; "
        if status in ["Cấp 1", "Cấp 2"]:
            style += "color: #28a745;"
        elif status == "Cấp 3":
            style += "color: #ffc107;"
        elif status in ["Cấp 4", "Cấp 5"]:
            style += "color: #dc3545;"
        else:
            style += "color: #333;"
        
        self.info_labels["status"].setStyleSheet(style)
    
    def _on_camera_error(self, error: str):
        QMessageBox.critical(self, "Lỗi Camera", error)
        self.stop_camera()
    
    def _on_camera_started(self):
        self.status_label.setText("Trạng thái: Đang quét...")
        self._update_status_style("scanning")
    
    def _on_camera_stopped(self):
        self.status_label.setText("Trạng thái: Đã dừng")
        self._update_status_style("stopped")
    
    def _on_reset(self):
        self.current_equipment = None
        self.equipment_info.hide()
        self.no_result_label.show()
        self.status_label.setText("Trạng thái: Sẵn sàng quét mã mới")
        self._update_status_style("default")
        if self.camera_service:
            self.camera_service.reset_qr_detection()

    def _on_view_detail(self):
        if not self.current_equipment: return
        logs = MaintenanceLog.get_by_equipment(self.current_equipment.id)
        dialog = EquipmentDetailDialog(self, self.current_equipment, logs, self.qr_service)
        dialog.exec()
    
    def _on_add_maintenance(self):
        if not self.current_equipment: return
        
        # Check permission - Viewer cannot add maintenance
        if self.main_window and self.main_window.current_user:
            if self.main_window.current_user.role == UserRole.VIEWER:
                QMessageBox.warning(
                    self, 
                    "Không có quyền", 
                    "Bạn chỉ có quyền xem thông tin thiết bị, không được phép thao tác!"
                )
                return
        
        active_log = MaintenanceLog.get_active_by_equipment(self.current_equipment.id)
        
        if active_log:
            reply = QMessageBox.question(self, "Công việc đang thực hiện", f"Thiết bị này đang có công việc '{active_log.maintenance_type}'. Cập nhật nó?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                dialog = MaintenanceDialog(self, self.current_equipment, active_log)
                is_update = True
            else: return
        else:
            dialog = MaintenanceDialog(self, self.current_equipment)
            is_update = False
        
        if dialog.exec():
            log_data = dialog.get_data_as_dict()
            new_status = dialog.get_new_equipment_status()
            
            if is_update:
                success, msg = self.maintenance_controller.update_maintenance_log(active_log.id, log_data)
                if success and new_status:
                    self.current_equipment.status = new_status
                    self.current_equipment.save()
            else:
                success, msg, _ = self.maintenance_controller.create_maintenance_log(self.current_equipment.id, log_data, new_status)
            
            if success:
                if new_status: self.current_equipment = Equipment.get_by_id(self.current_equipment.id)
                self._show_equipment_info(self.current_equipment)
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)
    
    def _update_status_style(self, state):
        base_style = """
            QLabel {
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 13px;
                border-radius: 15px;
                padding: 0 20px;
                min-width: 250px;
                max-height: 30px;
        """
        if state == "success": # Green
            color = "color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb;"
        elif state == "scanning": # Blue
            color = "color: #004085; background-color: #cce5ff; border: 1px solid #b8daff;"
        elif state == "stopped": # Red/Gray
            color = "color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb;"
        else: # Waiting/Default
            color = "color: #333; background-color: #f8f9fa; border: 1px solid #dee2e6;"
            
        self.status_label.setStyleSheet(base_style + color + "}")

    def update_styles(self, stylesheet):
        # Có thể thêm logic cập nhật style dark mode ở đây nếu cần
        pass
    
    def showEvent(self, event):
        super().showEvent(event)
        # Chỉ quét camera khi chưa có dữ liệu hoặc danh sách rỗng
        if self.camera_combo.count() == 0:
            self._populate_cameras()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        if self.camera_service and self.camera_service.is_running():
            self.stop_camera()