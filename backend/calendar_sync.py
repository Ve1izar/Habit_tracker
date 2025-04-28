import datetime
import os
import pickle
from typing import List, Optional

import streamlit as st

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Права доступу — дозволяє читати та створювати події
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Файл авторизації, який зберігає токени
TOKEN_PATH = "token.pickle"

# Ім'я календаря, куди будемо додавати події
DEFAULT_CALENDAR_ID = "primary"

# ====================
# Авторизація
# ====================
# def authorize_google_calendar():
#     creds = None
#
#     # Якщо токен вже є — завантажити його
#     if os.path.exists(TOKEN_PATH):
#         with open(TOKEN_PATH, "rb") as token:
#             creds = pickle.load(token)
#
#     # Якщо немає або токен протермінований — запустити авторизацію
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)
#
#         # Зберегти токен
#         with open(TOKEN_PATH, "wb") as token:
#             pickle.dump(creds, token)
#
#     service = build("calendar", "v3", credentials=creds)
#     return service

def authorize_google_calendar():
    creds = None

    # Спробувати завантажити токен
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
        except (EOFError, pickle.UnpicklingError):
            # Якщо токен битий або порожній
            st.warning("⚠️ Зламаний токен! Потрібна нова авторизація.")
            creds = None

    # Якщо токена немає або він недійсний
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None  # Якщо не вдалось оновити токен
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Зберегти новий токен
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    return service

# ====================
# Додавання події
# ====================
def add_event_to_calendar(
    summary: str,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    description: str = "",
    recurrence: Optional[List[str]] = None  # <-- Додаємо це!
):
    service = authorize_google_calendar()

    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
    }

    if recurrence:  # Якщо recurrence передано — додаємо його до event
        event["recurrence"] = recurrence

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Подія створена: {created_event.get('htmlLink')}")
    return created_event
    return event

# ====================
# Отримання подій
# ====================
def get_events_from_calendar(start_time: datetime.datetime, end_time: datetime.datetime) -> List[dict]:
    service = authorize_google_calendar()

    events_result = (
        service.events()
        .list(
            calendarId=DEFAULT_CALENDAR_ID,
            timeMin=start_time.isoformat() + "Z",
            timeMax=end_time.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return events
