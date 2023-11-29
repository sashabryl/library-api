import datetime
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.urls import reverse

from book.models import Book, Borrowing, Payment
from book.serializers import BorrowListSerializer, BorrowDetailSerializer

BORROW_URL = reverse("book:borrow-list")


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


def get_detail_url(pk: int):
    return reverse("book:borrow-detail", args=[pk])


class UnauthenticatedBorrowApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.borrowing = sample_borrowing()

    def test_list_forbidden(self):
        res = self.client.get(BORROW_URL)
        self.assertEqual(res.status_code, 401)

    def test_retrieve_forbidden(self):
        res = self.client.get(get_detail_url(self.borrowing.id))
        self.assertEqual(res.status_code, 401)

    def test_create_forbidden(self):
        payload = {
            "book": self.borrowing.book,
            "expected_return_date": (
                datetime.date.today() + datetime.timedelta(days=2)
            ),
        }
        res = self.client.post(BORROW_URL, payload)
        self.assertEqual(res.status_code, 401)

    def test_update_partial_update_forbidden(self):
        sample_book()
        sample_user()
        payload = {
            "borrow_date": datetime.date.today(),
            "expected_return_date": (
                datetime.date.today() + datetime.timedelta(days=2)
            ),
            "actual_return_date": datetime.date.today()
            + datetime.timedelta(days=1),
            "book": 2,
            "user": 2,
        }
        res = self.client.put(get_detail_url(self.borrowing.id), payload)
        self.assertEqual(res.status_code, 401)

        payload = {"actual_return_date": datetime.date.today()}
        res = self.client.patch(get_detail_url(self.borrowing.id), payload)
        self.assertEqual(res.status_code, 401)

        self.assertEqual(self.borrowing.actual_return_date, None)

    def test_delete_forbidden(self):
        res = self.client.delete(get_detail_url(self.borrowing.id))
        self.assertEqual(res.status_code, 401)

        self.assertTrue(
            Borrowing.objects.filter(id=self.borrowing.id).exists()
        )


class AuthenticatedBorrowingApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(
            email="someuser@gmail.com", password="fnewia21!2"
        )
        cls.user = user
        cls.borrowing = sample_borrowing(user=user)

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def test_list_returns_only_your_borrowings(self):
        other_borrowing_one = sample_borrowing()
        other_borrowing_two = sample_borrowing()
        res = self.client.get(BORROW_URL)
        other_serializer = BorrowListSerializer(
            [other_borrowing_two, other_borrowing_one], many=True
        )
        my_serializer = BorrowListSerializer([self.borrowing], many=True)

        self.assertEqual(res.status_code, 200)
        self.assertNotIn(other_serializer.data, res.data)
        self.assertEqual(my_serializer.data, res.data)

    def test_retrieve_not_your_borrowings_forbidden(self):
        other_borrowing = sample_borrowing()
        res = self.client.get(get_detail_url(other_borrowing.id))
        self.assertEqual(res.status_code, 403)

    def test_retrieve_works(self):
        res = self.client.get(get_detail_url(self.borrowing.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("id"), self.borrowing.id)

    def test_update_partial_update_forbidden(self):
        sample_book()
        sample_user()
        payload = {
            "borrow_date": datetime.date.today(),
            "expected_return_date": (
                datetime.date.today() + datetime.timedelta(days=2)
            ),
            "actual_return_date": (
                datetime.date.today() + datetime.timedelta(days=1)
            ),
            "book": 2,
            "user": 2,
        }
        res = self.client.put(get_detail_url(self.borrowing.id), payload)
        self.assertEqual(res.status_code, 405)

        payload = {"actual_return_date": datetime.date.today()}
        res = self.client.patch(get_detail_url(self.borrowing.id), payload)
        self.assertEqual(res.status_code, 405)

        self.assertEqual(self.borrowing.actual_return_date, None)

    def test_delete_forbidden(self):
        res = self.client.delete(get_detail_url(self.borrowing.id))
        self.assertEqual(res.status_code, 405)
        self.assertTrue(Borrowing.objects.filter(id=self.borrowing.id).exists)

    def test_create_works(self):
        expected_return_date = datetime.date.today() + datetime.timedelta(
            days=2
        )
        book = sample_book()
        payload = {
            "expected_return_date": expected_return_date,
            "book": book.id,
        }
        res = self.client.post(BORROW_URL, payload)

        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            Borrowing.objects.filter(
                user=self.user,
                book=book,
                expected_return_date=expected_return_date,
            ).exists()
        )

    def test_create_forbidden_when_user_has_pending_payments(self):
        Payment.objects.create(
            borrowing=sample_borrowing(user=self.user),
            status="PENDING",
            type="PAYMENT",
            money_to_pay=Decimal("20.00"),
        )

        expected_return_date = datetime.date.today() + datetime.timedelta(
            days=2
        )
        book = sample_book()
        payload = {
            "expected_return_date": expected_return_date,
            "book": book.id,
        }
        res = self.client.post(BORROW_URL, payload)

        self.assertEqual(res.status_code, 403)
        self.assertFalse(
            Borrowing.objects.filter(
                user=self.user,
                book=book,
                expected_return_date=expected_return_date,
            ).exists()
        )

    def test_return_book_action_forbidden(self):
        url = get_detail_url(self.borrowing.id) + "return/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.borrowing.actual_return_date, None)