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


