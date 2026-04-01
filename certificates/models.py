from django.contrib.auth.models import User
from internships.models import Internship
from django.db import models
from courses.models import Course


class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to='certificates/')
    is_manual = models.BooleanField(default=False)
    internship = models.ForeignKey(
        Internship, null=True, blank=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
