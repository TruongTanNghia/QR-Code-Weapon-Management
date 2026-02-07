"""
Unit Model - Represents a military unit/organization
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from .database import Database


@dataclass
class Unit:
    """
    Data class representing a military unit
    Cấp đơn vị: 0 là cao nhất (không có cấp trên), 1, 2, 3... là các cấp thấp hơn
    """
    id: Optional[int] = None
    name: str = ""
    code: str = ""  # Mã đơn vị
    parent_id: Optional[int] = None  # Đơn vị cấp trên
    level: int = 0  # Cấp đơn vị (0: cao nhất, 1, 2, 3... cấp thấp hơn)
    address: str = ""
    phone: str = ""
    commander: str = ""  # Chỉ huy
    description: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Transient field for display
    parent_name: str = ""
    
    def __post_init__(self):
        self.db = Database()
    
    def save(self) -> int:
        """Save unit to database (insert or update)"""
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        """Insert new unit"""
        query = '''
            INSERT INTO units 
            (name, code, parent_id, level, address, phone, commander, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            self.name, self.code, self.parent_id, self.level,
            self.address, self.phone, self.commander, self.description,
            1 if self.is_active else 0
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        """Update existing unit"""
        query = '''
            UPDATE units SET
                name = ?, code = ?, parent_id = ?, level = ?,
                address = ?, phone = ?, commander = ?, description = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        params = (
            self.name, self.code, self.parent_id, self.level,
            self.address, self.phone, self.commander, self.description,
            1 if self.is_active else 0, self.id
        )
        self.db.execute(query, params)
        return self.id
    
    def delete(self) -> bool:
        """Delete unit from database (soft delete)"""
        if not self.id:
            return False
        # Soft delete - just mark as inactive
        query = "UPDATE units SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    def hard_delete(self) -> bool:
        """Permanently delete unit from database"""
        if not self.id:
            return False
        query = "DELETE FROM units WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    @classmethod
    def get_by_id(cls, unit_id: int) -> Optional['Unit']:
        """Get unit by ID"""
        db = Database()
        row = db.fetch_one("SELECT * FROM units WHERE id = ?", (unit_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional['Unit']:
        """Get unit by code"""
        db = Database()
        row = db.fetch_one("SELECT * FROM units WHERE code = ?", (code,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_all(cls, include_inactive: bool = False) -> List['Unit']:
        """Get all units with parent name"""
        db = Database()
        if include_inactive:
            rows = db.fetch_all("""
                SELECT u.*, p.name as parent_name 
                FROM units u 
                LEFT JOIN units p ON u.parent_id = p.id 
                ORDER BY u.level, u.name
            """)
        else:
            rows = db.fetch_all("""
                SELECT u.*, p.name as parent_name 
                FROM units u 
                LEFT JOIN units p ON u.parent_id = p.id 
                WHERE u.is_active = 1 
                ORDER BY u.level, u.name
            """)
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_level(cls, level: int) -> List['Unit']:
        """Get units by level"""
        db = Database()
        rows = db.fetch_all(
            "SELECT * FROM units WHERE level = ? AND is_active = 1 ORDER BY name",
            (level,)
        )
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_potential_parents(cls, current_level: int, exclude_id: int = None) -> List['Unit']:
        """Get units that can be parent (level must be < current_level)
        For level 0: no parents available
        For level 1: only level 0 units can be parent
        For level 2: only level 0, 1 units can be parent, etc.
        """
        if current_level == 0:
            return []  # Level 0 has no parent
        
        db = Database()
        if exclude_id:
            rows = db.fetch_all(
                "SELECT * FROM units WHERE level < ? AND is_active = 1 AND id != ? ORDER BY level, name",
                (current_level, exclude_id)
            )
        else:
            rows = db.fetch_all(
                "SELECT * FROM units WHERE level < ? AND is_active = 1 ORDER BY level, name",
                (current_level,)
            )
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_parent(cls, parent_id: int) -> List['Unit']:
        """Get child units"""
        db = Database()
        rows = db.fetch_all(
            "SELECT * FROM units WHERE parent_id = ? AND is_active = 1 ORDER BY name",
            (parent_id,)
        )
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_children(cls, parent_id: int) -> List['Unit']:
        """Alias for get_by_parent - Get child units of a parent"""
        return cls.get_by_parent(parent_id)
    
    @classmethod
    def get_top_level(cls) -> List['Unit']:
        """Get top-level units (no parent)"""
        db = Database()
        rows = db.fetch_all(
            "SELECT * FROM units WHERE parent_id IS NULL AND is_active = 1 ORDER BY name"
        )
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def search(cls, keyword: str) -> List['Unit']:
        """Search units by name or code"""
        db = Database()
        search_pattern = f"%{keyword}%"
        rows = db.fetch_all('''
            SELECT * FROM units 
            WHERE (name LIKE ? OR code LIKE ?) AND is_active = 1
            ORDER BY level, name
        ''', (search_pattern, search_pattern))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def count(cls, include_inactive: bool = False) -> int:
        """Get total unit count"""
        db = Database()
        if include_inactive:
            row = db.fetch_one("SELECT COUNT(*) as count FROM units")
        else:
            row = db.fetch_one("SELECT COUNT(*) as count FROM units WHERE is_active = 1")
        return row['count'] if row else 0
    
    @classmethod
    def code_exists(cls, code: str, exclude_id: int = None) -> bool:
        """Check if unit code already exists"""
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM units WHERE code = ? AND id != ?",
                (code, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM units WHERE code = ?",
                (code,)
            )
        return row is not None
    
    @classmethod
    def _from_row(cls, row) -> 'Unit':
        """Create Unit instance from database row"""
        unit = cls()
        unit.id = row['id']
        unit.name = row['name']
        unit.code = row['code'] or ""
        unit.parent_id = row['parent_id']
        unit.level = row['level'] if row['level'] is not None else 0
        unit.address = row['address'] or ""
        unit.phone = row['phone'] or ""
        unit.commander = row['commander'] or ""
        unit.description = row['description'] or ""
        unit.is_active = bool(row['is_active'])
        unit.created_at = row['created_at']
        unit.updated_at = row['updated_at']
        # Handle parent_name from JOIN query
        try:
            unit.parent_name = row['parent_name'] or ""
        except (KeyError, IndexError):
            unit.parent_name = ""
        return unit
    
    def get_parent(self) -> Optional['Unit']:
        """Get parent unit"""
        if self.parent_id:
            return Unit.get_by_id(self.parent_id)
        return None
    
    def get_child_units(self) -> List['Unit']:
        """Get child units of this unit (instance method)"""
        if self.id:
            return Unit.get_by_parent(self.id)
        return []
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'parent_id': self.parent_id,
            'level': self.level,
            'address': self.address,
            'phone': self.phone,
            'commander': self.commander,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.code})" if self.code else self.name


# Unit level descriptions (for display)
def get_level_name(level: int) -> str:
    """Get display name for unit level"""
    return f"Cấp {level}"


# Keep for backward compatibility but deprecated
UNIT_LEVELS = {
    0: "Cấp 0 (Cao nhất)",
    1: "Cấp 1",
    2: "Cấp 2", 
    3: "Cấp 3",
    4: "Cấp 4",
    5: "Cấp 5"
}
