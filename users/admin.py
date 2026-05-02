from django.contrib import admin
from .models import Profile, Notification

from django.utils.html import format_html

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'domain', 'is_verified', 'registration_number', 'view_certificate']
    list_editable = ['is_verified']
    list_filter = ['role', 'is_verified']

    def view_certificate(self, obj):
        if obj.registration_proof:
            return format_html('<a href="{}" target="_blank">View Document</a>', obj.registration_proof.url)
        return "No Document"
    view_certificate.short_description = "Registration Proof"


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Notification)
