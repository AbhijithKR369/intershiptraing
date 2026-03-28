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
        'submit-quiz/<int:course_id>/',
        views.submit_quiz,
        name='submit_quiz'
    ),
    path('quiz/<int:course_id>/', views.take_quiz, name='take_quiz'),
    path('student-courses/', views.student_courses, name='student_courses'),

]
