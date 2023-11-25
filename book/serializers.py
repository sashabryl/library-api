import datetime

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

    @staticmethod
    def validate_book(value):
        if value.inventory == 0:
            raise ValidationError(
                f"Sorry {value} is not available at the moment"
            )
        return value

    @staticmethod
    def validate_expected_return_date(value):
        if datetime.date.today() == value:
            raise ValidationError(
                "Please choose tomorrow if you want to "
                "borrow a book just for one day"
            )
        if datetime.date.today() > value:
            raise ValidationError("Please choose a date in the future")
        return value

    def create(self, validated_data):
        book = validated_data.get("book")
        book.inventory -= 1
        book.save()
        return super().create(validated_data)


class BorrowDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    book = serializers.StringRelatedField()

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "is_active",
            "actual_return_date",
        )


class BorrowListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "user",
            "is_active",
        )
