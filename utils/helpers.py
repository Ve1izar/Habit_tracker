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
