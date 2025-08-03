from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from shop.models import Shop

User = get_user_model()


class ShopViewsTest(APITestCase):
    
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
        
    def authenticate_user(self, user):
        """Helper method to authenticate a user"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
    def test_shop_list_authenticated_user(self):
        """Test shop list endpoint for authenticated user"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_shop_create_authenticated_user(self):
        """Test shop creation by authenticated user"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        data = {
            'name': 'New Test Shop'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Shop.objects.filter(name='New Test Shop').exists())
        
    def test_shop_detail_view(self):
        """Test shop detail endpoint"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-detail', kwargs={'pk': self.shop.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Shop')
        
    def test_shop_update(self):
        """Test updating shop"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-detail', kwargs={'pk': self.shop.pk})
        data = {
            'name': 'Updated Shop Name'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.name, 'Updated Shop Name')
        
    def test_shop_delete(self):
        """Test deleting shop"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-detail', kwargs={'pk': self.shop.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Shop.objects.filter(id=self.shop.id).exists())
        
    def test_shop_access_permission_own_shop(self):
        """Test that user can access their own shop"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-detail', kwargs={'pk': self.shop.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_shop_access_permission_other_shop(self):
        """Test that user cannot access other shops"""
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
        
        url = reverse('shop-detail', kwargs={'pk': other_shop.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_staff_user_sees_all_shops(self):
        """Test that staff user sees all shops"""
        other_user = User.objects.create_user(
            username='shopowner',
            email='other@example.com',
            password='testpass123'
        )
        Shop.objects.create(
            name="Other Shop",
            owner=other_user
        )
        
        self.authenticate_user(self.staff_user)
        
        url = reverse('shop-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Staff should see all shops (2 total)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_shop_filtering_by_owner(self):
        """Test filtering shops by owner"""
        self.authenticate_user(self.staff_user)
        
        url = reverse('shop-list-create')
        response = self.client.get(url, {'owner': self.user.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only show shops owned by this user
        for shop in response.data['results']:
            self.assertEqual(shop['owner'], self.user.id)
            
    def test_shop_search_functionality(self):
        """Test shop search functionality"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        response = self.client.get(url, {'search': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Shop')
        
    def test_shop_ordering_by_name(self):
        """Test ordering shops by name"""
        Shop.objects.create(name='A Shop', owner=self.user)
        Shop.objects.create(name='Z Shop', owner=self.user)
        
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        response = self.client.get(url, {'ordering': 'name'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by name ascending
        
    def test_shop_creation_auto_owner_assignment(self):
        """Test that owner is automatically assigned to created shops"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        data = {
            'name': 'Auto Owner Shop'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_shop = Shop.objects.get(name='Auto Owner Shop')
        self.assertEqual(created_shop.owner, self.user)
        
    def test_shop_creation_validation_empty_name(self):
        """Test shop creation with empty name"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        data = {
            'name': ''
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_shop_creation_validation_long_name(self):
        """Test shop creation with name exceeding max length"""
        self.authenticate_user(self.user)
        
        url = reverse('shop-list-create')
        data = {
            'name': 'x' * 256  # Exceeds max_length=255
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_user_without_shop_access_denied(self):
        """Test that user without shop assignment has limited access"""
        user_no_shop = User.objects.create_user(
            username='noshopuser',
            email='noshop@example.com',
            password='testpass123'
        )
        
        self.authenticate_user(user_no_shop)
        
        url = reverse('shop-list-create')
        response = self.client.get(url)
        
        # User without shop should see empty results or get forbidden
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access shop endpoints"""
        url = reverse('shop-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_shop_update_owner_change_forbidden(self):
        """Test that shop owner cannot be changed after creation"""
        other_user = User.objects.create_user(
            username='otherowner',
            email='other@example.com',
            password='testpass123'
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('shop-detail', kwargs={'pk': self.shop.pk})
        data = {'owner': other_user.id}
        response = self.client.patch(url, data)
        
        # Should either be forbidden or ignored
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        # Owner should remain unchanged
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.owner, self.user)
        
    def test_shop_delete_by_non_owner_forbidden(self):
        """Test that non-owners cannot delete shops"""
        other_user = User.objects.create_user(
            username='nonowner',
            email='other@example.com',
            password='testpass123'
        )
        other_shop = Shop.objects.create(
            name="Other Shop",
            owner=other_user
        )
        
        self.authenticate_user(self.user)
        
        url = reverse('shop-detail', kwargs={'pk': other_shop.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
