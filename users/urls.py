from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('company/', views.company_dashboard, name='company_dashboard'),
    path('trainer/', views.trainer_dashboard, name='trainer_dashboard'),
]
