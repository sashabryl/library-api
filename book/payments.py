import stripe
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from book.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment(request, borrowing):
    borrowing_days = (
        borrowing.expected_return_date - borrowing.borrow_date
    ).days
    price = int(borrowing_days * borrowing.book.daily_fee * 100)

    payment = Payment.objects.create(
        borrowing=borrowing,
        status="PENDING",
        type="PAYMENT",
        money_to_pay=price,
    )
    success_url = request.build_absolute_uri(
        reverse_lazy(
            "book:payment-success",
            kwargs={"pk": payment.id}
        ) + "?session_id={CHECKOUT_SESSION_ID}",
    )
    cancel_url = request.build_absolute_uri(
        reverse_lazy(
            "book:payment-cancel",
            kwargs={"pk": payment.id}
        )
    )
    session = stripe.checkout.Session.create(
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": borrowing.book,
                },
                "unit_amount": price,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return HttpResponseRedirect(redirect_to=session.url)