"""
Loan Controller - Business logic for equipment loans
"""
from typing import List, Optional, Tuple
from datetime import datetime
from ..models.equipment import Equipment
from ..models.loan_log import LoanLog
from ..models.database import Database # [MỚI] Import DB để ghi log
from .user_controller import UserController # [MỚI] Import để lấy user hiện tại


class LoanController:
    """
    Controller handling equipment loan business logic
    """
    
    def __init__(self):
        self.db = Database() # [MỚI] Khởi tạo kết nối DB
        
    def _get_current_user_info(self):
        """[MỚI] Hàm tiện ích lấy thông tin người dùng đang thao tác"""
        user = UserController.get_current_user()
        if user:
            return user.id, user.username
        return None, "Hệ thống"
    
    def create_loan(
        self, 
        equipment_id: int, 
        loan_data: dict
    ) -> Tuple[bool, str, Optional[LoanLog]]:
        """
        Create new loan record and update equipment loan_status
        """
        # Verify equipment exists
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!", None
        
        # Check if equipment is available for loan
        if equipment.loan_status == "Đã cho mượn":
            return False, "Thiết bị đang được cho mượn, không thể tạo phiếu mượn mới!", None
        
        # Check if there's an active loan for this equipment
        active_loan = LoanLog.get_active_by_equipment(equipment_id)
        if active_loan:
            return False, "Thiết bị đang có phiếu mượn chưa hoàn thành!", None
        
        # Validate required fields
        if not loan_data.get('borrower_unit'):
            return False, "Vui lòng nhập đơn vị mượn!", None
        
        try:
            # Create loan log
            loan = LoanLog()
            loan.equipment_id = equipment_id
            loan.borrower_unit = loan_data['borrower_unit']
            
            # Handle dates
            loan_date = loan_data.get('loan_date')
            if loan_date:
                loan.loan_date = loan_date
            else:
                loan.loan_date = datetime.now()
            
            expected_return = loan_data.get('expected_return_date')
            if expected_return:
                loan.expected_return_date = expected_return
            
            loan.notes = loan_data.get('notes', '')
            loan.status = "Đang mượn"
            
            loan.save()
            
            # Update equipment loan_status to "Đã cho mượn"
            equipment.update_loan_status("Đã cho mượn")
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            log_details = f"Tạo phiếu mượn cho thiết bị '{equipment.name}' (ID: {equipment_id}). Đơn vị mượn: {loan.borrower_unit}"
            self.db.log_action(user_id, username, "CREATE", "Loan", loan.id, log_details)
            
            return True, "Đã tạo phiếu cho mượn thiết bị!", loan
            
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            return False, f"Lỗi: {str(e)}", None
    
    def update_loan(self, loan_id: int, loan_data: dict) -> Tuple[bool, str]:
        """
        Update existing loan log
        """
        loan = LoanLog.get_by_id(loan_id)
        if not loan:
            return False, "Không tìm thấy bản ghi!"
        
        try:
            loan.borrower_unit = loan_data.get('borrower_unit', loan.borrower_unit)
            loan.notes = loan_data.get('notes', loan.notes)
            
            if loan_data.get('expected_return_date'):
                loan.expected_return_date = loan_data['expected_return_date']
            
            loan.save()
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            log_details = f"Cập nhật phiếu mượn ID {loan_id}. Đơn vị mượn: {loan.borrower_unit}"
            self.db.log_action(user_id, username, "UPDATE", "Loan", loan_id, log_details)
            
            return True, "Đã cập nhật thông tin cho mượn!"
            
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            return False, f"Lỗi: {str(e)}"
    
    def return_equipment(
        self, 
        loan_id: int, 
        notes: str = "",
        return_date: datetime = None
    ) -> Tuple[bool, str]:
        """
        Mark loan as returned and update equipment loan_status to "Đang ở kho"
        """
        loan = LoanLog.get_by_id(loan_id)
        if not loan:
            return False, "Không tìm thấy bản ghi!"
        
        if loan.status == "Đã trả":
            return False, "Thiết bị đã được trả trước đó!"
        
        try:
            # Update loan status
            loan.status = "Đã trả"
            loan.return_date = return_date or datetime.now()
            if notes:
                loan.notes = notes
            loan.save()
            
            # Update equipment loan_status to "Đang ở kho"
            equipment = Equipment.get_by_id(loan.equipment_id)
            if equipment:
                equipment.update_loan_status("Đang ở kho")
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            equip_name = equipment.name if equipment else f"ID {loan.equipment_id}"
            log_details = f"Ghi nhận trả thiết bị '{equip_name}' cho phiếu mượn ID {loan_id}"
            self.db.log_action(user_id, username, "UPDATE", "Loan", loan_id, log_details)
            
            return True, "Đã ghi nhận trả thiết bị!"
            
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            return False, f"Lỗi: {str(e)}"
    
    def delete_loan(self, loan_id: int) -> Tuple[bool, str]:
        """Delete loan log"""
        loan = LoanLog.get_by_id(loan_id)
        if not loan:
            return False, "Không tìm thấy bản ghi!"
        
        try:
            # If loan is active, update equipment status back to "Đang ở kho"
            if loan.status == "Đang mượn":
                equipment = Equipment.get_by_id(loan.equipment_id)
                if equipment:
                    equipment.update_loan_status("Đang ở kho")
            
            borrower_unit = loan.borrower_unit
            equip_id = loan.equipment_id
            
            loan.delete()
            
            # [QUAN TRỌNG] Ghi nhật ký (Audit Log)
            user_id, username = self._get_current_user_info()
            log_details = f"Xóa phiếu mượn ID {loan_id} (Đơn vị mượn: {borrower_unit}, Thiết bị ID: {equip_id})"
            self.db.log_action(user_id, username, "DELETE", "Loan", loan_id, log_details)
            
            return True, "Đã xóa bản ghi!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    # Get data methods
    def get_equipment_loan_history(self, equipment_id: int) -> List[LoanLog]:
        """Get loan history for an equipment"""
        return LoanLog.get_by_equipment(equipment_id)
    
    def get_active_loans(self) -> List[LoanLog]:
        """Get all active loans"""
        return LoanLog.get_active()
    
    def get_recent_loans(self, limit: int = 10) -> List[LoanLog]:
        """Get recent loans"""
        return LoanLog.get_recent(limit)
    
    def get_loan_statistics(self) -> dict:
        """Get loan statistics"""
        all_logs = LoanLog.get_all(limit=1000)
        active_logs = [l for l in all_logs if l.status == 'Đang mượn']
        returned_logs = [l for l in all_logs if l.status == 'Đã trả']
        
        # Group by borrower unit
        by_unit = {}
        for log in all_logs:
            unit = log.borrower_unit
            by_unit[unit] = by_unit.get(unit, 0) + 1
        
        return {
            'total': len(all_logs),
            'active': len(active_logs),
            'returned': len(returned_logs),
            'by_unit': by_unit
        }
    
    def check_equipment_available(self, equipment_id: int) -> Tuple[bool, str]:
        """Check if equipment is available for loan"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            return False, "Không tìm thấy thiết bị!"
        
        if equipment.loan_status == "Đã cho mượn":
            active_loan = LoanLog.get_active_by_equipment(equipment_id)
            if active_loan:
                return False, f"Thiết bị đang được mượn bởi: {active_loan.borrower_unit}"
            return False, "Thiết bị đang ở trạng thái cho mượn"
        
        return True, "Thiết bị sẵn sàng cho mượn"