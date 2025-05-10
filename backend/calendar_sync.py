import datetime
from datetime import timedelta
from googleapiclient.discovery import build
from backend.google_auth import get_calendar_service_for_user
from backend.database import update_entry
from utils.helpers import format_recurrence, format_datetime_for_gcal, get_next_occurrence

def add_event_to_calendar(user_id: str, summary: str, start: datetime, end: datetime,
                          description: str = "", recurrence: list = None,
                          frequency: str = None, day_of_week: int = None, monthly_week: int = None) -> str:
    service = get_calendar_service_for_user(user_id)

    # Обчислити правильну дату початку для повторюваних звичок
    if recurrence and frequency:
        first_date = get_next_occurrence(frequency, day_of_week, monthly_week)
        start = start.replace(year=first_date.year, month=first_date.month, day=first_date.day)
        end = start + timedelta(hours=1)

    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": format_datetime_for_gcal(start),
            "timeZone": "Europe/Kyiv"
        },
        "end": {
            "dateTime": format_datetime_for_gcal(end),
            "timeZone": "Europe/Kyiv"
        },
    }

    if recurrence:
        event["recurrence"] = recurrence

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event["id"]



# -------------------------------
# Оновити подію
# -------------------------------
def update_event_in_calendar(user_id: str, event_id: str, entry: dict):
    service = get_calendar_service_for_user(user_id)

    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    event["summary"] = entry.get("name", event["summary"])
    event["description"] = entry.get("description", event.get("description", ""))
    event["start"] = {
        "dateTime": format_datetime_for_gcal(entry["start_time"]),
        "timeZone": "Europe/Kyiv"
    }
    event["end"] = {
        "dateTime": format_datetime_for_gcal(entry["end_time"]),
        "timeZone": "Europe/Kyiv"
    }

    if entry.get("frequency") and entry.get("day_of_week") is not None:
        from utils.helpers import get_byday_rrule_code
        byday = get_byday_rrule_code(entry["day_of_week"], entry.get("monthly_week", 1))
        freq = entry["frequency"]
        if freq == "daily":
            event["recurrence"] = ["RRULE:FREQ=DAILY"]
        elif freq == "weekly":
            event["recurrence"] = [f"RRULE:FREQ=WEEKLY;BYDAY={byday[-2:]}"]
        elif freq == "monthly":
            event["recurrence"] = [f"RRULE:FREQ=MONTHLY;BYDAY={byday}"]

    service.events().update(calendarId='primary', eventId=event_id, body=event).execute()



# -------------------------------
# Видалити подію з primary календаря
# -------------------------------
def delete_event_by_id(user_id: str, event_id: str):
    service = get_calendar_service_for_user(user_id)
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        print(f"⚠️ Не вдалося видалити подію {event_id}: {e}")



# -------------------------------
# Масова синхронізація (для наявних записів)
# -------------------------------
import datetime
from backend.calendar_sync import add_event_to_calendar
from backend.database import update_entry, fetch_table
from utils.helpers import format_recurrence, get_next_occurrence

def sync_all_to_calendar(user_id: str):
    habits = fetch_table("habits_active", user_id)
    tasks = fetch_table("tasks_active", user_id)

    # --- Синхронізація звичок ---
    for h in habits:
        event_id = h.get("event_id")
        if event_id and str(event_id).strip():
            print(f"✅ Пропущено (вже синхронізовано): {h['name']}")
            continue

        try:
            time_str = h.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            start = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            end = start + datetime.timedelta(hours=1)

            recurrence = format_recurrence(h)

            # Якщо це monthly — визначити найближчу дату для старту
            if h["frequency"] == "monthly":
                day = h.get("day_of_week", 0)
                week = h.get("monthly_week", 1)
                try:
                    next_date = get_next_occurrence(day, week)
                    start = datetime.datetime.combine(next_date, datetime.time(hour, minute))
                    end = start + datetime.timedelta(hours=1)
                except Exception as e:
                    print(f"⚠️ Помилка у get_next_occurrence для звички {h['name']}: {e}")
                    continue

            event_id = add_event_to_calendar(
                user_id,
                h["name"],
                start,
                end,
                h.get("description", ""),
                recurrence
            )

            update_entry("habits_active", h["id"], {"event_id": event_id}, user_id)
            print(f"✅ Синхронізовано звичку: {h['name']}")

        except Exception as e:
            print(f"❌ Помилка синхронізації звички {h['name']}: {e}")

    # --- Синхронізація завдань ---
    for t in tasks:
        event_id = t.get("event_id")
        if event_id and str(event_id).strip():
            print(f"✅ Пропущено (вже синхронізовано): {t['name']}")
            continue
        if not t.get("date") or not t.get("time"):
            print(f"⚠️ Пропущено завдання без дати або часу: {t['name']}")
            continue

        try:
            start = datetime.datetime.fromisoformat(f"{t['date']}T{t['time']}")
            end = start + datetime.timedelta(hours=1)
            event_id = add_event_to_calendar(
                user_id,
                t["name"],
                start,
                end,
                t.get("description", "")
            )
            update_entry("tasks_active", t["id"], {"event_id": event_id}, user_id)
            print(f"✅ Синхронізовано завдання: {t['name']}")
        except Exception as e:
            print(f"❌ Помилка синхронізації завдання {t['name']}: {e}")



# -------------------------------
# Очистити всі події з primary календаря (на 30 днів уперед)
# -------------------------------
def delete_spam_events(user_id: str):
    service = get_calendar_service_for_user(user_id)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + "Z"

    events = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=future,
        singleEvents=True,
        orderBy='startTime'
    ).execute().get("items", [])

    for event in events:
        try:
            service.events().delete(calendarId="primary", eventId=event["id"]).execute()
        except Exception as e:
            print(f"Не вдалося видалити {event['id']}: {e}")
