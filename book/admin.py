from django.contrib import admin

from book.models import Book, Borrowing, Payment


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "title",
        "cover",
        "inventory",
        "daily_fee"
    )
    list_filter = ("cover", "author")
    search_fields = ("title",)


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = (
        "borrow_date",
        "expected_return_date",
        "user",
        "book",
        "actual_return_date"
    )
    search_fields = ("user",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "status",
        "type",
        "borrowing",
        "user",
        "session_url",
        "session_id",
        "money_to_pay"
    )
    list_filter = ("status", "type")
    search_fields = ("user", "session_id")

