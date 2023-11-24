from django.conf import settings
from django.db import models


class Book(models.Model):
    class CoverChoices(models.TextChoices):
        HARD = "HARD", "Hardcover"
        SOFT = "SORT", "Softcover"

    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    cover = models.CharField(max_length=True, choices=CoverChoices.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["title", "author"]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}, {self.cover}"


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

    def __str__(self) -> str:
        return f"{self.borrow_date} - {self.user} {self.book} - {self.expected_return_date}"
