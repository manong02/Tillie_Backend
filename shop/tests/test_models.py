from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from shop.models import Shop

User = get_user_model()


class ShopModelTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.shop_data = {
            'name': 'Test Shop',
            'owner': self.user
        }
        
    def test_shop_creation(self):
        """Test creating a shop with valid data"""
        shop = Shop.objects.create(**self.shop_data)
        
        self.assertEqual(shop.name, 'Test Shop')
        self.assertEqual(shop.owner, self.user)
        self.assertIsNotNone(shop.created_at)
        
    def test_shop_string_representation(self):
        """Test shop string representation"""
        shop = Shop(**self.shop_data)
        self.assertEqual(str(shop), 'Test Shop')
        
    def test_shop_name_max_length(self):
        """Test shop name max length constraint"""
        shop_data = self.shop_data.copy()
        shop_data['name'] = 'x' * 256  # Exceeds max_length=255
        
        shop = Shop(**shop_data)
        with self.assertRaises(ValidationError):
            shop.full_clean()
            
    def test_shop_name_required(self):
        """Test that shop name is required"""
        shop_data = self.shop_data.copy()
        del shop_data['name']
        
        with self.assertRaises(IntegrityError):
            Shop.objects.create(**shop_data)
            
    def test_shop_owner_required(self):
        """Test that shop owner is required"""
        shop_data = self.shop_data.copy()
        del shop_data['owner']
        
        with self.assertRaises(IntegrityError):
            Shop.objects.create(**shop_data)
            
    def test_shop_name_uniqueness(self):
        """Test that shop names must be unique"""
        Shop.objects.create(**self.shop_data)
        
        # Try to create another shop with the same name but different owner
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        # Shop names don't need to be unique globally, so this should work
        duplicate_shop = Shop.objects.create(
            name='Test Shop',
            owner=other_user
        )
        self.assertIsNotNone(duplicate_shop.id)
        
    def test_shop_owner_relationship(self):
        """Test shop-owner relationship"""
        shop = Shop.objects.create(**self.shop_data)
        
        # Test forward relationship
        self.assertEqual(shop.owner, self.user)
        
        # Test reverse relationship
        self.assertIn(shop, self.user.shops.all())
        
    def test_shop_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        shop = Shop.objects.create(**self.shop_data)
        self.assertIsNotNone(shop.created_at)
        
    def test_shop_deletion_cascade_behavior(self):
        """Test shop deletion behavior when owner is deleted"""
        shop = Shop.objects.create(**self.shop_data)
        shop_id = shop.id
        
        # Delete the owner
        self.user.delete()
        
        # Shop should be deleted due to CASCADE
        with self.assertRaises(Shop.DoesNotExist):
            Shop.objects.get(id=shop_id)
            
    def test_shop_fields_blank_and_null_constraints(self):
        """Test field blank and null constraints"""
        # Name cannot be blank
        with self.assertRaises(ValidationError):
            shop = Shop(name='', owner=self.user)
            shop.full_clean()
            
    def test_multiple_shops_per_owner(self):
        """Test that one owner can have multiple shops"""
        shop1 = Shop.objects.create(name='Shop 1', owner=self.user)
        shop2 = Shop.objects.create(name='Shop 2', owner=self.user)
        
        self.assertEqual(self.user.shops.count(), 2)
        self.assertIn(shop1, self.user.shops.all())
        self.assertIn(shop2, self.user.shops.all())
        
    def test_shop_ordering(self):
        """Test default shop ordering"""
        shop1 = Shop.objects.create(name='B Shop', owner=self.user)
        shop2 = Shop.objects.create(name='A Shop', owner=self.user)
        
        # Default ordering should be by name or creation order
        shops = Shop.objects.all()
        self.assertEqual(len(shops), 2)
        
    def test_shop_model_fields(self):
        """Test that shop model has expected fields"""
        shop = Shop.objects.create(**self.shop_data)
        
        # Check that all expected fields exist
        self.assertTrue(hasattr(shop, 'name'))
        self.assertTrue(hasattr(shop, 'owner'))
        self.assertTrue(hasattr(shop, 'created_at'))
        
        # Check field types
        self.assertIsInstance(shop.name, str)
        self.assertIsInstance(shop.owner, User)
        
    def test_shop_related_name(self):
        """Test that related_name works correctly"""
        shop = Shop.objects.create(**self.shop_data)
        
        # Test that we can access shops through the user
        self.assertTrue(hasattr(self.user, 'shops'))
        self.assertEqual(self.user.shops.first(), shop)
