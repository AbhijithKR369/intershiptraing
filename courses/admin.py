from django.contrib import admin
from .models import (
    Course, Material, Enrollment, TrainerApplication,
    QuizBatch, ReattemptRequest, QuizResult, Question,
    StudentAnswer, CourseMessage
)

admin.site.register(Course)
admin.site.register(Material)
admin.site.register(Enrollment)
admin.site.register(TrainerApplication)
admin.site.register(QuizBatch)
admin.site.register(ReattemptRequest)
admin.site.register(QuizResult)
admin.site.register(Question)
admin.site.register(StudentAnswer)
admin.site.register(CourseMessage)
