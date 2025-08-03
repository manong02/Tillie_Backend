from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from decimal import Decimal
from inventory.models import Category, Product, Inventory
from shop.models import Shop

User = get_user_model()


class CategoryModelTest(TestCase):
    
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
        
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name="Electronics",
            shop_id=self.shop
        )
        
        self.assertEqual(category.name, "Electronics")
        self.assertEqual(category.shop_id, self.shop)
        
    def test_category_string_representation(self):
        """Test category string representation"""
        category = Category.objects.create(
            name="Books",
            shop_id=self.shop
        )
        self.assertEqual(str(category), "Books")
        
    def test_category_name_uniqueness_per_shop(self):
        """Test that category names must be unique per shop"""
        Category.objects.create(name="Electronics", shop_id=self.shop)
        
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Electronics", shop_id=self.shop)
            
    def test_category_can_have_same_name_different_shops(self):
        """Test that different shops can have categories with same name"""
        shop2 = Shop.objects.create(
            name="Another Shop",
            address="456 Another Street",
            phone_number="0987654321"
        )
        
        Category.objects.create(name="Electronics", shop_id=self.shop)
        category2 = Category.objects.create(name="Electronics", shop_id=shop2)
        
        self.assertEqual(Category.objects.filter(name="Electronics").count(), 2)


class ProductModelTest(TestCase):
    
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
        self.category = Category.objects.create(
            name="Electronics",
            shop_id=self.shop
        )
        
    def test_create_product(self):
        """Test creating a product"""
        product = Product.objects.create(
            name="Laptop",
            price=Decimal('999.99'),
            vat=Decimal('20.00'),
            stock_quantity=10,
            category_id=self.category,
            shop_id=self.shop
        )
        
        self.assertEqual(product.name, "Laptop")
        self.assertEqual(product.price, Decimal('999.99'))
        self.assertEqual(product.vat, Decimal('20.00'))
        self.assertEqual(product.stock_quantity, 10)
        self.assertEqual(product.category_id, self.category)
        self.assertEqual(product.shop_id, self.shop)
        
    def test_product_string_representation(self):
        """Test product string representation"""
        product = Product.objects.create(
            name="Mouse",
            price=Decimal('29.99'),
            category_id=self.category,
            shop_id=self.shop
        )
        self.assertEqual(str(product), "Mouse")
        
    def test_product_price_validation(self):
        """Test product price validation"""
        # Negative price should raise validation error
        product = Product(
            name="Invalid Product",
            price=Decimal('-10.00'),
            category_id=self.category,
            shop_id=self.shop
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
            
    def test_product_vat_validation(self):
        """Test VAT validation (0-100%)"""
        # VAT over 100% should raise validation error
        product = Product(
            name="Invalid VAT Product",
            price=Decimal('100.00'),
            vat=Decimal('150.00'),
            category_id=self.category,
            shop_id=self.shop
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
            
    def test_product_stock_quantity_validation(self):
        """Test stock quantity validation"""
        # Negative stock should raise validation error
        product = Product(
            name="Invalid Stock Product",
            price=Decimal('50.00'),
            stock_quantity=-5,
            category_id=self.category,
            shop_id=self.shop
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
            
    def test_product_automatic_inventory_creation(self):
        """Test that creating product with stock creates initial inventory entry"""
        product = Product.objects.create(
            name="Auto Inventory Product",
            price=Decimal('100.00'),
            stock_quantity=50,
            category_id=self.category,
            shop_id=self.shop
        )
        
        # Should automatically create an initial inventory entry
        inventory_entries = Inventory.objects.filter(product_id=product)
        self.assertEqual(inventory_entries.count(), 1)
        
        initial_entry = inventory_entries.first()
        self.assertEqual(initial_entry.movement_type, 'initial_stock')
        self.assertEqual(initial_entry.quantity, 50)
        
    def test_product_without_stock_no_inventory_creation(self):
        """Test that creating product without stock doesn't create inventory entry"""
        product = Product.objects.create(
            name="No Stock Product",
            price=Decimal('100.00'),
            stock_quantity=0,
            category_id=self.category,
            shop_id=self.shop
        )
        
        # Should not create inventory entry for zero stock
        inventory_entries = Inventory.objects.filter(product_id=product)
        self.assertEqual(inventory_entries.count(), 0)


class InventoryModelTest(TestCase):
    
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
        self.category = Category.objects.create(
            name="Electronics",
            shop_id=self.shop
        )
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal('50.00'),
            stock_quantity=0,  # Start with 0 to avoid auto inventory creation
            category_id=self.category,
            shop_id=self.shop
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        
    def test_create_inventory_entry(self):
        """Test creating an inventory entry"""
        inventory = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=25,
            notes="Initial stock addition"
        )
        
        self.assertEqual(inventory.product_id, self.product)
        self.assertEqual(inventory.shop_id, self.shop)
        self.assertEqual(inventory.user_id, self.user)
        self.assertEqual(inventory.movement_type, 'addition')
        self.assertEqual(inventory.quantity, 25)
        self.assertEqual(inventory.notes, "Initial stock addition")
        
    def test_inventory_string_representation(self):
        """Test inventory string representation"""
        inventory = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=10
        )
        expected_str = f"addition of 10 for {self.product.name}"
        self.assertEqual(str(inventory), expected_str)
        
    def test_inventory_movement_type_choices(self):
        """Test inventory movement type choices"""
        valid_types = ['addition', 'removal', 'adjustment', 'return', 'transfer', 'initial_stock']
        
        for movement_type in valid_types:
            inventory = Inventory.objects.create(
                product_id=self.product,
                shop_id=self.shop,
                user_id=self.user,
                movement_type=movement_type,
                quantity=5
            )
            self.assertEqual(inventory.movement_type, movement_type)
            
    def test_inventory_quantity_validation(self):
        """Test inventory quantity validation"""
        # Zero quantity should be allowed for adjustments
        inventory = Inventory(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='adjustment',
            quantity=0
        )
        inventory.full_clean()  # Should not raise
        
        # Negative quantity should raise validation error for additions
        inventory = Inventory(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=-5
        )
        with self.assertRaises(ValidationError):
            inventory.full_clean()
            
    def test_inventory_created_at_auto_now_add(self):
        """Test that created_at is automatically set"""
        inventory = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=10
        )
        self.assertIsNotNone(inventory.created_at)
        
    def test_inventory_user_can_be_null(self):
        """Test that inventory can be created without user (system entries)"""
        inventory = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            movement_type='initial_stock',
            quantity=100
        )
        self.assertIsNone(inventory.user_id)
        
    def test_inventory_notes_optional(self):
        """Test that notes field is optional"""
        inventory = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=5
        )
        self.assertEqual(inventory.notes, "")
        
    def test_inventory_ordering(self):
        """Test default ordering of inventory entries"""
        # Create multiple entries
        inventory1 = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='addition',
            quantity=10
        )
        inventory2 = Inventory.objects.create(
            product_id=self.product,
            shop_id=self.shop,
            user_id=self.user,
            movement_type='removal',
            quantity=5
        )
        
        # Should be ordered by created_at descending (newest first)
        entries = list(Inventory.objects.all())
        self.assertEqual(entries[0], inventory2)  # Most recent first
        self.assertEqual(entries[1], inventory1)
