from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import APIView
from django.db.models import Sum, Count, Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product, Inventory
from .serializers import (
    CategorySerializer, ProductSerializer, InventorySerializer,
    ProductListSerializer, InventoryListSerializer
)
from shop.models import Shop


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['shop_id']
    search_fields = ['name']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Category.objects.all()
        # Regular users see only categories from their shop
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Category.objects.filter(shop_id=self.request.user.shop_id)
        return Category.objects.none()
    
    def perform_create(self, serializer):
        # Auto-assign shop_id from authenticated user
        print(f"DEBUG: User: {self.request.user}")
        print(f"DEBUG: User ID: {self.request.user.id}")
        print(f"DEBUG: User is_staff: {self.request.user.is_staff}")
        print(f"DEBUG: User has shop_id attr: {hasattr(self.request.user, 'shop_id')}")
        if hasattr(self.request.user, 'shop_id'):
            print(f"DEBUG: User shop_id value: {self.request.user.shop_id}")
            print(f"DEBUG: User shop_id type: {type(self.request.user.shop_id)}")
        
        # Check if user has shop_id assigned (works for both staff and non-staff)
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            print(f"DEBUG: Auto-assigning shop_id: {self.request.user.shop_id}")
            serializer.save(shop_id=self.request.user.shop_id)
        elif not self.request.user.is_staff:
            # Non-staff users must have a shop assigned
            print(f"DEBUG: Non-staff user without shop assignment")
            raise PermissionDenied("You must be assigned to a shop to create categories.")
        else:
            # Staff users without shop assignment - require shop_id in request
            print(f"DEBUG: Staff user without shop assignment - checking request data")
            if 'shop_id' not in serializer.validated_data:
                raise PermissionDenied("Staff users must specify shop_id or be assigned to a shop.")
            serializer.save()


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Category.objects.all()
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Category.objects.filter(shop_id=self.request.user.shop_id)
        return Category.objects.none()


class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category_id', 'shop_id']
    search_fields = ['name']
    ordering_fields = ['name', 'price', 'stock_quantity', 'date_added']
    ordering = ['-date_added']
    
    def post(self, request, *args, **kwargs):
        print(f"DEBUG POST: User: {request.user}")
        print(f"DEBUG POST: Request data: {request.data}")
        print(f"DEBUG POST: User shop_id: {getattr(request.user, 'shop_id', 'NOT FOUND')}")
        return super().post(request, *args, **kwargs)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductListSerializer
        return ProductSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.select_related('category_id', 'shop_id')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Product.objects.filter(shop_id=self.request.user.shop_id).select_related('category_id', 'shop_id')
        return Product.objects.none()
    
    def perform_create(self, serializer):
        # Auto-assign shop_id from authenticated user
        category_id = serializer.validated_data.get('category_id')
        
        # Debug logging
        print(f"DEBUG: User: {self.request.user}")
        print(f"DEBUG: User has shop_id: {hasattr(self.request.user, 'shop_id')}")
        print(f"DEBUG: User shop_id value: {getattr(self.request.user, 'shop_id', 'NOT FOUND')}")
        print(f"DEBUG: User shop object: {getattr(self.request.user, 'shop_id', None)}")
        print(f"DEBUG: User is_staff: {self.request.user.is_staff}")
        
        # Check if user has shop_id assigned (works for both staff and non-staff)
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            print(f"DEBUG: Auto-assigning shop_id: {self.request.user.shop_id}")
            serializer.save(shop_id=self.request.user.shop_id)
        elif not self.request.user.is_staff:
            # Non-staff users must have a shop assigned
            print(f"DEBUG: Non-staff user without shop assignment")
            raise PermissionDenied("You must be assigned to a shop to create products.")
        else:
            # Staff users without shop assignment - require shop_id in request
            print(f"DEBUG: Staff user without shop assignment - checking request data")
            if 'shop_id' not in serializer.validated_data:
                raise PermissionDenied("Staff users must specify shop_id or be assigned to a shop.")
            shop_id = serializer.validated_data.get('shop_id')
            
            # If no shop_id provided and user has a shop, auto-assign it
            if not shop_id and hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
                print(f"DEBUG: Staff user has no shop_id in request, auto-assigning: {self.request.user.shop_id}")
                serializer.save(shop_id=self.request.user.shop_id)
            else:
                # Ensure category belongs to the same shop
                if category_id and shop_id and category_id.shop_id != shop_id:
                    raise ValidationError("Category must belong to the same shop as the product.")
                
                serializer.save()


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.select_related('category_id', 'shop_id')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Product.objects.filter(shop_id=self.request.user.shop_id).select_related('category_id', 'shop_id')
        return Product.objects.none()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Custom validation before deletion
        if instance.stock_quantity > 0:
            return Response(
                {"error": "Cannot delete product with remaining stock. Please adjust inventory first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class InventoryListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product_id', 'shop_id', 'change_type']
    search_fields = ['product_id__name', 'notes']
    ordering_fields = ['date', 'quantity']
    ordering = ['-date']
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return InventoryListSerializer
        return InventorySerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Inventory.objects.select_related('product_id', 'shop_id', 'user_id')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Inventory.objects.filter(shop_id=self.request.user.shop_id).select_related('product_id', 'shop_id', 'user_id')
        return Inventory.objects.none()
    
    def perform_create(self, serializer):
        # Custom validation and business logic
        product = serializer.validated_data.get('product_id')
        quantity = serializer.validated_data.get('quantity')
        change_type = serializer.validated_data.get('change_type')
        
        # Validate stock removal doesn't go negative
        if change_type == 'removal' and quantity > 0:
            if product.stock_quantity < quantity:
                raise ValidationError(
                    f"Cannot remove {quantity} items. Only {product.stock_quantity} available in stock."
                )
        
        # Update product stock quantity
        if change_type == 'addition':
            product.stock_quantity += abs(quantity)
        elif change_type == 'removal':
            product.stock_quantity -= abs(quantity)
        elif change_type == 'adjustment':
            product.stock_quantity = abs(quantity)
        
        product.save()
        
        # Automatically set the user who made the inventory change
        serializer.save(user_id=self.request.user)


class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Inventory.objects.select_related('product_id', 'shop_id', 'user_id')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Inventory.objects.filter(shop_id=self.request.user.shop_id).select_related('product_id', 'shop_id', 'user_id')
        return Inventory.objects.none()


class LowStockProductsView(generics.ListAPIView):
    """View to get products with low stock (less than 10 items)"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        threshold = int(self.request.query_params.get('threshold', 10))
        
        # Validate threshold
        if threshold < 0:
            raise ValidationError("Threshold must be a positive number.")
        
        if self.request.user.is_staff:
            return Product.objects.filter(stock_quantity__lt=threshold).select_related('category_id')
        if hasattr(self.request.user, 'shop_id') and self.request.user.shop_id:
            return Product.objects.filter(
                shop_id=self.request.user.shop_id,
                stock_quantity__lt=threshold
            ).select_related('category_id')
        return Product.objects.none()


class InventoryDashboardView(APIView):
    """
    Dashboard view providing all product data for frontend calculations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get user's shop or all shops for staff
        if request.user.is_staff:
            products = Product.objects.select_related('category_id', 'shop_id')
        elif hasattr(request.user, 'shop_id') and request.user.shop_id:
            products = Product.objects.filter(shop_id=request.user.shop_id).select_related('category_id', 'shop_id')
        else:
            return Response({"error": "User not assigned to any shop"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all products with necessary fields
        products_data = products.values(
            'id', 
            'name', 
            'stock_quantity', 
            'price',
            'category_id__name',
            'category_id__id'
        ).order_by('name')
        
        return Response({
            'products': list(products_data)
        })
