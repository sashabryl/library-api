from django.contrib.auth import get_user_model
from rest_framework import generics

from user.serializers import UserCreateSerializer, UserDetailSerializer


class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = get_user_model().objects.all
    authentication_classes = []
    permission_classes = []


class ManageMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    queryset = get_user_model().objects.all()
