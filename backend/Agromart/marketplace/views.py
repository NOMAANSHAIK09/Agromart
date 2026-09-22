from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSeller
from .models import Product, ProductListing , BuyerRequirement
from .serializers import ProductSerializer, ProductListingSerializer , BuyerRequirementSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import ProductListingFilter
from rest_framework.response import Response

from rest_framework.views import APIView
from .matching import get_matching_allocations


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSeller()]
        return [IsAuthenticated()]


class ProductListingListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductListingSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    # filterset_fields = [
    #     "product",
    #     "product__category",
    #     "location",
    #     "status",
    # ]
    filterset_class = ProductListingFilter


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
        
class BuyerRequirementListCreateView(generics.ListCreateAPIView):
    serializer_class = BuyerRequirementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BuyerRequirement.objects.filter(
            buyer=self.request.user
        ).select_related("product", "buyer")

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)
        
# class BuyerRequirementMatchesView(generics.ListAPIView):
#     serializer_class = ProductListingSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         requirement_id = self.kwargs["pk"]

#         try:
#             requirement = BuyerRequirement.objects.select_related(
#                 "buyer",
#                 "product",
#             ).get(
#                 id=requirement_id,
#                 buyer=self.request.user,
#             )
#         except BuyerRequirement.DoesNotExist:
#             return ProductListing.objects.none()

#         from .matching import get_matching_listings

#         return get_matching_listings(requirement)

class BuyerRequirementMatchesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        try:
            requirement = BuyerRequirement.objects.select_related(
                "buyer",
                "product"
            ).get(
                id=pk,
                buyer=request.user
            )

        except BuyerRequirement.DoesNotExist:
            return Response(
                {"detail": "Requirement not found."},
                status=404
            )

        result = get_matching_allocations(requirement)

        return Response(result)