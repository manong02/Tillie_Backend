from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_shop_name', 'total_items', 'delivery_date', 'get_status', 'get_user_name', 'created_at')
    list_filter = ('shop_id', 'delivery_date', 'created_at')
    search_fields = ('shop_id__name', 'user_id__username', 'notes')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'delivery_date'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('shop_id', 'total_items', 'delivery_date')
        }),
        ('Additional Details', {
            'fields': ('notes', 'user_id')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_shop_name(self, obj):
        return obj.shop_id.name if obj.shop_id else 'N/A'
    get_shop_name.short_description = 'Shop'
    get_shop_name.admin_order_field = 'shop_id__name'
    
    def get_user_name(self, obj):
        return obj.user_id.username if obj.user_id else 'System'
    get_user_name.short_description = 'Created By'
    get_user_name.admin_order_field = 'user_id__username'
    
    def get_status(self, obj):
        now = timezone.now()
        if obj.delivery_date <= now:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Delivered</span>'
            )
        elif obj.delivery_date <= now + timezone.timedelta(days=1):
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⚠ Due Soon</span>'
            )
        else:
            return format_html(
                '<span style="color: #007bff; font-weight: bold;">📅 Pending</span>'
            )
    get_status.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shop_id', 'user_id')
    
    # Custom actions
    actions = ['mark_as_urgent', 'extend_delivery_date']
    
    def mark_as_urgent(self, request, queryset):
        # Add urgent note to selected orders
        updated = 0
        for order in queryset:
            if order.delivery_date > timezone.now():
                current_notes = order.notes or ""
                if "URGENT" not in current_notes:
                    order.notes = f"URGENT: {current_notes}".strip()
                    order.save()
                    updated += 1
        
        self.message_user(request, f'{updated} orders marked as urgent.')
    mark_as_urgent.short_description = "Mark selected orders as urgent"
    
    def extend_delivery_date(self, request, queryset):
        # Extend delivery date by 1 day for future orders
        from datetime import timedelta
        updated = 0
        
        for order in queryset:
            if order.delivery_date > timezone.now():
                order.delivery_date += timedelta(days=1)
                order.save()
                updated += 1
        
        self.message_user(request, f'{updated} orders had their delivery date extended by 1 day.')
    extend_delivery_date.short_description = "Extend delivery date by 1 day"
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of future orders
        if obj and obj.delivery_date <= timezone.now():
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        
        # Make delivery_date readonly for past orders
        if obj and obj.delivery_date <= timezone.now():
            readonly.extend(['delivery_date', 'total_items', 'shop_id'])
            
        return readonly
