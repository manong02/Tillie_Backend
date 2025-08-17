from django.shortcuts import render
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from .models import Order
from .serializers import OrderSerializer, OrderListSerializer, OrderCreateSerializer
from shop.models import Shop


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['shop']
    search_fields = ['notes', 'shop__name']
    ordering_fields = ['delivery_date', 'created_at', 'total_items']
    ordering = ['created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        elif self.request.method == 'GET':
            return OrderListSerializer
        return OrderSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.select_related('shop', 'user')
        # Regular users see only orders from their shop
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(shop=self.request.user.shop_id).select_related('shop', 'user')
        return Order.objects.none()
    
    def perform_create(self, serializer):
        # Custom validation: ensure user can only create orders for their shop
        if not self.request.user.is_staff:
            if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
                # Force the shop to be the user's shop
                serializer.save(user=self.request.user, shop=self.request.user.shop_id)
            else:
                raise PermissionDenied("You must be assigned to a shop to create orders.")
        else:
            # Staff can create orders for any shop, but still set the user
            serializer.save(user=self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.select_related('shop', 'user')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(shop=self.request.user.shop_id).select_related('shop', 'user')
        return Order.objects.none()
    
    def perform_update(self, serializer):
        # Additional validation for updates
        instance = self.get_object()
        
        # Check if delivery date has passed
        if instance.delivery_date <= timezone.now():
            raise ValidationError("Cannot update orders with past delivery dates.")
        
        # Prevent changing shop after creation
        if 'shop' in serializer.validated_data:
            if serializer.validated_data['shop'] != instance.shop:
                raise ValidationError("Cannot change shop for existing order.")
        
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Custom validation before deletion
        if instance.delivery_date <= timezone.now():
            return Response(
                {"error": "Cannot delete orders with past delivery dates."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow deletion by the user who created the order or staff
        if not request.user.is_staff and instance.user != request.user:
            return Response(
                {"error": "You can only delete orders you created."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class UpcomingOrdersView(views.APIView):
    """View to get orders with delivery dates in the next 7 days"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from datetime import timedelta, date
        
        # Get orders for the next 7 days
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        end_date = timezone.now() + timedelta(days=7)
        
        if hasattr(request.user, 'shop_id'):
        
        # Debug: Check all orders first
          all_orders = Order.objects.all()
        
        if request.user.is_staff:
            orders = Order.objects.filter(
                delivery_date__gte=timezone.now()
            ).select_related('shop').order_by('delivery_date')
        elif hasattr(request.user, 'shop_id') and request.user.shop_id:
            orders = Order.objects.filter(
                shop=request.user.shop_id,
                delivery_date__gte=timezone.now()
            ).select_related('shop').order_by('delivery_date')
            
            # Debug: Check orders without date filter
            all_shop_orders = Order.objects.filter(shop=request.user.shop_id)
            
            # Debug: Check date range
            for order in all_shop_orders:
                print(f"Order {order.id}: delivery_date = {order.delivery_date}")
        else:
            orders = Order.objects.none()
        
        # Transform data to match frontend model structure
        upcoming_orders = []
        for order in orders:
            # Determine status based on delivery date
            delivery_date = order.delivery_date.date()
            if delivery_date == today:
                status = 1  # today
            elif delivery_date == tomorrow:
                status = 2  # tomorrow
            else:
                status = 3  # upcoming
            
            upcoming_orders.append({
                'id': str(order.id),
                'items': order.total_items,
                'value': 0,  # Calculate if you have price data
                'category': order.category.name if order.category else 'Uncategorized',
                'dueDate': order.delivery_date.isoformat(),
                'status': status
            })
        
        print(f"Returning {len(upcoming_orders)} upcoming orders")
        return Response(upcoming_orders)


class PastOrdersView(generics.ListAPIView):
    """View to get completed/past orders"""
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.filter(
                delivery_date__lt=timezone.now()
            ).select_related('shop').order_by('-delivery_date')
        
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(
                shop=self.request.user.shop_id,
                delivery_date__lt=timezone.now()
            ).select_related('shop').order_by('-delivery_date')
        
        return Order.objects.none()
