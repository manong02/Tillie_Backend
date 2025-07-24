from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
