"""
Equipment Controller - Business logic for equipment management
"""
from typing import List, Optional, Tuple
import shutil
import os
import uuid

from ..models.equipment import Equipment
from ..models.maintenance_log import MaintenanceLog
from ..models.database import Database 
from ..services.qr_service import QRService
from ..services.export_service import ExportService
from .user_controller import UserController
from ..config import DATA_DIR # [MỚI] Để biết chỗ lưu ảnh


class EquipmentController:
    """
    Controller handling equipment-related business logic
    """
    
    def __init__(self):
        self.qr_service = QRService()
        self.export_service = ExportService()
        self.db = Database()
        
        # [MỚI] Khởi tạo thư mục lưu ảnh chung
        self.image_dir = DATA_DIR / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_current_user_info(self):
        user = UserController.get_current_user()
        if user:
            return user.id, user.username
        return None, "Hệ thống"

    # --- [MỚI] LOGIC XỬ LÝ ẢNH VẬT LÝ ---
    def _save_images(self, target_type: str, target_id: int, file_paths: List[str]):
        """Copy ảnh từ máy người dùng vào hệ thống và lưu DB"""
        if not file_paths: return
        
        for path in file_paths:
            if not os.path.exists(path): continue
            
            # Đổi tên file cho khỏi trùng (vd: equipment_12_uuid123.jpg)
            ext = os.path.splitext(path)[1]
            filename = f"{target_type.lower()}_{target_id}_{uuid.uuid4().hex[:8]}{ext}"
            dest_path = self.image_dir / filename
            
            # Copy file
            shutil.copy2(path, dest_path)
            
            # Lưu đường dẫn tương đối vào DB (vd: images/tên_file.jpg)
            db_path = f"images/{filename}"
            self.db.insert(
                "INSERT INTO item_images (target_type, target_id, file_path) VALUES (?, ?, ?)",
                (target_type, target_id, db_path)
            )

    def _delete_images(self, target_type: str, target_id: int, db_paths: List[str] = None):
        """Xóa ảnh vật lý và xóa khỏi DB"""
        # 1. Tìm đường dẫn DB cần xóa
        if db_paths is None:
            # Nếu không truyền list cụ thể -> Xóa TẤT CẢ ảnh của đối tượng này (khi xóa thiết bị)
            rows = self.db.fetch_all(
                "SELECT file_path FROM item_images WHERE target_type=? AND target_id=?", 
                (target_type, target_id)
            )
            paths_to_delete = [r['file_path'] for r in rows]
        else:
            paths_to_delete = db_paths

        if not paths_to_delete: return

        # 2. Xóa file vật lý trên ổ cứng
        for db_path in paths_to_delete:
            full_path = DATA_DIR / db_path
            if full_path.exists():
                try: os.remove(full_path)
                except Exception as e: print(f"Lỗi xóa file {full_path}: {e}")

        # 3. Xóa record trong DB
        if db_paths is None:
            self.db.execute(
                "DELETE FROM item_images WHERE target_type=? AND target_id=?", 
                (target_type, target_id)
            )
        else:
            for p in paths_to_delete:
                self.db.execute(
                    "DELETE FROM item_images WHERE target_type=? AND target_id=? AND file_path=?", 
                    (target_type, target_id, p)
                )
    # ------------------------------------

    def create_equipment(self, equipment_data: dict, image_paths: List[str] = None) -> Tuple[bool, str, Optional[Equipment]]:
        """[FIX] Thêm tham số image_paths"""
        required_fields = ['name', 'serial_number', 'category']
        for field in required_fields:
            if not equipment_data.get(field):
                return False, f"Trường '{field}' là bắt buộc!", None
        
        if Equipment.serial_exists(equipment_data['serial_number']):
            return False, f"Số hiệu '{equipment_data['serial_number']}' đã tồn tại!", None
        
        try:
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
            
            equipment.save() # Lưu để có ID
            
            # [MỚI] Gọi hàm lưu ảnh
            if image_paths:
                self._save_images("Equipment", equipment.id, image_paths)
            
            _, qr_path = self.qr_service.generate_equipment_qr(equipment.id, equipment.serial_number)
            equipment.qr_code_path = qr_path
            equipment.save()
            
            user_id, username = self._get_current_user_info()
            log_details = f"Thêm mới trang bị: {equipment.name} (Số hiệu: {equipment.serial_number})"
            self.db.log_action(user_id, username, "CREATE", "Equipment", equipment.id, log_details)
            
            return True, f"Đã thêm thiết bị '{equipment.name}'!", equipment
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    def update_equipment(self, equipment_id: int, equipment_data: dict, 
                         new_images: List[str] = None, deleted_images: List[str] = None) -> Tuple[bool, str]:
        """[FIX] Thêm tham số mảng ảnh mới và ảnh bị xóa"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        new_serial = equipment_data.get('serial_number', equipment.serial_number)
        if new_serial != equipment.serial_number:
            if Equipment.serial_exists(new_serial, exclude_id=equipment_id):
                return False, f"Số hiệu '{new_serial}' đã tồn tại!"
        
        try:
            old_name = equipment.name
            old_serial = equipment.serial_number
            
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
            
            # [MỚI] Cập nhật ảnh
            if deleted_images:
                self._delete_images("Equipment", equipment.id, deleted_images)
            if new_images:
                self._save_images("Equipment", equipment.id, new_images)
            
            if new_serial != old_serial:
                self.qr_service.delete_qr(equipment_id, old_serial)
                _, qr_path = self.qr_service.generate_equipment_qr(equipment_id, new_serial)
                equipment.qr_code_path = qr_path
                equipment.save()
            
            user_id, username = self._get_current_user_info()
            log_details = f"Cập nhật trang bị: {equipment.name} (Số hiệu: {equipment.serial_number})"
            if new_serial != old_serial: log_details += f" [Đổi số hiệu]"
            self.db.log_action(user_id, username, "UPDATE", "Equipment", equipment.id, log_details)
            
            return True, f"Đã cập nhật thiết bị '{equipment.name}'!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def delete_equipment(self, equipment_id: int) -> Tuple[bool, str]:
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        try:
            name = equipment.name
            serial = equipment.serial_number
            
            self.qr_service.delete_qr(equipment_id, equipment.serial_number)
            
            # [MỚI] Xóa sạch ảnh vật lý của thiết bị này trước khi xóa dữ liệu
            self._delete_images("Equipment", equipment_id)
            
            equipment.delete()
            
            user_id, username = self._get_current_user_info()
            log_details = f"Xóa trang bị: {name} (Số hiệu: {serial})"
            self.db.log_action(user_id, username, "DELETE", "Equipment", equipment_id, log_details)
            
            return True, f"Đã xóa thiết bị '{name}'!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # ... (Các hàm khác như get_equipment_list, get_equipment_detail... giữ nguyên) ...
    def get_equipment_list(self, keyword: str = None, category: str = None, status: str = None, limit: int = 500) -> List[Equipment]:
        if keyword: results = Equipment.search(keyword)
        elif category: results = Equipment.get_by_category(category)
        elif status: results = Equipment.get_by_status(status)
        else: results = Equipment.get_all(limit=limit)
        
        if keyword and category: results = [e for e in results if e.category == category]
        if keyword and status: results = [e for e in results if e.status == status]
        if category and status and not keyword: results = [e for e in results if e.status == status]
        return results
    
    def get_equipment_detail(self, equipment_id: int) -> Tuple[Optional[Equipment], List[MaintenanceLog]]:
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment: return None, []
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        return equipment, logs
    
    def lookup_by_qr(self, qr_data: str) -> Tuple[bool, str, Optional[Equipment]]:
        decoded = self.qr_service.decode_qr_data(qr_data)
        if decoded['type'] == 'equipment':
            equipment = Equipment.get_by_id(decoded['equipment_id'])
            if equipment: return True, "Tìm thấy thiết bị!", equipment
            else: return False, f"Không tìm thấy thiết bị với ID: {decoded['equipment_id']}", None
        elif decoded['type'] == 'unknown':
            return False, "Mã QR không thuộc hệ thống VKTBKT!", None
        else:
            return False, "Lỗi giải mã QR!", None
    
    def export_equipment_list_pdf(self, equipment_list: List[Equipment]) -> Tuple[bool, str]:
        if not equipment_list: return False, "Không có dữ liệu để xuất!"
        try:
            filepath = self.export_service.export_equipment_list(equipment_list)
            return True, filepath
        except Exception as e: return False, f"Lỗi xuất file: {str(e)}"
    
    def export_qr_sheet_pdf(self, equipment_list: List[Equipment]) -> Tuple[bool, str]:
        if not equipment_list: return False, "Không có dữ liệu để xuất!"
        try:
            filepath = self.export_service.export_qr_sheet(equipment_list)
            return True, filepath
        except Exception as e: return False, f"Lỗi xuất file: {str(e)}"
    
    def export_equipment_detail_pdf(self, equipment_id: int) -> Tuple[bool, str]:
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment: return False, "Không tìm thấy thiết bị!"
        logs = MaintenanceLog.get_by_equipment(equipment_id)
        try:
            filepath = self.export_service.export_equipment_detail(equipment, logs)
            return True, filepath
        except Exception as e: return False, f"Lỗi xuất file: {str(e)}"