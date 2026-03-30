from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_internship, name='add_internship'),
    path('list/', views.view_internships, name='view_internships'),
    path('apply/<int:id>/', views.apply_internship, name='apply_internship'),
    path('applications/', views.view_applications, name='view_applications'),
    path('approve/<int:id>/', views.approve_application,
         name='approve_application'),
    path('reject/<int:id>/', views.reject_application,
         name='reject_application'),
    path('certificate/<int:id>/', views.download_certificate,
         name='download_certificate'),
]
