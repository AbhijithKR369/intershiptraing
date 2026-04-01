from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='company_courses'   # ✅ added
    )

    trainer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainer_courses'   # ✅ added
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    max_students = models.IntegerField(default=30)

    def __str__(self):
        return self.title


class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    file = models.FileField(upload_to='materials/', null=True, blank=True)
    link = models.URLField(blank=True)

    class_link = models.URLField(blank=True)
    class_time = models.DateTimeField(null=True, blank=True)

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_materials'   # ✅ added
    )

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    roll_number = models.IntegerField(null=True, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.student.username} - {self.course.title} ({self.status})"


class TrainerApplication(models.Model):
    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trainer_applications'   # ✅ added
    )

    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='company_trainer_requests'   # ✅ added
    )

    resume = models.FileField(
        upload_to='trainer_resumes/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.trainer.username} → {self.company.username}"


class QuizBatch(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='batches')
    title = models.CharField(max_length=100)  # e.g. "Quiz 1", "Week 1 Test"
    is_final = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class QuizResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    batch = models.ForeignKey(QuizBatch, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()


class Question(models.Model):
    batch = models.ForeignKey(
        QuizBatch,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    question_text = models.TextField()

    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)

    correct_option = models.IntegerField()  # 1,2,3,4

    def __str__(self):
        return self.question_text


class StudentAnswer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.IntegerField()

    class Meta:
        unique_together = ('student', 'question')
