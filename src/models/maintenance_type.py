"""
Maintenance Type Model - Represents maintenance work types
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from .database import Database


@dataclass
class MaintenanceType:
    """
    Data class representing a maintenance work type
    """
    id: Optional[int] = None
    name: str = ""
    code: str = ""  # Mã loại công việc
    description: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        self.db = Database()
    
    def save(self) -> int:
        """Save maintenance type to database (insert or update)"""
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        """Insert new maintenance type"""
        query = '''
            INSERT INTO maintenance_types (name, code, description, is_active)
            VALUES (?, ?, ?, ?)
        '''
        params = (
            self.name, self.code, self.description,
            1 if self.is_active else 0
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        """Update existing maintenance type with Cascade Update for logs"""
        # [BƯỚC 1] Lấy tên cũ trước khi cập nhật
        old_name = None
        current_row = self.db.fetch_one("SELECT name FROM maintenance_types WHERE id = ?", (self.id,))
        if current_row:
            old_name = current_row['name']

        # [BƯỚC 2] Cập nhật thông tin mới vào bảng loại công việc
        query = '''
            UPDATE maintenance_types SET
                name = ?, code = ?, description = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        params = (
            self.name, self.code, self.description,
            1 if self.is_active else 0, self.id
        )
        self.db.execute(query, params)

        # [BƯỚC 3] QUAN TRỌNG: Nếu tên thay đổi, cập nhật đồng loạt trong bảng nhật ký (maintenance_log)
        # Để đảm bảo tính nhất quán dữ liệu và số lượng đếm không bị về 0
        if old_name and old_name != self.name:
            try:
                update_log_query = "UPDATE maintenance_log SET maintenance_type = ? WHERE maintenance_type = ?"
                self.db.execute(update_log_query, (self.name, old_name))
                print(f"Đã cập nhật tên loại công việc từ '{old_name}' thành '{self.name}' trong lịch sử bảo dưỡng.")
            except Exception as e:
                print(f"Lỗi khi cập nhật đồng bộ tên loại công việc: {e}")
            
        return self.id
    
    def delete(self) -> bool:
        """Delete maintenance type (soft delete)"""
        if not self.id:
            return False
        query = "UPDATE maintenance_types SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    def hard_delete(self) -> bool:
        """Permanently delete maintenance type"""
        if not self.id:
            return False
        query = "DELETE FROM maintenance_types WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True

    def get_maintenance_count(self) -> int:
        """Get count of maintenance logs using this type"""
        if not self.name:
            return 0
        # Sử dụng đúng tên bảng 'maintenance_log' (số ít)
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM maintenance_log WHERE maintenance_type = ?", 
            (self.name,)
        )
        return row['count'] if row else 0
    
    @classmethod
    def get_by_id(cls, type_id: int) -> Optional['MaintenanceType']:
        """Get maintenance type by ID"""
        db = Database()
        row = db.fetch_one("SELECT * FROM maintenance_types WHERE id = ?", (type_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['MaintenanceType']:
        """Get maintenance type by name"""
        db = Database()
        row = db.fetch_one("SELECT * FROM maintenance_types WHERE name = ?", (name,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_all(cls, include_inactive: bool = False) -> List['MaintenanceType']:
        """Get all maintenance types"""
        db = Database()
        if include_inactive:
            query = "SELECT * FROM maintenance_types ORDER BY id ASC"
            rows = db.fetch_all(query)
        else:
            query = "SELECT * FROM maintenance_types WHERE is_active = 1 ORDER BY id ASC"
            rows = db.fetch_all(query)
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_active_types(cls) -> List['MaintenanceType']:
        """Get only active maintenance types (for dropdowns)"""
        return cls.get_all(include_inactive=False)
    
    @classmethod
    def name_exists(cls, name: str, exclude_id: int = None) -> bool:
        """Check if name already exists"""
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM maintenance_types WHERE name = ? AND id != ?", 
                (name, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM maintenance_types WHERE name = ?", 
                (name,)
            )
        return row is not None
    
    @classmethod
    def code_exists(cls, code: str, exclude_id: int = None) -> bool:
        """Check if code already exists"""
        if not code:
            return False
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM maintenance_types WHERE code = ? AND id != ?", 
                (code, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM maintenance_types WHERE code = ?", 
                (code,)
            )
        return row is not None
    
    @classmethod
    def _from_row(cls, row) -> 'MaintenanceType':
        """Create MaintenanceType from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            code=row['code'] or "",
            description=row['description'] or "",
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    @classmethod
    def search(cls, keyword: str, include_inactive: bool = False) -> List['MaintenanceType']:
        """Search maintenance types by name or code"""
        db = Database()
        keyword = f"%{keyword}%"
        if include_inactive:
            query = """
                SELECT * FROM maintenance_types 
                WHERE name LIKE ? OR code LIKE ? OR description LIKE ?
                ORDER BY id ASC
            """
        else:
            query = """
                SELECT * FROM maintenance_types 
                WHERE (name LIKE ? OR code LIKE ? OR description LIKE ?) AND is_active = 1
                ORDER BY id ASC
            """
        rows = db.fetch_all(query, (keyword, keyword, keyword))
        return [cls._from_row(row) for row in rows]


# Default maintenance types for initialization
DEFAULT_MAINTENANCE_TYPES = [
    ("Bảo dưỡng định kỳ", "BD-DK", "Bảo dưỡng theo lịch định kỳ"),
    ("Sửa chữa", "SC", "Sửa chữa thiết bị hỏng hóc"),
    ("Kiểm tra kỹ thuật", "KT-KT", "Kiểm tra tình trạng kỹ thuật"),
    ("Thay thế linh kiện", "TT-LK", "Thay thế các linh kiện hư hỏng"),
    ("Làm sạch/Bôi trơn", "LS-BT", "Vệ sinh và bôi trơn thiết bị"),
    ("Hiệu chỉnh", "HC", "Hiệu chỉnh, căn chỉnh thiết bị"),
    ("Khác", "KHAC", "Công việc bảo dưỡng khác"),
]


def get_maintenance_type_names() -> List[str]:
    """Get list of active maintenance type names for dropdowns"""
    types = MaintenanceType.get_active_types()
    if types:
        return [t.name for t in types]
    return [t[0] for t in DEFAULT_MAINTENANCE_TYPES]