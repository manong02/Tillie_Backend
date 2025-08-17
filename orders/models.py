from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_changes')
    category = models.ForeignKey('inventory.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    total_items = models.IntegerField()
    delivery_date = models.DateTimeField()
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.total_items} items order for {self.shop.name} on {self.delivery_date.strftime('%Y-%m-%d')}."
