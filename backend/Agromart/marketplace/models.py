from django.db import models
from django.conf import settings


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("vegetables", "Vegetables"),
        ("fruits", "Fruits"),
        ("grains", "Grains"),
        ("pulses", "Pulses"),
        ("spices", "Spices"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    unit = models.CharField(max_length=20)
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class ProductListing(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("sold_out", "Sold Out"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="listings"
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_listings"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    location = models.CharField(max_length=255)

    available_from = models.DateTimeField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.seller.username}"