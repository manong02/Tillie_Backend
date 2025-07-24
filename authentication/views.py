from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import RegisterSerializer
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from rest_framework_simplejwt.views import TokenObtainPairView

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @ratelimit(key='ip', rate='5/m', block=True)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class LoginView(TokenObtainPairView):

    @ratelimit(key='ip', rate='5/m', block=True)
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
    
