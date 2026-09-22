import django_filters

from .models import ProductListing


class ProductListingFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte"
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte"
    )

    min_quantity = django_filters.NumberFilter(
        field_name="quantity",
        lookup_expr="gte"
    )

    max_quantity = django_filters.NumberFilter(
        field_name="quantity",
        lookup_expr="lte"
    )

    class Meta:
        model = ProductListing
        fields = [
            "product",
            "product__category",
            "location",
            "status",
        ]