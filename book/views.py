import datetime
import os

import stripe
from django.db.models import Q
from django.http import HttpResponseRedirect
from drf_spectacular.utils import extend_schema, OpenApiParameter
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
    IsAdminOrListOnly,
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
    permission_classes = [IsAdminOrListOnly]

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
            if is_active.lower() == "true":
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
        """
        If the user does not have unpaid payment,
        redirects to a stripe payment session.
        Otherwise, return 403.
        """
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
        """
        Sets the current date as actual_return_date of the borrowing.
        If it is not null already, returns status code 400.
        If the actual_return_date turns out to be later than expected,
        a fine payment is created.
        """
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
            f"here is their fine: "
            f"{create_payment(request, borrowing, 'FINE')}"
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                description=(
                    "Filter by case-insensitive is_active "
                    "(bool) (ex. ?is_active=TRUe)"
                ),
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="user_id",
                description="Filter by id of a user (ex. ?user_id=2)",
                required=False,
                type=int,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Filtering is for superusers only."""
        return super().list(request, *args, **kwargs)


class PaymentViewSet(
    viewsets.GenericViewSet, ListModelMixin, RetrieveModelMixin
):
    permission_classes = [PaymentIsAdminOrAuthenticatedOwner]

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "borrowing__user", "borrowing__book"
        )

        if self.action == "list" and not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer

        return PaymentDetailSerializer

    @action(methods=["GET"], detail=True, url_path="success")
    def success(self, request, pk=None):
        """
        Endpoint to which Stripe redirects users after a successful payment.
        Here Payment status becomes "PAID"
        """
        payment = self.get_object()
        session = stripe.checkout.Session.retrieve(payment.session_id)
        if session.payment_status == "paid":
            customer = stripe.Customer.retrieve(session.customer)
            payment.status = "PAID"
            payment.save()
            return Response(f"Thank you, {customer.name}!", status=200)

        return Response(f"Not yet, pay first: {session.url}", status=403)

    @action(methods=["GET"], detail=True, url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Endpoint to which Stripe redirects users after a canceled payment.
        """
        return Response(
            "Please don't forget to complete this payment "
            "later (the session is active for 24 hours). "
            "Link to the session can be found on the payment detail page.",
            status=200,
        )

    @action(methods=["GET"], detail=True, url_path="renew-session")
    def renew_session(self, request, pk=None):
        """
        Here users can "renew" their expired payments
        (a new stripe checkout session is created with the same data).
        """
        payment = self.get_object()
        if payment.status != "EXPIRED":
            return Response(
                "This payment is totally fine, no need for a renewal",
                status=403,
            )

        recover_payment(request, payment)
        return Response(f"Renewed successfully. Link: {payment.session_url}")
