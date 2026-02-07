"""
Unit Controller - Business logic for unit management
"""
from typing import List, Optional
from ..models.unit import Unit, UNIT_LEVELS


class UnitController:
    """Controller for unit-related operations"""
    
    @staticmethod
    def get_all_units(include_inactive: bool = False) -> List[Unit]:
        """Get all units"""
        return Unit.get_all(include_inactive=include_inactive)
    
    @staticmethod
    def get_unit_by_id(unit_id: int) -> Optional[Unit]:
        """Get unit by ID"""
        return Unit.get_by_id(unit_id)
    
    @staticmethod
    def get_unit_by_code(code: str) -> Optional[Unit]:
        """Get unit by code"""
        return Unit.get_by_code(code)
    
    @staticmethod
    def search_units(keyword: str) -> List[Unit]:
        """Search units by keyword"""
        return Unit.search(keyword)
    
    @staticmethod
    def get_child_units(parent_id: int) -> List[Unit]:
        """Get child units of a parent unit"""
        return Unit.get_by_parent(parent_id)
    
    @staticmethod
    def get_top_level_units() -> List[Unit]:
        """Get units without parent"""
        return Unit.get_top_level()
    
    @staticmethod
    def create_unit(name: str, code: str = "", level: int = 1,
                    parent_id: int = None, commander: str = "",
                    phone: str = "", address: str = "",
                    description: str = "") -> Unit:
        """Create a new unit"""
        unit = Unit()
        unit.name = name
        unit.code = code
        unit.level = level
        unit.parent_id = parent_id
        unit.commander = commander
        unit.phone = phone
        unit.address = address
        unit.description = description
        unit.is_active = True
        unit.save()
        return unit
    
    @staticmethod
    def update_unit(unit_id: int, **kwargs) -> Optional[Unit]:
        """Update an existing unit"""
        unit = Unit.get_by_id(unit_id)
        if not unit:
            return None
        
        for key, value in kwargs.items():
            if hasattr(unit, key):
                setattr(unit, key, value)
        
        unit.save()
        return unit
    
    @staticmethod
    def delete_unit(unit_id: int, hard_delete: bool = False) -> bool:
        """Delete a unit (soft or hard delete)"""
        unit = Unit.get_by_id(unit_id)
        if not unit:
            return False
        
        if hard_delete:
            return unit.hard_delete()
        else:
            return unit.delete()
    
    @staticmethod
    def get_unit_count(include_inactive: bool = False) -> int:
        """Get total unit count"""
        return Unit.count(include_inactive=include_inactive)
    
    @staticmethod
    def code_exists(code: str, exclude_id: int = None) -> bool:
        """Check if unit code already exists"""
        return Unit.code_exists(code, exclude_id)
    
    @staticmethod
    def get_unit_levels() -> dict:
        """Get available unit levels"""
        return UNIT_LEVELS.copy()
    
    @staticmethod
    def get_units_for_dropdown() -> List[tuple]:
        """Get units formatted for dropdown/combobox"""
        units = Unit.get_all()
        return [(unit.id, str(unit)) for unit in units]
    
    @staticmethod
    def get_unit_hierarchy() -> List[dict]:
        """Get units in hierarchical structure"""
        def build_tree(parent_id=None, level=0):
            if parent_id:
                children = Unit.get_by_parent(parent_id)
            else:
                children = Unit.get_top_level()
            
            result = []
            for unit in children:
                node = {
                    'id': unit.id,
                    'name': unit.name,
                    'code': unit.code,
                    'level': level,
                    'unit_level': unit.level,
                    'children': build_tree(unit.id, level + 1)
                }
                result.append(node)
            return result
        
        return build_tree()
