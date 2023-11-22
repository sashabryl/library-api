from django.contrib.auth import get_user_model
from django.core import exceptions
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password



class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=255, write_only=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        max_length=255, write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "confirm_password"
        )


