"""
Audit Log Model - Represents a system activity log
"""
from datetime import datetime
from typing import List, Optional
from .database import Database

class AuditLog:
    def __init__(self):
        self.id: Optional[int] = None
        self.user_id: Optional[int] = None
        self.username: str = ""
        self.action: str = ""
        self.target_type: str = ""
        self.target_id: Optional[int] = None
        self.details: str = ""
        self.ip_address: str = ""
        self.created_at: Optional[datetime] = None

    @classmethod
    def _from_row(cls, row) -> 'AuditLog':
        log = cls()
        log.id = row['id']
        log.user_id = row['user_id']
        log.username = row['username']
        log.action = row['action']
        log.target_type = row['target_type']
        log.target_id = row['target_id']
        log.details = row['details']
        log.ip_address = row['ip_address']
        log.created_at = row['created_at']
        return log

    @classmethod
    def get_filtered(cls, keyword: str = None, action: str = None, 
                     start_date: str = None, end_date: str = None, limit: int = 1000) -> List['AuditLog']:
        """Lấy danh sách log có bộ lọc"""
        db = Database()
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if keyword:
            query += " AND (username LIKE ? OR details LIKE ? OR target_type LIKE ?)"
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern, pattern])

        if action:
            query += " AND action = ?"
            params.append(action)

        if start_date and end_date:
            # SQLite so sánh datetime chuẩn ISO YYYY-MM-DD HH:MM:SS
            query += " AND created_at >= ? AND created_at <= ?"
            params.extend([start_date, end_date])

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = db.fetch_all(query, tuple(params))
        return [cls._from_row(r) for r in rows]