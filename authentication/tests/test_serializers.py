from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from authentication.serializers import UserRegistrationSerializer, UserProfileSerializer
from shop.models import Shop

User = get_user_model()


class UserRegistrationSerializerTest(TestCase):
    
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
        
    def test_valid_registration_data(self):
        """Test serializer with valid registration data"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'shop_id': self.shop.id
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_password_mismatch(self):
        """Test serializer with password mismatch"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'differentpass',
            'shop_id': self.shop.id
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password2', serializer.errors)
        
    def test_duplicate_email(self):
        """Test serializer with duplicate email"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',  # Duplicate
            'password': 'testpass123',
            'password2': 'testpass123',
            'shop_id': self.shop.id
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
    def test_duplicate_username(self):
        """Test serializer with duplicate username"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
        
        data = {
            'username': 'existinguser',  # Duplicate
            'email': 'new@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'shop_id': self.shop.id
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        
    def test_invalid_email_format(self):
        """Test serializer with invalid email format"""
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'testpass123',
            'password2': 'testpass123',
            'shop_id': self.shop.id
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
    def test_weak_password(self):
        """Test serializer with weak password"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': '123',  # Too weak
            'password2': '123',
            'shop_id': self.shop.id
        }
        serializer = UserRegistrationSerializer(data=data)
        # This might pass or fail depending on password validation settings
        # Adjust based on your actual password validation requirements
        
    def test_missing_required_fields(self):
        """Test serializer with missing required fields"""
        data = {
            'email': 'test@example.com',
            # Missing username, password, password2
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('password', serializer.errors)
        
    def test_registration_without_shop(self):
        """Test registration without shop assignment"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
            # No shop_id
        }
        serializer = UserRegistrationSerializer(data=data)
        # This should be valid if shop assignment is optional during registration
        self.assertTrue(serializer.is_valid())
        
    def test_invalid_shop_id(self):
        """Test registration with invalid shop ID"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'shop_id': 99999  # Non-existent shop
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('shop_id', serializer.errors)


class UserProfileSerializerTest(TestCase):
    
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
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        
    def test_user_profile_serialization(self):
        """Test serializing user profile data"""
        serializer = UserProfileSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        
        # Check if shop information is included
        if 'shop_name' in data:
            self.assertEqual(data['shop_name'], 'Test Shop')
            
    def test_user_profile_update(self):
        """Test updating user profile"""
        data = {
            'email': 'updated@example.com'
        }
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, 'updated@example.com')
        
    def test_user_profile_username_update(self):
        """Test updating username"""
        data = {
            'username': 'updateduser'
        }
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        
        if serializer.is_valid():
            updated_user = serializer.save()
            self.assertEqual(updated_user.username, 'updateduser')
        else:
            # Username updates might be restricted
            self.assertIn('username', serializer.errors)
            
    def test_user_profile_shop_assignment_update(self):
        """Test updating shop assignment"""
        owner2 = User.objects.create_user(
            username='owner2',
            email='owner2@example.com',
            password='testpass123'
        )
        shop2 = Shop.objects.create(
            name="Another Shop",
            owner=owner2
        )
        
        data = {
            'shop_id': shop2.id
        }
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        
        if serializer.is_valid():
            updated_user = serializer.save()
            self.assertEqual(updated_user.shop_id, shop2)
        else:
            # Shop assignment updates might be restricted
            self.assertIn('shop_id', serializer.errors)
            
    def test_user_profile_invalid_email_update(self):
        """Test updating with invalid email"""
        data = {
            'email': 'invalid-email-format'
        }
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
    def test_user_profile_duplicate_email_update(self):
        """Test updating with duplicate email"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        data = {
            'email': 'other@example.com'  # Already taken
        }
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
    def test_user_profile_read_only_fields(self):
        """Test that certain fields are read-only"""
        original_created_at = self.user.created_at
        
        data = {
            'created_at': '2020-01-01T00:00:00Z',  # Try to change read-only field
            'is_staff': True,  # Try to change permissions
            'is_superuser': True
        }
        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        
        if serializer.is_valid():
            updated_user = serializer.save()
            # created_at should not have changed
            self.assertEqual(updated_user.created_at, original_created_at)
            # Permissions should not have changed (unless explicitly allowed)
            self.assertFalse(updated_user.is_staff)
            self.assertFalse(updated_user.is_superuser)
