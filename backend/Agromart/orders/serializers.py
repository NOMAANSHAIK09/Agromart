from rest_framework import serializers
from .models import Order
from marketplace.models import ProductListing


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "seller",
            "listing",
            "quantity",
            "price_per_unit",
            "total_amount",
            "delivery_location",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "buyer",
            "seller",
            "price_per_unit",
            "total_amount",
            "created_at",
            "updated_at",
        ]

    def validate_listing(self, listing):
        if listing.status != "active":
            raise serializers.ValidationError(
                "This listing is not available for ordering."
            )

        if listing.quantity <= 0:
            raise serializers.ValidationError(
                "This listing has no available inventory."
            )

        return listing

    def validate_quantity(self, quantity):
        if quantity <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than zero."
            )

        return quantity

    def validate_delivery_location(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Delivery location is required."
            )

        return value.strip()

    def validate(self, attrs):
        request = self.context["request"]

        #PATCH/UPDATE validation
        if self.instance is not None:
            return attrs

    # CREATE validation
        buyer = request.user
        listing = attrs["listing"]
        quantity = attrs["quantity"]
        seller = listing.seller

        if seller.role not in ["farmer", "bulk_buyer", "retailer"]:
            raise serializers.ValidationError(
                "This user is not allowed to sell products."
            )

        if buyer == seller:
            raise serializers.ValidationError(
                "Buyer and seller cannot be the same user."
            )

        valid_flow = {
            "farmer": "bulk_buyer",
            "bulk_buyer": "retailer",
            "retailer": "consumer",
        }

        expected_buyer_role = valid_flow.get(seller.role)

        if buyer.role != expected_buyer_role:
            raise serializers.ValidationError(
                f"A {seller.role} can only sell to a {expected_buyer_role}."
            )

        if quantity > listing.quantity:
            raise serializers.ValidationError(
            "Requested quantity exceeds available inventory."
            )

        return attrs