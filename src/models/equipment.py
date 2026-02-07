"""
Equipment Model - Represents a weapon/equipment item
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from .database import Database


@dataclass
class Equipment:
    """
    Data class representing a weapon/equipment item
    """
    id: Optional[int] = None
    name: str = ""
    serial_number: str = ""
    category: str = ""
    manufacturer: str = ""
    manufacture_year: Optional[int] = None
    status: str = "Trong kho"
    unit_id: Optional[int] = None  # Foreign key to units table
    location: str = ""
    description: str = ""
    qr_code_path: str = ""
    receive_date: Optional[datetime] = None  # Ngày cấp phát/nhập kho
    loan_status: str = "Đang ở kho"  # Trạng thái cho mượn: Đang ở kho / Đã cho mượn
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None  # Foreign key to users table
    
    # Transient fields (not stored in DB directly)
    unit_name: str = ""  # For display purposes
    
    def __post_init__(self):
        self.db = Database()
    
    def save(self) -> int:
        """Save equipment to database (insert or update)"""
        if self.id:
            return self._update()
        else:
            return self._insert()
    
    def _insert(self) -> int:
        """Insert new equipment"""
        query = '''
            INSERT INTO equipment 
            (name, serial_number, category, manufacturer, manufacture_year, 
             status, unit_id, location, description, qr_code_path, 
             receive_date, loan_status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            self.name, self.serial_number, self.category, self.manufacturer,
            self.manufacture_year, self.status, self.unit_id, self.location,
            self.description, self.qr_code_path, self.receive_date, 
            self.loan_status, self.created_by
        )
        self.id = self.db.insert(query, params)
        return self.id
    
    def _update(self) -> int:
        """Update existing equipment"""
        query = '''
            UPDATE equipment SET
                name = ?, serial_number = ?, category = ?, manufacturer = ?,
                manufacture_year = ?, status = ?, unit_id = ?, location = ?,
                description = ?, qr_code_path = ?, receive_date = ?, 
                loan_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        params = (
            self.name, self.serial_number, self.category, self.manufacturer,
            self.manufacture_year, self.status, self.unit_id, self.location,
            self.description, self.qr_code_path, self.receive_date,
            self.loan_status, self.id
        )
        self.db.execute(query, params)
        return self.id
    
    def delete(self) -> bool:
        """Delete equipment from database"""
        if not self.id:
            return False
        query = "DELETE FROM equipment WHERE id = ?"
        self.db.execute(query, (self.id,))
        return True
    
    @classmethod
    def get_by_id(cls, equipment_id: int) -> Optional['Equipment']:
        """Get equipment by ID"""
        db = Database()
        row = db.fetch_one('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.id = ?
        ''', (equipment_id,))
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_by_serial(cls, serial_number: str) -> Optional['Equipment']:
        """Get equipment by serial number"""
        db = Database()
        row = db.fetch_one(
            "SELECT * FROM equipment WHERE serial_number = ?", 
            (serial_number,)
        )
        if row:
            return cls._from_row(row)
        return None
    
    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List['Equipment']:
        """Get all equipment with pagination"""
        db = Database()
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            ORDER BY e.created_at DESC LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def search(cls, keyword: str) -> List['Equipment']:
        """Search equipment by name or serial number"""
        db = Database()
        search_pattern = f"%{keyword}%"
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.name LIKE ? OR e.serial_number LIKE ? OR e.category LIKE ?
            ORDER BY e.name
        ''', (search_pattern, search_pattern, search_pattern))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_status(cls, status: str) -> List['Equipment']:
        """Get equipment by status"""
        db = Database()
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.status = ? ORDER BY e.name
        ''', (status,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_category(cls, category: str) -> List['Equipment']:
        """Get equipment by category"""
        db = Database()
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.category = ? ORDER BY e.name
        ''', (category,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_unit(cls, unit_id: int) -> List['Equipment']:
        """Get equipment by unit"""
        db = Database()
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.unit_id = ? ORDER BY e.name
        ''', (unit_id,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_by_date_range(cls, start_date: datetime, end_date: datetime) -> List['Equipment']:
        """[MỚI] Get equipment by receive date range"""
        db = Database()
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.receive_date BETWEEN ? AND ?
            ORDER BY e.receive_date DESC
        ''', (start_date, end_date))
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_by_loan_status(cls, loan_status: str) -> List['Equipment']:
        """Get equipment by loan status"""
        db = Database()
        rows = db.fetch_all('''
            SELECT e.*, u.name as unit_name 
            FROM equipment e 
            LEFT JOIN units u ON e.unit_id = u.id 
            WHERE e.loan_status = ? ORDER BY e.name
        ''', (loan_status,))
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_available_for_loan(cls) -> List['Equipment']:
        """Get equipment that is available for loan (Đang ở kho)"""
        return cls.get_by_loan_status("Đang ở kho")
    
    def update_loan_status(self, new_status: str) -> bool:
        """Update loan status for this equipment"""
        if not self.id:
            return False
        self.loan_status = new_status
        query = "UPDATE equipment SET loan_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (new_status, self.id))
        return True
    
    @classmethod
    def count(cls) -> int:
        """Get total equipment count"""
        db = Database()
        row = db.fetch_one("SELECT COUNT(*) as count FROM equipment")
        return row['count'] if row else 0
    
    @classmethod
    def serial_exists(cls, serial_number: str, exclude_id: int = None) -> bool:
        """Check if serial number already exists"""
        db = Database()
        if exclude_id:
            row = db.fetch_one(
                "SELECT id FROM equipment WHERE serial_number = ? AND id != ?",
                (serial_number, exclude_id)
            )
        else:
            row = db.fetch_one(
                "SELECT id FROM equipment WHERE serial_number = ?",
                (serial_number,)
            )
        return row is not None
    
    @classmethod
    def _from_row(cls, row) -> 'Equipment':
        """Create Equipment instance from database row"""
        equipment = cls()
        equipment.id = row['id']
        equipment.name = row['name']
        equipment.serial_number = row['serial_number']
        equipment.category = row['category']
        equipment.manufacturer = row['manufacturer'] or ""
        equipment.manufacture_year = row['manufacture_year']
        equipment.status = row['status']
        equipment.unit_id = row['unit_id']
        equipment.location = row['location'] or ""
        equipment.description = row['description'] or ""
        equipment.qr_code_path = row['qr_code_path'] or ""
        equipment.receive_date = row['receive_date'] if 'receive_date' in row.keys() else None
        equipment.loan_status = row['loan_status'] if 'loan_status' in row.keys() else "Đang ở kho"
        equipment.created_at = row['created_at']
        equipment.updated_at = row['updated_at']
        # Handle unit_name from JOIN query
        try:
            equipment.unit_name = row['unit_name'] or ""
        except (KeyError, IndexError):
            equipment.unit_name = ""
        return equipment
    
    def get_unit(self):
        """Get the unit object for this equipment"""
        if self.unit_id:
            from .unit import Unit
            return Unit.get_by_id(self.unit_id)
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'serial_number': self.serial_number,
            'category': self.category,
            'manufacturer': self.manufacturer,
            'manufacture_year': self.manufacture_year,
            'status': self.status,
            'unit_id': self.unit_id,
            'unit_name': self.unit_name,
            'location': self.location,
            'description': self.description,
            'qr_code_path': self.qr_code_path,
            'receive_date': str(self.receive_date) if self.receive_date else None,
            'loan_status': self.loan_status,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None
        }