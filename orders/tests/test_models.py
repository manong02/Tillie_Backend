from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from shop.models import Shop

User = get_user_model()


class OrderModelTest(TestCase):
    
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
        
    def test_create_order_with_required_fields(self):
        """Test creating an order with all required fields"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=50,
            delivery_date=self.future_date,
            notes="Test order"
        )
        
        self.assertEqual(order.shop_id, self.shop)
        self.assertEqual(order.user_id, self.user)
        self.assertEqual(order.total_items, 50)
        self.assertEqual(order.delivery_date, self.future_date)
        self.assertEqual(order.notes, "Test order")
        self.assertIsNotNone(order.created_at)
        
    def test_order_string_representation(self):
        """Test order string representation"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=25,
            delivery_date=self.future_date
        )
        expected_str = f"25 items order for {self.shop.name} on {self.future_date.strftime('%Y-%m-%d')}."
        self.assertEqual(str(order), expected_str)
        
    def test_order_without_user(self):
        """Test creating order without user (system order)"""
        order = Order.objects.create(
            shop_id=self.shop,
            total_items=100,
            delivery_date=self.future_date,
            notes="System generated order"
        )
        
        self.assertIsNone(order.user_id)
        self.assertEqual(order.total_items, 100)
        
    def test_order_without_notes(self):
        """Test creating order without notes"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=30,
            delivery_date=self.future_date
        )
        
        self.assertEqual(order.notes, "")
        
    def test_order_total_items_validation(self):
        """Test total items validation"""
        # Zero items should raise validation error
        order = Order(
            shop_id=self.shop,
            user_id=self.user,
            total_items=0,
            delivery_date=self.future_date
        )
        with self.assertRaises(ValidationError):
            order.full_clean()
            
        # Negative items should raise validation error
        order = Order(
            shop_id=self.shop,
            user_id=self.user,
            total_items=-5,
            delivery_date=self.future_date
        )
        with self.assertRaises(ValidationError):
            order.full_clean()
            
    def test_order_delivery_date_validation(self):
        """Test delivery date validation"""
        past_date = timezone.now() - timedelta(days=1)
        
        # Past delivery date should raise validation error
        order = Order(
            shop_id=self.shop,
            user_id=self.user,
            total_items=10,
            delivery_date=past_date
        )
        with self.assertRaises(ValidationError):
            order.full_clean()
            
    def test_order_notes_max_length(self):
        """Test notes field maximum length"""
        long_notes = 'x' * 501  # Assuming max_length=500
        
        order = Order(
            shop_id=self.shop,
            user_id=self.user,
            total_items=10,
            delivery_date=self.future_date,
            notes=long_notes
        )
        with self.assertRaises(ValidationError):
            order.full_clean()
            
    def test_order_shop_relationship(self):
        """Test the relationship between order and shop"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=15,
            delivery_date=self.future_date
        )
        
        # Test forward relationship
        self.assertEqual(order.shop_id.name, "Test Shop")
        
        # Test reverse relationship
        self.assertIn(order, self.shop.orders.all())
        
    def test_order_user_relationship(self):
        """Test the relationship between order and user"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=20,
            delivery_date=self.future_date
        )
        
        # Test forward relationship
        self.assertEqual(order.user_id.email, "test@example.com")
        
        # Test reverse relationship
        self.assertIn(order, self.user.orders_changes.all())
        
    def test_order_created_at_auto_now_add(self):
        """Test that created_at is automatically set"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=35,
            delivery_date=self.future_date
        )
        
        self.assertIsNotNone(order.created_at)
        
        # Test that created_at doesn't change on update
        original_created_at = order.created_at
        order.notes = "Updated notes"
        order.save()
        order.refresh_from_db()
        self.assertEqual(order.created_at, original_created_at)
        
    def test_order_deletion_cascade_behavior(self):
        """Test what happens when related objects are deleted"""
        order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=40,
            delivery_date=self.future_date
        )
        
        # Delete user and check order behavior (should set user to NULL)
        user_id = self.user.id
        self.user.delete()
        order.refresh_from_db()
        self.assertIsNone(order.user_id)
        
        # Delete shop and check order behavior (should delete order)
        shop_id = self.shop.id
        self.shop.delete()
        self.assertFalse(Order.objects.filter(id=order.id).exists())
        
    def test_multiple_orders_same_shop(self):
        """Test that multiple orders can be created for the same shop"""
        order1 = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=10,
            delivery_date=self.future_date
        )
        order2 = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=20,
            delivery_date=self.future_date + timedelta(days=1)
        )
        
        self.assertEqual(self.shop.orders.count(), 2)
        self.assertIn(order1, self.shop.orders.all())
        self.assertIn(order2, self.shop.orders.all())
        
    def test_order_default_ordering(self):
        """Test default ordering of orders"""
        # Create orders with different creation times
        order1 = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=10,
            delivery_date=self.future_date
        )
        order2 = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=20,
            delivery_date=self.future_date + timedelta(days=1)
        )
        
        # Should be ordered by created_at descending (newest first)
        orders = list(Order.objects.all())
        self.assertEqual(orders[0], order2)  # Most recent first
        self.assertEqual(orders[1], order1)
        
    def test_order_fields_blank_and_null_constraints(self):
        """Test field constraints for blank and null values"""
        # Shop should not be null
        with self.assertRaises(ValidationError):
            order = Order(
                user_id=self.user,
                total_items=10,
                delivery_date=self.future_date
            )
            order.full_clean()
            
        # Total items should not be null
        with self.assertRaises(ValidationError):
            order = Order(
                shop_id=self.shop,
                user_id=self.user,
                delivery_date=self.future_date
            )
            order.full_clean()
            
        # Delivery date should not be null
        with self.assertRaises(ValidationError):
            order = Order(
                shop_id=self.shop,
                user_id=self.user,
                total_items=10
            )
            order.full_clean()
