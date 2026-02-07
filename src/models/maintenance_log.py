"""
MaintenanceLog Model - Represents maintenance/repair history
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from .database import Database


@dataclass
class MaintenanceLog:
    """
    Data class representing a maintenance/repair log entry
    """
    id: Optional[int] = None
    equipment_id: int = 0
    maintenance_type: str = ""  # Bảo dưỡng định kỳ, Sửa chữa, Kiểm tra, etc.
    description: str = ""
    technician_name: str = ""  # Name of technician
    technician_id: Optional[int] = None  # Foreign key to users table
    status: str = "Đang thực hiện"  # Đang thực hiện, Hoàn thành, Tạm dừng
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: str = ""
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Related equipment info (populated from joins)
    equipment_name: str = ""
    equipment_serial: str = ""
    
    def __post_init__(self):
        self.db = Database()
    
    def save(self) -> int:
        """Save maintenance log to database (insert or update)"""
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        """Insert new maintenance log"""
        query = '''
            INSERT INTO maintenance_log 
            (equipment_id, maintenance_type, description, technician_name, 
             technician_id, status, start_date, end_date, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        start_date = self.start_date or datetime.now()
        params = (
            self.equipment_id, self.maintenance_type, self.description,
            self.technician_name, self.technician_id, self.status, 
            start_date, self.end_date, self.notes, self.created_by
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        """Update existing maintenance log"""
        query = '''
            UPDATE maintenance_log SET
                equipment_id = ?, maintenance_type = ?, description = ?,
                technician_name = ?, technician_id = ?, status = ?, 
                start_date = ?, end_date = ?, notes = ?
            WHERE id = ?
        '''
        params = (
            self.equipment_id, self.maintenance_type, self.description,
            self.technician_name, self.technician_id, self.status, 
            self.start_date, self.end_date, self.notes, self.id
        )
        self.db.execute(query, params)
        return self.id
    
    def complete(self, notes: str = "") -> bool:
        """Mark maintenance as completed"""
        if not self.id:
            return False
        self.status = "Hoàn thành"
        self.end_date = datetime.now()
        if notes:
            self.notes = notes
        self._update()
        return True
    
    def delete(self) -> bool:
        """Delete maintenance log from database"""
        if not self.id:
            return False
        query = "DELETE FROM maintenance_log WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    @classmethod
    def get_by_id(cls, log_id: int) -> Optional['MaintenanceLog']:
        """Get maintenance log by ID"""
        db = Database()
        row = db.fetch_one('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            WHERE m.id = ?
        ''', (log_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_by_equipment(cls, equipment_id: int) -> List['MaintenanceLog']:
        """Get all maintenance logs for an equipment"""
        db = Database()
        rows = db.fetch_all('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            WHERE m.equipment_id = ?
            ORDER BY m.start_date DESC
        ''', (equipment_id,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_active_by_equipment(cls, equipment_id: int) -> Optional['MaintenanceLog']:
        """Get active (ongoing) maintenance log for an equipment, returns None if no active log"""
        db = Database()
        row = db.fetch_one('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            WHERE m.equipment_id = ? AND m.status != 'Hoàn thành'
            ORDER BY m.start_date DESC
            LIMIT 1
        ''', (equipment_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_active(cls) -> List['MaintenanceLog']:
        """Get all active (ongoing) maintenance logs"""
        db = Database()
        rows = db.fetch_all('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            WHERE m.status = 'Đang thực hiện'
            ORDER BY m.start_date DESC
        ''')
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List['MaintenanceLog']:
        """Get all maintenance logs with pagination"""
        db = Database()
        rows = db.fetch_all('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            ORDER BY m.start_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_recent(cls, limit: int = 10) -> List['MaintenanceLog']:
        """Get recent maintenance logs"""
        db = Database()
        rows = db.fetch_all('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            ORDER BY m.created_at DESC
            LIMIT ?
        ''', (limit,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_today(cls) -> List['MaintenanceLog']:
        """Get maintenance logs created/updated today"""
        db = Database()
        today = datetime.now().strftime('%Y-%m-%d')
        rows = db.fetch_all('''
            SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            WHERE DATE(m.start_date) = ? OR DATE(m.created_at) = ?
            ORDER BY m.start_date DESC
        ''', (today, today))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_date_range(cls, start_date: datetime, end_date: datetime = None) -> List['MaintenanceLog']:
        """Get maintenance logs within a date range"""
        db = Database()
        start_str = start_date.strftime('%Y-%m-%d')
        if end_date:
            end_str = end_date.strftime('%Y-%m-%d')
            rows = db.fetch_all('''
                SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM maintenance_log m
                JOIN equipment e ON m.equipment_id = e.id
                WHERE DATE(m.start_date) >= ? AND DATE(m.start_date) <= ?
                ORDER BY m.start_date DESC
            ''', (start_str, end_str))
        else:
            rows = db.fetch_all('''
                SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM maintenance_log m
                JOIN equipment e ON m.equipment_id = e.id
                WHERE DATE(m.start_date) = ?
                ORDER BY m.start_date DESC
            ''', (start_str,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_equipment_and_date(cls, equipment_id: int, start_date: datetime = None, end_date: datetime = None) -> List['MaintenanceLog']:
        """Get maintenance logs for equipment within optional date range"""
        db = Database()
        if start_date and end_date:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            rows = db.fetch_all('''
                SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM maintenance_log m
                JOIN equipment e ON m.equipment_id = e.id
                WHERE m.equipment_id = ? AND DATE(m.start_date) >= ? AND DATE(m.start_date) <= ?
                ORDER BY m.start_date DESC
            ''', (equipment_id, start_str, end_str))
        elif start_date:
            start_str = start_date.strftime('%Y-%m-%d')
            rows = db.fetch_all('''
                SELECT m.*, e.name as equipment_name, e.serial_number as equipment_serial
                FROM maintenance_log m
                JOIN equipment e ON m.equipment_id = e.id
                WHERE m.equipment_id = ? AND DATE(m.start_date) = ?
                ORDER BY m.start_date DESC
            ''', (equipment_id, start_str))
        else:
            return cls.get_by_equipment(equipment_id)
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def count_active(cls) -> int:
        """Count active maintenance logs"""
        db = Database()
        row = db.fetch_one(
            "SELECT COUNT(*) as count FROM maintenance_log WHERE status = 'Đang thực hiện'"
        )
        return row['count'] if row else 0
    
    @classmethod
    def _from_row(cls, row) -> 'MaintenanceLog':
        """Create MaintenanceLog instance from database row"""
        log = cls()
        log.id = row['id']
        log.equipment_id = row['equipment_id']
        log.maintenance_type = row['maintenance_type']
        log.description = row['description'] or ""
        log.technician_name = row['technician_name'] or ""
        log.technician_id = row['technician_id']
        log.status = row['status']
        log.start_date = row['start_date']
        log.end_date = row['end_date']
        log.notes = row['notes'] or ""
        log.created_at = row['created_at']
        log.created_by = row['created_by'] if 'created_by' in row.keys() else None
        
        # Equipment info from join
        if 'equipment_name' in row.keys():
            log.equipment_name = row['equipment_name']
        if 'equipment_serial' in row.keys():
            log.equipment_serial = row['equipment_serial']
        
        return log
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment_name,
            'equipment_serial': self.equipment_serial,
            'maintenance_type': self.maintenance_type,
            'description': self.description,
            'technician_name': self.technician_name,
            'technician_id': self.technician_id,
            'status': self.status,
            'start_date': str(self.start_date) if self.start_date else None,
            'end_date': str(self.end_date) if self.end_date else None,
            'notes': self.notes,
            'created_at': str(self.created_at) if self.created_at else None
        }


# Legacy maintenance type options (kept for backward compatibility)
# Use get_maintenance_type_names() from maintenance_type.py for dynamic types
MAINTENANCE_TYPES = [
    "Bảo dưỡng định kỳ",
    "Sửa chữa",
    "Kiểm tra kỹ thuật",
    "Thay thế linh kiện",
    "Làm sạch/Bôi trơn",
    "Hiệu chỉnh",
    "Khác"
]

# Maintenance status options
MAINTENANCE_STATUS = [
    "Đang thực hiện",
    "Hoàn thành",
    "Tạm dừng",
    "Chờ linh kiện"
]
