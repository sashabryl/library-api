import datetime
import os

import stripe
from django.db.models import Q
from django.http import HttpResponseRedirect
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from book.models import Book, Borrowing, Payment
from book.payments import create_payment, recover_payment
from book.permissions import (
    IsAdminOrReadOnly,
    BorrowingIsAdminOrAuthenticatedOwner,
    PaymentIsAdminOrAuthenticatedOwner,
)
from book.serializers import (
    BookListSerializer,
    BookSerializer,
    BorrowSerializer,
    BorrowListSerializer,
    BorrowDetailSerializer,
    PaymentListSerializer,
    PaymentDetailSerializer,
)


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


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
    RetrieveModelMixin,
):
    permission_classes = [BorrowingIsAdminOrAuthenticatedOwner]

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowSerializer

        if self.action == "list":
            return BorrowListSerializer

        return BorrowDetailSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.all()

        if self.action == "list" and not self.request.user.is_staff:
            return queryset.filter(user=self.request.user).select_related(
                "user", "book"
            )

        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            queryset = queryset.filter(user__id=user_id)

        if is_active is not None:
            if is_active == "True":
                queryset = queryset.filter(actual_return_date__isnull=True)
            else:
                queryset = queryset.filter(
                    Q(actual_return_date__isnull=False)
                )

        if self.action == "list":
            queryset = queryset.select_related("user")

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if Payment.objects.filter(
            borrowing__in=request.user.borrowings.all(), status="PENDING"
        ).exists():
            return Response(
                "You will be able to borrow new books once "
                "you have completed all your payments",
                status=403,
            )

        response = super().create(request, *args, **kwargs)
        borrowing = Borrowing.objects.get(id=response.data.get("id"))
        return HttpResponseRedirect(
            redirect_to=create_payment(
                request=request, borrowing=borrowing, type="PAYMENT"
            )
        )

    @action(
        methods=["GET"],
        detail=True,
        url_path="return",
        permission_classes=[IsAdminUser],
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date:
            return Response(
                f"This book has been already "
                f"returned on {borrowing.actual_return_date}!",
                status=400,
            )
        borrowing.actual_return_date = datetime.date.today()
        borrowing.save()
        book = borrowing.book
        book.inventory += 1
        book.save()

        if borrowing.actual_return_date <= borrowing.expected_return_date:
            return Response(
                f"{book.title} has been returned on "
                f"{datetime.date.today()} successfully."
            )

        return Response(
            f"Well, well, silly {borrowing.user}, "
            f"here is their fine: {create_payment(borrowing=borrowing, request=request, type='FINE')}"
        )


class PaymentViewSet(
    viewsets.GenericViewSet, ListModelMixin, RetrieveModelMixin
):
    permission_classes = [PaymentIsAdminOrAuthenticatedOwner]

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "borrowing__user", "borrowing__book"
        )

        if not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer

        return PaymentDetailSerializer

    @action(methods=["GET"], detail=True, url_path="success")
    def success(self, request, pk=None):
        payment = self.get_object()
        session = stripe.checkout.Session.retrieve(payment.session_id)
        customer = stripe.Customer.retrieve(session.customer)
        payment.status = "PAID"
        payment.save()
        return Response(f"Thank you, {customer.name}!", status=200)

    @action(methods=["GET"], detail=True, url_path="cancel")
    def cancel(self, request, pk=None):
        return Response(
            f"Please don't forget to complete this payment "
            f"later (the session is active for 24 hours). "
            f"Link to the session can be found on the payment detail page.",
            status=200,
        )

    @action(methods=["GET"], detail=True, url_path="renew-session")
    def renew_session(self, request, pk=None):
        payment = self.get_object()
        if payment.status != "EXPIRED":
            return Response(
                "This payment is totally fine, no need for a renewal",
                status=403,
            )

        recover_payment(request, payment)
        return Response(f"Renewed successfully. Link: {payment.session_url}")
