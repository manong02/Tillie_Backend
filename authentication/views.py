from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserUpdateSerializer, UserListSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from django_ratelimit.decorators import ratelimit
from rest_framework.permissions import IsAdminUser

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @ratelimit(key='ip', rate='5/m', block=True)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class UserUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Users can only update their own profile, or admins can update any user
        if self.request.user.is_staff:
            return generics.get_object_or_404(User, pk=self.kwargs['pk'])
        return self.request.user


class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Users can only delete their own profile, or admins can delete any user
        if self.request.user.is_staff:
            return generics.get_object_or_404(User, pk=self.kwargs['pk'])
        return self.request.user
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @ratelimit(key='ip', rate='5/m', block=True)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]