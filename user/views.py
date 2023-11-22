from django.contrib.auth import get_user_model
from rest_framework import generics

from user.serializers import UserCreateSerializer


class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = get_user_model().objects.all
    authentication_classes = []
    permission_classes = []
