from rest_framework import serializers
from .models import Category, Product, Inventory


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'shop_id', 'products_count']
        extra_kwargs = {
            'shop_id': {'required': False}
        }
        
    def get_products_count(self, obj):
        return obj.products.count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category_id.name', read_only=True)
    shop_name = serializers.CharField(source='shop_id.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'category_id', 'category_name', 'shop_id', 'shop_name', 
                 'price', 'vat', 'stock_quantity', 'description', 'date_added']
        read_only_fields = ['date_added']
        extra_kwargs = {
            'shop_id': {'required': False}
        }
    
    def validate(self, data):
        print(f"DEBUG SERIALIZER: Validating data: {data}")
        print(f"DEBUG SERIALIZER: shop_id in data: {'shop_id' in data}")
        print(f"DEBUG SERIALIZER: shop_id value: {data.get('shop_id', 'NOT PROVIDED')}")
        return super().validate(data)
        
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
        
    def validate_vat(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("VAT must be between 0 and 100.")
        return value


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_id.name', read_only=True)
    shop_name = serializers.CharField(source='shop_id.name', read_only=True)
    user_username = serializers.CharField(source='user_id.username', read_only=True)
    
    class Meta:
        model = Inventory
        fields = ['id', 'shop_id', 'shop_name', 'product_id', 'product_name', 
                 'quantity', 'change_type', 'date', 'notes', 'user_id', 'user_username']
        read_only_fields = ['date']


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product listings"""
    category_name = serializers.CharField(source='category_id.name', read_only=True)
    shop_name = serializers.CharField(source='shop_id.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'category_id', 'category_name', 'shop_id', 'shop_name', 
                 'price', 'vat', 'stock_quantity', 'description', 'date_added']
        read_only_fields = ['date_added']


class InventoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for inventory listings"""
    product_name = serializers.CharField(source='product_id.name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = ['id', 'product_name', 'quantity', 'change_type', 'date']
