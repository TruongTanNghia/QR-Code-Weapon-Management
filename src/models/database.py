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
            
            # Categories table
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
            
            # Units table
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
            
            # Users table
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
            
            # Maintenance types table
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
            
            # Loan log table
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

            # [MỚI] Audit Logs Table - Bảng ghi nhật ký hệ thống
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id INTEGER,
                    details TEXT,
                    ip_address TEXT DEFAULT 'localhost',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # [MỚI] Bảng lưu trữ đường dẫn Hình ảnh cho toàn hệ thống
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS item_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_type TEXT NOT NULL, 
                    target_id INTEGER NOT NULL, 
                    image_category TEXT DEFAULT 'general', -- [MỚI] 'before', 'after', 'general'
                    file_path TEXT NOT NULL,    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # [MỚI] Lệnh an toàn để nâng cấp DB cũ chưa có cột image_category
            try: cursor.execute("ALTER TABLE item_images ADD COLUMN image_category TEXT DEFAULT 'general'")
            except: pass
            
            # Add columns safely
            try: cursor.execute('ALTER TABLE equipment ADD COLUMN receive_date TIMESTAMP')
            except: pass
            
            try: cursor.execute("ALTER TABLE equipment ADD COLUMN loan_status TEXT DEFAULT 'Đang ở kho'")
            except: pass
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_units_code ON units(code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_serial ON equipment(serial_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_unit ON equipment(unit_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_equipment ON maintenance_log(equipment_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_equipment ON loan_log(equipment_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_status ON loan_log(status)')
            
            # Index cho bảng audit
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)')
            # [MỚI] Index cho ảnh để tải nhanh
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_target ON item_images(target_type, target_id)')
            
            conn.commit()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def insert(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def get_statistics(self) -> dict:
        stats = {}
        row = self.fetch_one("SELECT COUNT(*) as count FROM equipment")
        stats['total_equipment'] = row['count'] if row else 0
        
        rows = self.fetch_all("SELECT status, COUNT(*) as count FROM equipment GROUP BY status")
        stats['by_status'] = {row['status']: row['count'] for row in rows}
        
        rows = self.fetch_all("SELECT category, COUNT(*) as count FROM equipment GROUP BY category")
        stats['by_category'] = {row['category']: row['count'] for row in rows}
        
        row = self.fetch_one("SELECT COUNT(*) as count FROM maintenance_log WHERE status = 'Đang thực hiện'")
        stats['active_maintenance'] = row['count'] if row else 0
        
        row = self.fetch_one("SELECT COUNT(*) as count FROM loan_log WHERE status = 'Đang mượn'")
        stats['active_loans'] = row['count'] if row else 0
        
        rows = self.fetch_all("SELECT loan_status, COUNT(*) as count FROM equipment GROUP BY loan_status")
        stats['by_loan_status'] = {row['loan_status']: row['count'] for row in rows}
        
        rows = self.fetch_all('''
            SELECT e.name, m.maintenance_type, m.start_date
            FROM maintenance_log m
            JOIN equipment e ON m.equipment_id = e.id
            ORDER BY m.start_date DESC
            LIMIT 5
        ''')
        stats['recent_activities'] = [dict(row) for row in rows]
        
        return stats

    # Hàm ghi nhật ký hệ thống chung cho toàn dự án
    def log_action(self, user_id: Optional[int], username: str, action: str, target_type: str, target_id: Optional[int], details: str):
        """
        Ghi lại nhật ký thao tác người dùng.
        :param action: 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'EXPORT'
        :param target_type: 'Equipment', 'User', 'Maintenance', v.v.
        """
        query = '''
            INSERT INTO audit_logs (user_id, username, action, target_type, target_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        try:
            self.execute(query, (user_id, username, action, target_type, target_id, details))
        except Exception as e:
            print(f"Lỗi ghi Audit Log: {e}")