from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")

    @staticmethod
    def validate_inventory(value):
        if value < 0:
            raise ValidationError("Inventory cannot be negative")
        return value


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "daily_fee", "is_available")
