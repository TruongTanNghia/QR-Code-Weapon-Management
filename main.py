"""
VKTBKT Management System - Main Entry Point
Phần mềm Quản lý Vũ khí Trang bị Kỹ thuật thông qua mã QR

Author: VKTBKT Team
Version: 1.0.0
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.views.main_window import MainWindow
from src.views.login_dialog import LoginDialog
from src.models.database import Database
from src.models.user import User
from src.models.category import Category
from src.models.maintenance_type import MaintenanceType
from src.controllers.user_controller import UserController
from src.controllers.maintenance_type_controller import MaintenanceTypeController
from src.config import APP_NAME


def setup_high_dpi():
    """Enable high DPI scaling for modern displays"""
    # PyQt6 handles this automatically, but we ensure it's enabled
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)


def setup_application_font(app: QApplication):
    """Setup default application font"""
    font = QFont("Segoe UI", 10)
    app.setFont(font)


def initialize_database():
    """Initialize database connection and tables"""
    db = Database()
    # Create default admin if not exists
    User.create_default_admin("admin", "admin123")
    # Initialize default categories
    Category.initialize_default_categories()
    # Initialize default maintenance types
    MaintenanceTypeController.initialize_default_types()
    return db


def show_login_and_main(app: QApplication) -> bool:
    """Show login dialog and main window in a loop for logout support"""
    while True:
        # Show login dialog
        login_dialog = LoginDialog()
        result = login_dialog.exec()
        
        if result != LoginDialog.DialogCode.Accepted:
            # User closed login dialog - exit app
            return False
        
        # Get logged in user
        current_user = login_dialog.get_user()
        if not current_user:
            return False
        
        # Set current user in controller
        UserController.set_current_user(current_user)
        
        # Create and show main window
        window = MainWindow(current_user=current_user)
        window.show()
        
        # Run until window is closed
        app.exec()
        
        # Check if user logged out (wants to go back to login)
        # or just closed window (wants to exit)
        if not getattr(window, 'logout_requested', False):
            # Window closed normally - exit app
            return False
        
        # User logged out - continue loop to show login again


def main():
    """Main application entry point"""
    # Setup high DPI before creating QApplication
    setup_high_dpi()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("VKTBKT Team")
    
    # Setup font
    setup_application_font(app)
    
    # Initialize database
    initialize_database()
    
    # Show login and main window (loop for logout support)
    show_login_and_main(app)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
