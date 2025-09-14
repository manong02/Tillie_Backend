from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'shop', 'shop_name', 'user', 'user_username', 
                 'category', 'category_name', 'total_items', 'delivery_date', 'notes', 'created_at']
        read_only_fields = ['created_at']
        
    def validate_total_items(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total items must be greater than 0.")
        if value > 10000:
            raise serializers.ValidationError("Total items cannot exceed 10,000.")
        return value
        
    def validate_delivery_date(self, value):
        # Ensure delivery date is in the future
        if value <= timezone.now():
            raise serializers.ValidationError("Delivery date must be in the future.")
        
        # Ensure delivery date is not more than 1 year in the future
        max_date = timezone.now() + timedelta(days=365)
        if value > max_date:
            raise serializers.ValidationError("Delivery date cannot be more than 1 year in the future.")
        
        return value
    
    def validate_notes(self, value):
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Notes must be at least 3 characters long if provided.")
        return value.strip() if value else value


class OrderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for order listings"""
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'shop_name', 'category_name', 'total_items', 'delivery_date', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Specialized serializer for order creation with additional validation"""
    
    class Meta:
        model = Order
        fields = ['shop', 'category', 'total_items', 'delivery_date', 'notes']
        extra_kwargs = {
            'shop': {'required': False},  
            'category': {'required': True},
            'total_items': {'required': True},
            'delivery_date': {'required': True},
            'notes': {'required': False, 'allow_blank': True}
        }
        
    def validate_total_items(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total items must be greater than 0.")
        if value > 10000:
            raise serializers.ValidationError("Total items cannot exceed 10,000.")
        return value
        
    def validate_delivery_date(self, value):
        # Ensure delivery date is at least 24 hours from now
        min_date = timezone.now() + timedelta(hours=24)
        if value < min_date:
            raise serializers.ValidationError("Delivery date must be at least 24 hours from now.")
        
        # Ensure delivery date is not more than 1 year in the future
        max_date = timezone.now() + timedelta(days=365)
        if value > max_date:
            raise serializers.ValidationError("Delivery date cannot be more than 1 year in the future.")
        
        return value
    
    def validate(self, attrs):
        return attrs


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Specialized serializer for order updates without shop field requirement"""
    
    class Meta:
        model = Order
        fields = ['category', 'total_items', 'delivery_date', 'notes']
        extra_kwargs = {
            'category': {'required': True},
            'total_items': {'required': True},
            'delivery_date': {'required': True},
            'notes': {'required': False, 'allow_blank': True}
        }
        
    def validate_total_items(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total items must be greater than 0.")
        if value > 10000:
            raise serializers.ValidationError("Total items cannot exceed 10,000.")
        return value
        
    def validate_delivery_date(self, value):
        # Ensure delivery date is in the future
        if value <= timezone.now():
            raise serializers.ValidationError("Delivery date must be in the future.")
        
        # Ensure delivery date is not more than 1 year in the future
        max_date = timezone.now() + timedelta(days=365)
        if value > max_date:
            raise serializers.ValidationError("Delivery date cannot be more than 1 year in the future.")
        
        return value
    
    def validate_notes(self, value):
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Notes must be at least 3 characters long if provided.")
        return value.strip() if value else value
