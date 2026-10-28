import re
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


_FULL_MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)
# "march", "mar" and "sept" all work; "marc" and "marchish" do not.
_MONTH_NUMBERS = {
    **{name: number for number, name in enumerate(_FULL_MONTHS, start=1)},
    **{name[:3]: number for number, name in enumerate(_FULL_MONTHS, start=1)},
    "sept": 9,
}

# 2021-03-14
_ISO = re.compile(r"(?<![\d-])(\d{4})-(\d{2})-(\d{2})(?!\d)")
# 14/03/2021, day first (UK)
_UK = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\d/])")
# 14 March 2021, 14th Mar 2021
_LONG = re.compile(
    r"(?<![\w/-])(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\s+(\d{4})(?!\d)"
)


def find_dated_spans(text: str, today: date) -> list[tuple[int, int, date]]:
    """Every real date in `text` as (start, end, date), in the order they appear.

    Reads 14/03/2021, 14 March 2021 and 2021-03-14. Something that isn't a real
    date (31/02/2021) is skipped, and so is a date after `today`: it is a misread.
    """
    found = []
    for match in _ISO.finditer(text):
        year, month, day = (int(g) for g in match.groups())
        found.append((match.start(), match.end(), (year, month, day)))
    for match in _UK.finditer(text):
        day, month, year = (int(g) for g in match.groups())
        found.append((match.start(), match.end(), (year, month, day)))
    for match in _LONG.finditer(text):
        month = _MONTH_NUMBERS.get(match.group(2).lower())
        if month is not None:
            found.append(
                (
                    match.start(),
                    match.end(),
                    (int(match.group(3)), month, int(match.group(1))),
                )
            )

    dated = []
    for start, end, (year, month, day) in sorted(found):
        try:
            when = date(year, month, day)
        except ValueError:  # 31 February and the like
            continue
        if when <= today:
            dated.append((start, end, when))
    return dated


def find_dates(text: str, today: date) -> list[date]:
    """Every real date in `text` that isn't after `today`, in the order they appear."""
    return [when for _, _, when in find_dated_spans(text, today)]
