from rest_framework import serializers
from .models import Product, ProductListing, BuyerRequirement


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
        
class BuyerRequirementSerializer(serializers.ModelSerializer):
    buyer = serializers.ReadOnlyField(source="buyer.username")
    buyer_role = serializers.ReadOnlyField(source="buyer.role")

    class Meta:
        model = BuyerRequirement
        fields = [
            "id",
            "buyer",
            "buyer_role",
            "product",
            "quantity",
            "location",
            "required_by",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "buyer",
            "buyer_role",
            "status",
            "created_at",
        ]
    def validate(self, attrs):
        user = self.context["request"].user

        if user.role not in ["bulk_buyer", "retailer"]:
            raise serializers.ValidationError(
                "Only bulk buyers and retailers can create requirements."
            )

        return attrs