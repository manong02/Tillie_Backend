from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from inventory.models import Category, Product, Inventory
from inventory.serializers import (
    CategorySerializer, ProductSerializer, ProductListSerializer,
    InventorySerializer
)
from shop.models import Shop

User = get_user_model()


class CategorySerializerTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.shop = Shop.objects.create(
            name="Test Shop",
            address="123 Test Street",
            phone_number="1234567890"
        )
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic items",
            shop_id=self.shop
        )
        
    def test_category_serialization(self):
        """Test serializing category data"""
        serializer = CategorySerializer(self.category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Electronics')
        self.assertEqual(data['description'], 'Electronic items')
        self.assertEqual(data['shop_name'], 'Test Shop')
        
    def test_category_creation_valid_data(self):
        """Test creating category with valid data"""
        data = {
            'name': 'Books',
            'description': 'Book category',
            'shop_id': self.shop.id
        }
        serializer = CategorySerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, 'Books')
        
    def test_category_creation_missing_name(self):
        """Test creating category without name"""
        data = {
            'description': 'No name category',
            'shop_id': self.shop.id
        }
        serializer = CategorySerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        
    def test_category_creation_invalid_shop(self):
        """Test creating category with invalid shop ID"""
        data = {
            'name': 'Invalid Shop Category',
            'shop_id': 999  # Non-existent shop
        }
        serializer = CategorySerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('shop_id', serializer.errors)


class ProductSerializerTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.shop = Shop.objects.create(
            name="Test Shop",
            address="123 Test Street",
            phone_number="1234567890"
        )
        self.category = Category.objects.create(
            name="Electronics",
            shop_id=self.shop
        )
        self.product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal('99.99'),
            vat=Decimal('20.00'),
            stock_quantity=100,
            category_id=self.category,
            shop_id=self.shop
        )
        
    def test_product_serialization(self):
        """Test serializing product data"""
        serializer = ProductSerializer(self.product)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Product')
        self.assertEqual(Decimal(data['price']), Decimal('99.99'))
        self.assertEqual(Decimal(data['vat']), Decimal('20.00'))
        self.assertEqual(data['stock_quantity'], 100)
        self.assertEqual(data['category_name'], 'Electronics')
        self.assertEqual(data['shop_name'], 'Test Shop')
        
    def test_product_creation_valid_data(self):
        """Test creating product with valid data"""
        data = {
            'name': 'New Product',
            'description': 'New product description',
            'price': '49.99',
            'vat': '15.00',
            'stock_quantity': 25,
            'category_id': self.category.id,
            'shop_id': self.shop.id
        }
        serializer = ProductSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertEqual(product.name, 'New Product')
        self.assertEqual(product.price, Decimal('49.99'))
        
    def test_product_price_validation_negative(self):
        """Test product price validation for negative values"""
        data = {
            'name': 'Invalid Product',
            'price': '-10.00',
            'category_id': self.category.id,
            'shop_id': self.shop.id
        }
        serializer = ProductSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        
    def test_product_vat_validation_over_100(self):
        """Test VAT validation for values over 100%"""
        data = {
            'name': 'Invalid VAT Product',
            'price': '50.00',
            'vat': '150.00',
            'category_id': self.category.id,
            'shop_id': self.shop.id
        }
        serializer = ProductSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('vat', serializer.errors)
        
    def test_product_vat_validation_negative(self):
        """Test VAT validation for negative values"""
        data = {
            'name': 'Negative VAT Product',
            'price': '50.00',
            'vat': '-5.00',
            'category_id': self.category.id,
            'shop_id': self.shop.id
        }
        serializer = ProductSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('vat', serializer.errors)
        
    def test_product_list_serializer(self):
        """Test simplified product list serializer"""
        serializer = ProductListSerializer(self.product)
        data = serializer.data
        
        # Should have fewer fields for performance
        expected_fields = ['id', 'name', 'price', 'stock_quantity', 'category_name']
        for field in expected_fields:
            self.assertIn(field, data)
            
        # Should not have description field
        self.assertNotIn('description', data)


class InventorySerializerTest(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.shop = Shop.objects.create(
            name="Test Shop",
            address="123 Test Street",
            phone_number="1234567890"
        )
        self.category = Category.objects.create(
            name="Electronics",
            shop_id=self.shop
        )
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal('50.00'),
            stock_quantity=100,
            category_id=self.category,
            shop_id=self.shop
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        self.inventory = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=25,
            notes='Test inventory entry'
        )
        
    def test_inventory_serialization(self):
        """Test serializing inventory data"""
        serializer = InventorySerializer(self.inventory)
        data = serializer.data
        
        self.assertEqual(data['movement_type'], 'addition')
        self.assertEqual(data['quantity'], 25)
        self.assertEqual(data['notes'], 'Test inventory entry')
        self.assertEqual(data['product_name'], 'Test Product')
        self.assertEqual(data['shop_name'], 'Test Shop')
        self.assertEqual(data['user_username'], 'test@example.com')
        
    def test_inventory_creation_valid_data(self):
        """Test creating inventory entry with valid data"""
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'removal',
            'quantity': 10,
            'notes': 'Stock removal'
        }
        serializer = InventorySerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        inventory = serializer.save(user_id=self.user)
        self.assertEqual(inventory.movement_type, 'removal')
        self.assertEqual(inventory.quantity, 10)
        
    def test_inventory_creation_invalid_movement_type(self):
        """Test creating inventory with invalid movement type"""
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'invalid_type',
            'quantity': 10
        }
        serializer = InventorySerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('movement_type', serializer.errors)
        
    def test_inventory_quantity_validation_negative(self):
        """Test inventory quantity validation for negative values"""
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'addition',
            'quantity': -5
        }
        serializer = InventorySerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
        
    def test_inventory_quantity_validation_zero_allowed(self):
        """Test that zero quantity is allowed for adjustments"""
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'adjustment',
            'quantity': 0
        }
        serializer = InventorySerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        
    def test_inventory_missing_required_fields(self):
        """Test inventory creation with missing required fields"""
        data = {
            'movement_type': 'addition',
            'quantity': 10
            # Missing product_id and shop_id
        }
        serializer = InventorySerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)
        self.assertIn('shop_id', serializer.errors)
        
    def test_inventory_notes_optional(self):
        """Test that notes field is optional"""
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'addition',
            'quantity': 15
            # No notes field
        }
        serializer = InventorySerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        inventory = serializer.save(user_id=self.user)
        self.assertEqual(inventory.notes, "")
        
    def test_inventory_readonly_fields(self):
        """Test that certain fields are read-only"""
        serializer = InventorySerializer(self.inventory)
        
        # These fields should be read-only
        readonly_fields = ['created_at', 'product_name', 'shop_name', 'user_username']
        
        for field in readonly_fields:
            if field in serializer.fields:
                self.assertTrue(serializer.fields[field].read_only)
