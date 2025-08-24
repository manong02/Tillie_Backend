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
        # For non-staff users, always use their assigned shop
        if not self.request.user.is_staff:
            if not hasattr(self.request.user, 'shop_id') or not self.request.user.shop_id:
                raise PermissionDenied("You must be assigned to a shop to create orders.")
            serializer.save(user=self.request.user, shop=self.request.user.shop_id)
        else:
            # For staff users, use the provided shop or default to their assigned shop
            shop = serializer.validated_data.get('shop')
            if not shop and hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
                shop = self.request.user.shop_id
            
            if not shop:
                raise ValidationError({"shop": ["This field is required."]})
                
            serializer.save(user=self.request.user, shop=shop)


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


# In views.py
class AllOrdersView(views.APIView):
    """View to get all orders with their status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = timezone.now().date()
        orders = self.get_queryset()
        
        result = []
        for order in orders:
            # Determine status
            if hasattr(order, 'is_cancelled') and order.is_cancelled:
                status = 'cancelled'
            elif order.delivery_date.date() < today:
                status = 'past'
            else:
                status = 'upcoming'
            
            result.append({
                'id': order.id,
                'shop_name': order.shop.name,
                'category_name': order.category.name if order.category else 'Uncategorized',
                'total_items': order.total_items,
                'created_at': order.created_at,
                'delivery_date': order.delivery_date,
                'status': status
            })
        
        return Response({
            'count': len(result),
            'next': None,  # Add pagination if needed
            'previous': None,  # Add pagination if needed
            'results': result
        })
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().select_related('shop', 'category')
        
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Order.objects.filter(
                shop=self.request.user.shop_id
            ).select_related('shop', 'category')
        
        return Order.objects.none()