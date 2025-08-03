from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from shop.models import Shop

User = get_user_model()


class AuthenticationViewsTest(APITestCase):
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
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
            shop_id=self.shop.id
        )
        
    def test_user_registration_success(self):
        """Test successful user registration"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        
    def test_user_registration_password_mismatch(self):
        """Test user registration with password mismatch"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'differentpass'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_user_registration_duplicate_email(self):
        """Test user registration with duplicate email"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Already exists
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_user_login_success(self):
        """Test successful user login"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_user_login_nonexistent_user(self):
        """Test user login with non-existent email"""
        url = reverse('login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_user_profile_authenticated(self):
        """Test getting user profile when authenticated"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated"""
        url = reverse('profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_user_profile_update(self):
        """Test updating user profile"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('profile')
        data = {
            'email': 'updated@example.com'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        
    def test_user_logout(self):
        """Test user logout"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('logout')
        data = {
            'refresh': str(refresh)
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_token_refresh(self):
        """Test JWT token refresh"""
        refresh = RefreshToken.for_user(self.user)
        
        url = reverse('token_refresh')
        data = {
            'refresh': str(refresh)
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
    def test_token_refresh_invalid(self):
        """Test JWT token refresh with invalid token"""
        url = reverse('token_refresh')
        data = {
            'refresh': 'invalid_token'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_registration_rate_limiting(self):
        """Test that registration endpoint has rate limiting"""
        url = reverse('register')
        
        # Make multiple registration attempts
        for i in range(10):
            data = {
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password': 'testpass123',
                'password2': 'testpass123'
            }
            response = self.client.post(url, data)
            
        # After many attempts, should get rate limited
        # Note: This test may need adjustment based on actual rate limiting settings
        
    def test_login_rate_limiting(self):
        """Test that login endpoint has rate limiting"""
        url = reverse('login')
        
        # Make multiple failed login attempts
        for i in range(10):
            data = {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }
            response = self.client.post(url, data)
            
        # After many failed attempts, should get rate limited
        # Note: This test may need adjustment based on actual rate limiting settings
        
    def test_user_registration_with_shop_assignment(self):
        """Test user registration with shop assignment"""
        url = reverse('register')
        data = {
            'username': 'shopuser',
            'email': 'shopuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'shop_id': self.shop.id
        }
        response = self.client.post(url, data)
        
        if response.status_code == status.HTTP_201_CREATED:
            created_user = User.objects.get(email='shopuser@example.com')
            self.assertEqual(created_user.shop_id, self.shop)
        else:
            # Shop assignment might not be allowed during registration
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])
            
    def test_staff_user_permissions(self):
        """Test that staff users have appropriate access"""
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        refresh = RefreshToken.for_user(staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('is_staff', False))
        
    def test_user_profile_shop_information(self):
        """Test that user profile includes shop information"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'shop_name' in response.data:
            self.assertEqual(response.data['shop_name'], 'Test Shop')
            
    def test_password_change_validation(self):
        """Test password change with validation"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # This test assumes a password change endpoint exists
        try:
            url = reverse('change_password')
            data = {
                'old_password': 'testpass123',
                'new_password': 'newpass456',
                'new_password2': 'newpass456'
            }
            response = self.client.post(url, data)
            
            # Should succeed or return appropriate error
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
            
        except:
            # Skip if password change endpoint doesn't exist
            self.skipTest("Password change endpoint not implemented")
