from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import UserRegisterView, ManageMeView

app_name = "user"

urlpatterns = [
    path("", UserRegisterView.as_view(), name="register"),
    path("me/", ManageMeView.as_view(), name="me"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
