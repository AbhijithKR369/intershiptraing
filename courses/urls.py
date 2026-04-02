from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_course, name='add_course'),
    path(
        'materials/<int:course_id>/',
        views.add_material,
        name='add_material'
    ),
    path('list/', views.view_courses, name='view_courses'),
    path('enroll/<int:id>/', views.enroll_course, name='enroll_course'),
    path(
        'trainer/apply/',
        views.trainer_apply_list,
        name='trainer_apply_list'
    ),
    path(
        'trainer/apply/<int:company_id>/',
        views.apply_company,
        name='apply_company'
    ),
    path(
        'trainer/requests/',
        views.view_trainer_requests,
        name='view_trainer_requests'
    ),
    path(
        'trainer/approve/<int:id>/',
        views.approve_trainer,
        name='approve_trainer'
    ),
    path(
        'trainer/reject/<int:id>/',
        views.reject_trainer,
        name='reject_trainer'
    ),
    path(
        'assign-trainer/<int:course_id>/',
        views.assign_trainer,
        name='assign_trainer'
    ),
    path(
        'add-question/<int:course_id>/',
        views.add_question,
        name='add_question'
    ),
    path(
        'batches/<int:course_id>/',
        views.course_quizzes,
        name='course_quizzes'
    ),
    path('quiz/<int:batch_id>/', views.take_quiz, name='take_quiz'),
    path('submit/<int:batch_id>/', views.submit_quiz, name='submit_quiz'),
    path('review/<int:batch_id>/', views.review_quiz, name='review_quiz'),
    path('enroll/approve/<int:id>/', views.approve_enrollment,
         name='approve_enrollment'),
    path('enroll/reject/<int:id>/', views.reject_enrollment,
         name='reject_enrollment'),
    path('results/<int:course_id>/', views.view_results, name='view_results'),
    path('student-courses/', views.student_courses, name='student_courses'),
    path(
        'manage-certificates/',
        views.manage_certificates,
        name='manage_certificates'
    ),
    path(
        'quiz-batches/<int:course_id>/',
        views.quiz_batches,
        name='quiz_batches'
    ),

]
