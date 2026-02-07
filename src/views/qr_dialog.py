"""
QR Dialog - Display and save QR code for equipment
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QPainter, QImage
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
import io

from ..models.equipment import Equipment
from ..services.qr_service import QRService


class QRDialog(QDialog):
    """
    Dialog to display QR code for equipment with Print Preview
    """
    
    def __init__(self, parent=None, equipment: Equipment = None, qr_service: QRService = None):
        super().__init__(parent)
        self.equipment = equipment
        self.qr_service = qr_service or QRService()
        self.qr_image = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"Mã QR: {self.equipment.serial_number}")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🏷️ Mã QR thiết bị")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Equipment info
        info_label = QLabel(
            f"<b>{self.equipment.name}</b><br>"
            f"Số hiệu: {self.equipment.serial_number}"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # QR Code image
        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Generate QR code with label
        self.qr_image, _ = self.qr_service.generate_qr_with_label(
            f"VKTBKT|{self.equipment.id}|{self.equipment.serial_number}",
            f"{self.equipment.serial_number}"
        )
        
        # Convert PIL Image to QPixmap
        buffer = io.BytesIO()
        self.qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        scaled_pixmap = pixmap.scaled(
            250, 280,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        qr_label.setPixmap(scaled_pixmap)
        layout.addWidget(qr_label)
        
        # Instructions
        instruction = QLabel(
            "In mã QR này ra giấy Decal và dán lên thiết bị\n"
            "để tra cứu nhanh bằng camera"
        )
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(instruction)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Lưu ảnh")
        save_btn.clicked.connect(self._save_qr)
        button_layout.addWidget(save_btn)
        
        print_btn = QPushButton("🖨️ In") # Nút này giờ sẽ gọi Preview
        print_btn.clicked.connect(self._open_print_preview)
        button_layout.addWidget(print_btn)
        
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _save_qr(self):
        """Save QR code image to file"""
        default_name = f"QR_{self.equipment.serial_number}.png"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu mã QR",
            default_name,
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        
        if filepath:
            try:
                self.qr_image.save(filepath)
                QMessageBox.information(
                    self, "Thành công",
                    f"Đã lưu mã QR tại:\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Lỗi",
                    f"Không thể lưu file: {str(e)}"
                )
    
    def _open_print_preview(self):
        """Open Print Preview Dialog"""
        try:
            # Khởi tạo máy in
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # Khởi tạo hộp thoại xem trước (Print Preview Dialog)
            preview_dialog = QPrintPreviewDialog(printer, self)
            preview_dialog.setMinimumSize(1000, 800)
            preview_dialog.setWindowTitle(f"Xem trước bản in - {self.equipment.serial_number}")
            
            # Kết nối tín hiệu vẽ (paintRequested) với hàm vẽ của chúng ta
            preview_dialog.paintRequested.connect(self._handle_paint_request)
            
            # Hiển thị
            preview_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở xem trước: {str(e)}")

    def _handle_paint_request(self, printer):
        """
        Callback function to render content onto the printer/preview
        """
        try:
            painter = QPainter()
            if not painter.begin(printer):
                print("Failed to begin painting on printer")
                return

            # --- BẮT ĐẦU VẼ NỘI DUNG ---
            
            # 1. Chuẩn bị ảnh từ PIL sang QImage
            buffer = io.BytesIO()
            self.qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            q_image = QImage()
            q_image.loadFromData(buffer.getvalue())
            
            if q_image.isNull():
                painter.end()
                return

            # 2. Tính toán vùng in (Page Rect)
            rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            
            # 3. Cấu hình kích thước (Chiếm 50% khổ giấy)
            scale_factor = 0.5 
            target_width = int(rect.width() * scale_factor)
            
            scaled_image = q_image.scaledToWidth(
                target_width, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 4. Tính tọa độ để căn giữa trang
            x_img = int(rect.left() + (rect.width() - target_width) / 2)
            y_img = int(rect.top() + (rect.height() * 0.1)) # Cách lề trên 10%
            
            # 5. Vẽ ảnh QR
            painter.drawImage(x_img, y_img, scaled_image)
            
            # 6. Vẽ viền nét đứt bao quanh để dễ cắt (Optional)
            pen = painter.pen()
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(4)
            pen.setColor(Qt.GlobalColor.gray)
            painter.setPen(pen)
            
            border_padding = 50
            painter.drawRect(
                x_img - border_padding, 
                y_img - border_padding,
                scaled_image.width() + (border_padding * 2),
                scaled_image.height() + int(rect.height() * 0.2)
            )
            
            # 7. Vẽ thông tin văn bản bên dưới
            # Reset Pen về màu đen
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setColor(Qt.GlobalColor.black)
            painter.setPen(pen)

            # Font size tự động theo khổ giấy
            font_pixel_size = int(rect.width() * 0.025) 
            font = QFont("Arial")
            font.setPixelSize(font_pixel_size)
            font.setBold(True)
            painter.setFont(font)
            
            text_y = y_img + scaled_image.height() + int(rect.height() * 0.02)
            text_height = int(rect.height() * 0.15)
            
            info_text = f"{self.equipment.name}\nSố hiệu: {self.equipment.serial_number}"
            
            painter.drawText(
                int(rect.left()), text_y, int(rect.width()), text_height,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                info_text
            )
            
            painter.end()
            
        except Exception as e:
            print(f"Drawing Error: {e}")