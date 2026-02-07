"""
Maintenance Type Controller - Business logic for maintenance work types
"""
from typing import List, Optional
from ..models.maintenance_type import MaintenanceType, DEFAULT_MAINTENANCE_TYPES


class MaintenanceTypeController:
    """
    Controller for managing maintenance work types
    """
    
    @staticmethod
    def get_all_types(include_inactive: bool = False) -> List[MaintenanceType]:
        """
        Get all maintenance types
        
        Args:
            include_inactive: Include inactive types
            
        Returns:
            List of MaintenanceType objects
        """
        return MaintenanceType.get_all(include_inactive=include_inactive)
    
    @staticmethod
    def get_active_types() -> List[MaintenanceType]:
        """
        Get only active maintenance types (for dropdowns)
        
        Returns:
            List of active MaintenanceType objects
        """
        return MaintenanceType.get_all(include_inactive=False)
    
    @staticmethod
    def get_type_by_id(type_id: int) -> Optional[MaintenanceType]:
        """
        Get a maintenance type by ID
        
        Args:
            type_id: The maintenance type ID
            
        Returns:
            MaintenanceType object or None
        """
        return MaintenanceType.get_by_id(type_id)
    
    @staticmethod
    def get_type_by_name(name: str) -> Optional[MaintenanceType]:
        """
        Get a maintenance type by name
        
        Args:
            name: The maintenance type name
            
        Returns:
            MaintenanceType object or None
        """
        return MaintenanceType.get_by_name(name)
    
    @staticmethod
    def create_type(name: str, code: str = None, description: str = None) -> MaintenanceType:
        """
        Create a new maintenance type
        
        Args:
            name: Type name (required)
            code: Type code (optional)
            description: Type description (optional)
            
        Returns:
            Created MaintenanceType object
            
        Raises:
            ValueError: If name already exists
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Tên loại công việc không được để trống")
        
        name = name.strip()
        
        # Check if name exists
        if MaintenanceType.name_exists(name):
            raise ValueError(f"Loại công việc '{name}' đã tồn tại")
        
        # Check if code exists
        if code and MaintenanceType.code_exists(code.strip()):
            raise ValueError(f"Mã loại công việc '{code}' đã tồn tại")
        
        # Create maintenance type
        mtype = MaintenanceType(
            name=name,
            code=code.strip() if code else None,
            description=description.strip() if description else None,
            is_active=True
        )
        mtype.save()
        
        return mtype
    
    @staticmethod
    def update_type(type_id: int, name: str = None, code: str = None, 
                   description: str = None, is_active: bool = None) -> MaintenanceType:
        """
        Update an existing maintenance type
        
        Args:
            type_id: The type ID to update
            name: New name (optional)
            code: New code (optional)
            description: New description (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated MaintenanceType object
            
        Raises:
            ValueError: If type not found or name already exists
        """
        mtype = MaintenanceType.get_by_id(type_id)
        if not mtype:
            raise ValueError("Không tìm thấy loại công việc")
        
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Tên loại công việc không được để trống")
            if MaintenanceType.name_exists(name, type_id):
                raise ValueError(f"Loại công việc '{name}' đã tồn tại")
            mtype.name = name
        
        if code is not None:
            code = code.strip() if code else None
            if code and MaintenanceType.code_exists(code, type_id):
                raise ValueError(f"Mã loại công việc '{code}' đã tồn tại")
            mtype.code = code
        
        if description is not None:
            mtype.description = description.strip() if description else None
        
        if is_active is not None:
            mtype.is_active = is_active
        
        mtype.save()
        return mtype
    
    @staticmethod
    def delete_type(type_id: int, force: bool = False) -> bool:
        """
        Delete a maintenance type (soft delete by default)
        
        Args:
            type_id: The type ID to delete
            force: If True, permanently delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If type not found or has maintenance logs
        """
        mtype = MaintenanceType.get_by_id(type_id)
        if not mtype:
            raise ValueError("Không tìm thấy loại công việc")
        
        # Check if type has maintenance logs
        count = mtype.get_maintenance_count()
        if count > 0 and not force:
            raise ValueError(
                f"Không thể xóa loại công việc này vì đang có {count} bản ghi bảo dưỡng sử dụng. "
                "Bạn có thể chuyển sang trạng thái ngừng sử dụng thay vì xóa."
            )
        
        if force:
            return mtype.hard_delete()
        else:
            return mtype.delete()
    
    @staticmethod
    def search_types(keyword: str, include_inactive: bool = False) -> List[MaintenanceType]:
        """
        Search maintenance types by keyword
        
        Args:
            keyword: Search keyword
            include_inactive: Include inactive types
            
        Returns:
            List of matching MaintenanceType objects
        """
        if not keyword or not keyword.strip():
            return MaintenanceType.get_all(include_inactive=include_inactive)
        return MaintenanceType.search(keyword.strip(), include_inactive)
    
    @staticmethod
    def initialize_default_types():
        """
        Initialize default maintenance types if table is empty
        """
        existing = MaintenanceType.get_all(include_inactive=True)
        if not existing:
            for name, code, description in DEFAULT_MAINTENANCE_TYPES:
                try:
                    mtype = MaintenanceType(
                        name=name,
                        code=code,
                        description=description,
                        is_active=True
                    )
                    mtype.save()
                except Exception as e:
                    print(f"Error creating default type {name}: {e}")
    
    @staticmethod
    def get_type_names() -> List[str]:
        """
        Get list of active maintenance type names for dropdowns
        
        Returns:
            List of maintenance type names
        """
        types = MaintenanceType.get_active_types()
        if types:
            return [t.name for t in types]
        # Fallback to defaults if no types in database
        return [t[0] for t in DEFAULT_MAINTENANCE_TYPES]
