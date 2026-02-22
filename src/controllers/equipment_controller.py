"""
Equipment Controller - Business logic for equipment management
"""
from typing import List, Optional, Tuple
from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..models.database import Database # [QUAN TRỌNG] Import Database để ghi log
from ..services.qr_service import QRService
from ..services.export_service import ExportService
from .user_controller import UserController # [QUAN TRỌNG] Import để lấy user hiện tại


class EquipmentController:
    """
    Controller handling equipment-related business logic
    """
    
    def __init__(self):
        self.qr_service = QRService()
        self.export_service = ExportService()
        self.db = Database() # [QUAN TRỌNG] Khởi tạo kết nối DB
    
    def _get_current_user_info(self):
        """Hàm tiện ích lấy thông tin người dùng đang thao tác"""
        user = UserController.get_current_user()
        if user:
            return user.id, user.username
        return None, "Hệ thống"

    def create_equipment(self, equipment_data: dict) -> Tuple[bool, str, Optional[Equipment]]:
        """
        Create new equipment with validation
        """
        # Validate required fields
        required_fields = ['name', 'serial_number', 'category']
        for field in required_fields:
            if not equipment_data.get(field):
                return False, f"Trường '{field}' là bắt buộc!", None
        
        # Check serial uniqueness
        if Equipment.serial_exists(equipment_data['serial_number']):
            return False, f"Số hiệu '{equipment_data['serial_number']}' đã tồn tại!", None
        
        try:
            # Create equipment
            equipment = Equipment()
            equipment.name = equipment_data['name']
            equipment.serial_number = equipment_data['serial_number']
            equipment.category = equipment_data['category']
            equipment.manufacturer = equipment_data.get('manufacturer', '')
            equipment.manufacture_year = equipment_data.get('manufacture_year')
            equipment.status = equipment_data.get('status', 'Trong kho')
            equipment.unit_id = equipment_data.get('unit_id')
            equipment.location = equipment_data.get('location', '')
            equipment.description = equipment_data.get('description', '')
            equipment.receive_date = equipment_data.get('receive_date')
            
            equipment.save()
            
            # Generate QR code
            _, qr_path = self.qr_service.generate_equipment_qr(
                equipment.id,
                equipment.serial_number
            )
            equipment.qr_code_path = qr_path
            equipment.save()
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            log_details = f"Thêm mới trang bị: {equipment.name} (Số hiệu: {equipment.serial_number}, Loại: {equipment.category})"
            self.db.log_action(user_id, username, "CREATE", "Equipment", equipment.id, log_details)
            
            return True, f"Đã thêm thiết bị '{equipment.name}'!", equipment
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    def update_equipment(self, equipment_id: int, equipment_data: dict) -> Tuple[bool, str]:
        """
        Update existing equipment
        """
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        # Check serial uniqueness (excluding current)
        new_serial = equipment_data.get('serial_number', equipment.serial_number)
        if new_serial != equipment.serial_number:
            if Equipment.serial_exists(new_serial, exclude_id=equipment_id):
                return False, f"Số hiệu '{new_serial}' đã tồn tại!"
        
        try:
            old_name = equipment.name
            old_serial = equipment.serial_number
            
            # Update fields
            equipment.name = equipment_data.get('name', equipment.name)
            equipment.serial_number = new_serial
            equipment.category = equipment_data.get('category', equipment.category)
            equipment.manufacturer = equipment_data.get('manufacturer', equipment.manufacturer)
            equipment.manufacture_year = equipment_data.get('manufacture_year', equipment.manufacture_year)
            equipment.status = equipment_data.get('status', equipment.status)
            equipment.unit_id = equipment_data.get('unit_id', equipment.unit_id)
            equipment.location = equipment_data.get('location', equipment.location)
            equipment.description = equipment_data.get('description', equipment.description)
            equipment.receive_date = equipment_data.get('receive_date', equipment.receive_date)
            
            equipment.save()
            
            # Regenerate QR if serial changed
            if new_serial != old_serial:
                self.qr_service.delete_qr(equipment_id, old_serial)
                _, qr_path = self.qr_service.generate_equipment_qr(
                    equipment_id,
                    new_serial
                )
                equipment.qr_code_path = qr_path
                equipment.save()
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            log_details = f"Cập nhật trang bị: {equipment.name} (Số hiệu: {equipment.serial_number})"
            if new_serial != old_serial:
                log_details += f" [Đổi số hiệu từ {old_serial} sang {new_serial}]"
            self.db.log_action(user_id, username, "UPDATE", "Equipment", equipment.id, log_details)
            
            return True, f"Đã cập nhật thiết bị '{equipment.name}'!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def delete_equipment(self, equipment_id: int) -> Tuple[bool, str]:
        """
        Delete equipment
        """
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        try:
            name = equipment.name
            serial = equipment.serial_number
            
            # Delete QR code file
            self.qr_service.delete_qr(equipment_id, equipment.serial_number)
            
            # Delete equipment (cascades to maintenance logs)
            equipment.delete()
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            log_details = f"Xóa trang bị: {name} (Số hiệu: {serial})"
            self.db.log_action(user_id, username, "DELETE", "Equipment", equipment_id, log_details)
            
            return True, f"Đã xóa thiết bị '{name}'!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def get_equipment_list(
        self, 
        keyword: str = None, 
        category: str = None, 
        status: str = None,
        limit: int = 500
    ) -> List[Equipment]:
        """Get filtered equipment list"""
        if keyword:
            results = Equipment.search(keyword)
        elif category:
            results = Equipment.get_by_category(category)
        elif status:
            results = Equipment.get_by_status(status)
        else:
            results = Equipment.get_all(limit=limit)
        
        if keyword and category:
            results = [e for e in results if e.category == category]
        if keyword and status:
            results = [e for e in results if e.status == status]
        if category and status and not keyword:
            results = [e for e in results if e.status == status]
        
        return results
    
    def get_equipment_detail(self, equipment_id: int) -> Tuple[Optional[Equipment], List[MaintenanceLog]]:
        """Get equipment with maintenance history"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return None, []
        
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        return equipment, logs
    
    def lookup_by_qr(self, qr_data: str) -> Tuple[bool, str, Optional[Equipment]]:
        """Look up equipment by QR code data"""
        decoded = self.qr_service.decode_qr_data(qr_data)
        
        if decoded['type'] == 'equipment':
            equipment = Equipment.get_by_id(decoded['equipment_id'])
            if equipment:
                return True, "Tìm thấy thiết bị!", equipment
            else:
                return False, f"Không tìm thấy thiết bị với ID: {decoded['equipment_id']}", None
        elif decoded['type'] == 'unknown':
            return False, "Mã QR không thuộc hệ thống VKTBKT!", None
        else:
            return False, "Lỗi giải mã QR!", None
    
    def export_equipment_list_pdf(self, equipment_list: List[Equipment]) -> Tuple[bool, str]:
        """Export equipment list to PDF"""
        if not equipment_list:
            return False, "Không có dữ liệu để xuất!"
        try:
            filepath = self.export_service.export_equipment_list(equipment_list)
            return True, filepath
        except Exception as e:
            return False, f"Lỗi xuất file: {str(e)}"
    
    def export_qr_sheet_pdf(self, equipment_list: List[Equipment]) -> Tuple[bool, str]:
        """Export QR code sheet to PDF"""
        if not equipment_list:
            return False, "Không có dữ liệu để xuất!"
        try:
            filepath = self.export_service.export_qr_sheet(equipment_list)
            return True, filepath
        except Exception as e:
            return False, f"Lỗi xuất file: {str(e)}"
    
    def export_equipment_detail_pdf(self, equipment_id: int) -> Tuple[bool, str]:
        """Export equipment detail to PDF"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        try:
            filepath = self.export_service.export_equipment_detail(equipment, logs)
            return True, filepath
        except Exception as e:
            return False, f"Lỗi xuất file: {str(e)}"