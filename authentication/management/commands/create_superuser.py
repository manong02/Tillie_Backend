from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Shop

class Command(BaseCommand):
    help = 'Creates a superuser and shop if they do not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create superuser first
        user, user_created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if user_created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists'))
        
        # Create or get the default shop with the user as owner
        shop, shop_created = Shop.objects.get_or_create(
            name='Default Shop',
            defaults={
                'owner': user
            }
        )
        
        if shop_created:
            self.stdout.write(self.style.SUCCESS('Default shop created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('Default shop already exists'))
        
        # Assign shop to user if not already assigned
        if not user.shop_id:
            user.shop_id = shop
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser assigned to shop'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already has shop assignment'))
