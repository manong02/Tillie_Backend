from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from orders.models import Order
from shop.models import Shop

User = get_user_model()


class OrderViewsTest(APITestCase):
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner=self.user
        )
        # Assign user to the shop
        self.user.shop_id = self.shop
        self.user.save()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.future_date = timezone.now() + timedelta(days=7)
        self.past_date = timezone.now() - timedelta(days=1)
        
        # Create test orders
        self.future_order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=50,
            delivery_date=self.future_date,
            notes="Future order"
        )
        self.past_order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=25,
            delivery_date=self.past_date,
            notes="Past order"
        )
        
    def authenticate_user(self, user):
        """Helper method to authenticate a user"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
    def test_order_list_authenticated_user(self):
        """Test order list endpoint for authenticated user"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_order_create_authenticated_user(self):
        """Test order creation by authenticated user"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        data = {
            'shop_id': self.shop.id,
            'total_items': 75,
            'delivery_date': (timezone.now() + timedelta(days=10)).isoformat(),
            'notes': 'New test order'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Order.objects.filter(notes='New test order').exists())
        
    def test_order_create_wrong_shop_permission(self):
        """Test that user cannot create order for different shop"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_shop = Shop.objects.create(
            name="Other Shop",
            owner=other_user
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        data = {
            'shop_id': other_shop.id,
            'total_items': 30,
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Unauthorized order'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_order_create_invalid_delivery_date(self):
        """Test order creation with invalid delivery date"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        data = {
            'shop_id': self.shop.id,
            'total_items': 20,
            'delivery_date': (timezone.now() + timedelta(hours=12)).isoformat(),  # Less than 24 hours
            'notes': 'Invalid date order'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_order_create_invalid_total_items(self):
        """Test order creation with invalid total items"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        data = {
            'shop_id': self.shop.id,
            'total_items': 0,  # Invalid: must be > 0
            'delivery_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'notes': 'Invalid items order'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_order_detail_view(self):
        """Test order detail endpoint"""
        self.authenticate_user(self.user)
        
        url = reverse('order-detail', kwargs={'pk': self.future_order.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 50)
        self.assertEqual(response.data['notes'], 'Future order')
        
    def test_order_update_future_order(self):
        """Test updating future order"""
        self.authenticate_user(self.user)
        
        url = reverse('order-detail', kwargs={'pk': self.future_order.pk})
        data = {
            'total_items': 60,
            'notes': 'Updated future order'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.future_order.refresh_from_db()
        self.assertEqual(self.future_order.total_items, 60)
        self.assertEqual(self.future_order.notes, 'Updated future order')
        
    def test_order_update_past_order_forbidden(self):
        """Test that past orders cannot be updated"""
        self.authenticate_user(self.user)
        
        url = reverse('order-detail', kwargs={'pk': self.past_order.pk})
        data = {
            'total_items': 30,
            'notes': 'Trying to update past order'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_order_update_shop_change_forbidden(self):
        """Test that shop cannot be changed after order creation"""
        other_user = User.objects.create_user(
            username='otheruser2',
            email='other2@example.com',
            password='testpass123'
        )
        other_shop = Shop.objects.create(
            name="Other Shop 2",
            owner=other_user
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('order-detail', kwargs={'pk': self.future_order.pk})
        data = {'shop_id': other_shop.id}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_order_delete_future_order(self):
        """Test deleting future order"""
        self.authenticate_user(self.user)
        
        url = reverse('order-detail', kwargs={'pk': self.future_order.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=self.future_order.id).exists())
        
    def test_order_delete_past_order_forbidden(self):
        """Test that past orders cannot be deleted"""
        self.authenticate_user(self.user)
        
        url = reverse('order-detail', kwargs={'pk': self.past_order.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_order_delete_by_different_user_forbidden(self):
        """Test that user cannot delete order created by another user"""
        other_user = User.objects.create_user(
            username='otheruser3',
            email='other3@example.com',
            password='testpass123'
        )
        # Assign other user to same shop
        other_user.shop_id = self.shop
        other_user.save()
        
        self.authenticate_user(other_user)
        
        url = reverse('order-detail', kwargs={'pk': self.future_order.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_upcoming_orders_view(self):
        """Test upcoming orders endpoint (next 7 days)"""
        # Create an order for next week
        upcoming_order = Order.objects.create(
            shop_id=self.shop,
            user_id=self.user,
            total_items=40,
            delivery_date=timezone.now() + timedelta(days=3),
            notes="Upcoming order"
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('upcoming-orders')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include future_order (7 days) and upcoming_order (3 days)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_past_orders_view(self):
        """Test past orders endpoint"""
        self.authenticate_user(self.user)
        
        url = reverse('past-orders')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['notes'], 'Past order')
        
    def test_staff_user_sees_all_shops(self):
        """Test that staff user sees orders from all shops"""
        # Create another shop with orders
        other_user = User.objects.create_user(
            username='shopowner',
            email='shopowner@example.com',
            password='testpass123'
        )
        other_shop = Shop.objects.create(
            name="Other Shop",
            owner=other_user
        )
        Order.objects.create(
            shop_id=other_shop,
            total_items=30,
            delivery_date=timezone.now() + timedelta(days=5),
            notes="Other shop order"
        )
        
        self.authenticate_user(self.staff_user)
        
        url = reverse('order-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Staff should see orders from both shops (3 total)
        self.assertEqual(len(response.data['results']), 3)
        
    def test_order_filtering_by_shop(self):
        """Test filtering orders by shop"""
        self.authenticate_user(self.staff_user)
        
        url = reverse('order-list-create')
        response = self.client.get(url, {'shop_id': self.shop.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only show orders for this shop
        for order in response.data['results']:
            self.assertEqual(order['shop_name'], 'Test Shop')
            
    def test_order_search_functionality(self):
        """Test order search functionality"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        response = self.client.get(url, {'search': 'Future'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['notes'], 'Future order')
        
    def test_order_ordering_by_delivery_date(self):
        """Test ordering orders by delivery date"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        response = self.client.get(url, {'ordering': 'delivery_date'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by delivery date ascending
        
    def test_user_without_shop_access_denied(self):
        """Test that user without shop assignment cannot access orders"""
        user_no_shop = User.objects.create_user(
            username='noshopuser',
            email='noshop@example.com',
            password='testpass123'
        )
        
        self.authenticate_user(user_no_shop)
        
        url = reverse('order-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access orders"""
        url = reverse('order-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_order_automatic_user_assignment(self):
        """Test that user is automatically assigned to created orders"""
        self.authenticate_user(self.user)
        
        url = reverse('order-list-create')
        data = {
            'shop_id': self.shop.id,
            'total_items': 35,
            'delivery_date': (timezone.now() + timedelta(days=8)).isoformat(),
            'notes': 'Auto user assignment test'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_order = Order.objects.get(notes='Auto user assignment test')
        self.assertEqual(created_order.user_id, self.user)
