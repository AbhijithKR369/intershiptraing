from courses.models import Enrollment

courses = set(Enrollment.objects.values_list('course_id', flat=True))

for course_id in courses:
    enrolls = Enrollment.objects.filter(
        course_id=course_id,
        status='approved'
    ).order_by('id')

    for i, e in enumerate(enrolls, start=1):
        e.roll_number = i
        e.save()

print("Roll numbers updated successfully")
