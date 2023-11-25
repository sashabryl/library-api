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
            "confirm_password",
        )

    def validate(self, data):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError("Passwords don't match")
        del data["confirm_password"]
        return super().validate(data)

    @staticmethod
    def validate_password(value):
        try:
            validate_password(value)
        except exceptions.ValidationError as exc:
            raise ValidationError(str(exc))
        return value

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
        )


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name")
