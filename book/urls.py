from django.urls import path, include
from rest_framework.routers import DefaultRouter

from book.views import BookViewSet


app_name = "book"

router = DefaultRouter()
router.register("books", BookViewSet)

urlpatterns = [
    path("", include(router.urls))
]
