from django.db import models
from django.contrib.auth.models import User


class Internship(models.Model):
    company = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)

    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def progress_percentage(self):
        if not self.start_date or not self.end_date:
            return 0
        import datetime
        today = datetime.date.today()
        if today < self.start_date:
            return 0
        if today > self.end_date:
            return 100
        total_days = (self.end_date - self.start_date).days
        passed_days = (today - self.start_date).days
        if total_days <= 0:
            return 100
        return int((passed_days / total_days) * 100)

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
    roll_number = models.IntegerField(null=True, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.internship.title}"
