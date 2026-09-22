from django.db.models import Q
from decimal import Decimal

from .models import BuyerRequirement, ProductListing


def get_matching_allocations(requirement):
    """
    Find marketplace listings that can potentially
    fulfill a buyer requirement.
    """

    buyer_role = requirement.buyer.role

    if buyer_role == "bulk_buyer":
        allowed_seller_role = "farmer"

    elif buyer_role == "retailer":
        allowed_seller_role = "bulk_buyer"

    else:
        return {
            "required_quantity": requirement.quantity,
            "matched_quantity": Decimal("0"),
            "remaining_quantity": requirement.quantity,
            "fulfillable": False,
            "matches": [],
        }

    listings = ProductListing.objects.filter(
        product=requirement.product,
        status="active",
        quantity__gt=0,
        seller__role=allowed_seller_role,
        location__iexact=requirement.location,
    ).select_related(
        "product",
        "seller",
    ).order_by(
        "price",
        "-quantity",
    )

    remaining = requirement.quantity
    matched_quantity = Decimal("0")
    matches = []

    for listing in listings:

        if remaining <= 0:
            break

        allocated_quantity = min(
            listing.quantity,
            remaining
        )

        matches.append({
            "listing_id": listing.id,
            "seller": listing.seller.username,
            "seller_role": listing.seller.role,
            "available_quantity": listing.quantity,
            "allocated_quantity": allocated_quantity,
            "price": listing.price,
            "location": listing.location,
        })

        matched_quantity += allocated_quantity
        remaining -= allocated_quantity

    return {
        "required_quantity": requirement.quantity,
        "matched_quantity": matched_quantity,
        "remaining_quantity": max(remaining, Decimal("0")),
        "fulfillable": remaining <= 0,
        "matches": matches,
    }