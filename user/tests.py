import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


REGISTER_URL = reverse("user:register")


def sample_user(**params):
    defaults = {
        "email": f"user{uuid.uuid4()}@gmail.com",
        "password": f"{uuid.uuid4()}feawfr"
    }
    defaults.update(**params)
    return get_user_model().objects.create_user(**defaults)


class UserRegisterTests(APITestCase):

    def test_register_works(self):
        payload = {
            "email": "testuser@gmail.com",
            "password": "asdfasdf!qwe321",
            "confirm_password": "asdfasdf!qwe321"
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(
            email="testuser@gmail.com"
        ).exists())
        user = get_user_model().objects.get(email="testuser@gmail.com")
        self.assertTrue(user.check_password("asdfasdf!qwe321"))

    def test_password_confirm_validation_works(self):
        payload = {
            "email": "testuser2@gmail.com",
            "password": "asdf!qwe321",
            "password_confirm": "asdf!qwe123"
        }
        res = self.client.post(REGISTER_URL, payload)

        self.assertTrue(res.status_code, 400)
        self.assertFalse(
            get_user_model().objects.filter(
                email="testuser2@gmail.com"
            ).exists()
        )



