"""
Database connection and initialization module
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Any
from contextlib import contextmanager

from ..config import DATABASE_PATH


class Database:
    """
    SQLite Database Manager with connection pooling and context management
    """
    _instance: Optional['Database'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.db_path = DATABASE_PATH
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
        self._initialized = True
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Categories table (Loại trang bị)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    code TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Units table (Đơn vị)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    code TEXT UNIQUE,
                    parent_id INTEGER,
                    level INTEGER DEFAULT 0,
                    address TEXT,
                    phone TEXT,
                    commander TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES units(id) ON DELETE SET NULL
                )
            ''')
            
            # Users table (Người dùng)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    phone TEXT,
                    role TEXT DEFAULT 'viewer',
                    unit_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Equipment table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    serial_number TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    manufacturer TEXT,
                    manufacture_year INTEGER,
                    status TEXT DEFAULT 'Trong kho',
                    unit_id INTEGER,
                    location TEXT,
                    description TEXT,
                    qr_code_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Maintenance log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    maintenance_type TEXT NOT NULL,
                    description TEXT,
                    technician_id INTEGER,
                    technician_name TEXT,
                    status TEXT DEFAULT 'Đang thực hiện',
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
                    FOREIGN KEY (technician_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Maintenance types table (Loại công việc bảo dưỡng)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    code TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Loan log table (Quản lý cho mượn)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loan_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    borrower_unit TEXT NOT NULL,
                    loan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expected_return_date TIMESTAMP,
                    return_date TIMESTAMP,
                    status TEXT DEFAULT 'Đang mượn',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Add new columns to equipment table if not exists
            # receive_date: Ngày cấp phát/nhập kho
            # loan_status: Trạng thái cho mượn (Đang ở kho / Đã cho mượn)
            try:
                cursor.execute('ALTER TABLE equipment ADD COLUMN receive_date TIMESTAMP')
            except:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE equipment ADD COLUMN loan_status TEXT DEFAULT 'Đang ở kho'")
            except:
                pass  # Column already exists
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_units_code 
                ON units(code)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_role 
                ON users(role)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_serial 
                ON equipment(serial_number)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_status 
                ON equipment(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_unit 
                ON equipment(unit_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_maintenance_equipment 
                ON maintenance_log(equipment_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_loan_equipment 
                ON loan_log(equipment_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_loan_status 
                ON loan_log(status)
            ''')
            
            conn.commit()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def insert(self, query: str, params: tuple = ()) -> int:
        """Insert and return the last row id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def get_statistics(self) -> dict:
        """Get database statistics for dashboard"""
        stats = {}
        
        # Total equipment count
        row = self.fetch_one("SELECT COUNT(*) as count FROM equipment")
        stats['total_equipment'] = row['count'] if row else 0
        
        # Equipment by status
        rows = self.fetch_all('''
            SELECT status, COUNT(*) as count 
            FROM equipment 
            GROUP BY status
        ''')
        stats['by_status'] = {row['status']: row['count'] for row in rows}
        
        # Equipment by category
        rows = self.fetch_all('''
            SELECT category, COUNT(*) as count 
            FROM equipment 
            GROUP BY category
        ''')
        stats['by_category'] = {row['category']: row['count'] for row in rows}
        
        # Active maintenance count
        row = self.fetch_one('''
            SELECT COUNT(*) as count 
            FROM maintenance_log 
            WHERE status = 'Đang thực hiện'
        ''')
        stats['active_maintenance'] = row['count'] if row else 0
        
        # Active loans count
        row = self.fetch_one('''
            SELECT COUNT(*) as count 
            FROM loan_log 
            WHERE status = 'Đang mượn'
        ''')
        stats['active_loans'] = row['count'] if row else 0
        
        # Equipment by loan_status
        rows = self.fetch_all('''
            SELECT loan_status, COUNT(*) as count 
            FROM equipment 
            GROUP BY loan_status
        ''')
        stats['by_loan_status'] = {row['loan_status']: row['count'] for row in rows}
        
        # Recent activities
        rows = self.fetch_all('''
            SELECT e.name, m.maintenance_type, m.start_date
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            ORDER BY m.start_date DESC
            LIMIT 5
        ''')
        stats['recent_activities'] = [dict(row) for row in rows]
        
        return stats
