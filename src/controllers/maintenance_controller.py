"""
Maintenance Controller - Business logic for maintenance logs
"""
from typing import List, Optional, Tuple
from datetime import datetime
from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog


class MaintenanceController:
    """
    Controller handling maintenance log business logic
    """
    
    def create_maintenance_log(
        self, 
        equipment_id: int, 
        log_data: dict,
        update_equipment_status: str = None
    ) -> Tuple[bool, str, Optional[MaintenanceLog]]:
        """
        Create new maintenance log
        """
        # Verify equipment exists
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!", None
        
        # Validate required fields
        if not log_data.get('maintenance_type'):
            return False, "Vui lòng chọn loại công việc!", None
        
        try:
            # Create log
            log = MaintenanceLog()
            log.equipment_id = equipment_id
            log.maintenance_type = log_data['maintenance_type']
            log.description = log_data.get('description', '')
            log.technician_name = log_data.get('technician', '')
            log.status = log_data.get('status', 'Đang thực hiện')
            
            # Handle dates carefully
            start = log_data.get('start_date')
            if start:
                log.start_date = start
            else:
                log.start_date = datetime.now()
                
            end = log_data.get('end_date')
            if end:
                log.end_date = end
            
            log.notes = log_data.get('notes', '')
            
            log.save()
            
            # Update equipment status if requested
            if update_equipment_status:
                equipment.status = update_equipment_status
                equipment.save()
            
            return True, "Đã ghi nhật ký bảo dưỡng!", log
            
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            return False, f"Lỗi: {str(e)}", None
    
    def update_maintenance_log(
        self, 
        log_id: int, 
        log_data: dict, 
        update_equipment_status: str = None # [FIX] Thêm tham số này
    ) -> Tuple[bool, str]:
        """
        Update existing maintenance log
        """
        log = MaintenanceLog.get_by_id(log_id)
        if not log:
            return False, "Không tìm thấy bản ghi!"
        
        try:
            log.maintenance_type = log_data.get('maintenance_type', log.maintenance_type)
            log.description = log_data.get('description', log.description)
            log.technician_name = log_data.get('technician', log.technician_name)
            log.status = log_data.get('status', log.status)
            log.notes = log_data.get('notes', log.notes)
            
            if log_data.get('end_date'):
                log.end_date = log_data['end_date']
            
            log.save()
            
            # [FIX] Logic cập nhật trạng thái thiết bị (Giống hàm create)
            if update_equipment_status:
                equipment = Equipment.get_by_id(log.equipment_id)
                if equipment:
                    equipment.status = update_equipment_status
                    equipment.save()
            
            return True, "Đã cập nhật bản ghi!"
            
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            return False, f"Lỗi: {str(e)}"
    
    def complete_maintenance(
        self, 
        log_id: int, 
        notes: str = "",
        update_equipment_status: str = None
    ) -> Tuple[bool, str]:
        """Mark maintenance as completed"""
        log = MaintenanceLog.get_by_id(log_id)
        if not log:
            return False, "Không tìm thấy bản ghi!"
        
        try:
            log.complete(notes)
            
            # Update equipment status if requested
            if update_equipment_status:
                equipment = Equipment.get_by_id(log.equipment_id)
                if equipment:
                    equipment.status = update_equipment_status
                    equipment.save()
            
            return True, "Đã hoàn thành công việc bảo dưỡng!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def delete_maintenance_log(self, log_id: int) -> Tuple[bool, str]:
        """Delete maintenance log"""
        log = MaintenanceLog.get_by_id(log_id)
        if not log:
            return False, "Không tìm thấy bản ghi!"
        
        try:
            log.delete()
            return True, "Đã xóa bản ghi!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def get_equipment_maintenance_history(self, equipment_id: int) -> List[MaintenanceLog]:
        return MaintenanceLog.get_by_equipment(equipment_id)
    
    def get_active_maintenance(self) -> List[MaintenanceLog]:
        return MaintenanceLog.get_active()
    
    def get_recent_maintenance(self, limit: int = 10) -> List[MaintenanceLog]:
        return MaintenanceLog.get_recent(limit)
    
    def get_maintenance_statistics(self) -> dict:
        all_logs = MaintenanceLog.get_all(limit=1000)
        active_logs = [l for l in all_logs if l.status == 'Đang thực hiện']
        completed_logs = [l for l in all_logs if l.status == 'Hoàn thành']
        
        by_type = {}
        for log in all_logs:
            mtype = log.maintenance_type
            by_type[mtype] = by_type.get(mtype, 0) + 1
        
        return {
            'total': len(all_logs),
            'active': len(active_logs),
            'completed': len(completed_logs),
            'by_type': by_type
        }