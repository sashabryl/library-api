from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


from book.views import BookViewSet
from book.models import Book


BOOK_URL = reverse("book:book-list")


def sample_book(**params):
    defaults = {
        "title": "Blue Seas",
        "author": "Sasha Brul",
        "inventory": 10,
        "cover": "HARD",
        "daily_fee": Decimal("10.00")
    }
    defaults.update(**params)
    return Book.objects.create(**defaults)


def get_detail_url(pk: int):
    return reverse("book:book-detail", args=[pk])


class UnauthenticatedBookAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.book = sample_book()

    def test_list_allowed(self):
        res = self.client.get(BOOK_URL)
        self.assertEquals(res.status_code, 200)

    def test_retrieve_forbidden(self):
        res = self.client.get(get_detail_url(self.book.id))
        self.assertEquals(res.status_code, 401)

    def test_update_partial_update_forbidden(self):
        payload = {
            "title": "Black Rivers",
            "author": "Felix Krull",
            "inventory": 5,
            "cover": "SOFT",
            "daily_fee": Decimal("20.00")
        }
        res = self.client.put(get_detail_url(self.book.id), payload)
        self.assertEquals(res.status_code, 401)

        payload = {
            "title": "Green Fields"
        }
        res = self.client.patch(get_detail_url(self.book.id), payload)
        self.assertEquals(res.status_code, 401)

        self.assertEquals(self.book.title, "Blue Seas")

    def test_create_forbidden(self):
        payload = {
            "title": "Black Rivers",
            "author": "Felix Krull",
            "inventory": 5,
            "cover": "SOFT",
            "daily_fee": Decimal("20.00")
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEquals(res.status_code, 401)
        self.assertFalse(
            Book.objects.filter(title=payload.get("title")).exists()
        )

    def test_delete_forbidden(self):
        res = self.client.delete(get_detail_url(self.book.id))
        self.assertEquals(res.status_code, 401)
        self.assertTrue(Book.objects.filter(title="Blue Seas").exists())


class AuthenticatedBookAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.book = sample_book()
        cls.user = get_user_model().objects.create_user(
            email="testuser@gmail.com", password="fjewia321!uf"
        )

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def test_list_allowed(self):
        res = self.client.get(BOOK_URL)
        self.assertEquals(res.status_code, 200)

    def test_retrieve_forbidden(self):
        res = self.client.get(get_detail_url(self.book.id))
        self.assertEquals(res.status_code, 403)

    def test_update_partial_update_forbidden(self):
        payload = {
            "title": "Black Rivers",
            "author": "Felix Krull",
            "inventory": 5,
            "cover": "SOFT",
            "daily_fee": Decimal("20.00")
        }
        res = self.client.put(get_detail_url(self.book.id), payload)
        self.assertEquals(res.status_code, 403)

        payload = {
            "title": "Green Fields"
        }
        res = self.client.patch(get_detail_url(self.book.id), payload)
        self.assertEquals(res.status_code, 403)

        self.assertEquals(self.book.title, "Blue Seas")

    def test_create_forbidden(self):
        payload = {
            "title": "Black Rivers",
            "author": "Felix Krull",
            "inventory": 5,
            "cover": "SOFT",
            "daily_fee": Decimal("20.00")
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEquals(res.status_code, 403)
        self.assertFalse(
            Book.objects.filter(title=payload.get("title")).exists()
        )

    def test_delete_forbidden(self):
        res = self.client.delete(get_detail_url(self.book.id))
        self.assertEquals(res.status_code, 403)
        self.assertTrue(Book.objects.filter(title="Blue Seas").exists())
