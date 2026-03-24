from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('company', 'Company'),
        ('trainer', 'Trainer'),
    )

    DOMAIN_CHOICES = (
        ('it', 'IT'),
        ('cloud', 'Cloud'),
        ('management', 'Management'),
        ('ai', 'AI'),
        ('data', 'Data Science'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    domain = models.CharField(
        max_length=20,
        choices=DOMAIN_CHOICES,
        blank=True,
        null=True
    )

    # 👨‍🎓 Student fields
    full_name = models.CharField(max_length=100, blank=True, null=True)
    college_name = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    # 🏢 Company fields
    company_name = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)

    # 👨‍🏫 Trainer fields
    qualification = models.CharField(max_length=200, blank=True, null=True)
    place = models.CharField(max_length=200, blank=True, null=True)

    # 📞 Common fields
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.user.username
