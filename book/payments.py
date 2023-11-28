import stripe
from django.conf import settings
from django.urls import reverse_lazy
from rest_framework.exceptions import ValidationError

from book.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


FINE_MULTIPLIER = 2


def create_payment(request, borrowing, type):
    if type == "PAYMENT":
        borrowing_days = (
            borrowing.expected_return_date - borrowing.borrow_date
        ).days
        money_to_pay = borrowing_days * borrowing.book.daily_fee

    elif type == "FINE":
        overdue_days = (
            borrowing.actual_return_date - borrowing.expected_return_date
        ).days
        money_to_pay = (
            overdue_days * borrowing.book.daily_fee * FINE_MULTIPLIER
        )

    else:
        raise ValidationError(
            f"'type' argument must be either PAYMENT or FINE, not {type}"
        )

    payment = Payment.objects.create(
        borrowing=borrowing,
        status="PENDING",
        type=type,
        money_to_pay=money_to_pay,
    )

    price = int(money_to_pay * 100)
    success_url = request.build_absolute_uri(
        reverse_lazy("book:payment-success", kwargs={"pk": payment.id})
    )
    cancel_url = request.build_absolute_uri(
        reverse_lazy("book:payment-cancel", kwargs={"pk": payment.id})
    )
    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": borrowing.book,
                    },
                    "unit_amount": price,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_creation="always",
    )

    payment.session_id = session.id
    payment.save()
    payment.session_url = session.url
    payment.save()

    return session.url


def recover_payment(request, payment):
    price = int(payment.money_to_pay * 100)
    success_url = request.build_absolute_uri(
        reverse_lazy("book:payment-success", kwargs={"pk": payment.id})
    )
    cancel_url = request.build_absolute_uri(
        reverse_lazy("book:payment-cancel", kwargs={"pk": payment.id})
    )
    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": payment.borrowing.book,
                    },
                    "unit_amount": price,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_creation="always",
    )

    payment.session_id = session.id
    payment.save()
    payment.session_url = session.url
    payment.save()
