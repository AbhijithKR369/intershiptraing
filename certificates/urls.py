from django.urls import path
from . import views

urlpatterns = [
    path(
        'certificate/<int:cert_id>/download/',
        views.download_certificate,
        name='download_certificate'
    ),
]
