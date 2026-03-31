from certificates.models import Certificate
from certificates.utils import generate_certificate
from courses.models import QuizResult

certs = Certificate.objects.all()

for cert in certs:
    student = cert.student
    course = cert.course

    result = QuizResult.objects.filter(
        student=student,
        batch__course=course,
        batch__is_final=True
    ).first()

    if not result:
        continue

    file_path = generate_certificate(
        student_name=student.username,
        course_name=course.title,
        score=result.score,
        total=result.total,
        company_name=course.company.username
    )

    cert.file = file_path
    cert.save()

print("Certificates updated successfully")
