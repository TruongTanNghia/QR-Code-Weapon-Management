"""
QR Code Service - Generate and decode QR codes
"""
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple
import io
import base64

from ..config import QR_BOX_SIZE, QR_BORDER, QR_VERSION, DATA_DIR


class QRService:
    """
    Service for generating and handling QR codes
    """
    
    # Directory for storing QR code images
    QR_STORAGE_DIR = DATA_DIR / "qr_codes"
    
    def __init__(self):
        # Ensure QR storage directory exists
        self.QR_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    def generate_qr_code(
        self, 
        data: str, 
        filename: str = None,
        box_size: int = QR_BOX_SIZE,
        border: int = QR_BORDER,
        fill_color: str = "black",
        back_color: str = "white"
    ) -> Tuple[Image.Image, Optional[str]]:
        """
        Generate a QR code image
        
        Args:
            data: The data to encode in QR code
            filename: Optional filename to save the QR code
            box_size: Size of each box in pixels
            border: Border size in boxes
            fill_color: Color of QR code
            back_color: Background color
            
        Returns:
            Tuple of (PIL Image, saved file path or None)
        """
        qr = qrcode.QRCode(
            version=QR_VERSION,
            error_correction=ERROR_CORRECT_H,  # High error correction
            box_size=box_size,
            border=border
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        # Convert to PIL Image if not already
        if not isinstance(img, Image.Image):
            img = img.get_image()
        
        saved_path = None
        if filename:
            # Ensure .png extension
            if not filename.lower().endswith('.png'):
                filename += '.png'
            
            file_path = self.QR_STORAGE_DIR / filename
            img.save(str(file_path))
            saved_path = str(file_path)
        
        return img, saved_path
    
    def generate_equipment_qr(
        self, 
        equipment_id: int, 
        serial_number: str
    ) -> Tuple[Image.Image, str]:
        """
        Generate QR code for equipment
        
        Args:
            equipment_id: Equipment ID
            serial_number: Equipment serial number
            
        Returns:
            Tuple of (PIL Image, saved file path)
        """
        # QR data format: VKTBKT|ID|SERIAL
        qr_data = f"VKTBKT|{equipment_id}|{serial_number}"
        filename = f"equip_{equipment_id}_{serial_number}.png"
        
        img, path = self.generate_qr_code(qr_data, filename)
        return img, path
    
    def decode_qr_data(self, qr_data: str) -> Optional[dict]:
        """
        Decode QR data string
        
        Args:
            qr_data: Raw QR code data string
            
        Returns:
            Dictionary with decoded data or None
        """
        try:
            parts = qr_data.split('|')
            if len(parts) >= 3 and parts[0] == 'VKTBKT':
                return {
                    'type': 'equipment',
                    'equipment_id': int(parts[1]),
                    'serial_number': parts[2]
                }
            # Unknown format, return raw
            return {
                'type': 'unknown',
                'raw_data': qr_data
            }
        except Exception:
            return {
                'type': 'error',
                'raw_data': qr_data
            }
    
    def image_to_base64(self, img: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    def base64_to_image(self, b64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image"""
        img_data = base64.b64decode(b64_string)
        return Image.open(io.BytesIO(img_data))
    
    def get_qr_path(self, equipment_id: int, serial_number: str) -> Path:
        """Get the expected path for an equipment's QR code"""
        filename = f"equip_{equipment_id}_{serial_number}.png"
        return self.QR_STORAGE_DIR / filename
    
    def qr_exists(self, equipment_id: int, serial_number: str) -> bool:
        """Check if QR code file exists for equipment"""
        return self.get_qr_path(equipment_id, serial_number).exists()
    
    def delete_qr(self, equipment_id: int, serial_number: str) -> bool:
        """Delete QR code file for equipment"""
        path = self.get_qr_path(equipment_id, serial_number)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def generate_qr_with_label(
        self,
        data: str,
        label: str,
        filename: str = None,
        label_height: int = 40
    ) -> Tuple[Image.Image, Optional[str]]:
        """
        Generate QR code with text label below
        
        Args:
            data: The data to encode
            label: Text label to display below QR
            filename: Optional filename to save
            label_height: Height of label area in pixels
            
        Returns:
            Tuple of (PIL Image, saved file path or None)
        """
        from PIL import ImageDraw, ImageFont
        
        # Generate base QR
        qr_img, _ = self.generate_qr_code(data)
        
        # Create new image with space for label
        qr_width, qr_height = qr_img.size
        new_height = qr_height + label_height
        
        combined = Image.new('RGB', (qr_width, new_height), 'white')
        combined.paste(qr_img, (0, 0))
        
        # Add label text
        draw = ImageDraw.Draw(combined)
        
        # Try to use a better font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Center the text
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (qr_width - text_width) // 2
        text_y = qr_height + (label_height - (bbox[3] - bbox[1])) // 2
        
        draw.text((text_x, text_y), label, fill='black', font=font)
        
        saved_path = None
        if filename:
            if not filename.lower().endswith('.png'):
                filename += '.png'
            file_path = self.QR_STORAGE_DIR / filename
            combined.save(str(file_path))
            saved_path = str(file_path)
        
        return combined, saved_path
