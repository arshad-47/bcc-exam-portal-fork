import io
import os
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
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

        def resolve_path(path_value):
            if not path_value:
                return None
            path_value = os.path.expanduser(path_value)
            if os.path.isabs(path_value):
                return path_value
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", path_value))

        template_path = resolve_path(Config.CERTIFICATE_TEMPLATE_PATH)
        signature_path = resolve_path(Config.PROGRAM_DIRECTOR_SIGNATURE_PATH)

        c = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))

        if template_path and os.path.exists(template_path):
            c.drawImage(template_path, 0, 0, width=page_width, height=page_height, mask='auto')
        else:
            c.setFillColor(colors.whitesmoke)
            c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        navy_color = colors.HexColor("#1E3A8A")
        charcoal = colors.HexColor("#1F2937")
        gold_color = colors.HexColor("#B45309")
        gray_color = colors.HexColor("#6B7280")

        def wrapped_centered_text(text, x_center, y_start, max_width, font_name, font_size, leading):
            words = text.split()
            current_line = ""
            y = y_start
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if stringWidth(test_line, font_name, font_size) <= max_width:
                    current_line = test_line
                else:
                    c.drawCentredString(x_center, y, current_line)
                    y -= leading
                    current_line = word
            if current_line:
                c.drawCentredString(x_center, y, current_line)
                y -= leading
            return y

        c.setFillColor(navy_color)
        c.setFont("Times-Italic", 28)
        c.drawCentredString(page_width / 2, page_height - 305, cert_data['student_name'].upper())

        exam = cert_data.get('exam_title', 'Examination')
        percentage = cert_data.get('percentage', 0.0)
        grade = cert_data.get('grade', 'F')
        roll = cert_data.get('roll_number', 'N/A')
        issue_date = cert_data.get('issue_date')
        if isinstance(issue_date, datetime):
            issue_date_str = issue_date.strftime("%B %d, %Y")
        else:
            issue_date_str = str(issue_date or datetime.now().strftime("%B %d, %Y"))

        c.setFont("Helvetica-Oblique", 14)
        c.setFillColor(charcoal)
        y = page_height - 340
        desc_text = (
            f"for successfully completing the {Config.COURSE_NAME} assessment titled \"{exam}\"."
        )
        y = wrapped_centered_text(
            desc_text,
            page_width / 2,
            y,
            page_width * 0.7,
            "Helvetica",
            14,
            18
        )

        score_text = (
            f"The candidate secured an overall score of {percentage:.2f}% and is awarded Grade \"{grade}\"."
        )
        y = wrapped_centered_text(
            score_text,
            page_width / 2,
            y - 6,
            page_width * 0.7,
            "Helvetica",
            14,
            18
        )

        # Typing test line (if available)
        typing_wpm = cert_data.get("typing_wpm")
        typing_accuracy = cert_data.get("typing_accuracy")
        if typing_wpm is not None:
            typing_text = f"Typing Proficiency: {typing_wpm} WPM | Accuracy: {typing_accuracy:.1f}%"
            c.setFont("Helvetica-Oblique", 11)
            c.setFillColor(gold_color)
            c.drawCentredString(page_width / 2, y - 6, typing_text)
            y -= 14

        # Module grades (if available)
        bcc_grade = cert_data.get("bcc_grade")
        msoffice_grade = cert_data.get("msoffice_grade")
        if bcc_grade and bcc_grade != "N/A" and msoffice_grade and msoffice_grade != "N/A":
            module_text = f"BCC Module: Grade {bcc_grade} | MS Office Module: Grade {msoffice_grade}"
            c.setFont("Helvetica", 10)
            c.setFillColor(navy_color)
            c.drawCentredString(page_width / 2, y - 6, module_text)

        meta_x = 90
        meta_y = 165
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(navy_color)
        c.drawString(meta_x, meta_y, "Certificate ID:")
        c.drawString(meta_x, meta_y - 18, "Roll Number:")
        c.drawString(meta_x, meta_y - 36, "Issue Date:")
        c.drawString(meta_x, meta_y - 54, "Status:")

        c.setFont("Helvetica", 10)
        c.setFillColor(charcoal)
        c.drawString(meta_x + 110, meta_y, cert_data['certificate_id'])
        c.drawString(meta_x + 110, meta_y - 18, roll)
        c.drawString(meta_x + 110, meta_y - 36, issue_date_str)
        c.setFillColor(colors.green)
        c.drawString(meta_x + 110, meta_y - 54, "VERIFIED")

        qr_buf = io.BytesIO()
        qr = qrcode.QRCode(version=1, box_size=8, border=1)
        qr.add_data(cert_data.get('verification_url', ''))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#1E3A8A", back_color="white")
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        qr_reader = ImageReader(qr_buf)

        qr_size = 70
        qr_x = 90
        qr_y = 40
        c.drawImage(qr_reader, qr_x, qr_y, qr_size, qr_size, mask='auto')
        c.setFont("Helvetica", 8)
        c.setFillColor(gray_color)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 12, "Scan to verify")

        sig_x = page_width - 290
        sig_y = 90
        
        if signature_path and os.path.exists(signature_path):
            try:
                c.drawImage(signature_path, sig_x + 30, sig_y + 18, width=120, height=45, mask='auto')
            except Exception:
                pass
        
        c.setStrokeColor(charcoal)
        c.setLineWidth(1.2)
        c.line(sig_x, sig_y + 20, sig_x + 180, sig_y + 20)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(navy_color)
        c.drawCentredString(sig_x + 90, sig_y, Config.PROGRAM_DIRECTOR_NAME)
        c.setFont("Helvetica", 9)
        c.setFillColor(gray_color)
        c.drawCentredString(sig_x + 90, sig_y - 15, Config.PROGRAM_DIRECTOR_TITLE)

        c.showPage()
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer
