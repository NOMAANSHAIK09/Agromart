from django.shortcuts import render

# Create your views here.

from rest_framework import generics
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    
    
class LonginView(TokenObtainPairView):
    pass


