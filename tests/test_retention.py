"""AT-18: retention, R1 to R5."""

from datetime import date

import texts
from conftest import FIXED_NOW

from docmanager.models.box import Box
from docmanager.models.document import DocState, Document
from docmanager.models.document_types import DOCUMENT_TYPES
from docmanager.rules.dates import add_years

INVOICE = DOCUMENT_TYPES["invoice"]
LETTER = DOCUMENT_TYPES["letter"]
TODAY = date(2026, 10, 25)


def test_each_types_retention_years():
    assert INVOICE.retention_years == 6
    assert LETTER.retention_years == 3


def test_r1_an_invoice_is_kept_six_years():
    assert INVOICE.keep_until(date(2021, 3, 14)) == date(2027, 3, 14)


def test_r2_a_letter_is_kept_three_years():
    assert LETTER.keep_until(date(2022, 5, 10)) == date(2025, 5, 10)


def test_r3_a_leap_day_becomes_28_february():
    assert LETTER.keep_until(date(2020, 2, 29)) == date(2023, 2, 28)


def test_a_leap_day_that_lands_on_a_leap_year_stays_29_february():
    assert add_years(date(2020, 2, 29), 4) == date(2024, 2, 29)


def test_no_date_means_no_keep_until():
    assert INVOICE.keep_until(None) is None


def test_change_type_sets_keep_until_from_the_new_types_rule(session):
    document = Document(
        box=Box(name="Box 1", created_at=FIXED_NOW), ocr_text=texts.INVOICE_C1
    )
    session.add(document)
    session.flush()

    document.change_type(INVOICE, today=TODAY)
    assert document.document_date == date(2021, 3, 14)
    assert document.keep_until == date(2027, 3, 14)

    document.change_type(LETTER, today=TODAY)  # a letter is kept 3 years
    assert document.keep_until == add_years(document.document_date, 3)


def test_change_type_with_no_date_clears_keep_until(session):
    document = Document(
        box=Box(name="Box 1", created_at=FIXED_NOW),
        ocr_text="Dear Sir\nRe: Hello",
        keep_until=date(2030, 1, 1),
    )
    session.add(document)
    session.flush()

    document.change_type(LETTER, today=TODAY)

    assert document.keep_until is None


def _filed(session, keep_until):
    document = Document(
        box=Box(name="Box 1", created_at=FIXED_NOW),
        doc_type="invoice",
        keep_until=keep_until,
    )
    document._state = DocState.FILED.value  # tests may set the state directly
    session.add(document)
    return document


def test_r4_due_the_day_after_keep_until_but_not_on_it():
    day = date(2026, 10, 24)
    due = Document(keep_until=day)
    due._state = DocState.FILED.value
    kept = Document(keep_until=date(2026, 10, 25))
    kept._state = DocState.FILED.value
    assert due.is_due(TODAY)
    assert not kept.is_due(TODAY)  # kept through that day
    assert "Due" in due.markers(TODAY)
    assert "Due" not in kept.markers(TODAY)


def test_r5_a_document_with_no_date_is_never_due():
    document = Document(keep_until=None, document_date=None)
    document._state = DocState.FILED.value
    assert not document.is_due(date(2099, 1, 1))
    assert "Due" not in document.markers(date(2099, 1, 1))


def test_r5_the_document_page_says_keep_until_is_not_set(client, app):
    with app.extensions["docmanager_sessions"]() as db:
        document = _filed(db, None)
        document.document_date = None
        db.commit()
        ident = document.id
    page = client.get(f"/documents/{ident}").get_data(as_text=True)
    assert "Keep-until not set – add the document&#39;s date" in page or (
        "Keep-until not set – add the document's date" in page
    )


def test_the_document_page_shows_the_keep_until_date(client, app):
    with app.extensions["docmanager_sessions"]() as db:
        document = _filed(db, date(2027, 3, 14))
        db.commit()
        ident = document.id
    page = client.get(f"/documents/{ident}").get_data(as_text=True)
    assert "14 Mar 2027" in page
    assert "Keep-until not set" not in page
