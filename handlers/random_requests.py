import asyncio
import gzip
import logging

import brotli
import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from utils.settings import load_settings
from utils.generator import generate_name_from_db, generate_phone_from_db, generate_quantity
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# Глобальный флаг и список задач для управления выполнением запросов
stop_random_requests_flag = False
tasks = []  # Список активных задач

# Configure logging to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)

def generate_schedule(request_count):
    """Генерирует расписание запросов с заданными пропорциями, начиная с текущего времени."""
    now = datetime.now()
    night_count = int(request_count * 0.3)  # 30% запросов ночью
    day_count = request_count - night_count  # Остальные днем

    night_intervals = [
        now + timedelta(seconds=random.randint(0, 7 * 3600))  # Интервал 00:00–07:00
        for _ in range(night_count)
    ]
    day_intervals = [
        now + timedelta(seconds=random.randint(7 * 3600, 23 * 3600 + 59 * 60))  # Интервал 07:00–23:59
        for _ in range(day_count)
    ]

    # Объединяем и сортируем временные интервалы
    full_schedule = sorted(night_intervals + day_intervals)
    return [time.strftime('%H:%M:%S') for time in full_schedule]


async def process_url(url, url_number, requests_count, update, context):
    """Asynchronously executes requests for a given URL using the new request mechanism."""
    global stop_random_requests_flag

    # Define headers within the function
    headers = {
        "Cookie": "_fbp=fb.1.1734529035075.618096322771607895",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not?A_Brand";v="99", "Chromium";v="130"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://new.busk.website",
        "Content-Type": "application/x-www-form-urlencoded",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://new.busk.website/hot/",
        "Accept-Encoding": "gzip, deflate, br"
    }

    for i in range(requests_count):
        if not stop_random_requests_flag:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Stopping requests for URL #{url_number} ({url}). Remaining requests: {requests_count - i} will not be executed."
            )
            logging.info(f"Stopped requests for URL #{url_number} ({url}). Remaining requests: {requests_count - i}.")
            return

        try:
            # Prepare the request data
            name = generate_name_from_db()
            phone = generate_phone_from_db()
            data = {
                "name": name,
                "phone": phone,
                "utm_source": "",
                "utm_medium": "",
                "utm_term": "",
                "utm_content": "",
                "utm_campaign": "",
                "utm_podmeni_zag": "",
                "comment": "nospam"
            }

            # Send the POST request
            logging.info(f"Sending POST request for URL #{url_number} ({url}).")
            response = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            logging.info(f"POST request for URL #{url_number} successful. Status Code: {response.status_code}")

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Request #{i + 1} for URL #{url_number} ({url}) successful."
            )

        except requests.exceptions.HTTPError as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error during request execution for URL #{url_number} ({url}): {e}"
            )
            logging.error(f"HTTP error for URL #{url_number}: {e}")
            continue

        except requests.exceptions.RequestException as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Connection error for URL #{url_number} ({url}): {e}"
            )
            logging.error(f"Request failed for URL #{url_number}: {e}")
            continue

        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Unexpected error for URL #{url_number} ({url}): {e}"
            )
            logging.error(f"Unexpected error for URL #{url_number}: {e}")
            continue

        # Delay before the next request
        delay = random.randint(60, 3600)
        next_request_time = datetime.now() + timedelta(seconds=delay)

        logging.info(f"Next request for URL #{url_number} scheduled at {next_request_time.strftime('%H:%M:%S')}.")
        await asyncio.sleep(delay)

async def run_random_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает выполнение запросов для каждой ссылки в отдельной задаче."""
    global stop_random_requests_flag, tasks
    stop_random_requests_flag = True  # Устанавливаем флаг перед запуском
    tasks = []  # Сброс задач

    settings = load_settings()
    urls = settings["urls"]
    min_requests = settings["min_requests"]
    max_requests = settings["max_requests"]

    if not urls:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Список ссылок пуст. Добавьте ссылки через /add_url."
        )
        return

    daily_requests = {url: random.randint(min_requests, max_requests) for url in urls}
    schedules = {url: generate_schedule(count) for url, count in daily_requests.items()}

    for i, (url, schedule) in enumerate(schedules.items()):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Schedule of requests for URL #{i + 1} ({url}):\n" + "\n".join(schedule)
        )

    tasks = [
        asyncio.create_task(process_url(url, i + 1, count, update, context))
        for i, (url, count) in enumerate(daily_requests.items())
    ]

    await asyncio.gather(*tasks, return_exceptions=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="All requests for today completed."
    )


async def stop_random_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Останавливает выполнение запросов."""
    global stop_random_requests_flag, tasks
    stop_random_requests_flag = False  # Устанавливаем флаг остановки

    # Отменяем все активные задачи
    for task in tasks:
        if not task.done():
            task.cancel()

    # Ждем завершения всех задач
    await asyncio.gather(*tasks, return_exceptions=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Random requests have been stopped."
    )


def get_random_request_handlers():
    """Возвращает список обработчиков для управления запросами."""
    return [
        CommandHandler("random_requests", run_random_requests),
        CommandHandler("stop_random_requests", stop_random_requests),
    ]