import datetime
import asyncio

import stripe
from celery import shared_task
from django.conf import settings

from book.models import Borrowing
from book.telegram_bot import send_notification


stripe.api_key = settings.STRIPE_SECRET_KEY

@shared_task
def check_for_overdue_borrowings():
    active_borrowings = Borrowing.objects.filter(
        actual_return_date__isnull=True
    )
    tomorrow_overdues = active_borrowings.filter(
        expected_return_date=(
            datetime.date.today() + datetime.timedelta(days=1)
        )
    )
    overdue_borrowings = active_borrowings.filter(
        expected_return_date__lte=(datetime.date.today())
    )

    if not overdue_borrowings and not tomorrow_overdues:
        return asyncio.run(
            send_notification(text="No borrowings overdue today!")
        )

    for tomorrow_borrow in tomorrow_overdues:
        print(
            f"{tomorrow_borrow.user} should return {tomorrow_borrow.book} tomorrow"
        )
        notification = (
            f"{tomorrow_borrow.user} !\n We are expecting you to return "
            f"'{tomorrow_borrow.book}' tomorrow, "
            f"on {tomorrow_borrow.expected_return_date} - "
            f"please pay attention in order to avoid a fine."
        )
        asyncio.run(send_notification(text=notification))

    for over_borrow in overdue_borrowings:
        print(
            f"{over_borrow.user} should return {over_borrow.book}"
            f" on {over_borrow.expected_return_date}"
        )
        notification = (
            f"{over_borrow.user} !\n You are supposed to return "
            f"'{over_borrow.book}' on {over_borrow.expected_return_date}, "
            f"but you still haven't. Please do not be silly and take "
            f"actions on this issue."
        )
        asyncio.run(send_notification(text=notification))


def get_expired_sessions():
    sessions = stripe.checkout.Session.list().data
    current_time = int(datetime.datetime.now().timestamp())
    return [
        session for session in sessions if
        session.expires_at < current_time and
        session.payment_status == "unpaid"
    ]

