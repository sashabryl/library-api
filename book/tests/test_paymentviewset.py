import datetime
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.urls import reverse

from book.models import Book, Borrowing, Payment
from book.serializers import PaymentListSerializer, PaymentDetailSerializer


PAYMENT_URL = reverse("book:payment-list")


def sample_user():
    return get_user_model().objects.create_user(
        email=f"{uuid.uuid4()}hwa@gmail.com", password="jewaifj@!3e"
    )


def sample_book(**params):
    defaults = {
        "title": "Blue Seas",
        "author": "Sasha Brul",
        "inventory": 10,
        "cover": "HARD",
        "daily_fee": Decimal("10.00"),
    }
    defaults.update(**params)
    return Book.objects.create(**defaults)


def sample_borrowing(**params):
    defaults = {
        "borrow_date": datetime.date.today(),
        "expected_return_date": (
            datetime.date.today() + datetime.timedelta(days=2)
        ),
        "actual_return_date": None,
        "book": sample_book(),
        "user": sample_user(),
    }
    defaults.update(**params)
    return Borrowing.objects.create(**defaults)


def sample_payment(**params):
    defaults = {
        "type": "FINE",
        "status": "PENDING",
        "money_to_pay": Decimal("20.00"),
        "borrowing": sample_borrowing()
    }
    defaults.update(**params)
    return Payment.objects.create(**defaults)


def get_detail_url(pk: int):
    return reverse("book:payment-detail", args=[pk])


class UnauthenticatedPaymentApiTests(APITestCase):
    def test_list_forbidden(self):
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, 401)

    def test_create_forbidden(self):
        sample_borrowing()
        payload = {
            "type": "FINE",
            "status": "PENDING",
            "money_to_pay": Decimal("20.00"),
            "borrowing": 1
        }
        res = self.client.post(PAYMENT_URL, payload)
        self.assertEqual(res.status_code, 401)

    def test_retrieve_forbidden(self):
        payment = sample_payment()
        res = self.client.get(get_detail_url(payment.id))
        self.assertEqual(res.status_code, 401)

    def test_update_partial_update_forbidden(self):
        payment = sample_payment()
        sample_borrowing()
        sample_borrowing()
        payload = {
            "type": "FINE",
            "status": "EXPIRED",
            "money_to_pay": Decimal("21.00"),
            "borrowing": 2
        }

        res = self.client.put(get_detail_url(payment.id), payload)
        self.assertEqual(res.status_code, 401)

        payload = {"status": "PAID"}
        res = self.client.patch(get_detail_url(payment.id), payload)
        self.assertEqual(res.status_code, 401)

    def test_delete_forbidden(self):
        payment = sample_payment()
        res = self.client.delete(get_detail_url(payment.id))
        self.assertEqual(res.status_code, 401)





