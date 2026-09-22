from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    """
    Farmers, bulk buyers, and retailers can create/manage listings.
    Consumers can only purchase.
    """

    SELLER_ROLES = [
        "farmer",
        "bulk_buyer",
        "retailer",
    ]

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.SELLER_ROLES
        )