import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
django.setup()

from users.models import Profile

# Set all existing profiles to verified so no one is locked out
profiles = Profile.objects.all()
for p in profiles:
    p.is_verified = True
    p.save()

print(f"Verified {profiles.count()} existing profiles.")
