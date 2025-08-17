from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Shop

class Command(BaseCommand):
    help = 'Check user shop assignments'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get all users
        users = User.objects.all()
        
        self.stdout.write(f"Found {users.count()} users:")
        
        for user in users:
            shop_info = "No shop assigned"
            if hasattr(user, 'shop_id') and user.shop_id:
                shop_info = f"Shop: {user.shop_id.name} (ID: {user.shop_id.id})"
            
            self.stdout.write(f"  - {user.username} ({user.email}): {shop_info}")
        
        # Show all shops
        shops = Shop.objects.all()
        self.stdout.write(f"\nFound {shops.count()} shops:")
        for shop in shops:
            self.stdout.write(f"  - {shop.name} (ID: {shop.id})")
        
        # Show users without shop assignments
        users_without_shop = User.objects.filter(shop_id__isnull=True)
        if users_without_shop.exists():
            self.stdout.write(f"\n{users_without_shop.count()} users need shop assignment:")
            for user in users_without_shop:
                self.stdout.write(f"  - {user.username}")
