from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIRequestFactory
from orders.models import Order
from orders.serializers import OrderSerializer, OrderListSerializer, OrderCreateSerializer
from shop.models import Shop

User = get_user_model()


class OrderSerializerTest(TestCase):
    
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
        self.future_date = timezone.now() + timedelta(days=7)
        self.order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=50,
            delivery_date=self.future_date,
            notes="Test order"
        )
        
    def test_order_serialization(self):
        """Test serializing order data"""
        serializer = OrderSerializer(self.order)
        data = serializer.data
        
        self.assertEqual(data['total_items'], 50)
        self.assertEqual(data['notes'], 'Test order')
        self.assertEqual(data['shop_name'], 'Test Shop')
        self.assertEqual(data['user_username'], 'testuser')
        self.assertIn('created_at', data)
        
    def test_order_creation_valid_data(self):
        """Test creating order with valid data"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 75,
            'delivery_date': (timezone.now() + timedelta(days=10)).isoformat(),
            'notes': 'New order'
        }
        serializer = OrderSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        order = serializer.save(user_id=self.user)
        self.assertEqual(order.total_items, 75)
        self.assertEqual(order.notes, 'New order')
        
    def test_order_total_items_validation_zero(self):
        """Test total items validation for zero value"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 0,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Invalid order'
        }
        serializer = OrderSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_items', serializer.errors)
        
    def test_order_total_items_validation_negative(self):
        """Test total items validation for negative value"""
        data = {
            'shop_id': self.shop.id,
            'total_items': -5,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Invalid order'
        }
        serializer = OrderSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_items', serializer.errors)
        
    def test_order_total_items_validation_too_large(self):
        """Test total items validation for values over 10,000"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 15000,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Too large order'
        }
        serializer = OrderSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_items', serializer.errors)
        
    def test_order_delivery_date_validation_past(self):
        """Test delivery date validation for past dates"""
        past_date = timezone.now() - timedelta(days=1)
        
        data = {
            'shop_id': self.shop.id,
            'total_items': 25,
            'delivery_date': past_date.isoformat(),
            'notes': 'Past date order'
        }
        serializer = OrderSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('delivery_date', serializer.errors)
        
    def test_order_delivery_date_validation_too_far_future(self):
        """Test delivery date validation for dates more than 1 year in future"""
        far_future = timezone.now() + timedelta(days=400)
        
        data = {
            'shop_id': self.shop.id,
            'total_items': 25,
            'delivery_date': far_future.isoformat(),
            'notes': 'Far future order'
        }
        serializer = OrderSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('delivery_date', serializer.errors)
        
    def test_order_notes_validation_too_short(self):
        """Test notes validation for very short notes"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 25,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'ab'  # Less than 3 characters
        }
        serializer = OrderSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('notes', serializer.errors)
        
    def test_order_notes_validation_empty_allowed(self):
        """Test that empty notes are allowed"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 25,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': ''
        }
        serializer = OrderSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        
    def test_order_notes_validation_whitespace_stripped(self):
        """Test that notes whitespace is stripped"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 25,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': '  Valid note  '
        }
        serializer = OrderSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        order = serializer.save(user_id=self.user)
        self.assertEqual(order.notes, 'Valid note')


class OrderListSerializerTest(TestCase):
    
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
        self.order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=30,
            delivery_date=timezone.now() + timedelta(days=5),
            notes="List test order"
        )
        
    def test_order_list_serialization(self):
        """Test serializing order for list view"""
        serializer = OrderListSerializer(self.order)
        data = serializer.data
        
        # Should have fewer fields for performance
        expected_fields = ['id', 'shop_name', 'total_items', 'delivery_date', 'created_at']
        for field in expected_fields:
            self.assertIn(field, data)
            
        # Should not have notes field for list view
        self.assertNotIn('notes', data)
        self.assertNotIn('user_username', data)
        
    def test_order_list_shop_name_display(self):
        """Test that shop name is properly displayed in list"""
        serializer = OrderListSerializer(self.order)
        data = serializer.data
        
        self.assertEqual(data['shop_name'], 'Test Shop')
        self.assertEqual(data['total_items'], 30)


class OrderCreateSerializerTest(TestCase):
    
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
        
    def test_order_create_serialization(self):
        """Test order creation serializer"""
        data = {
            'shop_id': self.shop.id,
            'total_items': 40,
            'delivery_date': (timezone.now() + timedelta(days=3)).isoformat(),
            'notes': 'Create test order'
        }
        serializer = OrderCreateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        order = serializer.save(user_id=self.user)
        self.assertEqual(order.total_items, 40)
        self.assertEqual(order.notes, 'Create test order')
        
    def test_order_create_minimum_delivery_time(self):
        """Test that delivery date must be at least 24 hours from now"""
        # Less than 24 hours should fail
        near_future = timezone.now() + timedelta(hours=12)
        
        data = {
            'shop_id': self.shop.id,
            'total_items': 20,
            'delivery_date': near_future.isoformat(),
            'notes': 'Too soon order'
        }
        serializer = OrderCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('delivery_date', serializer.errors)
        
    def test_order_create_valid_24_hours_plus(self):
        """Test that delivery date 24+ hours from now is valid"""
        valid_future = timezone.now() + timedelta(hours=25)
        
        data = {
            'shop_id': self.shop.id,
            'total_items': 20,
            'delivery_date': valid_future.isoformat(),
            'notes': 'Valid timing order'
        }
        serializer = OrderCreateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        
    def test_order_create_missing_required_fields(self):
        """Test order creation with missing required fields"""
        data = {
            'total_items': 15,
            'notes': 'Incomplete order'
            # Missing shop_id and delivery_date
        }
        serializer = OrderCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('shop_id', serializer.errors)
        self.assertIn('delivery_date', serializer.errors)
        
    def test_order_create_invalid_shop_id(self):
        """Test order creation with non-existent shop ID"""
        data = {
            'shop_id': 999,  # Non-existent shop
            'total_items': 25,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Invalid shop order'
        }
        serializer = OrderCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('shop_id', serializer.errors)
        
    def test_order_create_cross_field_validation(self):
        """Test cross-field validation in create serializer"""
        # This test can be expanded when more business rules are added
        data = {
            'shop_id': self.shop.id,
            'total_items': 50,
            'delivery_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'notes': 'Cross validation test'
        }
        serializer = OrderCreateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        # The validate() method should process without errors
        validated_data = serializer.validate(data)
        self.assertEqual(validated_data, data)
        
    def test_order_create_readonly_fields(self):
        """Test that certain fields are not included in create serializer"""
        serializer = OrderCreateSerializer()
        
        # These fields should not be in create serializer
        excluded_fields = ['id', 'user_id', 'created_at', 'shop_name', 'user_username']
        
        for field in excluded_fields:
            self.assertNotIn(field, serializer.fields)
            
    def test_order_create_field_validation_edge_cases(self):
        """Test edge cases for field validation"""
        # Test maximum valid total_items
        data = {
            'shop_id': self.shop.id,
            'total_items': 10000,  # Maximum allowed
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Max items order'
        }
        serializer = OrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test maximum future date (just under 1 year)
        max_future = timezone.now() + timedelta(days=364)
        data = {
            'shop_id': self.shop.id,
            'total_items': 25,
            'delivery_date': max_future.isoformat(),
            'notes': 'Max future order'
        }
        serializer = OrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
