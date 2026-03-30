from django.http import FileResponse
from .models import Certificate
import os
from django.conf import settings


def download_certificate(request, cert_id):
    cert = Certificate.objects.get(id=cert_id)

    file_path = os.path.join(settings.MEDIA_ROOT, str(cert.file))

    return FileResponse(open(file_path, 'rb'), as_attachment=True)
