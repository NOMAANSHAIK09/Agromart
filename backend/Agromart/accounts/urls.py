from django.urls import path
from .views import RegisterView,LonginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LonginView.as_view(), name='login')
] 
