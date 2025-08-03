from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from shop.models import Shop

User = get_user_model()


class ShopSerializerTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner=self.user
        )
        
    def test_shop_serializer_placeholder(self):
        """Placeholder test for shop serializer"""
        # This test will be implemented when shop serializers are created
        try:
            from shop.serializers import ShopSerializer
            
            serializer = ShopSerializer(self.shop)
            data = serializer.data
            
            self.assertEqual(data['name'], 'Test Shop')
            self.assertIn('created_at', data)
            
        except ImportError:
            # Skip test if serializer doesn't exist yet
            self.skipTest("ShopSerializer not implemented yet")
            
    def test_shop_create_serializer_placeholder(self):
        """Placeholder test for shop creation serializer"""
        try:
            from shop.serializers import ShopCreateSerializer
            
            # Test valid data
            valid_data = {
                'name': 'New Shop'
            }
            serializer = ShopCreateSerializer(data=valid_data)
            self.assertTrue(serializer.is_valid())
            
            # Test invalid data - missing required fields
            invalid_data = {
                # Missing name
            }
            serializer = ShopCreateSerializer(data=invalid_data)
            self.assertFalse(serializer.is_valid())
            
        except ImportError:
            self.skipTest("ShopCreateSerializer not implemented yet")
            
    def test_shop_update_serializer_placeholder(self):
        """Placeholder test for shop update serializer"""
        try:
            from shop.serializers import ShopUpdateSerializer
            
            data = {'name': 'Updated Shop Name'}
            serializer = ShopUpdateSerializer(self.shop, data=data, partial=True)
            self.assertTrue(serializer.is_valid())
            
        except ImportError:
            self.skipTest("ShopUpdateSerializer not implemented yet")
            
    def test_shop_list_serializer_placeholder(self):
        """Placeholder test for simplified shop list serializer"""
        try:
            from shop.serializers import ShopListSerializer
            
            serializer = ShopListSerializer(self.shop)
            data = serializer.data
            
            # List serializer should have fewer fields for performance
            expected_fields = ['id', 'name']
            for field in expected_fields:
                self.assertIn(field, data)
                
        except ImportError:
            self.skipTest("ShopListSerializer not implemented yet")
            
    def test_shop_serializer_with_owner_placeholder(self):
        """Placeholder test for shop serializer with owner relationship"""
        try:
            from shop.serializers import ShopSerializer
            
            owner = User.objects.create_user(
                username='testowner',
                email='owner@example.com',
                password='testpass123'
            )
            shop_with_owner = Shop.objects.create(
                name="Owned Shop",
                owner=owner
            )
            
            serializer = ShopSerializer(shop_with_owner)
            data = serializer.data
            
            self.assertEqual(data['owner'], owner.id)
            
        except ImportError:
            self.skipTest("ShopSerializer not implemented yet")
            
    def test_shop_serializer_validation_rules_placeholder(self):
        """Placeholder test for shop serializer validation rules"""
        try:
            from shop.serializers import ShopCreateSerializer
            
            # Test name length validation
            long_name_data = {
                'name': 'x' * 256  # Exceeds max_length=255
            }
            serializer = ShopCreateSerializer(data=long_name_data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('name', serializer.errors)
            
        except ImportError:
            self.skipTest("ShopCreateSerializer not implemented yet")
            
    def test_shop_model_direct_validation(self):
        """Test shop model validation directly (works without serializers)"""
        # Test that we can create a shop with valid data
        shop = Shop.objects.create(
            name="Direct Test Shop",
            owner=self.user
        )
        self.assertEqual(shop.name, "Direct Test Shop")
        self.assertEqual(shop.owner, self.user)
        
        # Test name length constraint
        with self.assertRaises(Exception):  # Could be ValidationError or DataError
            long_name_shop = Shop(
                name='x' * 256,  # Exceeds max_length=255
                owner=self.user
            )
            long_name_shop.full_clean()
            
    def test_shop_model_relationships(self):
        """Test shop model relationships (works without serializers)"""
        # Test that owner relationship works
        self.assertEqual(self.shop.owner, self.user)
        
        # Test reverse relationship
        self.assertIn(self.shop, self.user.shops.all())
        
        # Test multiple shops per owner
        shop2 = Shop.objects.create(
            name="Second Shop",
            owner=self.user
        )
        
        self.assertEqual(self.user.shops.count(), 2)
        self.assertIn(shop2, self.user.shops.all())
