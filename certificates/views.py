import os
from django.conf import settings
from django.http import FileResponse, HttpResponse
from .models import Certificate


def download_certificate(request, cert_id):
    cert = Certificate.objects.get(id=cert_id)

    file_path = os.path.join(settings.MEDIA_ROOT, str(cert.file))

    if not os.path.exists(file_path):
        return HttpResponse("File not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=True)
