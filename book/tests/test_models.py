import datetime
import uuid
from decimal import Decimal
from unittest import TestCase

from django.contrib.auth import get_user_model

from book.models import Payment, Borrowing, Book


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


class BookTests(TestCase):
    def test_is_available_property(self):
        book = sample_book(inventory=1)
        self.assertTrue(book.is_available)

        book = sample_book(inventory=0)
        self.assertFalse(book.is_available)


class BorrowingTests(TestCase):
    def test_is_active_property(self):
        borrow = sample_borrowing()
        self.assertTrue(borrow.is_active)

        borrow = sample_borrowing(actual_return_date=datetime.date.today())
        self.assertFalse(borrow.is_active)
