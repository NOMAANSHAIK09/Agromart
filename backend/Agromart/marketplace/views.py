from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSeller
from .models import Product, ProductListing
from .serializers import ProductSerializer, ProductListingSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ProductListingListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductListingSerializer
    
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "product",
        "product__category",
        "location",
        "status",
    ]

    search_fields = [
        "product__name",
        "location",
        "seller__username",
    ]

    ordering_fields = [
        "price",
        "quantity",
        "created_at",
    ]

    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSeller()]

        return [IsAuthenticated()]

    def get_queryset(self):
        return ProductListing.objects.filter(
            status="active"
        ).select_related("product", "seller")

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class MyListingsView(generics.ListAPIView):
    serializer_class = ProductListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductListing.objects.filter(
            seller=self.request.user
        ).select_related("product", "seller")


class ProductListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductListingSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [IsSeller()]

        return [IsAuthenticated()]

    def get_queryset(self):
        return ProductListing.objects.filter(
            seller=self.request.user
        )