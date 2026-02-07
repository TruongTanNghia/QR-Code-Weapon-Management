"""
Category Controller - Business logic for equipment categories
"""
from typing import List, Optional
from ..models.category import Category


class CategoryController:
    """
    Controller for managing equipment categories
    """
    
    @staticmethod
    def get_all_categories(include_inactive: bool = False) -> List[Category]:
        """
        Get all categories
        
        Args:
            include_inactive: Include inactive categories
            
        Returns:
            List of Category objects
        """
        return Category.get_all(include_inactive=include_inactive)
    
    @staticmethod
    def get_active_categories() -> List[Category]:
        """
        Get only active categories (for dropdowns)
        
        Returns:
            List of active Category objects
        """
        return Category.get_all(include_inactive=False)
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """
        Get a category by ID
        
        Args:
            category_id: The category ID
            
        Returns:
            Category object or None
        """
        return Category.get_by_id(category_id)
    
    @staticmethod
    def get_category_by_name(name: str) -> Optional[Category]:
        """
        Get a category by name
        
        Args:
            name: The category name
            
        Returns:
            Category object or None
        """
        return Category.get_by_name(name)
    
    @staticmethod
    def create_category(name: str, code: str = None, description: str = None) -> Category:
        """
        Create a new category
        
        Args:
            name: Category name (required)
            code: Category code (optional)
            description: Category description (optional)
            
        Returns:
            Created Category object
            
        Raises:
            ValueError: If name already exists
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Tên loại trang bị không được để trống")
        
        name = name.strip()
        
        # Check if name exists
        if Category.name_exists(name):
            raise ValueError(f"Loại trang bị '{name}' đã tồn tại")
        
        # Check if code exists
        if code and Category.code_exists(code.strip()):
            raise ValueError(f"Mã loại trang bị '{code}' đã tồn tại")
        
        # Create category
        category = Category(
            name=name,
            code=code.strip() if code else None,
            description=description.strip() if description else None,
            is_active=True
        )
        category.save()
        
        return category
    
    @staticmethod
    def update_category(category_id: int, name: str = None, code: str = None, 
                       description: str = None, is_active: bool = None) -> Optional[Category]:
        """
        Update an existing category
        
        Args:
            category_id: ID of category to update
            name: New name (optional)
            code: New code (optional)
            description: New description (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated Category object or None if not found
            
        Raises:
            ValueError: If validation fails
        """
        category = Category.get_by_id(category_id)
        if not category:
            return None
        
        # Update name if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Tên loại trang bị không được để trống")
            if Category.name_exists(name, category_id):
                raise ValueError(f"Loại trang bị '{name}' đã tồn tại")
            category.name = name
        
        # Update code if provided
        if code is not None:
            code = code.strip() if code else None
            if code and Category.code_exists(code, category_id):
                raise ValueError(f"Mã loại trang bị '{code}' đã tồn tại")
            category.code = code
        
        # Update description if provided
        if description is not None:
            category.description = description.strip() if description else None
        
        # Update active status if provided
        if is_active is not None:
            category.is_active = is_active
        
        category.save()
        return category
    
    @staticmethod
    def delete_category(category_id: int) -> bool:
        """
        Delete (soft delete) a category
        
        Args:
            category_id: ID of category to delete
            
        Returns:
            True if deleted, False if not found
        """
        category = Category.get_by_id(category_id)
        if not category:
            return False
        
        category.delete()
        return True
    
    @staticmethod
    def get_category_names() -> List[str]:
        """
        Get list of all active category names (for dropdowns)
        
        Returns:
            List of category names
        """
        categories = Category.get_all(include_inactive=False)
        return [cat.name for cat in categories]
    
    @staticmethod
    def search_categories(keyword: str) -> List[Category]:
        """
        Search categories by name or code
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching Category objects
        """
        return Category.search(keyword)
    
    @staticmethod
    def initialize_default_categories():
        """
        Initialize default categories if not exist
        """
        Category.initialize_default_categories()
    
    @staticmethod
    def get_equipment_count(category_id: int) -> int:
        """
        Get count of equipment using this category
        
        Args:
            category_id: The category ID
            
        Returns:
            Count of equipment
        """
        category = Category.get_by_id(category_id)
        if category:
            return category.get_equipment_count()
        return 0
