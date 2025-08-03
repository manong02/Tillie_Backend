from django.shortcuts import render
from rest_framework import generics, permissions, status
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
    filterset_fields = ['shop_id']
    search_fields = ['notes', 'shop_id__name']
    ordering_fields = ['delivery_date', 'created_at', 'total_items']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        elif self.request.method == 'GET':
            return OrderListSerializer
        return OrderSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.select_related('shop_id', 'user_id')
        # Regular users see only orders from their shop
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(shop_id=self.request.user.shop_id).select_related('shop_id', 'user_id')
        return Order.objects.none()
    
    def perform_create(self, serializer):
        # Custom validation: ensure user can only create orders for their shop
        shop_id = serializer.validated_data.get('shop_id')
        
        if not self.request.user.is_staff:
            if not hasattr(self.request.user, 'shop_id') or not self.request.user.shop_id:
                raise PermissionDenied("You must be assigned to a shop to create orders.")
            
            if shop_id != self.request.user.shop_id:
                raise PermissionDenied("You can only create orders for your own shop.")
        
        # Automatically set the user who created the order
        serializer.save(user_id=self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.select_related('shop_id', 'user_id')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(shop_id=self.request.user.shop_id).select_related('shop_id', 'user_id')
        return Order.objects.none()
    
    def perform_update(self, serializer):
        # Additional validation for updates
        instance = self.get_object()
        
        # Check if delivery date has passed
        if instance.delivery_date <= timezone.now():
            raise ValidationError("Cannot update orders with past delivery dates.")
        
        # Prevent changing shop_id after creation
        if 'shop_id' in serializer.validated_data:
            if serializer.validated_data['shop_id'] != instance.shop_id:
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
        if not request.user.is_staff and instance.user_id != request.user:
            return Response(
                {"error": "You can only delete orders you created."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class UpcomingOrdersView(generics.ListAPIView):
    """View to get orders with delivery dates in the next 7 days"""
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from datetime import timedelta
        
        # Get orders for the next 7 days
        end_date = timezone.now() + timedelta(days=7)
        
        if self.request.user.is_staff:
            return Order.objects.filter(
                delivery_date__gte=timezone.now(),
                delivery_date__lte=end_date
            ).select_related('shop_id').order_by('delivery_date')
        
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(
                shop_id=self.request.user.shop_id,
                delivery_date__gte=timezone.now(),
                delivery_date__lte=end_date
            ).select_related('shop_id').order_by('delivery_date')
        
        return Order.objects.none()


class PastOrdersView(generics.ListAPIView):
    """View to get completed/past orders"""
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.filter(
                delivery_date__lt=timezone.now()
            ).select_related('shop_id').order_by('-delivery_date')
        
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(
                shop_id=self.request.user.shop_id,
                delivery_date__lt=timezone.now()
            ).select_related('shop_id').order_by('-delivery_date')
        
        return Order.objects.none()
