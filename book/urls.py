from django.urls import path, include
from rest_framework.routers import DefaultRouter

from book.views import BookViewSet, BorrowViewSet

app_name = "book"

router = DefaultRouter()
router.register("books", BookViewSet)
router.register("borrowings", BorrowViewSet, basename="borrow")

urlpatterns = [
    path("", include(router.urls))
]
