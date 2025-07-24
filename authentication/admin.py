from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'get_hashed_password', 'email', 'get_shop_id', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'password')
    
    # Fields to show in the edit form
    fields = ('username', 'email', 'first_name', 'last_name', 'shop', 'is_active', 'is_staff', 'is_superuser', 'password', 'created_at', 'updated_at')
    
    # Allow editing these fields
    list_editable = ('email',)
    
    def get_hashed_password(self, obj):
        return obj.password[:20] + "..." if len(obj.password) > 20 else obj.password
    get_hashed_password.short_description = 'Hashed Password'
    
    def get_shop_id(self, obj):
        return obj.shop.id if obj.shop else "No shop"
    get_shop_id.short_description = 'Shop ID'
