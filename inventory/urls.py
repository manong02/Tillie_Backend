from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.InventoryDashboardView.as_view(), name='inventory-dashboard'),
    
    # Category URLs
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Product URLs
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/low-stock/', views.LowStockProductsView.as_view(), name='low-stock-products'),
    
    # Inventory URLs
    path('inventory/', views.InventoryListCreateView.as_view(), name='inventory-list-create'),
    path('inventory/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory-detail'),
]
