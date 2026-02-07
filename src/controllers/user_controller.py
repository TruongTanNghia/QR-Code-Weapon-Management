"""
User Controller - Business logic for user management
"""
from typing import List, Optional
from ..models.user import User, UserRole, ROLE_PERMISSIONS, ROLE_DISPLAY_NAMES


class UserController:
    """Controller for user-related operations"""
    
    _current_user: Optional[User] = None
    
    @classmethod
    def set_current_user(cls, user: User):
        cls._current_user = user
    
    @classmethod
    def get_current_user(cls) -> Optional[User]:
        return cls._current_user
    
    @classmethod
    def logout(cls):
        cls._current_user = None
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        return User.authenticate(username, password)
    
    @staticmethod
    def get_all_users(include_inactive: bool = False) -> List[User]:
        return User.get_all(include_inactive=include_inactive)
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        return User.get_by_id(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        return User.get_by_username(username)
    
    @staticmethod
    def search_users(keyword: str) -> List[User]:
        return User.search(keyword)
    
    @staticmethod
    def get_users_by_role(role: str) -> List[User]:
        return User.get_by_role(role)
    
    @staticmethod
    def get_users_by_unit(unit_id: int) -> List[User]:
        return User.get_by_unit(unit_id)
    
    @staticmethod
    def create_user(username: str, password: str, full_name: str = "",
                    email: str = "", phone: str = "", role: str = UserRole.VIEWER,
                    unit_id: int = None, created_by: int = None) -> User:
        user = User()
        user.username = username
        user.set_password(password)
        user.full_name = full_name
        user.email = email
        user.phone = phone
        user.role = role
        user.unit_id = unit_id
        user.is_active = True
        user.created_by = created_by
        user.save()
        return user
    
    @staticmethod
    def update_user(user_id: int, **kwargs) -> Optional[User]:
        user = User.get_by_id(user_id)
        if not user:
            return None
        
        password = kwargs.pop('password', None)
        
        for key, value in kwargs.items():
            if hasattr(user, key) and key not in ['password_hash', 'salt']:
                setattr(user, key, value)
        
        user.save()
        
        if password:
            user.update_password(password)
        
        return user
    
    @staticmethod
    def change_password(user_id: int, new_password: str) -> bool:
        user = User.get_by_id(user_id)
        if not user:
            return False
        return user.update_password(new_password)
    
    @staticmethod
    def delete_user(user_id: int, hard_delete: bool = False) -> bool:
        user = User.get_by_id(user_id)
        if not user:
            return False
        
        # [QUAN TRỌNG] Không cho phép xóa Superadmin qua Controller
        if user.role == UserRole.SUPERADMIN:
            return False
        
        if hard_delete:
            return user.hard_delete()
        else:
            return user.delete()
    
    @staticmethod
    def get_user_count(include_inactive: bool = False) -> int:
        return User.count(include_inactive=include_inactive)
    
    @staticmethod
    def username_exists(username: str, exclude_id: int = None) -> bool:
        return User.username_exists(username, exclude_id)
    
    @staticmethod
    def create_superadmin(username: str = "admin", password: str = "admin123") -> Optional[User]:
        return User.create_default_admin(username, password)
    
    @staticmethod
    def get_available_roles() -> dict:
        return ROLE_DISPLAY_NAMES.copy()
    
    @staticmethod
    def get_role_permissions(role: str) -> dict:
        return ROLE_PERMISSIONS.get(role, {})
    
    @classmethod
    def has_permission(cls, permission: str) -> bool:
        if cls._current_user:
            return cls._current_user.has_permission(permission)
        return False
    
    @classmethod
    def is_superadmin(cls) -> bool:
        """Check if current user is superadmin"""
        if cls._current_user:
            return cls._current_user.role == UserRole.SUPERADMIN
        return False
    
    @classmethod
    def is_admin(cls) -> bool:
        """Check if current user is admin OR superadmin (has admin rights)"""
        if cls._current_user:
            return cls._current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]
        return False
    
    @staticmethod
    def get_users_for_dropdown() -> List[tuple]:
        users = User.get_all()
        return [(user.id, str(user)) for user in users]
    
    @staticmethod
    def get_technicians() -> List[User]:
        """Get users who can be technicians (Manager or Admin)"""
        # Trong mô hình này, Manager và Admin đều có thể là kỹ thuật viên
        managers = User.get_by_role(UserRole.MANAGER)
        admins = User.get_by_role(UserRole.ADMIN)
        return managers + admins