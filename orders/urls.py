from django.urls import path
from . import views

urlpatterns = [
    # Order CRUD URLs
    path('', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    
    # Special order views
    path('all/', views.AllOrdersView.as_view(), name='all-orders'),
]
