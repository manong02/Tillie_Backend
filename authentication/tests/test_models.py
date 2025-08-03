from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from shop.models import Shop

User = get_user_model()


class CustomUserModelTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='shopowner',
            email='owner@example.com',
            password='testpass123'
        )
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner=self.owner
        )
        
    def test_create_user_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        
    def test_create_user_with_shop(self):
        """Test creating a user assigned to a shop"""
        user = User.objects.create_user(
            username='shopuser',
            email='shopuser@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        self.assertEqual(user.shop_id, self.shop)
        self.assertEqual(user.email, 'shopuser@example.com')
        
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)
        
    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')
        
    def test_email_unique_constraint(self):
        """Test that email must be unique"""
        User.objects.create_user(
            username='user1',
            email='duplicate@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='duplicate@example.com',
                password='testpass123'
            )
            
    def test_email_normalization(self):
        """Test that email is normalized"""
        user = User.objects.create_user(
            username='testuser',
            email='Test@EXAMPLE.COM',
            password='testpass123'
        )
        self.assertEqual(user.email, 'Test@example.com')
        
    def test_user_without_email_fails(self):
        """Test that creating user without email fails"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='testuser',
                email='',
                password='testpass123'
            )
            
    def test_user_without_password_fails(self):
        """Test that creating user without password fails"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password=''
            )
            
    def test_user_shop_relationship(self):
        """Test user-shop relationship"""
        user = User.objects.create_user(
            username='shopuser',
            email='shopuser@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        
        # Test forward relationship
        self.assertEqual(user.shop_id, self.shop)
        
        # Test that user can be None for shop (nullable)
        user_no_shop = User.objects.create_user(
            username='noshopuser',
            email='noshop@example.com',
            password='testpass123'
        )
        self.assertIsNone(user_no_shop.shop_id)
        
    def test_user_timestamps(self):
        """Test that created_at and updated_at are set"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        
        # Test that updated_at changes on save
        original_updated_at = user.updated_at
        user.email = 'updated@example.com'
        user.save()
        user.refresh_from_db()
        
        self.assertNotEqual(user.updated_at, original_updated_at)
        
    def test_user_shop_deletion_behavior(self):
        """Test what happens when shop is deleted"""
        user = User.objects.create_user(
            username='shopuser',
            email='shopuser@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        
        shop_id = self.shop.id
        self.shop.delete()
        
        # User should still exist but shop_id should be None due to CASCADE
        user.refresh_from_db()
        self.assertIsNone(user.shop_id)
        
    def test_multiple_users_same_shop(self):
        """Test that multiple users can be assigned to the same shop"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        
        self.assertEqual(user1.shop_id, self.shop)
        self.assertEqual(user2.shop_id, self.shop)
        
    def test_user_permissions_defaults(self):
        """Test default user permissions"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        
    def test_staff_user_creation(self):
        """Test creating staff user"""
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.assertTrue(staff_user.is_staff)
        self.assertFalse(staff_user.is_superuser)
        
    def test_user_model_fields(self):
        """Test that user model has expected custom fields"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Check that custom fields exist
        self.assertTrue(hasattr(user, 'shop_id'))
        self.assertTrue(hasattr(user, 'created_at'))
        self.assertTrue(hasattr(user, 'updated_at'))
        
        # Check inherited fields
        self.assertTrue(hasattr(user, 'username'))
        self.assertTrue(hasattr(user, 'email'))
        self.assertTrue(hasattr(user, 'is_staff'))
        self.assertTrue(hasattr(user, 'is_superuser'))
        self.assertTrue(hasattr(user, 'is_active'))
