from django.contrib import admin
from .models import Shop

# Register your models here.

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_linked_users')
    
    def get_linked_users(self, obj):
        users = obj.customuser_set.all()
        if users:
            return ', '.join([f"User {user.id}" for user in users])
        return "No users linked"
    get_linked_users.short_description = 'Linked Users'
