import os
import requests
from celery import shared_task
from .models import Habit


@shared_task
def send_telegram_reminder(habit_id):
    habit = Habit.objects.get(pk=habit_id)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    message = (
        f"⏰ Напоминание о привычке:\n"
        f"{habit.action}\n"
        f"Время: {habit.time_of_day}\n"
        f"Место: {habit.location or 'не указано'}\n"
        f"Периодичность: раз в {habit.periodicity_days} дн."
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, json=payload)
