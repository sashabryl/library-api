import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


REGISTER_URL = reverse("user:register")
ME_URL = reverse("user:me")


def sample_user(**params):
    defaults = {
        "email": f"user{uuid.uuid4()}@gmail.com",
        "password": f"{uuid.uuid4()}feawfr",
    }
    defaults.update(**params)
    return get_user_model().objects.create_user(**defaults)


class UserRegisterTests(APITestCase):
    def test_register_works(self):
        payload = {
            "email": "testuser@gmail.com",
            "password": "asdfasdf!qwe321",
            "confirm_password": "asdfasdf!qwe321",
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 201)
        self.assertTrue(
            get_user_model()
            .objects.filter(email="testuser@gmail.com")
            .exists()
        )
        user = get_user_model().objects.get(email="testuser@gmail.com")
        self.assertTrue(user.check_password("asdfasdf!qwe321"))

    def test_password_confirm_validation_works(self):
        payload = {
            "email": "testuser2@gmail.com",
            "password": "asdf!qwe321",
            "confirm_password": "asdf!qwe123",
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 400)
        self.assertFalse(
            get_user_model()
            .objects.filter(email="testuser2@gmail.com")
            .exists()
        )

    def test_django_password_validation_works(self):
        payload = {
            "email": "testuser3@gmail.com",
            "password": "abc",
            "confirm_password": "abc",
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 400)
        self.assertFalse(
            get_user_model()
            .objects.filter(email="testuser3@gmail.com")
            .exists()
        )

        payload = {
            "email": "testuser4@gmail.com",
            "password": "123456789",
            "confirm_password": "123456789",
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 400)
        self.assertFalse(
            get_user_model()
            .objects.filter(email="testuser4@gmail.com")
            .exists()
        )

    def test_unique_constraint_on_email(self):
        sample_user(email="simple@gmail.com")
        payload = {
            "email": "simple@gmail.com",
            "password": "asdf!qwe321",
            "confirm_password": "asdf!qwe321",
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 400)


class UserManageMeTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = sample_user()

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)

    def test_detail_page_returns_correct_user(self):
        res = self.client.get(ME_URL)

        self.assertEquals(res.status_code, 200)
        self.assertEquals(res.data.get("id"), self.user.id)
        self.assertEquals(res.data.get("email"), self.user.email)

    def test_update_method_works(self):
        payload = {
            "email": "newuser@gmail.com",
            "first_name": "Sasha",
            "last_name": "Bryl",
        }
        res = self.client.put(ME_URL, payload)

        self.assertEquals(res.status_code, 200)
        self.assertEquals(self.user.email, payload.get("email"))
        self.assertEquals(self.user.first_name, payload.get("first_name"))
        self.assertEquals(self.user.last_name, payload.get("last_name"))

    def test_partial_update_works(self):
        payload = {"first_name": "Isaac"}
        res = self.client.patch(ME_URL, payload)

        self.assertEquals(res.status_code, 200)
        self.assertEquals(self.user.first_name, payload.get("first_name"))

    def test_delete_method_forbidden(self):
        res = self.client.delete(ME_URL)

        self.assertEquals(res.status_code, 405)
        self.assertTrue(
            get_user_model().objects.filter(email=self.user.email).exists()
        )


class UnauthenticatedUserManageMeTests(APITestCase):
    def test_retrieve_forbidden(self):
        res = self.client.get(ME_URL)

        self.assertEquals(res.status_code, 401)

    def test_update_partial_update_forbidden(self):
        payload = {
            "email": "user2@gmail.com",
            "first_name": "Anna",
            "last_name": "Surfer",
        }
        res = self.client.put(ME_URL, payload)
        self.assertEquals(res.status_code, 401)

        payload = {"last_name": "Bryl"}
        res = self.client.patch(ME_URL, payload)
        self.assertEquals(res.status_code, 401)

    def test_delete_forbidden(self):
        res = self.client.delete(ME_URL)
        self.assertEquals(res.status_code, 401)
