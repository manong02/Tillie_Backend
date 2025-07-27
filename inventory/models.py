from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=255)
    shop_id = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    category_id = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    shop_id = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.DecimalField(max_digits=5, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_stock = 0

        if not is_new:
            old_stock = Product.objects.get(pk=self.pk).stock_quantity
        
        super().save(*args, **kwargs)

        if is_new and self.stock_quantity > 0:
            Inventory.objects.create(
                shop_id=self.shop_id,
                product_id=self,
                quantity=self.stock_quantity,
                change_type='initial_stock',
                notes='Initial stock entry',
                user_id=self.shop_id.owner
            )

class Inventory(models.Model):
    CHANGE_TYPES = [
        ('addition', 'Addition'),
        ('removal', 'Removal'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('transfer', 'Transfer'),
        ('initial_stock', 'Initial Stock'),
    ]

    shop_id = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='inventory_entries')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_entries')
    quantity = models.IntegerField()
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_changes')

    def __str__(self):
        return f"{self.change_type} of {self.quantity} × {self.product_id.name} ({self.shop_id.name})"
