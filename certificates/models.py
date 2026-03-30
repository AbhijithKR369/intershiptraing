from django.contrib.auth.models import User
from django.db import models


class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    file = models.FileField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True)
