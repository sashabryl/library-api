from django.urls import path, include
from rest_framework.routers import DefaultRouter

from book.views import BookViewSet, BorrowViewSet, PaymentViewSet

app_name = "book"

router = DefaultRouter()
router.register("books", BookViewSet)
router.register("borrowings", BorrowViewSet, basename="borrow")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [path("", include(router.urls))]
