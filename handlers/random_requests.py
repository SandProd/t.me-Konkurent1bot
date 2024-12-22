import asyncio
import logging
import random
from datetime import datetime, timedelta

import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from utils.settings import load_settings
from utils.generator import generate_name_from_db, generate_phone_from_db
from colorama import Fore, Style

# Глобальный флаг и список задач
stop_random_requests_flag = False
tasks = []  # Список активных задач

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


async def process_url(url, url_number, requests_count, update, context):
    """Asynchronously executes requests for a given URL."""
    global stop_random_requests_flag

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
    }

    for i in range(requests_count):
        if not stop_random_requests_flag:
            logging.info(f"{Fore.RED}Stopped requests for URL #{url_number} ({url}).{Style.RESET_ALL}")
            return

        try:
            # Prepare the request data
            name = generate_name_from_db()
            phone = generate_phone_from_db()
            data = {
                "name": name,
                "phone": phone,
                "comment": "nospam"
            }

            logging.info(f"{Fore.CYAN}Sending POST request for URL #{url_number} ({url}).{Style.RESET_ALL}")
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()

            logging.info(f"{Fore.GREEN}POST request for URL #{url_number} successful. Status Code: {response.status_code}{Style.RESET_ALL}")

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Request #{i + 1} for URL #{url_number} ({url}) successful."
            )

        except requests.exceptions.RequestException as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error during request execution for URL #{url_number} ({url}): {e}"
            )
            logging.error(f"{Fore.RED}Request failed for URL #{url_number}: {e}{Style.RESET_ALL}")

        # Add delay between requests
        delay = random.randint(5, 15)
        next_request_time = datetime.now() + timedelta(seconds=delay)
        logging.info(f"Next request for URL #{url_number} scheduled at {next_request_time.strftime('%H:%M:%S')}.")
        await asyncio.sleep(delay)


async def run_random_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts running random requests."""
    global stop_random_requests_flag, tasks
    stop_random_requests_flag = True  # Allow requests to execute
    tasks = []

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

    # Create and start background tasks
    for i, url in enumerate(urls, start=1):
        request_count = random.randint(min_requests, max_requests)
        task = asyncio.create_task(process_url(url, i, request_count, update, context))
        tasks.append(task)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Random requests started in background.")
    logging.info("Random requests started in background.")


async def stop_random_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops all running requests."""
    global stop_random_requests_flag, tasks
    stop_random_requests_flag = False  # Signal to stop tasks

    for task in tasks:
        if not task.done():
            task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="All requests have been stopped.")
    logging.info("All requests have been stopped.")


def get_random_request_handlers():
    """Returns a list of handlers for random requests."""
    return [
        CommandHandler("random_requests", run_random_requests),
        CommandHandler("stop_random_requests", stop_random_requests),
    ]