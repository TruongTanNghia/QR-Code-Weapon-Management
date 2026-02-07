"""
Export Service - Generate PDF reports and QR code sheets
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image as RLImage, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import io
import os

from ..config import DATA_DIR, APP_NAME
from ..models.equipment import Equipment
from ..services.qr_service import QRService


class ExportService:
    """
    Service for exporting data to PDF reports
    """
    
    EXPORT_DIR = DATA_DIR / "exports"
    
    def __init__(self):
        self.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.qr_service = QRService()
        
        # Default fonts fallback
        self.font_name = 'Helvetica'
        self.bold_font_name = 'Helvetica-Bold'
        
        self._register_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _register_fonts(self):
        """Register Vietnamese-compatible fonts (Arial)"""
        try:
            # Đường dẫn font trên Windows
            arial_path = "C:/Windows/Fonts/arial.ttf"
            arial_bold_path = "C:/Windows/Fonts/arialbd.ttf"
            
            # Kiểm tra và đăng ký Arial Regular
            if os.path.exists(arial_path):
                pdfmetrics.registerFont(TTFont('Arial', arial_path))
                self.font_name = 'Arial'
                
                # Kiểm tra và đăng ký Arial Bold
                if os.path.exists(arial_bold_path):
                    pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))
                    self.bold_font_name = 'Arial-Bold'
                else:
                    self.bold_font_name = 'Arial' # Fallback nếu không có bold
                    
        except Exception as e:
            print(f"Lỗi đăng ký font: {e}")
            # Vẫn chạy tiếp với font mặc định
    
    def _setup_styles(self):
        """Setup custom paragraph styles with Vietnamese font"""
        self.styles.add(ParagraphStyle(
            name='TitleVN',
            parent=self.styles['Title'],
            fontName=self.bold_font_name, 
            fontSize=18,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='HeadingVN',
            parent=self.styles['Heading2'],
            fontName=self.bold_font_name, 
            fontSize=14,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='BodyVN',
            parent=self.styles['Normal'],
            fontName=self.font_name, 
            fontSize=10,
            spaceAfter=6
        ))
    
    def export_equipment_list(
        self, 
        equipment_list: List[Equipment],
        save_path: str = None,  # [MỚI] Nhận đường dẫn lưu file
        title: str = "DANH SÁCH VŨ KHÍ TRANG BỊ"
    ) -> str:
        """
        Export equipment list to PDF
        """
        # [FIX] Logic xử lý đường dẫn lưu file
        if save_path:
            filepath = Path(save_path)
        else:
            # Fallback nếu không có đường dẫn (lưu vào mặc định)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"equipment_list_{timestamp}.pdf"
            filepath = self.EXPORT_DIR / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1*cm
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph(title, self.styles['TitleVN']))
        elements.append(Paragraph(
            f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['BodyVN']
        ))
        elements.append(Spacer(1, 10*mm))
        
        # Table data
        table_data = [
            ['STT', 'Tên thiết bị', 'Số hiệu', 'Loại', 'NSX', 
             'Năm SX', 'Tình trạng', 'Đơn vị', 'Vị trí']
        ]
        
        for idx, equip in enumerate(equipment_list, 1):
            unit_display = equip.unit_name if equip.unit_name else "-"
            
            table_data.append([
                str(idx),
                equip.name[:30] + '...' if len(equip.name) > 30 else equip.name,
                equip.serial_number,
                equip.category[:15] if len(equip.category) > 15 else equip.category,
                equip.manufacturer[:15] if len(equip.manufacturer) > 15 else equip.manufacturer,
                str(equip.manufacture_year) if equip.manufacture_year else '-',
                equip.status,
                unit_display[:15] if len(unit_display) > 15 else unit_display,
                equip.location[:15] if len(equip.location) > 15 else equip.location
            ])
        
        # Create table
        col_widths = [1*cm, 4*cm, 3*cm, 2.5*cm, 2.5*cm, 1.5*cm, 3*cm, 2*cm, 3*cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
        ]))
        
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(
            f"Tổng số: {len(equipment_list)} thiết bị",
            self.styles['BodyVN']
        ))
        
        doc.build(elements)
        return str(filepath)
    
    def export_qr_sheet(
        self,
        equipment_list: List[Equipment],
        save_path: str = None, # [MỚI] Nhận đường dẫn lưu file
        qr_per_row: int = 4,
        qr_size: int = 35  # mm
    ) -> str:
        """
        Export QR code sheet for printing
        """
        # [FIX] Logic xử lý đường dẫn lưu file
        if save_path:
            filepath = Path(save_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qr_sheet_{timestamp}.pdf"
            filepath = self.EXPORT_DIR / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1*cm
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph(
            "BẢNG MÃ QR VŨ KHÍ TRANG BỊ",
            self.styles['TitleVN']
        ))
        elements.append(Paragraph(
            f"Ngày in: {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['BodyVN']
        ))
        elements.append(Spacer(1, 5*mm))
        
        # Generate QR images and create table
        qr_data = []
        current_row = []
        
        for equip in equipment_list:
            # Generate QR with label
            qr_img, _ = self.qr_service.generate_qr_with_label(
                f"VKTBKT|{equip.id}|{equip.serial_number}",
                f"{equip.serial_number}"
            )
            
            # Convert PIL Image to ReportLab Image
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            rl_image = RLImage(img_buffer, width=qr_size*mm, height=(qr_size+8)*mm)
            
            # Create cell content
            cell_content = [
                rl_image,
                Paragraph(f"<b>{equip.name[:20]}</b>", self.styles['BodyVN'])
            ]
            
            current_row.append(cell_content)
            
            if len(current_row) == qr_per_row:
                qr_data.append(current_row)
                current_row = []
        
        # Add remaining items
        if current_row:
            while len(current_row) < qr_per_row:
                current_row.append([Paragraph("", self.styles['BodyVN'])])
            qr_data.append(current_row)
        
        if qr_data:
            col_width = (A4[0] - 2*cm) / qr_per_row
            table = Table(qr_data, colWidths=[col_width]*qr_per_row)
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5*mm),
                ('TOPPADDING', (0, 0), (-1, -1), 5*mm),
            ]))
            elements.append(table)
        
        doc.build(elements)
        return str(filepath)
    
    def export_equipment_detail(
        self,
        equipment: Equipment,
        maintenance_logs: list = None,
        loan_logs: list = None,
        save_path: str = None # [MỚI] Nhận đường dẫn lưu file
    ) -> str:
        """
        Export detailed equipment report with maintenance and loan history
        """
        # [FIX] Logic xử lý đường dẫn lưu file
        if save_path:
            filepath = Path(save_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"equipment_{equipment.serial_number}_{timestamp}.pdf"
            filepath = self.EXPORT_DIR / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph(
            "HỒ SƠ VŨ KHÍ TRANG BỊ",
            self.styles['TitleVN']
        ))
        elements.append(Spacer(1, 10*mm))
        
        # Generate QR code
        qr_img, _ = self.qr_service.generate_equipment_qr(
            equipment.id, 
            equipment.serial_number
        )
        
        # Equipment info table with QR
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        rl_qr = RLImage(img_buffer, width=40*mm, height=40*mm)
        
        unit_display = equipment.unit_name if equipment.unit_name else "-"
        
        # Format receive_date
        receive_date_str = "-"
        if equipment.receive_date:
            if hasattr(equipment.receive_date, 'strftime'):
                receive_date_str = equipment.receive_date.strftime('%d/%m/%Y')
            else:
                receive_date_str = str(equipment.receive_date)[:10]
        
        loan_status_display = equipment.loan_status if equipment.loan_status else "Đang ở kho"

        info_data = [
            ['Tên thiết bị:', equipment.name],
            ['Số hiệu:', equipment.serial_number],
            ['Loại:', equipment.category],
            ['Nhà sản xuất:', equipment.manufacturer or '-'],
            ['Năm sản xuất:', str(equipment.manufacture_year) if equipment.manufacture_year else '-'],
            ['Ngày cấp phát:', receive_date_str],
            ['Tình trạng:', equipment.status],
            ['TT cho mượn:', loan_status_display],
            ['Đơn vị:', unit_display],
            ['Vị trí:', equipment.location or '-'],
            ['Mô tả:', equipment.description or '-'],
        ]
        
        # Create two-column layout
        left_table = Table(info_data, colWidths=[4*cm, 8*cm])
        left_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name), 
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font_name), 
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        main_table = Table([[left_table, rl_qr]], colWidths=[12*cm, 5*cm])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        
        elements.append(main_table)
        elements.append(Spacer(1, 15*mm))
        
        # Maintenance history
        if maintenance_logs:
            elements.append(Paragraph(
                "LỊCH SỬ BẢO DƯỠNG/SỬA CHỮA",
                self.styles['HeadingVN']
            ))
            
            log_data = [['STT', 'Loại', 'Mô tả', 'Kỹ thuật viên', 'Ngày', 'Trạng thái']]
            
            for idx, log in enumerate(maintenance_logs, 1):
                start_date = log.start_date
                if isinstance(start_date, str):
                    date_str = start_date[:10]
                else:
                    date_str = start_date.strftime('%d/%m/%Y') if start_date else '-'
                
                tech_name = getattr(log, 'technician_name', None) or getattr(log, 'technician', '-')
                
                log_data.append([
                    str(idx),
                    log.maintenance_type,
                    log.description[:30] + '...' if len(log.description) > 30 else log.description,
                    tech_name,
                    date_str,
                    log.status
                ])
            
            log_table = Table(log_data, colWidths=[1*cm, 3*cm, 5*cm, 3*cm, 2.5*cm, 2.5*cm])
            log_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name), 
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name), 
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
            ]))
            
            elements.append(log_table)
        
        # Loan history
        if loan_logs:
            elements.append(Spacer(1, 10*mm))
            elements.append(Paragraph(
                "LỊCH SỬ CHO MƯỢN",
                self.styles['HeadingVN']
            ))
            
            loan_data = [['STT', 'Đơn vị mượn', 'Ngày mượn', 'Ngày trả', 'Trạng thái', 'Ghi chú']]
            
            for idx, loan in enumerate(loan_logs, 1):
                loan_date = loan.loan_date
                if isinstance(loan_date, str):
                    loan_date_str = loan_date[:10]
                else:
                    loan_date_str = loan_date.strftime('%d/%m/%Y') if loan_date else '-'
                
                return_date = loan.return_date
                if return_date:
                    if isinstance(return_date, str):
                        return_date_str = return_date[:10]
                    else:
                        return_date_str = return_date.strftime('%d/%m/%Y')
                else:
                    return_date_str = '-'
                
                loan_data.append([
                    str(idx),
                    loan.borrower_unit[:20] + '...' if len(loan.borrower_unit) > 20 else loan.borrower_unit,
                    loan_date_str,
                    return_date_str,
                    loan.status,
                    loan.notes[:20] + '...' if loan.notes and len(loan.notes) > 20 else (loan.notes or '-')
                ])
            
            loan_table = Table(loan_data, colWidths=[1*cm, 4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4.5*cm])
            loan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF3E0')])
            ]))
            
            elements.append(loan_table)
        
        # Footer
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph(
            f"Xuất ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')} | {APP_NAME}",
            self.styles['BodyVN']
        ))
        
        doc.build(elements)
        return str(filepath)