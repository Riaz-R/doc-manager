from datetime import date

_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def format_date(day: date) -> str:
    """A date as people write it in messages: "14 Mar 2027"."""
    return f"{day.day} {_MONTHS[day.month - 1]} {day.year}"
