from django.db.models import Q
from rest_framework import viewsets
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated

from book.models import Book, Borrowing
from book.permissions import IsAdminOrReadOnly
from book.serializers import (
    BookListSerializer,
    BookSerializer, BorrowSerializer, BorrowListSerializer, BorrowDetailSerializer
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer

        return BookSerializer


class BorrowViewSet(
    viewsets.GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin
):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowSerializer

        if self.action == "list":
            return BorrowListSerializer

        return BorrowDetailSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.all()

        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            queryset = queryset.filter(user__id=user_id)

        if is_active is not None:
            if is_active is True:
                queryset = queryset.filter(
                    actual_return_date__isnull=False
                ).exclude(actual_return_date="")
            else:
                queryset = queryset.filter(
                    Q(actual_return_date__isnull=True) | Q(actual_return_date="")
                )

        if self.action == "list":
            queryset = queryset.select_related("user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



