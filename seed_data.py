"""
Script tạo dữ liệu mẫu cho hệ thống Quản lý VKTBKT
Chạy lệnh: python seed_data.py
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Thêm thư mục hiện tại vào path để import được các module trong src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.database import Database
from src.models.user import User, UserRole
from src.models.category import Category
from src.models.equipment import Equipment
from src.models.maintenance_log import MaintenanceLog
from src.models.loan_log import LoanLog
from src.models.maintenance_type import MaintenanceType
from src.config import EQUIPMENT_STATUS, EQUIPMENT_CATEGORIES

# Khởi tạo DB
db = Database()

def clean_database():
    """Xóa dữ liệu cũ để nạp mới"""
    print("🧹 Đang dọn dẹp dữ liệu cũ...")
    tables = ["loan_logs", "maintenance_logs", "equipments", "users", "categories", "maintenance_types", "units"]
    for table in tables:
        try:
            db.execute(f"DELETE FROM {table}")
            # Reset ID về 1 (cho SQLite)
            db.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except Exception:
            pass
    print("✅ Đã dọn dẹp xong.")

def create_units():
    """Tạo đơn vị"""
    print("🏢 Đang tạo đơn vị...")
    units = [
        "Phòng Kỹ thuật", "Đại đội BB1", "Đại đội BB2", 
        "Trung đội Thông tin", "Trung đội Vận tải", "Kho K1"
    ]
    unit_ids = []
    for name in units:
        # Sử dụng raw SQL vì chưa có Unit Model trong context
        query = "INSERT INTO units (name, description) VALUES (?, ?)"
        try:
            uid = db.insert(query, (name, f"Đơn vị {name}"))
            unit_ids.append(uid)
        except Exception as e:
            # Nếu bảng chưa tồn tại hoặc lỗi, bỏ qua
            print(f"Lỗi tạo đơn vị {name}: {e}")
    return unit_ids

def create_users(unit_ids):
    """Tạo tài khoản người dùng"""
    print("👥 Đang tạo người dùng...")
    
    # 1. Super Admin (Giữ nguyên hoặc tạo mới)
    User.create_default_admin()
    
    # 2. Quản lý kho (Manager)
    manager = User()
    manager.username = "thukho"
    manager.set_password("123456")
    manager.full_name = "Nguyễn Văn Thủ Kho"
    manager.role = UserRole.MANAGER
    manager.unit_id = unit_ids[-1] if unit_ids else None # Thuộc Kho K1
    manager.save()
    print(f"   + Tạo user: thukho (Pass: 123456) - {manager.full_name}")

    # 3. Chỉ huy (Viewer)
    viewer = User()
    viewer.username = "chihuy"
    viewer.set_password("123456")
    viewer.full_name = "Trần Văn Chỉ Huy"
    viewer.role = UserRole.VIEWER
    viewer.unit_id = unit_ids[0] if unit_ids else None # Phòng Kỹ thuật
    viewer.save()
    print(f"   + Tạo user: chihuy (Pass: 123456) - {viewer.full_name}")

    # 4. Kỹ thuật viên (Dùng quyền Manager để demo)
    tech = User()
    tech.username = "kythuat"
    tech.set_password("123456")
    tech.full_name = "Lê Kỹ Thuật"
    tech.role = UserRole.MANAGER
    tech.save()
    print(f"   + Tạo user: kythuat (Pass: 123456) - {tech.full_name}")

def create_categories():
    """Tạo danh mục và loại công việc"""
    print("📂 Đang tạo danh mục...")
    
    # Categories
    cats = [
        ("Súng bộ binh", "VK-BB", "Các loại súng ngắn, súng trường"),
        ("Khí tài quang học", "KT-QH", "Ống nhòm, kính ngắm"),
        ("Phương tiện vận tải", "XE-VT", "Xe tải, xe con"),
        ("Vật tư kỹ thuật", "VT-KT", "Phụ tùng thay thế"),
        ("Thiết bị thông tin", "TB-TT", "Máy vô tuyến điện")
    ]
    for name, code, desc in cats:
        c = Category()
        c.name = name
        c.code = code
        c.description = desc
        c.is_active = True
        c.save()

    # Maintenance Types
    mtypes = [
        ("Bảo dưỡng Cấp 1", "BD-1", "Bảo dưỡng thường xuyên"),
        ("Bảo dưỡng Cấp 2", "BD-2", "Bảo dưỡng định kỳ"),
        ("Sửa chữa nhỏ", "SC-N", "Thay thế phụ tùng đơn giản"),
        ("Sửa chữa vừa", "SC-V", "Sửa chữa tại xưởng"),
        ("Kiểm tra kỹ thuật", "KT-KT", "Kiểm định định kỳ")
    ]
    for name, code, desc in mtypes:
        m = MaintenanceType()
        m.name = name
        m.code = code
        m.description = desc
        m.is_active = True
        m.save()

def create_equipments():
    """Tạo dữ liệu thiết bị"""
    print("📦 Đang tạo thiết bị mẫu...")
    
    sample_data = [
        ("Súng tiểu liên AK-47", "AK-12345", "Súng bộ binh", "Cấp 1", 2020, "Kho K1"),
        ("Súng ngắn K54", "K54-99887", "Súng bộ binh", "Cấp 2", 2019, "Tủ súng ĐĐ1"),
        ("Súng trung liên RPD", "RPD-55667", "Súng bộ binh", "Cấp 2", 2018, "Kho K1"),
        ("Ống nhòm T8", "ON-001", "Khí tài quang học", "Cấp 3", 2015, "Phòng kỹ thuật"),
        ("Xe Zil-130", "QX-12-34", "Phương tiện vận tải", "Cấp 4", 2010, "Khu xe"),
        ("Máy vô tuyến VRU-812", "VRU-888", "Thiết bị thông tin", "Cấp 1", 2022, "Kho Thông tin"),
        ("Súng B41", "B41-2233", "Súng bộ binh", "Cấp 5", 2005, "Kho chờ hủy"),
        ("Xe UAZ-469", "QB-56-78", "Phương tiện vận tải", "Cấp 2", 2012, "Ban Chỉ huy"),
        ("Kính ngắm ngày", "KN-Day", "Khí tài quang học", "Cấp 1", 2023, "Kho K1"),
        ("Mặt nạ phòng hóa", "MV-5", "Vật tư kỹ thuật", "Cấp 1", 2024, "Kho Hóa học"),
        ("Súng trường CKC", "CKC-777", "Súng bộ binh", "Cấp 3", 1990, "Kho K1"),
        ("Lốp xe Zil", "L-ZIL-01", "Vật tư kỹ thuật", "Cấp 1", 2025, "Kho Vật tư"),
    ]

    equipments = []
    for name, serial, cat, status, year, loc in sample_data:
        e = Equipment()
        e.name = name
        e.serial_number = serial
        e.category = cat
        e.status = status
        e.manufacture_year = year
        e.location = loc
        e.unit_name = "Kho K1" if "Kho" in loc else "Đại đội BB1"
        e.description = f"Thiết bị nhập kho năm {year}"
        e.receive_date = datetime.now() - timedelta(days=random.randint(100, 1000))
        eid = e.save()
        e.id = eid
        equipments.append(e)
    
    return equipments

def create_logs(equipments):
    """Tạo nhật ký bảo dưỡng và mượn trả"""
    print("📝 Đang tạo nhật ký hoạt động...")
    
    technicians = ["Nguyễn Văn A", "Trần Văn B", "Lê Thị C"]
    borrowers = ["Đại đội 1", "Đại đội 2", "Ban Tham mưu", "Ban Chính trị"]
    
    for equip in equipments:
        # Tạo 1-3 log bảo dưỡng ngẫu nhiên cho mỗi thiết bị
        for _ in range(random.randint(0, 3)):
            log = MaintenanceLog()
            log.equipment_id = equip.id
            log.maintenance_type = random.choice(["Bảo dưỡng Cấp 1", "Kiểm tra kỹ thuật", "Sửa chữa nhỏ"])
            
            # Ngày bắt đầu trong quá khứ
            days_ago = random.randint(10, 365)
            log.start_date = datetime.now() - timedelta(days=days_ago)
            
            # Trạng thái
            if random.random() > 0.2: # 80% là hoàn thành
                log.status = "Hoàn thành"
                log.end_date = log.start_date + timedelta(days=random.randint(1, 5))
                log.description = "Đã hoàn thành công việc theo quy trình."
            else:
                log.status = "Đang thực hiện"
                log.description = "Đang chờ vật tư thay thế."
            
            log.technician_name = random.choice(technicians)
            log.save()

        # Tạo log mượn trả (cho các thiết bị còn tốt)
        if equip.status in ["Cấp 1", "Cấp 2"]:
            if random.random() > 0.7:
                # Tạo 1 log đang mượn
                loan = LoanLog()
                loan.equipment_id = equip.id
                loan.borrower_unit = random.choice(borrowers)
                loan.loan_date = datetime.now() - timedelta(days=random.randint(1, 10))
                loan.expected_return_date = loan.loan_date + timedelta(days=7)
                loan.status = "Đang mượn"
                loan.notes = "Mượn phục vụ huấn luyện"
                loan.save()
                
                # Cập nhật trạng thái thiết bị
                equip.loan_status = "Đã cho mượn"
                equip.save()
            else:
                # Tạo log đã trả (lịch sử)
                loan = LoanLog()
                loan.equipment_id = equip.id
                loan.borrower_unit = random.choice(borrowers)
                loan.loan_date = datetime.now() - timedelta(days=random.randint(30, 60))
                loan.return_date = loan.loan_date + timedelta(days=5)
                loan.status = "Đã trả"
                loan.notes = "Đã trả đủ, tình trạng tốt"
                loan.save()

def main():
    print("="*50)
    print("CHƯƠNG TRÌNH KHỞI TẠO DỮ LIỆU MẪU VKTBKT")
    print("="*50)
    
    clean_database()
    unit_ids = create_units()
    create_users(unit_ids)
    create_categories()
    equips = create_equipments()
    create_logs(equips)
    
    print("\n" + "="*50)
    print("🎉 KHỞI TẠO THÀNH CÔNG!")
    print(f"📊 Tổng cộng: {len(equips)} thiết bị")
    print("🔑 Tài khoản đăng nhập:")
    print("   1. Admin:   admin / admin123")
    print("   2. Thủ kho: thukho / 123456")
    print("   3. Chỉ huy: chihuy / 123456")
    print("="*50)

if __name__ == "__main__":
    main()