from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Shop

class Command(BaseCommand):
    help = 'Creates a superuser and shop if they do not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create or get the default shop
        shop, shop_created = Shop.objects.get_or_create(
            name='Default Shop',
        )
        
        if shop_created:
            self.stdout.write(self.style.SUCCESS('Default shop created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('Default shop already exists'))
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            user.shop_id = shop
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser created and assigned to shop'))
        else:
            # Update existing superuser to have shop_id if not set
            user = User.objects.get(username='admin')
            if not user.shop_id:
                user.shop_id = shop
                user.save()
                self.stdout.write(self.style.SUCCESS('Superuser updated with shop assignment'))
            else:
                self.stdout.write(self.style.SUCCESS('Superuser already exists with shop assignment'))
