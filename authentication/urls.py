from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, MyTokenObtainPairView, UserUpdateView, UserDeleteView, UserListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/update/', UserUpdateView.as_view(), name='user_update'),
    path('user/update/<int:pk>/', UserUpdateView.as_view(), name='user_update_admin'),
    path('user/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('user/delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete_admin'),
    path('user/list/', UserListView.as_view(), name='user_list'),
]