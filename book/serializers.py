from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.models import Book


class BookSerializer(serializers.ModelSerializer):
    inventory = serializers.IntegerField(min_value=0)

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "daily_fee", "is_available")
