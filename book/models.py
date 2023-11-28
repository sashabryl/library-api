import datetime

from django.conf import settings
from django.db import models


class Book(models.Model):
    class CoverChoices(models.TextChoices):
        HARD = "HARD", "Hardcover"
        SOFT = "SOFT", "Softcover"

    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    cover = models.CharField(max_length=10, choices=CoverChoices.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["-daily_fee"]

    @property
    def is_available(self) -> bool:
        return self.inventory != 0

    def __str__(self) -> str:
        return f"{self.title.title()} by {self.author.title()}, cover: {self.cover}"


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )

    class Meta:
        ordering = ["-expected_return_date"]

    @property
    def is_active(self) -> bool:
        return not bool(self.actual_return_date)

    def __str__(self) -> str:
        return (
            f"from: {self.borrow_date} - {self.user} '{self.book}' "
            f"- exp: {self.expected_return_date}"
        )


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PAID = "PAID"
        PENDING = "PENDING"

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT"
        FINE = "FINE"

    status = models.CharField(max_length=7, choices=StatusChoices.choices)
    type = models.CharField(max_length=7, choices=TypeChoices.choices)
    borrowing = models.OneToOneField("Borrowing", on_delete=models.CASCADE)
    session_url = models.URLField(null=True, blank=True)
    session_id = models.CharField(max_length=512, null=True, blank=True)
    money_to_pay = models.DecimalField(max_digits=6, decimal_places=2)
