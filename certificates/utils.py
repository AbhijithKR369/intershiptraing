from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.conf import settings
import os
from datetime import datetime
import uuid


def generate_certificate(
    student_name, course_name, score, total, company_name
):

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    certificate_id = str(uuid.uuid4())[:8].upper()
    percentage = round((score / total) * 100, 2)
    date = datetime.now().strftime("%d %B %Y")

    filename = f"cert_{student_name}_{course_name}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'certificates', filename)

    # 🔶 Custom Canvas for border
    class BorderCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def draw_border(self):
            width, height = self._pagesize

            # Outer border
            self.setLineWidth(4)
            self.rect(20, 20, width - 40, height - 40)

            # Inner border
            self.setLineWidth(1)
            self.rect(30, 30, width - 60, height - 60)

        def showPage(self):
            self.draw_border()
            super().showPage()

    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()

    title = styles['Title']
    title.alignment = TA_CENTER

    center = styles['Normal']
    center.alignment = TA_CENTER

    elements = []

    # 🔶 LOGO (PLACE YOUR IMAGE IN media/logo.png)
    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.5 * inch, height=1.5 * inch))
        elements.append(Spacer(1, 10))

    # 🔶 TITLE
    elements.append(Paragraph("<b>CERTIFICATE OF COMPLETION</b>", title))
    elements.append(Spacer(1, 30))

    # 🔶 BODY
    elements.append(Paragraph("This is to certify that", center))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>{student_name}</b>", title))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("has successfully completed the course", center))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>{course_name}</b>", title))
    elements.append(Spacer(1, 20))

    # 🔶 SCORE
    elements.append(Paragraph(
        f"Score: {score}/{total} ({percentage}%)", center))
    elements.append(Spacer(1, 10))

    # 🔶 COMPANY
    elements.append(Paragraph(
        f"Issued by: <b>{company_name}</b>", center))
    elements.append(Spacer(1, 10))

    # 🔶 DATE
    elements.append(Paragraph(f"Date: {date}", center))
    elements.append(Spacer(1, 20))

    # 🔶 SIGNATURE (OPTIONAL)
    sign_path = os.path.join(settings.MEDIA_ROOT, 'signature.png')
    if os.path.exists(sign_path):
        elements.append(Image(sign_path, width=2 * inch, height=1 * inch))
        elements.append(Paragraph("Authorized Signature", center))

    elements.append(Spacer(1, 20))

    # 🔶 CERTIFICATE ID
    elements.append(Paragraph(
        f"Certificate ID: {certificate_id}", center))

    doc.build(elements, canvasmaker=BorderCanvas)

    return f"certificates/{filename}"
