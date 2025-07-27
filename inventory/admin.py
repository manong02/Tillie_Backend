from django.contrib import admin
from .models import Category, Product, Inventory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'shop_id', 'get_products_count')
    list_filter = ('shop_id',)
    search_fields = ('name', 'shop_id__name')
    ordering = ('name',)
    
    def get_products_count(self, obj):
        return obj.products.count()
    get_products_count.short_description = 'Products Count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shop_id')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_id', 'shop_id', 'price', 'vat', 'stock_quantity', 'date_added')
    list_filter = ('category_id', 'shop_id', 'date_added')
    search_fields = ('name', 'category_id__name', 'shop_id__name')
    readonly_fields = ('date_added',)
    ordering = ('-date_added',)
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category_id', 'shop_id')
        }),
        ('Pricing', {
            'fields': ('price', 'vat')
        }),
        ('Inventory', {
            'fields': ('stock_quantity',)
        }),
        ('Timestamps', {
            'fields': ('date_added',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category_id', 'shop_id')


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_product_name', 'get_shop_name', 'quantity', 'change_type', 'date', 'get_user_name')
    list_filter = ('change_type', 'date', 'shop_id', 'product_id__category_id')
    search_fields = ('product_id__name', 'shop_id__name', 'user_id__username', 'notes')
    readonly_fields = ('date',)
    ordering = ('-date',)
    list_per_page = 50
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shop_id', 'product_id', 'quantity', 'change_type')
        }),
        ('Additional Information', {
            'fields': ('notes', 'user_id')
        }),
        ('Timestamps', {
            'fields': ('date',),
            'classes': ('collapse',)
        }),
    )
    
    def get_product_name(self, obj):
        return obj.product_id.name if obj.product_id else 'N/A'
    get_product_name.short_description = 'Product'
    get_product_name.admin_order_field = 'product_id__name'
    
    def get_shop_name(self, obj):
        return obj.shop_id.name if obj.shop_id else 'N/A'
    get_shop_name.short_description = 'Shop'
    get_shop_name.admin_order_field = 'shop_id__name'
    
    def get_user_name(self, obj):
        return obj.user_id.username if obj.user_id else 'System'
    get_user_name.short_description = 'User'
    get_user_name.admin_order_field = 'user_id__username'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product_id', 'shop_id', 'user_id')
    
    # Custom actions
    actions = ['mark_as_adjustment']
    
    def mark_as_adjustment(self, request, queryset):
        updated = queryset.update(change_type='adjustment')
        self.message_user(request, f'{updated} inventory entries marked as adjustments.')
    mark_as_adjustment.short_description = "Mark selected entries as adjustments"
