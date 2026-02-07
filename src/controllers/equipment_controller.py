"""
Equipment Controller - Business logic for equipment management
"""
from typing import List, Optional, Tuple
from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..services.qr_service import QRService
from ..services.export_service import ExportService


class EquipmentController:
    """
    Controller handling equipment-related business logic
    """
    
    def __init__(self):
        self.qr_service = QRService()
        self.export_service = ExportService()
    
    def create_equipment(self, equipment_data: dict) -> Tuple[bool, str, Optional[Equipment]]:
        """
        Create new equipment with validation
        
        Args:
            equipment_data: Dictionary containing equipment fields
            
        Returns:
            Tuple of (success, message, equipment)
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
            equipment.unit = equipment_data.get('unit', '')
            equipment.location = equipment_data.get('location', '')
            equipment.description = equipment_data.get('description', '')
            
            equipment.save()
            
            # Generate QR code
            _, qr_path = self.qr_service.generate_equipment_qr(
                equipment.id,
                equipment.serial_number
            )
            equipment.qr_code_path = qr_path
            equipment.save()
            
            return True, f"Đã thêm thiết bị '{equipment.name}'!", equipment
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    def update_equipment(self, equipment_id: int, equipment_data: dict) -> Tuple[bool, str]:
        """
        Update existing equipment
        
        Args:
            equipment_id: ID of equipment to update
            equipment_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success, message)
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
            # Update fields
            equipment.name = equipment_data.get('name', equipment.name)
            equipment.serial_number = new_serial
            equipment.category = equipment_data.get('category', equipment.category)
            equipment.manufacturer = equipment_data.get('manufacturer', equipment.manufacturer)
            equipment.manufacture_year = equipment_data.get('manufacture_year', equipment.manufacture_year)
            equipment.status = equipment_data.get('status', equipment.status)
            equipment.unit = equipment_data.get('unit', equipment.unit)
            equipment.location = equipment_data.get('location', equipment.location)
            equipment.description = equipment_data.get('description', equipment.description)
            
            equipment.save()
            
            # Regenerate QR if serial changed
            if new_serial != equipment.serial_number:
                self.qr_service.delete_qr(equipment_id, equipment.serial_number)
                _, qr_path = self.qr_service.generate_equipment_qr(
                    equipment_id,
                    new_serial
                )
                equipment.qr_code_path = qr_path
                equipment.save()
            
            return True, f"Đã cập nhật thiết bị '{equipment.name}'!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def delete_equipment(self, equipment_id: int) -> Tuple[bool, str]:
        """
        Delete equipment
        
        Args:
            equipment_id: ID of equipment to delete
            
        Returns:
            Tuple of (success, message)
        """
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        try:
            name = equipment.name
            
            # Delete QR code file
            self.qr_service.delete_qr(equipment_id, equipment.serial_number)
            
            # Delete equipment (cascades to maintenance logs)
            equipment.delete()
            
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
        """
        Get filtered equipment list
        
        Args:
            keyword: Search keyword
            category: Filter by category
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of Equipment objects
        """
        if keyword:
            results = Equipment.search(keyword)
        elif category:
            results = Equipment.get_by_category(category)
        elif status:
            results = Equipment.get_by_status(status)
        else:
            results = Equipment.get_all(limit=limit)
        
        # Apply additional filters
        if keyword and category:
            results = [e for e in results if e.category == category]
        if keyword and status:
            results = [e for e in results if e.status == status]
        if category and status and not keyword:
            results = [e for e in results if e.status == status]
        
        return results
    
    def get_equipment_detail(self, equipment_id: int) -> Tuple[Optional[Equipment], List[MaintenanceLog]]:
        """
        Get equipment with maintenance history
        
        Args:
            equipment_id: Equipment ID
            
        Returns:
            Tuple of (equipment, maintenance_logs)
        """
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return None, []
        
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        return equipment, logs
    
    def lookup_by_qr(self, qr_data: str) -> Tuple[bool, str, Optional[Equipment]]:
        """
        Look up equipment by QR code data
        
        Args:
            qr_data: Raw QR code data string
            
        Returns:
            Tuple of (success, message, equipment)
        """
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
        """
        Export equipment list to PDF
        
        Args:
            equipment_list: List of equipment to export
            
        Returns:
            Tuple of (success, filepath or error message)
        """
        if not equipment_list:
            return False, "Không có dữ liệu để xuất!"
        
        try:
            filepath = self.export_service.export_equipment_list(equipment_list)
            return True, filepath
        except Exception as e:
            return False, f"Lỗi xuất file: {str(e)}"
    
    def export_qr_sheet_pdf(self, equipment_list: List[Equipment]) -> Tuple[bool, str]:
        """
        Export QR code sheet to PDF
        
        Args:
            equipment_list: List of equipment
            
        Returns:
            Tuple of (success, filepath or error message)
        """
        if not equipment_list:
            return False, "Không có dữ liệu để xuất!"
        
        try:
            filepath = self.export_service.export_qr_sheet(equipment_list)
            return True, filepath
        except Exception as e:
            return False, f"Lỗi xuất file: {str(e)}"
    
    def export_equipment_detail_pdf(self, equipment_id: int) -> Tuple[bool, str]:
        """
        Export equipment detail to PDF
        
        Args:
            equipment_id: Equipment ID
            
        Returns:
            Tuple of (success, filepath or error message)
        """
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        
        try:
            filepath = self.export_service.export_equipment_detail(equipment, logs)
            return True, filepath
        except Exception as e:
            return False, f"Lỗi xuất file: {str(e)}"
