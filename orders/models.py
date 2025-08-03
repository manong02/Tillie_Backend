from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):
    shop_id = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, related_name='orders')
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_changes')
    total_items = models.IntegerField()
    delivery_date = models.DateTimeField()
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.total_items} items order for {self.shop_id.name} on {self.delivery_date.strftime('%Y-%m-%d')}."
