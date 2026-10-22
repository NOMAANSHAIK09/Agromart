from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from marketplace.models import Product, ProductListing
from .models import Order


class OrderAPITestCase(APITestCase):

    def setUp(self):
        # Users
        self.farmer = User.objects.create_user(
            username="farmer_test",
            password="TestPass123!",
            role="farmer",
        )

        self.bulk_buyer = User.objects.create_user(
            username="bulk_test",
            password="TestPass123!",
            role="bulk_buyer",
        )

        self.retailer = User.objects.create_user(
            username="retailer_test",
            password="TestPass123!",
            role="retailer",
        )

        self.consumer = User.objects.create_user(
            username="consumer_test",
            password="TestPass123!",
            role="consumer",
        )

        # Extra unrelated user
        self.other_user = User.objects.create_user(
            username="other_test",
            password="TestPass123!",
            role="consumer",
        )

        # Product
        self.product = Product.objects.create(
            name="Test Tomato",
            category="vegetables",
            unit="kg",
        )

        # Farmer listing
        self.farmer_listing = ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=Decimal("500.00"),
            price=Decimal("40.00"),
            location="Hyderabad",
            status="active",
        )

        # Bulk buyer listing
        self.bulk_listing = ProductListing.objects.create(
            product=self.product,
            seller=self.bulk_buyer,
            quantity=Decimal("500.00"),
            price=Decimal("45.00"),
            location="Hyderabad",
            status="active",
        )

        # Retailer listing
        self.retailer_listing = ProductListing.objects.create(
            product=self.product,
            seller=self.retailer,
            quantity=Decimal("500.00"),
            price=Decimal("50.00"),
            location="Hyderabad",
            status="active",
        )

        self.url = "/api/orders/"

    # ---------------------------------------------------------
    # HELPER
    # ---------------------------------------------------------

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    # ---------------------------------------------------------
    # LISTING VALIDATION
    # ---------------------------------------------------------

    def test_cannot_order_nonexistent_listing(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": 99999,
                "quantity": "10.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_order_inactive_listing(self):
        self.farmer_listing.status = "inactive"
        self.farmer_listing.save()

        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "10.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_order_sold_out_listing(self):
        self.farmer_listing.quantity = 0
        self.farmer_listing.status = "sold_out"
        self.farmer_listing.save()

        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "10.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_order_zero_quantity(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "0",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_order_negative_quantity(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "-10",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_order_more_than_available_quantity(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "600",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------------------------------------------------------
    # PRICE
    # ---------------------------------------------------------

    def test_price_is_copied_from_listing(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Decimal(response.data["price_per_unit"]),
            Decimal("40.00"),
        )

    def test_total_amount_is_calculated(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Decimal(response.data["total_amount"]),
            Decimal("4000.00"),
        )

    def test_client_cannot_manipulate_price(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100",
                "price_per_unit": "1.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Decimal(response.data["price_per_unit"]),
            Decimal("40.00"),
        )

    def test_client_cannot_manipulate_total(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100",
                "total_amount": "1.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Decimal(response.data["total_amount"]),
            Decimal("4000.00"),
        )

    # ---------------------------------------------------------
    # INVENTORY
    # ---------------------------------------------------------

    def test_successful_order_reduces_inventory(self):
        self.authenticate(self.bulk_buyer)

        self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.farmer_listing.refresh_from_db()

        self.assertEqual(
            self.farmer_listing.quantity,
            Decimal("400.00"),
        )

    def test_listing_becomes_sold_out(self):
        self.farmer_listing.quantity = 100
        self.farmer_listing.save()

        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.farmer_listing.refresh_from_db()

        self.assertEqual(
            self.farmer_listing.quantity,
            Decimal("0.00"),
        )
        self.assertEqual(
            self.farmer_listing.status,
            "sold_out",
        )

    # ---------------------------------------------------------
    # VISIBILITY
    # ---------------------------------------------------------

    def test_order_visibility_for_buyer_and_seller(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["id"]

        # Buyer can see their order
        self.authenticate(self.bulk_buyer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Seller can see the same order
        self.authenticate(self.farmer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Seller can also access order detail
        response = self.client.get(f"{self.url}{order_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unrelated_user_cannot_see_order(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["id"]

        # Unrelated user cannot access the order
        self.authenticate(self.other_user)

        response = self.client.get(
            f"{self.url}{order_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # STATUS TRANSITIONS
    # ---------------------------------------------------------

    def test_seller_can_confirm_order(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["id"]

        self.authenticate(self.farmer)

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"status": "confirmed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "confirmed")

    def test_invalid_status_transition_is_rejected(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["id"]

        self.authenticate(self.farmer)

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"status": "shipped"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_patch_cannot_change_protected_order_fields(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["id"]

        original_quantity = response.data["quantity"]
        original_listing = response.data["listing"]
        original_total = response.data["total_amount"]

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {
                "listing": self.bulk_listing.id,
                "quantity": "10.00",
                "buyer": self.consumer.id,
                "seller": self.retailer.id,
                "price_per_unit": "1.00",
                "total_amount": "1.00",
                "delivery_location": "Chennai",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        response = self.client.get(f"{self.url}{order_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], original_quantity)
        self.assertEqual(response.data["listing"], original_listing)
        self.assertEqual(response.data["total_amount"], original_total)
        self.assertEqual(response.data["delivery_location"], "Hyderabad")

    def test_buyer_can_update_delivery_location(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["id"]

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"delivery_location": "Chennai"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["delivery_location"], "Chennai")

    # ---------------------------------------------------------
    # CANCELLATION
    # ---------------------------------------------------------

    def test_buyer_can_cancel_pending_order(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order_id = response.data["id"]

        self.authenticate(self.bulk_buyer)

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["status"],
            "cancelled",
        )

    def test_cancellation_restores_inventory(self):
        initial_quantity = self.farmer_listing.quantity

        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order_id = response.data["id"]

        self.farmer_listing.refresh_from_db()

        self.assertEqual(
            self.farmer_listing.quantity,
            initial_quantity - Decimal("50"),
        )

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.farmer_listing.refresh_from_db()

        self.assertEqual(
            self.farmer_listing.quantity,
            initial_quantity,
        )

    def test_cancelled_order_cannot_be_cancelled_again(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order_id = response.data["id"]

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.farmer_listing.refresh_from_db()

        quantity_after_cancel = self.farmer_listing.quantity

        response = self.client.patch(
            f"{self.url}{order_id}/",
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.farmer_listing.refresh_from_db()

        self.assertEqual(
            self.farmer_listing.quantity,
            quantity_after_cancel,
        )

    # ---------------------------------------------------------
    # PRICE SNAPSHOT
    # ---------------------------------------------------------

    def test_price_snapshot_survives_listing_price_change(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order_id = response.data["id"]

        self.farmer_listing.price = Decimal("99.00")
        self.farmer_listing.save(
            update_fields=["price", "updated_at"]
        )

        response = self.client.get(
            f"{self.url}{order_id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["price_per_unit"],
            "40.00",
        )

        self.assertEqual(
            response.data["total_amount"],
            "2000.00",
        )

    # ---------------------------------------------------------
    # 1. AUTHENTICATION
    # ---------------------------------------------------------

    def test_unauthenticated_user_cannot_create_order(self):
        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_create_valid_order(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "100.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["buyer"],
            self.bulk_buyer.id,
        )

        self.assertEqual(
            response.data["seller"],
            self.farmer.id,
        )

    # ---------------------------------------------------------
    # 2. VALID ROLE FLOWS
    # ---------------------------------------------------------

    def test_bulk_buyer_can_buy_from_farmer(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_retailer_can_buy_from_bulk_buyer(self):
        self.authenticate(self.retailer)

        response = self.client.post(
            self.url,
            {
                "listing": self.bulk_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_consumer_can_buy_from_retailer(self):
        self.authenticate(self.consumer)

        response = self.client.post(
            self.url,
            {
                "listing": self.retailer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    # ---------------------------------------------------------
    # 3. INVALID ROLE FLOWS
    # ---------------------------------------------------------

    def test_farmer_cannot_buy_from_farmer(self):
        self.authenticate(self.farmer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_retailer_cannot_buy_from_farmer(self):
        self.authenticate(self.retailer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_consumer_cannot_buy_from_farmer(self):
        self.authenticate(self.consumer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_consumer_cannot_buy_from_bulk_buyer(self):
        self.authenticate(self.consumer)

        response = self.client.post(
            self.url,
            {
                "listing": self.bulk_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_bulk_buyer_cannot_buy_from_retailer(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            self.url,
            {
                "listing": self.retailer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_cannot_buy_own_listing(self):
        self.authenticate(self.farmer)

        response = self.client.post(
            self.url,
            {
                "listing": self.farmer_listing.id,
                "quantity": "50.00",
                "delivery_location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )