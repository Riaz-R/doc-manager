from datetime import date

import pytest

from docmanager.rules.dates import find_dates

TODAY = date(2026, 10, 27)


@pytest.mark.parametrize(
    "text",
    [
        "Dated 14/03/2021 at the shop",
        "Dated 14 March 2021 at the shop",
        "Dated 2021-03-14 at the shop",
    ],
)
def test_each_of_the_three_formats_is_read(text):
    assert find_dates(text, TODAY) == [date(2021, 3, 14)]


def test_uk_dates_are_day_first():
    assert find_dates("3/4/2021", TODAY) == [date(2021, 4, 3)]
    assert find_dates("03/04/2021", TODAY) == [date(2021, 4, 3)]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 Jan 2021", date(2021, 1, 1)),
        ("1 JANUARY 2021", date(2021, 1, 1)),
        ("1st January 2021", date(2021, 1, 1)),
        ("22nd feb 2021", date(2021, 2, 22)),
        ("3rd Sept 2021", date(2021, 9, 3)),
        ("31 December 2020", date(2020, 12, 31)),
    ],
)
def test_month_names_can_be_full_or_short_in_any_case_with_ordinals(text, expected):
    assert find_dates(text, TODAY) == [expected]


def test_dates_come_back_in_the_order_they_appear():
    text = "Paid 2021-05-01, issued 14/03/2021 and delivered on 2 February 2021"

    assert find_dates(text, TODAY) == [
        date(2021, 5, 1),
        date(2021, 3, 14),
        date(2021, 2, 2),
    ]


def test_a_date_after_today_is_ignored_as_a_misread():
    text = "Invoice date 14/03/2031 and delivered 14/03/2021"

    assert find_dates(text, TODAY) == [date(2021, 3, 14)]


def test_today_itself_is_allowed_and_tomorrow_is_not():
    assert find_dates("27/10/2026", TODAY) == [date(2026, 10, 27)]
    assert find_dates("28/10/2026", TODAY) == []
    assert find_dates("2026-10-28", TODAY) == []
    assert find_dates("28 October 2026", TODAY) == []


@pytest.mark.parametrize(
    "text", ["31/02/2021", "00/05/2021", "14/13/2021", "2021-02-30", "31 June 2021"]
)
def test_dates_that_do_not_exist_are_skipped(text):
    assert find_dates(text, TODAY) == []


@pytest.mark.parametrize(
    "text",
    [
        "",
        "no dates here at all",
        "14/03/21",  # two-digit years are not read
        "14 Marchish 2021",
        "ref 114/03/2021x",
        "phone 0114 2021 3 14",
    ],
)
def test_text_without_a_real_date_gives_an_empty_list(text):
    assert find_dates(text, TODAY) == []


def test_the_same_date_written_twice_is_listed_twice():
    assert find_dates("14/03/2021 and again 14/03/2021", TODAY) == [
        date(2021, 3, 14),
        date(2021, 3, 14),
    ]
