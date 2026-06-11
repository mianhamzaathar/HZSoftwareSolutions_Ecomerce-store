from django.contrib import admin

from .models import OTPVerification, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'phone', 'address')


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'code', 'is_used', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_used')
    search_fields = ('user__username', 'code')
