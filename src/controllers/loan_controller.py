"""
Loan Controller - Business logic for equipment loans
"""
from typing import List, Optional, Tuple
from datetime import datetime
import shutil
import os
import uuid

from ..models.equipment import Equipment
from ..models.loan_log import LoanLog
from ..models.database import Database
from .user_controller import UserController
from ..config import DATA_DIR # [MỚI]


class LoanController:
    """
    Controller handling equipment loan business logic
    """
    
    def __init__(self):
        self.db = Database()
        # [MỚI] Khởi tạo thư mục ảnh
        self.image_dir = DATA_DIR / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_current_user_info(self):
        user = UserController.get_current_user()
        if user:
            return user.id, user.username
        return None, "Hệ thống"

    # --- [MỚI] HÀM XỬ LÝ ẢNH CHUNG ---
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
    # -----------------------------------
    
    def create_loan(
        self, equipment_id: int, loan_data: dict, 
        images_before: List[str] = None # [MỚI]
    ) -> Tuple[bool, str, Optional[LoanLog]]:
        
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!", None
        
        if equipment.loan_status == "Đã cho mượn":
            return False, "Thiết bị đang được cho mượn, không thể tạo phiếu mượn mới!", None
        
        active_loan = LoanLog.get_active_by_equipment(equipment_id)
        if active_loan:
            return False, "Thiết bị đang có phiếu mượn chưa hoàn thành!", None
        
        if not loan_data.get('borrower_unit'):
            return False, "Vui lòng nhập đơn vị mượn!", None
        
        try:
            loan = LoanLog()
            loan.equipment_id = equipment_id
            loan.borrower_unit = loan_data['borrower_unit']
            
            loan_date = loan_data.get('loan_date')
            if loan_date: loan.loan_date = loan_date
            else: loan.loan_date = datetime.now()
            
            expected_return = loan_data.get('expected_return_date')
            if expected_return: loan.expected_return_date = expected_return
            
            loan.notes = loan_data.get('notes', '')
            loan.status = "Đang mượn"
            
            loan.save()
            
            # [MỚI] Lưu ảnh lúc giao
            if images_before:
                self._save_images("Loan", loan.id, images_before, 'before')
            
            equipment.update_loan_status("Đã cho mượn")
            
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "CREATE", "Loan", loan.id, f"Tạo phiếu mượn cho thiết bị ID: {equipment_id}. Đơn vị: {loan.borrower_unit}")
            
            return True, "Đã tạo phiếu cho mượn thiết bị!", loan
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    def update_loan(
        self, loan_id: int, loan_data: dict,
        new_before: List[str] = None, deleted_before: List[str] = None, # [MỚI]
        new_after: List[str] = None, deleted_after: List[str] = None    # [MỚI]
    ) -> Tuple[bool, str]:
        
        loan = LoanLog.get_by_id(loan_id)
        if not loan:
            return False, "Không tìm thấy bản ghi!"
        
        try:
            loan.borrower_unit = loan_data.get('borrower_unit', loan.borrower_unit)
            loan.notes = loan_data.get('notes', loan.notes)
            if loan_data.get('expected_return_date'):
                loan.expected_return_date = loan_data['expected_return_date']
            
            loan.save()
            
            # [MỚI] Cập nhật ảnh
            all_deleted = (deleted_before or []) + (deleted_after or [])
            if all_deleted: self._delete_images("Loan", loan.id, all_deleted)
            
            if new_before: self._save_images("Loan", loan.id, new_before, 'before')
            if new_after: self._save_images("Loan", loan.id, new_after, 'after')
            
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "UPDATE", "Loan", loan_id, f"Cập nhật phiếu mượn ID {loan_id}")
            return True, "Đã cập nhật thông tin cho mượn!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def return_equipment(
        self, loan_id: int, notes: str = "", return_date: datetime = None,
        images_after: List[str] = None # [MỚI]
    ) -> Tuple[bool, str]:
        
        loan = LoanLog.get_by_id(loan_id)
        if not loan: return False, "Không tìm thấy bản ghi!"
        if loan.status == "Đã trả": return False, "Thiết bị đã được trả trước đó!"
        
        try:
            loan.status = "Đã trả"
            loan.return_date = return_date or datetime.now()
            if notes: loan.notes = notes
            loan.save()
            
            # [MỚI] Lưu ảnh lúc trả
            if images_after:
                self._save_images("Loan", loan.id, images_after, 'after')
            
            equipment = Equipment.get_by_id(loan.equipment_id)
            if equipment: equipment.update_loan_status("Đang ở kho")
            
            user_id, username = self._get_current_user_info()
            equip_name = equipment.name if equipment else f"ID {loan.equipment_id}"
            self.db.log_action(user_id, username, "UPDATE", "Loan", loan_id, f"Ghi nhận trả thiết bị '{equip_name}'")
            return True, "Đã ghi nhận trả thiết bị!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    def delete_loan(self, loan_id: int) -> Tuple[bool, str]:
        loan = LoanLog.get_by_id(loan_id)
        if not loan: return False, "Không tìm thấy bản ghi!"
        try:
            if loan.status == "Đang mượn":
                equipment = Equipment.get_by_id(loan.equipment_id)
                if equipment: equipment.update_loan_status("Đang ở kho")
            
            borrower_unit = loan.borrower_unit
            equip_id = loan.equipment_id
            
            # [MỚI] Xóa ảnh vật lý
            self._delete_images("Loan", loan_id)
            
            loan.delete()
            user_id, username = self._get_current_user_info()
            self.db.log_action(user_id, username, "DELETE", "Loan", loan_id, f"Xóa phiếu mượn ID {loan_id}")
            return True, "Đã xóa bản ghi!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"

    # ... (Các hàm lấy danh sách List giữ nguyên) ...
    def get_equipment_loan_history(self, equipment_id: int) -> List[LoanLog]: return LoanLog.get_by_equipment(equipment_id)
    def get_active_loans(self) -> List[LoanLog]: return LoanLog.get_active()
    def get_recent_loans(self, limit: int = 10) -> List[LoanLog]: return LoanLog.get_recent(limit)
    def get_loan_statistics(self) -> dict:
        all_logs = LoanLog.get_all(limit=1000)
        active_logs = [l for l in all_logs if l.status == 'Đang mượn']
        returned_logs = [l for l in all_logs if l.status == 'Đã trả']
        by_unit = {}
        for log in all_logs: by_unit[log.borrower_unit] = by_unit.get(log.borrower_unit, 0) + 1
        return {'total': len(all_logs), 'active': len(active_logs), 'returned': len(returned_logs), 'by_unit': by_unit}
    def check_equipment_available(self, equipment_id: int) -> Tuple[bool, str]:
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment: return False, "Không tìm thấy thiết bị!"
        if equipment.loan_status == "Đã cho mượn":
            active_loan = LoanLog.get_active_by_equipment(equipment_id)
            if active_loan: return False, f"Thiết bị đang được mượn bởi: {active_loan.borrower_unit}"
            return False, "Thiết bị đang ở trạng thái cho mượn"
        return True, "Thiết bị sẵn sàng cho mượn"