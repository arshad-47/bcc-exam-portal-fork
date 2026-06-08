import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from src.config import Config

class CertificateGenerator:
    @staticmethod
    def generate_cert_id(result_id: int) -> str:
        # Generate clean certificate ID: BCC-YYYYMMDD-RESULT_ID
        date_str = datetime.now().strftime("%Y%m%d")
        return f"BCC-{date_str}-{result_id:05d}"

    @staticmethod
    def create_pdf(cert_data: dict) -> io.BytesIO:
        """
        Creates a PDF certificate using ReportLab in memory.
        
        cert_data should contain:
        - 'certificate_id': str
        - 'student_name': str
        - 'roll_number': str
        - 'exam_title': str
        - 'percentage': float
        - 'grade': str
        - 'issue_date': datetime or str
        - 'verification_url': str
        """
        # Set page dimension to Landscape A4
        page_width, page_height = landscape(A4)
        
        pdf_buffer = io.BytesIO()
        
        # Build document with tight margins (50 points / ~0.7 inch)
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        # Color Palette - Premium Navy & Gold theme
        navy_color = colors.HexColor("#1E3A8A")  # Deep blue
        gold_color = colors.HexColor("#B45309")  # Amber/gold
        charcoal = colors.HexColor("#1F2937")    # Dark charcoal for text
        slate_gray = colors.HexColor("#64748B")  # Muted grey
        
        # Styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=34,
            leading=42,
            textColor=navy_color,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'CertSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=gold_color,
            alignment=TA_CENTER,
            spaceAfter=15
        )
        
        desc_style = ParagraphStyle(
            'CertDesc',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=14,
            leading=20,
            textColor=charcoal,
            alignment=TA_CENTER
        )
        
        student_style = ParagraphStyle(
            'CertStudent',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=32,
            textColor=navy_color,
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10
        )
        
        details_style = ParagraphStyle(
            'CertDetails',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            textColor=slate_gray,
            alignment=TA_CENTER
        )
        
        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=navy_color,
            alignment=TA_LEFT
        )
        
        meta_value_style = ParagraphStyle(
            'MetaValue',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            textColor=charcoal,
            alignment=TA_LEFT
        )

        elements = []
        
        # --- Spacer to center the content ---
        elements.append(Spacer(1, 10))
        
        # --- HEADER / INSTITUTE NAME ---
        elements.append(Paragraph(Config.INSTITUTE_NAME.upper(), title_style))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("CERTIFICATE OF ACHIEVEMENT", subtitle_style))
        
        # --- DECORATIVE LINE ---
        line_data = [[""]]
        line_table = Table(line_data, colWidths=[page_width - 120], rowHeights=[2])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), gold_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 20))
        
        # --- CERTIFICATE CONTENT DESCRIPTION ---
        elements.append(Paragraph("This is proudly presented to", desc_style))
        elements.append(Paragraph(cert_data['student_name'].upper(), student_style))
        
        percentage = cert_data.get('percentage', 0.0)
        grade = cert_data.get('grade', 'F')
        roll = cert_data.get('roll_number', 'N/A')
        exam = cert_data.get('exam_title', 'Examination')
        
        desc_text = (
            f"for successfully completing the <b>{Config.COURSE_NAME}</b> assessment "
            f"titled <b>\"{exam}\"</b>.<br/>"
            f"The candidate secured an overall score of <b>{percentage:.2f}%</b> and is awarded <b>Grade '{grade}'</b>."
        )
        elements.append(Paragraph(desc_text, desc_style))
        elements.append(Spacer(1, 25))
        
        # --- FOOTER BLOCK: QR, Signatures, Details ---
        
        # Generate QR code
        qr_buf = io.BytesIO()
        qr = qrcode.QRCode(version=1, box_size=8, border=1)
        qr.add_data(cert_data.get('verification_url', ''))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#1E3A8A", back_color="white")
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        
        # ReportLab Image for QR Code (80x80 points)
        rl_qr = RLImage(qr_buf, width=80, height=80)
        
        # Prepare Certificate metadata block (Cert ID, Roll, Date)
        issue_date = cert_data.get('issue_date')
        if isinstance(issue_date, datetime):
            issue_date_str = issue_date.strftime("%B %d, %Y")
        else:
            issue_date_str = str(issue_date)
            
        metadata_content = [
            [Paragraph("Certificate ID:", meta_label_style), Paragraph(cert_data['certificate_id'], meta_value_style)],
            [Paragraph("Roll Number:", meta_label_style), Paragraph(roll, meta_value_style)],
            [Paragraph("Issue Date:", meta_label_style), Paragraph(issue_date_str, meta_value_style)],
            [Paragraph("Status:", meta_label_style), Paragraph("<font color='green'><b>VERIFIED</b></font>", meta_value_style)]
        ]
        metadata_table = Table(metadata_content, colWidths=[90, 150])
        metadata_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Signatures
        sig_label_style = ParagraphStyle(
            'SigLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=13,
            textColor=navy_color,
            alignment=TA_CENTER
        )
        sig_title_style = ParagraphStyle(
            'SigTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=slate_gray,
            alignment=TA_CENTER
        )
        
        sig_block = [
            [Paragraph("____________________________", sig_label_style)],
            [Spacer(1, 5)],
            [Paragraph("Program Director", sig_label_style)],
            [Paragraph(Config.INSTITUTE_NAME, sig_title_style)]
        ]
        sig_table = Table(sig_block, colWidths=[200])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Assemble bottom row of certificate: Metadata, QR Code, Signature
        bottom_table_data = [
            [metadata_table, rl_qr, sig_table]
        ]
        
        bottom_table = Table(bottom_table_data, colWidths=[260, 120, 240])
        bottom_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('ALIGN', (1,0), (1,0), 'CENTER'), # Center the QR code
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        
        elements.append(bottom_table)
        
        # Draw elegant borders on the canvas
        def draw_borders(canvas, document):
            canvas.saveState()
            
            # Margins & dimensions
            w, h = landscape(A4)
            
            # Primary outer border (thick navy blue)
            canvas.setStrokeColor(navy_color)
            canvas.setLineWidth(5)
            canvas.rect(20, 20, w - 40, h - 40)
            
            # Secondary inner border (thin gold)
            canvas.setStrokeColor(gold_color)
            canvas.setLineWidth(1.5)
            canvas.rect(26, 26, w - 52, h - 52)
            
            # Corner accents (flourish graphics)
            canvas.setFillColor(navy_color)
            
            # Top-left corner design
            canvas.rect(26, h-40, 14, 14, fill=1, stroke=0)
            # Top-right
            canvas.rect(w-40, h-40, 14, 14, fill=1, stroke=0)
            # Bottom-left
            canvas.rect(26, 26, 14, 14, fill=1, stroke=0)
            # Bottom-right
            canvas.rect(w-40, 26, 14, 14, fill=1, stroke=0)
            
            canvas.restoreState()
            
        # Build the PDF using document template and the custom background function
        doc.build(elements, onFirstPage=draw_borders)
        
        pdf_buffer.seek(0)
        return pdf_buffer
