"""
Audit Controller - Business logic for system logs
"""
from typing import List
from datetime import datetime, time
from ..models.audit_log import AuditLog

class AuditController:
    """Controller for fetching audit logs"""
    
    def get_logs(self, keyword: str = None, action: str = None, 
                 from_date: datetime = None, to_date: datetime = None) -> List[AuditLog]:
        """
        Lấy danh sách nhật ký dựa trên bộ lọc
        """
        start_str = None
        end_str = None
        
        # Format datetime để SQLite có thể so sánh chuỗi chính xác
        if from_date and to_date:
            # Từ 00:00:00 của ngày bắt đầu
            start_dt = datetime.combine(from_date, time.min)
            # Đến 23:59:59 của ngày kết thúc
            end_dt = datetime.combine(to_date, time.max)
            
            start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
        return AuditLog.get_filtered(
            keyword=keyword, 
            action=action, 
            start_date=start_str, 
            end_date=end_str
        )