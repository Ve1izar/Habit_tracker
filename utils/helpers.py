from datetime import datetime
import pytz
import calendar

# Повертає список днів тижня у форматі RFC для Google Calendar (наприклад, ["MO", "WE"])
def get_google_weekdays(days: list[int]) -> list[str]:
    rfc_days = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
    return [rfc_days[d % 7] for d in days]

# Перетворює дату у форматі ISO в datetime-об'єкт
def parse_iso_datetime(iso_str: str) -> datetime:
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

# Форматує datetime до формату, потрібного для Google Calendar
def format_datetime_for_gcal(dt: datetime) -> str:
    kyiv_tz = pytz.timezone("Europe/Kyiv")
    localized = kyiv_tz.localize(dt) if dt.tzinfo is None else dt.astimezone(kyiv_tz)
    return localized.isoformat()

# Перевірка наявності події з таким самим UID серед подій Google Calendar
def event_exists(events: list[dict], uid: str) -> bool:
    return any(e.get("extendedProperties", {}).get("private", {}).get("uid") == uid for e in events)


def format_day_of_week(day_num: int) -> str:
    """Перетворює номер дня тижня (0=Пн, 6=Нд) у назву українською."""
    days_ukrainian = {
        0: "Понеділок",
        1: "Вівторок",
        2: "Середа",
        3: "Четвер",
        4: "П’ятниця",
        5: "Субота",
        6: "Неділя",
    }
    try:
        day_num = int(day_num)
    except (ValueError, TypeError):
        return "Невідомо"
    return days_ukrainian.get(day_num, "Невідомо")


def format_monthly_position(pos: int) -> str:
    mapping = {1: "Перший", 2: "Другий", 3: "Третій", 4: "Четвертий", -1: "Останній"}
    return mapping.get(pos, "—")


def get_byday_rrule_code(day_of_week: int, week_of_month: int) -> str:
    """
    Генерує код BYDAY для RRULE. Наприклад:
    - day_of_week = 2 (середа)
    - week_of_month = 2 (другий тиждень)
    → повертає '2WE'
    """
    rrule_days = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
    if 0 <= day_of_week <= 6 and 1 <= week_of_month <= 4:
        return f"{week_of_month}{rrule_days[day_of_week]}"
    return None

def format_recurrence(entry: dict) -> list[str] | None:
    frequency = entry.get("frequency")
    day = entry.get("day_of_week", 0)
    week = entry.get("monthly_week", 1)

    rrule_days = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
    if not frequency:
        return None

    if frequency == "daily":
        return ["RRULE:FREQ=DAILY"]
    elif frequency == "weekly":
        return [f"RRULE:FREQ=WEEKLY;BYDAY={rrule_days[day]}"]
    elif frequency == "monthly":
        if week not in [1, 2, 3, 4]:
            return None
        return [f"RRULE:FREQ=MONTHLY;BYDAY={week}{rrule_days[day]}"]

    return None


def get_next_occurrence(weekday: int, week_of_month: int, base_date: datetime = None) -> datetime:
    if base_date is None:
        base_date = datetime.now()

    year = base_date.year
    month = base_date.month

    for _ in range(2):  # перевірити поточний і наступний місяць
        month_cal = calendar.monthcalendar(year, month)
        valid_weeks = [week for week in month_cal if week[weekday] != 0]

        if len(valid_weeks) >= week_of_month:
            day = valid_weeks[week_of_month - 1][weekday]
            candidate = datetime(year, month, day)
            if candidate.date() >= base_date.date():
                return candidate

        # перейти на наступний місяць
        month = 1 if month == 12 else month + 1
        year = year + 1 if month == 1 else year

    raise ValueError("Не вдалося знайти відповідну дату для повторення.")
