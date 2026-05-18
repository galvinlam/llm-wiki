from __future__ import annotations

from typing import Any

import requests

from .config import Settings


def chat_allowed(settings: Settings, chat_id: str) -> bool:
    return not settings.allowed_chat_ids or chat_id in settings.allowed_chat_ids


def telegram_api(settings: Settings, method: str, *, http_method: str = "GET", **kwargs: Any) -> dict[str, Any]:
    if not settings.telegram_bot_token:
        raise RuntimeError("Telegram bot token is not configured")
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    if http_method == "POST":
        response = requests.post(url, timeout=60, data=kwargs)
    else:
        response = requests.get(url, timeout=60, params=kwargs)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
    return payload["result"]


def download_file(settings: Settings, file_id: str) -> tuple[bytes, str]:
    file_info = telegram_api(settings, "getFile", file_id=file_id)
    file_path = file_info.get("file_path")
    if not file_path:
        raise RuntimeError("Telegram file path missing")
    url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content, file_path


def send_message(settings: Settings, chat_id: str, text: str) -> None:
    telegram_api(settings, "sendMessage", http_method="POST", chat_id=chat_id, text=text)
