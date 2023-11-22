from django.urls import path

from user.views import UserRegisterView, ManageMeView

app_name = "user"

urlpatterns = [
    path("users/", UserRegisterView.as_view(), name="register"),
    path("me/", ManageMeView.as_view(), name="me"),
]
