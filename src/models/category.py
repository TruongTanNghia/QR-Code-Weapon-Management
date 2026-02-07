"""
Category Model - Represents equipment categories
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from .database import Database


@dataclass
class Category:
    """
    Data class representing an equipment category
    """
    id: Optional[int] = None
    name: str = ""
    code: str = ""  # Mã loại
    description: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        self.db = Database()
    
    def save(self) -> int:
        """Save category to database (insert or update)"""
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        """Insert new category"""
        query = '''
            INSERT INTO categories (name, code, description, is_active)
            VALUES (?, ?, ?, ?)
        '''
        params = (
            self.name, self.code, self.description,
            1 if self.is_active else 0
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        """Update existing category"""
        query = '''
            UPDATE categories SET
                name = ?, code = ?, description = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        params = (
            self.name, self.code, self.description,
            1 if self.is_active else 0, self.id
        )
        self.db.execute(query, params)
        return self.id
    
    def delete(self) -> bool:
        """Delete category (soft delete)"""
        if not self.id:
            return False
        query = "UPDATE categories SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    def hard_delete(self) -> bool:
        """Permanently delete category"""
        if not self.id:
            return False
        query = "DELETE FROM categories WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True

    def get_equipment_count(self) -> int:
        """
        [MỚI] Get count of equipment belonging to this category
        """
        if not self.name:
            return 0
        # Lưu ý: Bảng equipment liên kết với category bằng TÊN (string) chứ không phải ID
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM equipment WHERE category = ?", 
            (self.name,)
        )
        return row['count'] if row else 0
    
    @classmethod
    def get_by_id(cls, category_id: int) -> Optional['Category']:
        """Get category by ID"""
        db = Database()
        row = db.fetch_one("SELECT * FROM categories WHERE id = ?", (category_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['Category']:
        """Get category by name"""
        db = Database()
        row = db.fetch_one("SELECT * FROM categories WHERE name = ?", (name,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_all(cls, include_inactive: bool = False) -> List['Category']:
        """Get all categories"""
        db = Database()
        if include_inactive:
            rows = db.fetch_all("SELECT * FROM categories ORDER BY id")
        else:
            rows = db.fetch_all("SELECT * FROM categories WHERE is_active = 1 ORDER BY id")
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def search(cls, keyword: str) -> List['Category']:
        """Search categories by name or code"""
        db = Database()
        search_pattern = f"%{keyword}%"
        rows = db.fetch_all('''
            SELECT * FROM categories 
            WHERE (name LIKE ? OR code LIKE ?) AND is_active = 1
            ORDER BY name
        ''', (search_pattern, search_pattern))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def count(cls, include_inactive: bool = False) -> int:
        """Get total category count"""
        db = Database()
        if include_inactive:
            row = db.fetch_one("SELECT COUNT(*) as count FROM categories")
        else:
            row = db.fetch_one("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
        return row['count'] if row else 0
    
    @classmethod
    def name_exists(cls, name: str, exclude_id: int = None) -> bool:
        """Check if category name already exists"""
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM categories WHERE name = ? AND id != ?",
                (name, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM categories WHERE name = ?",
                (name,)
            )
        return row is not None

    @classmethod
    def code_exists(cls, code: str, exclude_id: int = None) -> bool:
        """Check if category code already exists"""
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM categories WHERE code = ? AND id != ?",
                (code, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM categories WHERE code = ?",
                (code,)
            )
        return row is not None
    
    @classmethod
    def _from_row(cls, row) -> 'Category':
        """Create Category instance from database row"""
        category = cls()
        category.id = row['id']
        category.name = row['name']
        category.code = row['code'] or ""
        category.description = row['description'] or ""
        category.is_active = bool(row['is_active'])
        category.created_at = row['created_at']
        category.updated_at = row['updated_at']
        return category
    
    @classmethod
    def initialize_default_categories(cls):
        """Initialize default categories if table is empty"""
        if cls.count(include_inactive=True) == 0:
            default_categories = [
                ("Súng ngắn", "SN", "Các loại súng ngắn"),
                ("Súng trường", "ST", "Các loại súng trường"),
                ("Súng máy", "SM", "Các loại súng máy"),
                ("Súng phóng lựu", "SPL", "Các loại súng phóng lựu"),
                ("Khí tài quang học", "KTQH", "Ống nhòm, kính ngắm..."),
                ("Khí tài thông tin", "KTTT", "Máy bộ đàm, điện thoại quân sự..."),
                ("Phương tiện vận tải", "PTVT", "Xe quân sự, xe tải..."),
                ("Trang bị bảo hộ", "TBBH", "Mũ, áo giáp, găng tay..."),
                ("Khác", "K", "Các loại trang bị khác"),
            ]
            for name, code, desc in default_categories:
                cat = cls()
                cat.name = name
                cat.code = code
                cat.description = desc
                cat.save()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None
        }
    
    def __str__(self) -> str:
        return self.name