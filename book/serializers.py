from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.models import Book, Borrowing


class BookSerializer(serializers.ModelSerializer):
    inventory = serializers.IntegerField(min_value=0)

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "daily_fee", "is_available")


class BorrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "expected_return_date", "book")


class BorrowDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date"
        )


