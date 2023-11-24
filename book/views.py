from rest_framework import viewsets

from book.models import Book
from book.serializers import (
    BookListSerializer,
    BookSerializer
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer

        return BookSerializer

