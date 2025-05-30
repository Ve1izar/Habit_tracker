import datetime
from datetime import timedelta
import time

from loguru import logger

from backend.google_auth import get_calendar_service_for_user
from utils.helpers import format_datetime_for_gcal, get_byday_rrule_code
from backend.database import fetch_table, update_entry
from utils.helpers import format_recurrence, get_next_occurrence


def add_event_to_calendar(
        user_id: str,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = "",
        recurrence: list | None = None,
        frequency: str | None = None,
        day_of_week: int | None = None,
        monthly_week: int | None = None,
) -> str:
    service = get_calendar_service_for_user(user_id)

    # Обчислити правильну дату початку для повторюваних звичок
    if recurrence is not None and frequency is not None:
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


def update_event_in_calendar(user_id: str, event_id: str, entry: dict):
    """
    Оновлення події в Google Calendar.
    :param user_id:
    :param event_id:
    :param entry:
    :return:
    """
    service = get_calendar_service_for_user(user_id)

    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    # Оновлення базової інформації
    event["summary"] = entry.get("name", event["summary"])
    event["description"] = entry.get("description", event.get("description", ""))

    start = format_datetime_for_gcal(entry["start_time"])
    end = format_datetime_for_gcal(entry["end_time"])

    event["start"]["dateTime"] = start
    event["end"]["dateTime"] = end

    # Оновлення повторення, якщо є частота та день тижня
    frequency = entry.get("frequency")
    day_of_week = entry.get("day_of_week")

    if frequency and day_of_week is not None:
        byday = get_byday_rrule_code(day_of_week, entry.get("monthly_week", 1))

        if frequency == "daily":
            event["recurrence"] = ["RRULE:FREQ=DAILY"]
        elif frequency == "weekly":
            event["recurrence"] = [f"RRULE:FREQ=WEEKLY;BYDAY={byday[-2:]}"]
        elif frequency == "monthly":
            event["recurrence"] = [f"RRULE:FREQ=MONTHLY;BYDAY={byday}"]

    service.events().update(calendarId='primary', eventId=event_id, body=event).execute()


def delete_event_by_id(user_id: str, event_id: str):
    """
    Видалити подію з Google Calendar за ID.
    :param user_id:
    :param event_id:
    :return:
    """
    service = get_calendar_service_for_user(user_id)
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        logger.warning(f"⚠️ Не вдалося видалити подію {event_id}: {e}")


def sync_all_to_calendar(user_id: str):
    """
    Синхронізація всіх звичок і завдань з Google Calendar.
    :param user_id:
    :return:
    """
    habits = fetch_table("habits_active", user_id)
    tasks = fetch_table("tasks_active", user_id)

    # --- Синхронізація звичок ---
    for h in habits:
        event_id = h.get("event_id")
        if event_id and str(event_id).strip():
            logger.info(f"✅ Пропущено (вже синхронізовано): {h['name']}")
            continue

        try:
            # --- Час виконання звички ---
            time_str = h.get("time", "09:00")
            time_parts = list(map(int, time_str.split(":")[:2]))  # підтримує "HH:MM" і "HH:MM:SS"
            hour, minute = time_parts[0], time_parts[1]

            frequency = h.get("frequency", "daily")
            recurrence = format_recurrence(h)

            # --- Обчислення дати старту ---
            if frequency == "monthly":
                day = h.get("day_of_week", 0)
                week = h.get("monthly_week", 1)
                next_date = get_next_occurrence(day, week)

            elif frequency == "weekly":
                today = datetime.date.today()
                today_weekday = today.weekday()
                target_day = h.get("day_of_week", 0)
                delta_days = (target_day - today_weekday) % 7
                if delta_days == 0:
                    delta_days = 7  # не сьогодні, а наступний тиждень
                next_date = today + datetime.timedelta(days=delta_days)

            else:
                # daily — просто сьогодні
                next_date = datetime.date.today()

            # --- Дата/час початку події ---
            start = datetime.datetime.combine(next_date, datetime.time(hour, minute))
            end = start + datetime.timedelta(hours=1)

            # --- Створення події ---
            new_event_id = add_event_to_calendar(
                user_id=user_id,
                summary=h["name"],
                start=start,
                end=end,
                description=h.get("description", ""),
                recurrence=recurrence,
                frequency=frequency,
                day_of_week=h.get("day_of_week"),
                monthly_week=h.get("monthly_week")
            )

            update_entry("habits_active", h["id"], {"event_id": new_event_id}, user_id)
            logger.info(f"✅ Синхронізовано звичку: {h['name']}")

        except Exception as e:
            logger.exception(f"❌ Помилка синхронізації звички {h.get('name', '[без назви]')}: {e}")

    # --- Синхронізація завдань ---
    for t in tasks:
        try:
            event_id = t.get("event_id")
            if event_id and str(event_id).strip():
                logger.info(f"✅ Пропущено (вже синхронізовано): {t['name']}")
                continue

            if not t.get("date") or not t.get("time"):
                continue

            start = datetime.datetime.fromisoformat(f"{t['date']}T{t['time']}")
            end = start + datetime.timedelta(hours=1)

            event_id = add_event_to_calendar(user_id, t["name"], start, end, t.get("description", ""))
            update_entry("tasks_active", t["id"], {"event_id": event_id}, user_id)
            logger.info(f"✅ Синхронізовано завдання: {t['name']}")

        except Exception as e:
            logger.error(f"❌ Помилка синхронізації завдання {t['name']}: {e}")


def delete_spam_events(user_id: str):
    """
    Видалити всі події з Google Calendar (на 30 днів уперед).
    :param user_id:
    :return:
    """
    service = get_calendar_service_for_user(user_id)
    events = []
    page_token = None

    while True:
        response = service.events().list(
            calendarId='primary',
            pageToken=page_token
        ).execute()

        events.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    deleted_count = 0

    for event in events:
        try:
            service.events().delete(calendarId='primary', eventId=event["id"]).execute()
            deleted_count += 1
            time.sleep(0.1)  # Затримка 100 мс
        except Exception as e:
            logger.warning(f"⚠️ Не вдалося видалити подію {event['id']}: {e}")

    return deleted_count
