"""
LoanLog Model - Represents equipment loan/borrowing history
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from .database import Database


@dataclass
class LoanLog:
    """
    Data class representing a loan/borrowing log entry
    """
    id: Optional[int] = None
    equipment_id: int = 0
    borrower_unit: str = ""  # Đơn vị mượn (nhập tay)
    loan_date: Optional[datetime] = None  # Ngày cho mượn
    expected_return_date: Optional[datetime] = None  # Ngày dự kiến trả
    return_date: Optional[datetime] = None  # Ngày trả thực tế
    status: str = "Đang mượn"  # Đang mượn, Đã trả
    notes: str = ""
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Related equipment info (populated from joins)
    equipment_name: str = ""
    equipment_serial: str = ""
    
    # [MỚI] Danh sách ảnh
    images_before: List[str] = field(default_factory=list) # Ảnh lúc giao
    images_after: List[str] = field(default_factory=list)  # Ảnh lúc trả
    
    def __post_init__(self):
        self.db = Database()
    
    def save(self) -> int:
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        query = '''
            INSERT INTO loan_log 
            (equipment_id, borrower_unit, loan_date, expected_return_date, 
             return_date, status, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        loan_date = self.loan_date or datetime.now()
        params = (
            self.equipment_id, self.borrower_unit, loan_date,
            self.expected_return_date, self.return_date, 
            self.status, self.notes, self.created_by
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        query = '''
            UPDATE loan_log SET
                equipment_id = ?, borrower_unit = ?, loan_date = ?,
                expected_return_date = ?, return_date = ?, status = ?, notes = ?
            WHERE id = ?
        '''
        params = (
            self.equipment_id, self.borrower_unit, self.loan_date,
            self.expected_return_date, self.return_date, 
            self.status, self.notes, self.id
        )
        self.db.execute(query, params)
        return self.id
    
    def complete_return(self, notes: str = "") -> bool:
        if not self.id:
            return False
        self.status = "Đã trả"
        self.return_date = datetime.now()
        if notes:
            self.notes = notes
        self._update()
        return True
    
    def delete(self) -> bool:
        if not self.id:
            return False
            
        # [MỚI] Xóa thông tin ảnh khỏi DB trước khi xóa log
        self.db.execute("DELETE FROM item_images WHERE target_type='Loan' AND target_id=?", (self.id,))
        
        query = "DELETE FROM loan_log WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
        
    def load_images(self):
        """[MỚI] Tải và phân loại ảnh từ Database"""
        if not self.id:
            return
        rows = self.db.fetch_all(
            "SELECT file_path, image_category FROM item_images WHERE target_type='Loan' AND target_id=?", 
            (self.id,)
        )
        self.images_before = [row['file_path'] for row in rows if row['image_category'] == 'before']
        self.images_after = [row['file_path'] for row in rows if row['image_category'] == 'after']
        
        # Backward compatibility cho DB cũ nếu có
        general_images = [row['file_path'] for row in rows if row['image_category'] == 'general']
        self.images_before.extend(general_images)
    
    @classmethod
    def get_by_id(cls, log_id: int) -> Optional['LoanLog']:
        db = Database()
        row = db.fetch_one('''
            SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM loan_log l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.id = ?
        ''', (log_id,))
        if row:
            log = cls._from_row(row)
            log.load_images()
            return log
        return None
    
    @classmethod
    def get_by_equipment(cls, equipment_id: int) -> List['LoanLog']:
        db = Database()
        rows = db.fetch_all('''
            SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM loan_log l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.equipment_id = ?
            ORDER BY l.loan_date DESC
        ''', (equipment_id,))
        logs = []
        for row in rows:
            log = cls._from_row(row)
            log.load_images()
            logs.append(log)
        return logs
    
    @classmethod
    def get_active_by_equipment(cls, equipment_id: int) -> Optional['LoanLog']:
        db = Database()
        row = db.fetch_one('''
            SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM loan_log l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.equipment_id = ? AND l.status = 'Đang mượn'
            ORDER BY l.loan_date DESC
            LIMIT 1
        ''', (equipment_id,))
        if row:
            log = cls._from_row(row)
            log.load_images()
            return log
        return None
    
    @classmethod
    def get_active(cls) -> List['LoanLog']:
        db = Database()
        rows = db.fetch_all('''
            SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM loan_log l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.status = 'Đang mượn'
            ORDER BY l.loan_date DESC
        ''')
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List['LoanLog']:
        db = Database()
        rows = db.fetch_all('''
            SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM loan_log l
            JOIN equipment e ON l.equipment_id = e.id
            ORDER BY l.loan_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_recent(cls, limit: int = 10) -> List['LoanLog']:
        db = Database()
        rows = db.fetch_all('''
            SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM loan_log l
            JOIN equipment e ON l.equipment_id = e.id
            ORDER BY l.created_at DESC
            LIMIT ?
        ''', (limit,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_date_range(cls, start_date, end_date=None) -> List['LoanLog']:
        db = Database()
        start_str = start_date.strftime('%Y-%m-%d')
        if end_date:
            end_str = end_date.strftime('%Y-%m-%d')
            rows = db.fetch_all('''
                SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM loan_log l
                JOIN equipment e ON l.equipment_id = e.id
                WHERE DATE(l.loan_date) >= ? AND DATE(l.loan_date) <= ?
                ORDER BY l.loan_date DESC
            ''', (start_str, end_str))
        else:
            rows = db.fetch_all('''
                SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM loan_log l
                JOIN equipment e ON l.equipment_id = e.id
                WHERE DATE(l.loan_date) = ?
                ORDER BY l.loan_date DESC
            ''', (start_str,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_equipment_and_date(cls, equipment_id: int, start_date=None, end_date=None) -> List['LoanLog']:
        db = Database()
        if start_date and end_date:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            rows = db.fetch_all('''
                SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM loan_log l
                JOIN equipment e ON l.equipment_id = e.id
                WHERE l.equipment_id = ? AND DATE(l.loan_date) >= ? AND DATE(l.loan_date) <= ?
                ORDER BY l.loan_date DESC
            ''', (equipment_id, start_str, end_str))
        elif start_date:
            start_str = start_date.strftime('%Y-%m-%d')
            rows = db.fetch_all('''
                SELECT l.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM loan_log l
                JOIN equipment e ON l.equipment_id = e.id
                WHERE l.equipment_id = ? AND DATE(l.loan_date) = ?
                ORDER BY l.loan_date DESC
            ''', (equipment_id, start_str))
        else:
            return cls.get_by_equipment(equipment_id)
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def count_active(cls) -> int:
        db = Database()
        row = db.fetch_one(
            "SELECT COUNT(*) as count FROM loan_log WHERE status = 'Đang mượn'"
        )
        return row['count'] if row else 0
    
    @classmethod
    def _from_row(cls, row) -> 'LoanLog':
        log = cls()
        log.id = row['id']
        log.equipment_id = row['equipment_id']
        log.borrower_unit = row['borrower_unit'] or ""
        log.loan_date = row['loan_date']
        log.expected_return_date = row['expected_return_date']
        log.return_date = row['return_date']
        log.status = row['status']
        log.notes = row['notes'] or ""
        log.created_at = row['created_at']
        log.created_by = row['created_by'] if 'created_by' in row.keys() else None
        
        if 'equipment_name' in row.keys():
            log.equipment_name = row['equipment_name']
        if 'equipment_serial' in row.keys():
            log.equipment_serial = row['equipment_serial']
        
        return log
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment_name,
            'equipment_serial': self.equipment_serial,
            'borrower_unit': self.borrower_unit,
            'loan_date': str(self.loan_date) if self.loan_date else None,
            'expected_return_date': str(self.expected_return_date) if self.expected_return_date else None,
            'return_date': str(self.return_date) if self.return_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': str(self.created_at) if self.created_at else None,
            'images_before': self.images_before,
            'images_after': self.images_after
        }


# Loan status options
LOAN_STATUS = [
    "Đang mượn",
    "Đã trả"
]