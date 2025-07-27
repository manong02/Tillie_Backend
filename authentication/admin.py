from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Add custom fields to the existing UserAdmin fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Shop Information', {'fields': ('shop_id', 'created_at', 'updated_at')}),
    )
    
    # Add custom fields to the add user form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Shop Information', {'fields': ('shop_id',)}),
    )
    
    # Customize the list display to show your desired fields
    list_display = ('id', 'username', 'email', 'get_shop_id', 'is_staff', 'is_active', 'created_at')
    
    # Add filters for easy management
    list_filter = UserAdmin.list_filter + ('shop_id', 'created_at')
    
    # Make timestamps read-only
    readonly_fields = ('created_at', 'updated_at')
    
    # Allow quick editing of some fields
    list_editable = ('is_active',)
    
    def get_shop_id(self, obj):
        return obj.shop_id.id if obj.shop_id else "No shop"
    get_shop_id.short_description = 'Shop ID'
