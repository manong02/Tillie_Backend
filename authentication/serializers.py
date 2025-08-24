from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from shop.models import Shop
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all(), required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'shop_id')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match")
        if len(data['password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        return data
 
    def create(self, validated_data):
        validated_data.pop('password2')
        shop_id = validated_data.pop('shop_id', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            shop_id=shop_id
        )
        return user
    

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])

        if user is None:
            raise serializers.ValidationError("Invalid username or password")

        data['user'] = user
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    shop_id = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'shop_id')
    
    def validate_username(self, value):
        # Allow current user to keep their username
        if self.instance and self.instance.username == value:
            return value
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def validate_email(self, value):
        # Allow current user to keep their email
        if self.instance and self.instance.email == value:
            return value
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already taken.")
        return value


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data.update({
            'username': self.user.username,
            'email': self.user.email,
            'shop_id': self.user.shop_id.id if hasattr(self.user, 'shop_id') and self.user.shop_id else None,
        })
        return data


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_active', 'shop_id']