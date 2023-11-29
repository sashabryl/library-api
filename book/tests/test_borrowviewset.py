import datetime
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.urls import reverse

from book.models import Book, Borrowing, Payment
from book.serializers import BorrowListSerializer


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
        book_inventory_before_borrowing = book.inventory
        payload = {
            "expected_return_date": expected_return_date,
            "book": book.id,
        }
        res = self.client.post(BORROW_URL, payload)
        book.refresh_from_db()

        self.assertEqual(res.status_code, 302)
        self.assertEqual(book_inventory_before_borrowing, book.inventory + 1)
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


class AdminBorrowApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            email="admin@admin.com", password="fejawi!3h2i1u"
        )

    def setUp(self) -> None:
        self.client.force_authenticate(self.superuser)

    def test_list_filtering_works(self):
        bob = sample_user()
        borrow_bob = sample_borrowing(user=bob)
        sample_borrowing(user=bob, actual_return_date=datetime.date.today())

        alice = sample_user()
        borrow_alice_one = sample_borrowing(user=alice)
        borrow_alice_two = sample_borrowing(
            user=alice, actual_return_date=datetime.date.today()
        )

        active_borrows_serializer = BorrowListSerializer(
            [borrow_bob, borrow_alice_one], many=True
        )
        alice_borrows_serializer = BorrowListSerializer(
            [borrow_alice_one, borrow_alice_two], many=True
        )

        res = self.client.get(BORROW_URL, data={"is_active": "True"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, active_borrows_serializer.data)

        res = self.client.get(BORROW_URL, data={"user_id": alice.id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, alice_borrows_serializer.data)

    def test_retrieve_other_borrowings_allowed(self):
        borrow = sample_borrowing()
        res = self.client.get(get_detail_url(borrow.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("user"), str(borrow.user))

    def test_delete_forbidden(self):
        borrow_id = sample_borrowing().id
        res = self.client.delete(get_detail_url(borrow_id))
        self.assertEqual(res.status_code, 405)
        self.assertTrue(Borrowing.objects.filter(id=borrow_id).exists())

    def test_update_partial_update_forbidden(self):
        borrowing = sample_borrowing()
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
        res = self.client.put(get_detail_url(borrowing.id), payload)
        self.assertEqual(res.status_code, 405)

        payload = {"actual_return_date": datetime.date.today()}
        res = self.client.patch(get_detail_url(borrowing.id), payload)
        self.assertEqual(res.status_code, 405)

        self.assertEqual(borrowing.actual_return_date, None)

    def test_return_book_action_works(self):
        borrowing = sample_borrowing()
        book_inventory_after_borrowing = borrowing.book.inventory
        res = self.client.get(get_detail_url(borrowing.id) + "return/")
        borrowing.refresh_from_db()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(borrowing.actual_return_date, datetime.date.today())
        self.assertEqual(
            borrowing.book.inventory, book_inventory_after_borrowing + 1
        )

        res = self.client.get(get_detail_url(borrowing.id) + "return/")
        self.assertEqual(res.status_code, 400)

    def test_return_book_creates_fine_when_borrow_overdue(self):
        borrowing = sample_borrowing(
            borrow_date=(datetime.date.today() - datetime.timedelta(days=4)),
            expected_return_date=(
                datetime.date.today() - datetime.timedelta(days=2)
            ),
        )
        res = self.client.get(get_detail_url(borrowing.id) + "return/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            Payment.objects.filter(borrowing=borrowing, type="FINE").exists()
        )
