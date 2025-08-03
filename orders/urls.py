from django.urls import path
from . import views

urlpatterns = [
    # Order CRUD URLs
    path('', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    
    # Special order views
    path('upcoming/', views.UpcomingOrdersView.as_view(), name='upcoming-orders'),
    path('past/', views.PastOrdersView.as_view(), name='past-orders'),
]
