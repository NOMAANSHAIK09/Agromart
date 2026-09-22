from rest_framework import serializers
from .models import Product, ProductListing


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "unit",
            "image",
        ]


class ProductListingSerializer(serializers.ModelSerializer):
    seller = serializers.ReadOnlyField(source="seller.username")

    class Meta:
        model = ProductListing
        fields = [
            "id",
            "product",
            "seller",
            "quantity",
            "price",
            "location",
            "available_from",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "seller",
            "status",
            "created_at",
            "updated_at",
        ]