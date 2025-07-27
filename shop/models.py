from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model ()

class Shop(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name