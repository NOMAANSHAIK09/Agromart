from django.urls import path

from .views import (
    ProductListCreateView,
    ProductListingListCreateView,
    MyListingsView,
    ProductListingDetailView,
    BuyerRequirementListCreateView,
    BuyerRequirementMatchesView,
)


urlpatterns = [
    path(
        "products/",
        ProductListCreateView.as_view(),
        name="product-list-create",
    ),

    path(
        "listings/",
        ProductListingListCreateView.as_view(),
        name="listing-list-create",
    ),

    path(
        "listings/my/",
        MyListingsView.as_view(),
        name="my-listings",
    ),

    path(
        "listings/<int:pk>/",
        ProductListingDetailView.as_view(),
        name="listing-detail",
    ),
    
    
    path(
        "requirements/",
        BuyerRequirementListCreateView.as_view(),
        name="buyer-requirements",
    ),
    
    path(
        "requirements/<int:pk>/matches/",
        BuyerRequirementMatchesView.as_view(),
        name="requirement-matches",
    ),
]