from django.contrib import admin
from .models import Shop

# Register your models here.

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'get_employee_count', 'created_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('name', 'owner__username', 'owner__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_employee_count(self, obj):
        """Show how many employees (users) are linked to this shop"""
        employee_count = obj.customuser_set.count()
        return f"{employee_count} employees"
    get_employee_count.short_description = 'Employees'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related owner"""
        return super().get_queryset(request).select_related('owner')
