from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from inventory.models import Category, Product, Inventory
from shop.models import Shop

User = get_user_model()


class InventoryViewsTest(APITestCase):
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.shop = Shop.objects.create(
            name="Test Shop",
            address="123 Test Street",
            phone_number="1234567890"
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            shop_id=self.shop
        )
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpass123',
            is_staff=True
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
        
    def authenticate_user(self, user):
        """Helper method to authenticate a user"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
    def test_category_list_authenticated_user(self):
        """Test category list endpoint for authenticated user"""
        self.authenticate_user(self.user)
        
        url = reverse('category-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Electronics')
        
    def test_category_create_authenticated_user(self):
        """Test category creation by authenticated user"""
        self.authenticate_user(self.user)
        
        url = reverse('category-list-create')
        data = {
            'name': 'Books',
            'description': 'Book category',
            'shop_id': self.shop.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name='Books').exists())
        
    def test_category_create_wrong_shop_permission(self):
        """Test that user cannot create category for different shop"""
        other_shop = Shop.objects.create(
            name="Other Shop",
            address="456 Other Street",
            phone_number="0987654321"
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('category-list-create')
        data = {
            'name': 'Unauthorized Category',
            'shop_id': other_shop.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_product_list_with_filtering(self):
        """Test product list with category filtering"""
        self.authenticate_user(self.user)
        
        url = reverse('product-list-create')
        response = self.client.get(url, {'category_id': self.category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_product_create_with_validation(self):
        """Test product creation with validation"""
        self.authenticate_user(self.user)
        
        url = reverse('product-list-create')
        data = {
            'name': 'New Product',
            'price': '99.99',
            'vat': '20.00',
            'stock_quantity': 50,
            'category_id': self.category.id,
            'shop_id': self.shop.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name='New Product').exists())
        
    def test_product_create_invalid_price(self):
        """Test product creation with invalid price"""
        self.authenticate_user(self.user)
        
        url = reverse('product-list-create')
        data = {
            'name': 'Invalid Product',
            'price': '-10.00',  # Negative price
            'category_id': self.category.id,
            'shop_id': self.shop.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_product_update_stock_validation(self):
        """Test product update with stock validation"""
        self.authenticate_user(self.user)
        
        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        data = {'stock_quantity': 0}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_product_delete_with_stock_prevention(self):
        """Test that product with stock cannot be deleted"""
        self.authenticate_user(self.user)
        
        url = reverse('product-detail', kwargs={'pk': self.product.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock', response.data['error'].lower())
        
    def test_inventory_create_entry(self):
        """Test creating inventory entry"""
        self.authenticate_user(self.user)
        
        url = reverse('inventory-list-create')
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'addition',
            'quantity': 25,
            'notes': 'Stock addition'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Inventory.objects.filter(notes='Stock addition').exists())
        
    def test_inventory_removal_exceeds_stock(self):
        """Test inventory removal that exceeds available stock"""
        self.authenticate_user(self.user)
        
        url = reverse('inventory-list-create')
        data = {
            'product_id': self.product.id,
            'shop_id': self.shop.id,
            'movement_type': 'removal',
            'quantity': 150,  # More than available stock (100)
            'notes': 'Invalid removal'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_low_stock_products_view(self):
        """Test low stock products endpoint"""
        # Create a low stock product
        low_stock_product = Product.objects.create(
            name="Low Stock Product",
            price=Decimal('25.00'),
            stock_quantity=5,  # Low stock
            category_id=self.category,
            shop_id=self.shop
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('low-stock-products')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Low Stock Product')
        
    def test_inventory_dashboard_view(self):
        """Test inventory dashboard endpoint"""
        self.authenticate_user(self.user)
        
        url = reverse('inventory-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('category_breakdown', response.data)
        self.assertIn('overall_stats', response.data)
        self.assertIn('top_products', response.data)
        self.assertIn('low_stock_alerts', response.data)
        
    def test_dashboard_category_breakdown(self):
        """Test dashboard category breakdown data"""
        self.authenticate_user(self.user)
        
        url = reverse('inventory-dashboard')
        response = self.client.get(url)
        
        category_breakdown = response.data['category_breakdown']
        self.assertEqual(len(category_breakdown), 1)
        self.assertEqual(category_breakdown[0]['category_id__name'], 'Electronics')
        self.assertEqual(category_breakdown[0]['total_stock'], 100)
        
    def test_dashboard_staff_sees_all_shops(self):
        """Test that staff user sees data from all shops"""
        # Create another shop with data
        other_shop = Shop.objects.create(
            name="Other Shop",
            address="456 Other Street",
            phone_number="0987654321"
        )
        other_category = Category.objects.create(
            name="Books",
            shop_id=other_shop
        )
        Product.objects.create(
            name="Book Product",
            price=Decimal('15.00'),
            stock_quantity=50,
            category_id=other_category,
            shop_id=other_shop
        )
        
        self.authenticate_user(self.staff_user)
        
        url = reverse('inventory-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Staff should see data from both shops
        self.assertEqual(response.data['overall_stats']['total_stock'], 150)  # 100 + 50
        
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access endpoints"""
        url = reverse('category-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_inventory_search_functionality(self):
        """Test inventory search functionality"""
        self.authenticate_user(self.user)
        
        url = reverse('product-list-create')
        response = self.client.get(url, {'search': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product')
        
    def test_inventory_ordering(self):
        """Test inventory ordering functionality"""
        self.authenticate_user(self.user)
        
        url = reverse('product-list-create')
        response = self.client.get(url, {'ordering': '-price'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by price descending
        
    def test_user_without_shop_access_denied(self):
        """Test that user without shop assignment cannot access inventory"""
        user_no_shop = User.objects.create_user(
            email='noshop@example.com',
            password='testpass123'
        )
        
        self.authenticate_user(user_no_shop)
        
        url = reverse('category-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
