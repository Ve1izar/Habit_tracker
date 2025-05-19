import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Шлях до папки з токенами
TOKENS_DIR = Path("tokens")
TOKENS_DIR.mkdir(exist_ok=True)

# Шлях до credentials.json
CREDENTIALS_PATH = "credentials.json"

# Скоупи для доступу до Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_token_path(user_id: str) -> Path:
    """
    Отримати шлях до токена користувача.
    :param user_id:
    :return:
    """
    return TOKENS_DIR / f"user_{user_id}.json"


def get_credentials(user_id: str) -> Credentials:
    """
    Отримати об'єкт Credentials для користувача.
    :param user_id:
    :return:
    """
    token_path = get_token_path(user_id)

    if not token_path.exists():
        return None
        # raise Exception("❌ Access token не знайдено. Користувач не авторизований.")

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def save_credentials(user_id: str, creds: Credentials):
    """
    Зберегти об'єкт Credentials у файл.
    :param user_id:
    :param creds:
    :return:
    """
    token_path = get_token_path(user_id)
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())


def start_auth_flow():
    """
    Запустити авторизаційний потік.
    :return:
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH, SCOPES, redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return flow, auth_url


def finish_auth_flow(flow, code: str, user_id: str):
    """
    Завершити авторизаційний потік.
    :param flow:
    :param code:
    :param user_id:
    :return:
    """
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_credentials(user_id, creds)
    return creds


def get_calendar_service_for_user(user_id: str):
    """
    Отримати сервіс Google Calendar для користувача.
    :param user_id:
    :return:
    """
    creds = get_credentials(user_id)
    if not creds:
        return None

    return build("calendar", "v3", credentials=creds)


def revoke_credentials(user_id: str):
    """Видаляє токен користувача (вихід з Google)."""
    token_path = get_token_path(user_id)
    if token_path.exists():
        token_path.unlink()