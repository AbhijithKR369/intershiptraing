from django.db import models
from django.contrib.auth.models import User


class Internship(models.Model):
    company = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Application(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    certificate = models.FileField(
        upload_to='internship_certificates/',
        null=True,
        blank=True
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.internship.title}"
