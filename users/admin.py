from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
    # 在后台列表显示自定义字段
    list_display = ('username', 'email', 'role', 'balance', 'credit_rating', 'is_staff')
    # 在详情也增加自定义字段集的显示
    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('role', 'credit_rating', 'id_card', 'business_license', 'balance')}),
    )