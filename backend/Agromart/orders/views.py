from django.db import transaction
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Order
from .serializers import OrderSerializer
from marketplace.models import ProductListing


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            Q(buyer=self.request.user) |
            Q(seller=self.request.user)
        ).select_related(
            "buyer",
            "seller",
            "listing",
            "listing__product",
        ).order_by("-created_at")

    def perform_create(self, serializer):
        with transaction.atomic():
            listing_id = serializer.validated_data["listing"].id

            listing = (
                ProductListing.objects
                .select_for_update()
                .select_related("seller", "product")
                .get(pk=listing_id)
            )

            if listing.status != "active":
                raise ValidationError(
                    {"listing": "This listing is not available for ordering."}
                )

            quantity = serializer.validated_data["quantity"]

            if quantity <= 0:
                raise ValidationError(
                    {"quantity": "Quantity must be greater than zero."}
                )

            if quantity > listing.quantity:
                raise ValidationError(
                    {"quantity": "Requested quantity exceeds available inventory."}
                )

            buyer = self.request.user
            seller = listing.seller

            if buyer == seller:
                raise ValidationError(
                    {"order": "Buyer and seller cannot be the same user."}
                )

            valid_flow = {
                "farmer": "bulk_buyer",
                "bulk_buyer": "retailer",
                "retailer": "consumer",
            }

            if seller.role not in valid_flow:
                raise ValidationError(
                    {"seller": "This user is not allowed to sell products."}
                )

            if buyer.role != valid_flow[seller.role]:
                raise ValidationError(
                    {
                        "order": (
                            f"A {seller.role} can only sell "
                            f"to a {valid_flow[seller.role]}."
                        )
                    }
                )

            price_per_unit = listing.price
            total_amount = quantity * price_per_unit

            serializer.save(
                buyer=buyer,
                seller=seller,
                price_per_unit=price_per_unit,
                total_amount=total_amount,
            )

            listing.quantity -= quantity

            if listing.quantity == 0:
                listing.status = "sold_out"

            listing.save(
                update_fields=["quantity", "status", "updated_at"]
            )


class OrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            Q(buyer=self.request.user) |
            Q(seller=self.request.user)
        ).select_related(
            "buyer",
            "seller",
            "listing",
            "listing__product",
        )

    def perform_update(self, serializer):
        order = self.get_object()
        new_status = serializer.validated_data.get("status")

        if new_status is None:
            serializer.save()
            return

        current_status = order.status
        user = self.request.user

        # Buyer can cancel only their own pending order.
        if new_status == "cancelled":
            if user != order.buyer:
                raise ValidationError(
                    "Only the buyer can cancel this order."
                )

            if current_status != "pending":
                raise ValidationError(
                    "Only pending orders can be cancelled."
                )

            with transaction.atomic():
                locked_order = (
                    Order.objects
                    .select_for_update()
                    .select_related("listing")
                    .get(pk=order.pk)
                )

                if locked_order.status != "pending":
                    raise ValidationError(
                        "This order can no longer be cancelled."
                    )

                listing = (
                    ProductListing.objects
                    .select_for_update()
                    .get(pk=locked_order.listing_id)
                )

                listing.quantity += locked_order.quantity
                listing.status = "active"

                listing.save(
                    update_fields=[
                        "quantity",
                        "status",
                        "updated_at",
                    ]
                )

                locked_order.status = "cancelled"
                locked_order.save(
                    update_fields=["status", "updated_at"]
                )
                serializer.instance = locked_order

            return

        # Only seller can move the order forward.
        if user != order.seller:
            raise ValidationError(
                "Only the seller can update the order status."
            )

        allowed_transitions = {
            "pending": ["confirmed"],
            "confirmed": ["processing"],
            "processing": ["shipped"],
            "shipped": ["delivered"],
        }

        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid status transition: "
                f"{current_status} -> {new_status}."
            )

        serializer.save(status=new_status)