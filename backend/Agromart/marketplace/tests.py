from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Product, ProductListing, BuyerRequirement


User = get_user_model()


class MarketplaceTests(APITestCase):

    def setUp(self):
        # Users
        self.farmer = User.objects.create_user(
            username="farmer1",
            password="testpass123",
            role="farmer",
        )

        self.bulk_buyer = User.objects.create_user(
            username="bulkbuyer1",
            password="testpass123",
            role="bulk_buyer",
        )

        self.retailer = User.objects.create_user(
            username="retailer1",
            password="testpass123",
            role="retailer",
        )

        self.consumer = User.objects.create_user(
            username="consumer1",
            password="testpass123",
            role="consumer",
        )

        # Product
        self.product = Product.objects.create(
            name="Tomato",
            category="vegetables",
            unit="kg",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    # ============================================================
    # PRODUCT TESTS
    # ============================================================

    def test_farmer_can_create_product(self):
        self.authenticate(self.farmer)

        response = self.client.post(
            "/api/marketplace/products/",
            {
                "name": "Potato",
                "category": "vegetables",
                "unit": "kg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_bulk_buyer_can_create_product(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            "/api/marketplace/products/",
            {
                "name": "Rice",
                "category": "grains",
                "unit": "kg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_retailer_can_create_product(self):
        self.authenticate(self.retailer)

        response = self.client.post(
            "/api/marketplace/products/",
            {
                "name": "Onion",
                "category": "vegetables",
                "unit": "kg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_consumer_cannot_create_product(self):
        self.authenticate(self.consumer)

        response = self.client.post(
            "/api/marketplace/products/",
            {
                "name": "Carrot",
                "category": "vegetables",
                "unit": "kg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    # ============================================================
    # PRODUCT LISTING TESTS
    # ============================================================

    def test_farmer_can_create_listing(self):
        self.authenticate(self.farmer)

        response = self.client.post(
            "/api/marketplace/listings/",
            {
                "product": self.product.id,
                "quantity": "500.00",
                "price": "40.00",
                "location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        listing = ProductListing.objects.get(id=response.data["id"])

        self.assertEqual(listing.seller, self.farmer)
        self.assertEqual(listing.quantity, Decimal("500.00"))
        self.assertEqual(listing.price, Decimal("40.00"))

    def test_consumer_cannot_create_listing(self):
        self.authenticate(self.consumer)

        response = self.client.post(
            "/api/marketplace/listings/",
            {
                "product": self.product.id,
                "quantity": "100.00",
                "price": "50.00",
                "location": "Hyderabad",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_seller_can_update_own_listing(self):
        listing = ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=500,
            price=40,
            location="Hyderabad",
        )

        self.authenticate(self.farmer)

        response = self.client.patch(
            f"/api/marketplace/listings/{listing.id}/",
            {
                "price": "45.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        listing.refresh_from_db()

        self.assertEqual(listing.price, Decimal("45.00"))

    def test_seller_cannot_update_other_sellers_listing(self):
        listing = ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=500,
            price=40,
            location="Hyderabad",
        )

        self.authenticate(self.bulk_buyer)

        response = self.client.patch(
            f"/api/marketplace/listings/{listing.id}/",
            {
                "price": "45.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        listing.refresh_from_db()

        self.assertEqual(listing.price, Decimal("40.00"))

    # ============================================================
    # BUYER REQUIREMENT + MATCHING TESTS
    # ============================================================

    def test_bulk_buyer_matches_farmer_listings(self):
        listing = ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=200,
            price=40,
            location="Hyderabad",
        )

        requirement = BuyerRequirement.objects.create(
            buyer=self.bulk_buyer,
            product=self.product,
            quantity=200,
            location="Hyderabad",
            required_by="2026-12-31T12:00:00Z",
        )

        self.authenticate(self.bulk_buyer)

        response = self.client.get(
            f"/api/marketplace/requirements/{requirement.id}/matches/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["required_quantity"],
            Decimal("200.00"),
        )

        self.assertEqual(
            response.data["matched_quantity"],
            Decimal("200.00"),
        )

        self.assertEqual(
            response.data["remaining_quantity"],
            Decimal("0.00"),
        )

        self.assertTrue(response.data["fulfillable"])

        self.assertEqual(len(response.data["matches"]), 1)

        self.assertEqual(
            response.data["matches"][0]["seller_role"],
            "farmer",
        )

    def test_requirement_can_be_fulfilled_from_multiple_listings(self):
        ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=200,
            price=40,
            location="Hyderabad",
        )

        ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=150,
            price=42,
            location="Hyderabad",
        )

        ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=200,
            price=45,
            location="Hyderabad",
        )

        requirement = BuyerRequirement.objects.create(
            buyer=self.bulk_buyer,
            product=self.product,
            quantity=500,
            location="Hyderabad",
            required_by="2026-12-31T12:00:00Z",
        )

        self.authenticate(self.bulk_buyer)

        response = self.client.get(
            f"/api/marketplace/requirements/{requirement.id}/matches/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["required_quantity"],
            Decimal("500.00"),
        )

        self.assertEqual(
            response.data["matched_quantity"],
            Decimal("500.00"),
        )

        self.assertEqual(
            response.data["remaining_quantity"],
            Decimal("0.00"),
        )

        self.assertTrue(response.data["fulfillable"])

        self.assertEqual(len(response.data["matches"]), 3)

    def test_requirement_is_not_fulfillable_when_quantity_is_insufficient(self):
        ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=200,
            price=40,
            location="Hyderabad",
        )

        requirement = BuyerRequirement.objects.create(
            buyer=self.bulk_buyer,
            product=self.product,
            quantity=500,
            location="Hyderabad",
            required_by="2026-12-31T12:00:00Z",
        )

        self.authenticate(self.bulk_buyer)

        response = self.client.get(
            f"/api/marketplace/requirements/{requirement.id}/matches/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["required_quantity"],
            Decimal("500.00"),
        )

        self.assertEqual(
            response.data["matched_quantity"],
            Decimal("200.00"),
        )

        self.assertEqual(
            response.data["remaining_quantity"],
            Decimal("300.00"),
        )

        self.assertFalse(response.data["fulfillable"])

    def test_retailer_matches_bulk_buyer_listings(self):
        # Bulk buyer listing - SHOULD MATCH
        bulk_listing = ProductListing.objects.create(
            product=self.product,
            seller=self.bulk_buyer,
            quantity=500,
            price=60,
            location="Hyderabad",
        )

        # Farmer listing - SHOULD NOT MATCH
        ProductListing.objects.create(
            product=self.product,
            seller=self.farmer,
            quantity=500,
            price=40,
            location="Hyderabad",
        )

        requirement = BuyerRequirement.objects.create(
            buyer=self.retailer,
            product=self.product,
            quantity=300,
            location="Hyderabad",
            required_by="2026-12-31T12:00:00Z",
        )

        self.authenticate(self.retailer)

        response = self.client.get(
            f"/api/marketplace/requirements/{requirement.id}/matches/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["required_quantity"],
            Decimal("300.00"),
        )

        self.assertEqual(
            response.data["matched_quantity"],
            Decimal("300.00"),
        )

        self.assertEqual(
            response.data["remaining_quantity"],
            Decimal("0.00"),
        )

        self.assertTrue(response.data["fulfillable"])

        self.assertEqual(len(response.data["matches"]), 1)

        self.assertEqual(
            response.data["matches"][0]["listing_id"],
            bulk_listing.id,
        )

        self.assertEqual(
            response.data["matches"][0]["seller_role"],
            "bulk_buyer",
        )
        
        # ============================================================
    # BUYER REQUIREMENT PERMISSION TESTS
    # ============================================================

    def test_bulk_buyer_can_create_requirement(self):
        self.authenticate(self.bulk_buyer)

        response = self.client.post(
            "/api/marketplace/requirements/",
            {
                "product": self.product.id,
                "quantity": "500.00",
                "location": "Hyderabad",
                "required_by": "2026-12-31T12:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        requirement = BuyerRequirement.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(requirement.buyer, self.bulk_buyer)
        self.assertEqual(requirement.quantity, Decimal("500.00"))

    def test_retailer_can_create_requirement(self):
        self.authenticate(self.retailer)

        response = self.client.post(
            "/api/marketplace/requirements/",
            {
                "product": self.product.id,
                "quantity": "100.00",
                "location": "Hyderabad",
                "required_by": "2026-12-31T12:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        requirement = BuyerRequirement.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(requirement.buyer, self.retailer)

    def test_farmer_cannot_create_requirement(self):
        self.authenticate(self.farmer)

        response = self.client.post(
            "/api/marketplace/requirements/",
            {
                "product": self.product.id,
                "quantity": "500.00",
                "location": "Hyderabad",
                "required_by": "2026-12-31T12:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_consumer_cannot_create_requirement(self):
        self.authenticate(self.consumer)

        response = self.client.post(
            "/api/marketplace/requirements/",
            {
                "product": self.product.id,
                "quantity": "10.00",
                "location": "Hyderabad",
                "required_by": "2026-12-31T12:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)