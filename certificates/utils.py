from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from django.conf import settings


def generate_certificate(student_name, course_name, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'certificates', filename)

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    c = canvas.Canvas(file_path, pagesize=A4)

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 750, "Certificate of Completion")

    # Content
    c.setFont("Helvetica", 14)
    c.drawCentredString(300, 700, "This is to certify that")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 660, student_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(300, 620, "has successfully completed the course")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(300, 580, course_name)

    # Footer
    c.setFont("Helvetica", 12)
    c.drawString(50, 100, "Authorized Signature")

    c.save()

    return f"certificates/{filename}"
