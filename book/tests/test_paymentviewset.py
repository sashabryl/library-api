import datetime
import uuid
from decimal import Decimal

from freezegun import freeze_time
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.urls import reverse
import stripe

from book.models import Book, Borrowing, Payment
from book.serializers import PaymentListSerializer, PaymentDetailSerializer


PAYMENT_URL = reverse("book:payment-list")
BORROW_URL = reverse("book:borrow-list")

stripe.api_key = settings.STRIPE_SECRET_KEY


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
        "borrowing": sample_borrowing(),
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
            "borrowing": 1,
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
            "borrowing": 2,
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


class AuthenticatedPaymentApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="feniawj@hmail.com", password="fjewia3112!"
        )

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def test_list_returns_only_your_payments(self):
        my_borrow = sample_borrowing(user=self.user)
        my_payment_one = sample_payment(borrowing=my_borrow)
        my_payment_two = sample_payment(borrowing=my_borrow)
        alien_borrow = sample_borrowing()
        alien_payment = sample_payment(borrowing=alien_borrow)

        my_payments = PaymentListSerializer(
            [my_payment_one, my_payment_two], many=True
        ).data
        alien_payments = PaymentListSerializer(
            [alien_payment], many=True
        ).data

        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, my_payments)
        self.assertNotIn(alien_payments, res.data)

    def test_retrieving_only_your_payments_works(self):
        my_borrow = sample_borrowing(user=self.user)
        my_payment = sample_payment(borrowing=my_borrow)

        res = self.client.get(get_detail_url(my_payment.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("id"), my_payment.id)

    def test_you_cannot_retrieve_payments_of_others(self):
        alien_payment = sample_payment()
        alien_payment.refresh_from_db()
        res = self.client.get(get_detail_url(alien_payment.id))
        self.assertEqual(res.status_code, 403)

    def test_calculation_of_money_to_pay(self):
        book = sample_book(title="the_book", daily_fee=Decimal("10.00"))
        borrowing_payload = {
            "expected_return_date": (
                datetime.date.today() + datetime.timedelta(days=1)
            ),
            "book": book.id,
        }
        self.client.post(BORROW_URL, borrowing_payload)
        borrow = Borrowing.objects.get(book__title=book.title, user=self.user)
        payment = Payment.objects.get(borrowing=borrow)
        self.assertEqual(payment.money_to_pay, Decimal("10.00"))

    def test_renew_session_action(self):
        book = sample_book(title="my_book")
        borrowing_payload = {
            "expected_return_date": (
                datetime.date.today() + datetime.timedelta(days=1)
            ),
            "book": book.id,
        }
        self.client.post(BORROW_URL, borrowing_payload)
        borrow = Borrowing.objects.get(book__title=book.title, user=self.user)
        payment = Payment.objects.get(borrowing=borrow)
        stripe.checkout.Session.expire(payment.session_id)
        payment.status = "EXPIRED"  # simulating celery beat task
        payment.save()
        res = self.client.get(get_detail_url(payment.id) + "renew-session/")

        self.assertEqual(res.status_code, 200)
        payment.refresh_from_db()
        session = stripe.checkout.Session.retrieve(payment.session_id)
        self.assertEqual(session.status, "open")

    def test_create_forbidden(self):
        sample_borrowing()
        payload = {
            "type": "FINE",
            "status": "PENDING",
            "money_to_pay": Decimal("20.00"),
            "borrowing": 1,
        }
        res = self.client.post(PAYMENT_URL, payload)
        self.assertEqual(res.status_code, 405)

    def test_update_partial_update_forbidden(self):
        payment = sample_payment()
        sample_borrowing()
        sample_borrowing()
        payload = {
            "type": "FINE",
            "status": "EXPIRED",
            "money_to_pay": Decimal("21.00"),
            "borrowing": 2,
        }

        res = self.client.put(get_detail_url(payment.id), payload)
        self.assertEqual(res.status_code, 405)

        payload = {"status": "PAID"}
        res = self.client.patch(get_detail_url(payment.id), payload)
        self.assertEqual(res.status_code, 405)

    def test_delete_forbidden(self):
        payment = sample_payment()
        res = self.client.delete(get_detail_url(payment.id))
        self.assertEqual(res.status_code, 405)


class AdminPaymentApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            email="admin@admin.com", password="denwui@321f"
        )

    def setUp(self) -> None:
        self.client.force_authenticate(self.superuser)

    def test_list_returns_all_payments(self):
        payment_one = sample_payment()
        payment_two = sample_payment()
        payment_three = sample_payment()
        payments = PaymentListSerializer(
            [payment_one, payment_two, payment_three], many=True
        ).data
        res = self.client.get(PAYMENT_URL)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, payments)

    def test_admin_can_retrieve_payments_of_others(self):
        payment = sample_payment()
        res = self.client.get(get_detail_url(payment.id))
        self.assertEqual(res.status_code, 200)

    def test_create_forbidden(self):
        sample_borrowing()
        payload = {
            "type": "FINE",
            "status": "PENDING",
            "money_to_pay": Decimal("20.00"),
            "borrowing": 1,
        }
        res = self.client.post(PAYMENT_URL, payload)
        self.assertEqual(res.status_code, 405)

    def test_update_partial_update_forbidden(self):
        payment = sample_payment()
        sample_borrowing()
        sample_borrowing()
        payload = {
            "type": "FINE",
            "status": "EXPIRED",
            "money_to_pay": Decimal("21.00"),
            "borrowing": 2,
        }

        res = self.client.put(get_detail_url(payment.id), payload)
        self.assertEqual(res.status_code, 405)

        payload = {"status": "PAID"}
        res = self.client.patch(get_detail_url(payment.id), payload)
        self.assertEqual(res.status_code, 405)

    def test_delete_forbidden(self):
        payment = sample_payment()
        res = self.client.delete(get_detail_url(payment.id))
        self.assertEqual(res.status_code, 405)
