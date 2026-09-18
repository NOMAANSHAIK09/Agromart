from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("farmer", "Farmer"),
        ("bulk_buyer", "Bulk Buyer"),
        ("retailer", "Retailer"),
        ("consumer", "Consumer"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True
    )

    location = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        return f"{self.username} - {self.role}"
    