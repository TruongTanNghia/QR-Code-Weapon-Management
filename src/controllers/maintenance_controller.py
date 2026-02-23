"""
Maintenance Controller - Business logic for maintenance logs
"""
from typing import List, Optional, Tuple
from datetime import datetime
import shutil
import os
import uuid

from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..models.database import Database 
from .user_controller import UserController
from ..config import DATA_DIR 


class MaintenanceController:
    
    def __init__(self):
        self.db = Database()
        self.image_dir = DATA_DIR / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_current_user_info(self):
        user = UserController.get_current_user()
        if user: return user.id, user.username
        return None, "Hệ thống"

    # [FIX] Thêm tham số image_category
    def _save_images(self, target_type: str, target_id: int, file_paths: List[str], image_category: str = 'general'):
        if not file_paths: return
        for path in file_paths:
            if not os.path.exists(path): continue
            ext = os.path.splitext(path)[1]
            filename = f"{target_type.lower()}_{target_id}_{image_category}_{uuid.uuid4().hex[:8]}{ext}"
            dest_path = self.image_dir / filename
            shutil.copy2(path, dest_path)
            db_path = f"images/{filename}"
            self.db.insert(
                "INSERT INTO item_images (target_type, target_id, image_category, file_path) VALUES (?, ?, ?, ?)",
                (target_type, target_id, image_category, db_path)
            )

    def _delete_images(self, target_type: str, target_id: int, db_paths: List[str] = None):
        if db_paths is None:
            rows = self.db.fetch_all("SELECT file_path FROM item_images WHERE target_type=? AND target_id=?", (target_type, target_id))
            paths_to_delete = [r['file_path'] for r in rows]
        else:
            paths_to_delete = db_paths

        if not paths_to_delete: return

        for db_path in paths_to_delete:
            full_path = DATA_DIR / db_path
            if full_path.exists():
                try: os.remove(full_path)
                except Exception as e: print(f"Lỗi xóa file {full_path}: {e}")

        if db_paths is None:
            self.db.execute("DELETE FROM item_images WHERE target_type=? AND target_id=?", (target_type, target_id))
        else:
            for p in paths_to_delete:
                self.db.execute("DELETE FROM item_images WHERE target_type=? AND target_id=? AND file_path=?", (target_type, target_id, p))

    def create_maintenance_log(
        self, equipment_id: int, log_data: dict, update_equipment_status: str = None,
        images_before: List[str] = None, images_after: List[str] = None # [MỚI] Tách 2 loại
    ) -> Tuple[bool, str, Optional[MaintenanceLog]]:
        
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment: return False, "Không tìm thấy thiết bị!", None
        if not log_data.get('maintenance_type'): return False, "Vui lòng chọn loại công việc!", None
        
        try:
            log = MaintenanceLog()
            log.equipment_id = equipment_id
            log.maintenance_type = log_data['maintenance_type']
            log.description = log_data.get('description', '')
            log.technician_name = log_data.get('technician', '')
            log.status = log_data.get('status', 'Đang thực hiện')
            
            start = log_data.get('start_date')
            log.start_date = start if start else datetime.now()
            log.end_date = log_data.get('end_date')
            log.notes = log_data.get('notes', '')
            
            log.save() 
            
            # [MỚI] Lưu ảnh theo phân loại
            if images_before: self._save_images("Maintenance", log.id, images_before, 'before')
            if images_after: self._save_images("Maintenance", log.id, images_after, 'after')
            
            if update_equipment_status:
                equipment.status = update_equipment_status
                equipment.save()
            
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "CREATE", "Maintenance", log.id, f"Thêm lịch bảo dưỡng: '{log.maintenance_type}' cho ID: {equipment_id}")
            
            return True, "Đã ghi nhật ký bảo dưỡng!", log
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    def update_maintenance_log(
        self, log_id: int, log_data: dict, update_equipment_status: str = None,
        new_before: List[str] = None, deleted_before: List[str] = None, # [MỚI]
        new_after: List[str] = None, deleted_after: List[str] = None    # [MỚI]
    ) -> Tuple[bool, str]:
        
        log = MaintenanceLog.get_by_id(log_id)
        if not log: return False, "Không tìm thấy bản ghi!"
        
        try:
            log.maintenance_type = log_data.get('maintenance_type', log.maintenance_type)
            log.description = log_data.get('description', log.description)
            log.technician_name = log_data.get('technician', log.technician_name)
            log.status = log_data.get('status', log.status)
            log.notes = log_data.get('notes', log.notes)
            if log_data.get('end_date'): log.end_date = log_data['end_date']
            log.save()
            
            # [MỚI] Xử lý xóa và thêm ảnh
            all_deleted = (deleted_before or []) + (deleted_after or [])
            if all_deleted: self._delete_images("Maintenance", log.id, all_deleted)
            
            if new_before: self._save_images("Maintenance", log.id, new_before, 'before')
            if new_after: self._save_images("Maintenance", log.id, new_after, 'after')
            
            if update_equipment_status:
                equipment = Equipment.get_by_id(log.equipment_id)
                if equipment:
                    equipment.status = update_equipment_status
                    equipment.save()
            
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "UPDATE", "Maintenance", log.id, f"Cập nhật lịch bảo dưỡng ID {log_id}")
            return True, "Đã cập nhật bản ghi!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def complete_maintenance(self, log_id: int, notes: str = "", update_equipment_status: str = None) -> Tuple[bool, str]:
        log = MaintenanceLog.get_by_id(log_id)
        if not log: return False, "Không tìm thấy bản ghi!"
        try:
            log.complete(notes)
            if update_equipment_status:
                equipment = Equipment.get_by_id(log.equipment_id)
                if equipment:
                    equipment.status = update_equipment_status
                    equipment.save()
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "UPDATE", "Maintenance", log_id, f"Hoàn thành bảo dưỡng ID {log_id}")
            return True, "Đã hoàn thành công việc bảo dưỡng!"
        except Exception as e: return False, f"Lỗi: {str(e)}"
    
    def delete_maintenance_log(self, log_id: int) -> Tuple[bool, str]:
        log = MaintenanceLog.get_by_id(log_id)
        if not log: return False, "Không tìm thấy bản ghi!"
        try:
            log_type, equip_id = log.maintenance_type, log.equipment_id
            self._delete_images("Maintenance", log_id)
            log.delete()
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "DELETE", "Maintenance", log_id, f"Xóa lịch bảo dưỡng ID {log_id}")
            return True, "Đã xóa bản ghi!"
        except Exception as e: return False, f"Lỗi: {str(e)}"

    def get_equipment_maintenance_history(self, equipment_id: int) -> List[MaintenanceLog]: return MaintenanceLog.get_by_equipment(equipment_id)
    def get_active_maintenance(self) -> List[MaintenanceLog]: return MaintenanceLog.get_active()
    def get_recent_maintenance(self, limit: int = 10) -> List[MaintenanceLog]: return MaintenanceLog.get_recent(limit)
    def get_maintenance_statistics(self) -> dict:
        all_logs = MaintenanceLog.get_all(limit=1000)
        active_logs = [l for l in all_logs if l.status == 'Đang thực hiện']
        completed_logs = [l for l in all_logs if l.status == 'Hoàn thành']
        by_type = {}
        for log in all_logs: by_type[log.maintenance_type] = by_type.get(log.maintenance_type, 0) + 1
        return {'total': len(all_logs), 'active': len(active_logs), 'completed': len(completed_logs), 'by_type': by_type}