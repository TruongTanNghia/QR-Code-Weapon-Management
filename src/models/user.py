"""
User Model - Represents system users with authentication
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import hashlib
import secrets
from .database import Database


# User roles
class UserRole:
    SUPERADMIN = "superadmin" # Quản trị viên cao cấp (Không thể xóa)
    ADMIN = "admin"           # Quản trị viên hệ thống
    MANAGER = "manager"       # Quản lý kho
    VIEWER = "viewer"         # Người xem


# Role permissions
ROLE_PERMISSIONS = {
    UserRole.SUPERADMIN: {
        'manage_users': True,
        'manage_units': True,
        'manage_equipment': True,
        'manage_categories': True,
        'manage_maintenance': True,
        'manage_maintenance_types': True,
        'export_reports': True,
        'view_all': True,
        'delete_data': True,
        'system_settings': True,
        'scan_qr': True
    },
    UserRole.ADMIN: {
        'manage_users': True,
        'manage_units': True,
        'manage_equipment': True,
        'manage_categories': True,
        'manage_maintenance': True,
        'manage_maintenance_types': True,
        'export_reports': True,
        'view_all': True,
        'delete_data': True,
        'system_settings': False, # Admin thường không chỉnh cài đặt hệ thống sâu
        'scan_qr': True
    },
    UserRole.MANAGER: {
        'manage_users': False,
        'manage_units': True,
        'manage_equipment': True,
        'manage_categories': True,
        'manage_maintenance': True,
        'manage_maintenance_types': True,
        'export_reports': True,
        'view_all': True,
        'delete_data': True,
        'system_settings': False,
        'scan_qr': True
    },
    UserRole.VIEWER: {
        'manage_users': False,
        'manage_units': False,
        'manage_equipment': False,
        'manage_categories': False,
        'manage_maintenance': False,
        'manage_maintenance_types': False,
        'export_reports': False,
        'view_all': False,
        'delete_data': False,
        'system_settings': False,
        'scan_qr': True
    }
}


ROLE_DISPLAY_NAMES = {
    UserRole.SUPERADMIN: "Quản trị viên cao cấp",
    UserRole.ADMIN: "Quản trị viên",
    UserRole.MANAGER: "Quản lý kho",
    UserRole.VIEWER: "Người xem"
}


@dataclass
class User:
    """
    Data class representing a system user
    """
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    salt: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    role: str = UserRole.VIEWER
    unit_id: Optional[int] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    def __post_init__(self):
        self.db = Database()
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        if salt is None:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return password_hash, salt
    
    def set_password(self, password: str):
        self.password_hash, self.salt = self.hash_password(password)
    
    def verify_password(self, password: str) -> bool:
        password_hash, _ = self.hash_password(password, self.salt)
        return password_hash == self.password_hash
    
    def save(self) -> int:
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        query = '''
            INSERT INTO users 
            (username, password_hash, salt, full_name, email, phone, 
             role, unit_id, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            self.username, self.password_hash, self.salt, self.full_name,
            self.email, self.phone, self.role, self.unit_id,
            1 if self.is_active else 0, self.created_by
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        query = '''
            UPDATE users SET
                username = ?, full_name = ?, email = ?, phone = ?,
                role = ?, unit_id = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        params = (
            self.username, self.full_name, self.email, self.phone,
            self.role, self.unit_id, 1 if self.is_active else 0, self.id
        )
        self.db.execute(query, params)
        return self.id
    
    def update_password(self, new_password: str) -> bool:
        if not self.id:
            return False
        self.set_password(new_password)
        query = '''
            UPDATE users SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        self.db.execute(query, (self.password_hash, self.salt, self.id))
        return True
    
    def update_last_login(self):
        if not self.id:
            return
        query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (self.id,))
    
    def delete(self) -> bool:
        if not self.id:
            return False
        # Không cho phép xóa Superadmin bằng bất cứ giá nào
        if self.role == UserRole.SUPERADMIN:
            return False
        query = "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    def hard_delete(self) -> bool:
        if not self.id:
            return False
        if self.role == UserRole.SUPERADMIN:
            return False
        query = "DELETE FROM users WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    def has_permission(self, permission: str) -> bool:
        if self.role in ROLE_PERMISSIONS:
            return ROLE_PERMISSIONS[self.role].get(permission, False)
        return False
    
    def get_role_display(self) -> str:
        return ROLE_DISPLAY_NAMES.get(self.role, self.role)
    
    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        user = cls.get_by_username(username)
        if user and user.is_active and user.verify_password(password):
            user.update_last_login()
            return user
        return None
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        db = Database()
        row = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        db = Database()
        row = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_all(cls, include_inactive: bool = False) -> List['User']:
        db = Database()
        # Sắp xếp role để Superadmin/Admin lên đầu
        if include_inactive:
            rows = db.fetch_all("SELECT * FROM users ORDER BY CASE WHEN role='superadmin' THEN 1 WHEN role='admin' THEN 2 ELSE 3 END, full_name")
        else:
            rows = db.fetch_all("SELECT * FROM users WHERE is_active = 1 ORDER BY CASE WHEN role='superadmin' THEN 1 WHEN role='admin' THEN 2 ELSE 3 END, full_name")
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_role(cls, role: str) -> List['User']:
        db = Database()
        rows = db.fetch_all(
            "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY full_name",
            (role,)
        )
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_unit(cls, unit_id: int) -> List['User']:
        db = Database()
        rows = db.fetch_all(
            "SELECT * FROM users WHERE unit_id = ? AND is_active = 1 ORDER BY full_name",
            (unit_id,)
        )
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def search(cls, keyword: str) -> List['User']:
        db = Database()
        search_pattern = f"%{keyword}%"
        rows = db.fetch_all('''
            SELECT * FROM users 
            WHERE (username LIKE ? OR full_name LIKE ? OR email LIKE ?) AND is_active = 1
            ORDER BY full_name
        ''', (search_pattern, search_pattern, search_pattern))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def count(cls, include_inactive: bool = False) -> int:
        db = Database()
        if include_inactive:
            row = db.fetch_one("SELECT COUNT(*) as count FROM users")
        else:
            row = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
        return row['count'] if row else 0
    
    @classmethod
    def username_exists(cls, username: str, exclude_id: int = None) -> bool:
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM users WHERE username = ? AND id != ?",
                (username, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )
        return row is not None
    
    @classmethod
    def create_default_admin(cls, username: str = "admin", password: str = "admin123"):
        """Create default superadmin if not exists"""
        db = Database()
        # Chỉ kiểm tra role superadmin
        row = db.fetch_one("SELECT id FROM users WHERE role = ?", (UserRole.SUPERADMIN,))
        if row:
            return None # Đã có superadmin
        
        # Nếu chưa có superadmin nhưng có user 'admin' (do migrate), nâng cấp nó lên
        existing = db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            db.execute("UPDATE users SET role = ? WHERE id = ?", (UserRole.SUPERADMIN, existing['id']))
            return None

        # Tạo mới
        user = cls()
        user.username = username
        user.set_password(password)
        user.full_name = "Quản trị viên cao cấp"
        user.role = UserRole.SUPERADMIN
        user.is_active = True
        user.save()
        return user
    
    @classmethod
    def _from_row(cls, row) -> 'User':
        user = cls()
        user.id = row['id']
        user.username = row['username']
        user.password_hash = row['password_hash']
        user.salt = row['salt']
        user.full_name = row['full_name'] or ""
        user.email = row['email'] or ""
        user.phone = row['phone'] or ""
        user.role = row['role']
        user.unit_id = row['unit_id']
        user.is_active = bool(row['is_active'])
        user.last_login = row['last_login']
        user.created_at = row['created_at']
        user.updated_at = row['updated_at']
        user.created_by = row['created_by']
        return user
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'role_display': self.get_role_display(),
            'unit_id': self.unit_id,
            'is_active': self.is_active,
            'last_login': str(self.last_login) if self.last_login else None,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
            data['salt'] = self.salt
        return data
    
    def __str__(self) -> str:
        return f"{self.full_name} ({self.username})"