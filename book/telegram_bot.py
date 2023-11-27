from django.conf import settings
from telegram import Bot


async def send_creation_notification(text: str):
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=text)
