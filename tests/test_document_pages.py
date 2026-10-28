import html
from datetime import date, timedelta

import pytest
from conftest import FIXED_NOW
from sqlalchemy import select

from docmanager.models.box import Box
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.web import routes

PDF_BYTES = b"%PDF-1.4 pretend this is a PDF"
FILED_PATH = (
    "archive/C-0042 Hollybrook Bakery Ltd/Invoices/2021-03-14 Invoice INV-1043.pdf"
)


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


@pytest.fixture
def hollybrook(db):
    client = Client(ref="C-0042", name="Hollybrook Bakery Ltd", created_at=FIXED_NOW)
    db.add(client)
    db.commit()
    return client


@pytest.fixture
def make_document(db, data_dir, hollybrook):
    """Build a document in the database, with its PDF on disk unless told otherwise."""

    def make(
        state=DocState.FILED,
        *,
        doc_type="invoice",
        client=True,
        fields=None,
        document_date=date(2021, 3, 14),
        keep_until=None,
        pdf_path=FILED_PATH,
        write_pdf=True,
        ocr_error=None,
        filed_at=FIXED_NOW,
        filed_name="2021-03-14 Invoice INV-1043.pdf",
    ):
        box = db.scalars(select(Box)).first() or Box(name="Box 1", created_at=FIXED_NOW)
        document = Document(
            box=box,
            doc_type=doc_type,
            client=hollybrook if client else None,
            fields={"invoice_number": "INV-1043", "amount_pence": 12000}
            if fields is None
            else fields,
            document_date=document_date,
            keep_until=keep_until,
            pdf_path=pdf_path,
            ocr_error=ocr_error,
            filed_at=filed_at,
            filed_name=filed_name,
            ocr_text="some text",
        )
        document._state = state.value
        db.add(document)
        db.commit()
        if pdf_path and write_pdf:
            target = data_dir / pdf_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(PDF_BYTES)
        return document

    return make


def text(response):
    return html.unescape(response.get_data(as_text=True))


# --- Filed documents ---


def test_the_filed_list_says_so_when_nothing_is_filed(client):
    response = client.get("/documents")

    assert response.status_code == 200
    assert "No documents have been filed yet" in text(response)


def test_the_filed_list_shows_client_type_date_and_keep_until(client, make_document):
    make_document(keep_until=date(2027, 3, 14))

    page = text(client.get("/documents"))

    assert "C-0042 Hollybrook Bakery Ltd" in page
    assert "Invoice" in page
    assert "14 Mar 2021" in page
    assert "14 Mar 2027" in page


def test_the_filed_list_has_column_headings(client, make_document):
    make_document()

    page = text(client.get("/documents"))

    for heading in ("Client", "Type", "Date", "Keep until", "Markers"):
        assert f"<th>{heading}</th>" in page


def test_the_list_shows_a_filed_document_with_no_date_with_its_no_date_marker(
    client, make_document
):
    make_document(document_date=None, keep_until=None)

    page = text(client.get("/documents"))

    assert "No date" in page


def test_a_dated_document_has_no_no_date_marker(client, make_document):
    make_document(keep_until=date(2027, 3, 14))

    assert "No date" not in text(client.get("/documents"))


def test_a_document_past_its_keep_until_date_has_the_due_marker(client, make_document):
    make_document(keep_until=date(2026, 10, 26))  # the day before the fixed "today"

    assert "Due" in text(client.get("/documents"))


def test_a_document_is_kept_through_its_keep_until_day_so_it_is_not_due(
    client, make_document
):
    make_document(keep_until=date(2026, 10, 27))  # today

    assert "Due" not in text(client.get("/documents"))


def test_only_filed_documents_are_listed(client, make_document):
    make_document(DocState.FILED, filed_name="filed one.pdf")
    for state in (DocState.GROUPED, DocState.NEEDS_REVIEW, DocState.IN_BIN):
        make_document(state, client=False, doc_type=None, fields={})

    page = text(client.get("/documents"))

    assert page.count('href="/documents/') == 1


def test_the_newest_filed_document_comes_first(client, make_document):
    older = make_document(filed_at=FIXED_NOW - timedelta(days=1))
    newer = make_document(filed_at=FIXED_NOW)

    page = client.get("/documents").get_data(as_text=True)

    assert page.index(f'href="/documents/{newer.id}"') < page.index(
        f'href="/documents/{older.id}"'
    )


def test_each_row_links_to_its_document_page(client, make_document):
    document = make_document()

    page = client.get("/documents").get_data(as_text=True)

    assert f'href="/documents/{document.id}"' in page


def test_a_document_with_no_client_or_type_still_lists(client, make_document):
    make_document(client=False, doc_type=None, fields={})

    page = text(client.get("/documents"))

    assert "Unclassified" in page


def test_home_and_the_navigation_link_to_the_filed_documents(client):
    home = client.get("/").get_data(as_text=True)

    assert home.count('href="/documents"') >= 2  # the navigation bar and Home itself


# --- The Document page ---


def test_the_document_page_shows_its_state_label(client, make_document):
    document = make_document()

    page = text(client.get(f"/documents/{document.id}"))

    assert "Filed" in page
    assert f"Document {document.id}" in page


@pytest.mark.parametrize(
    "state,error,label",
    [
        (DocState.NEEDS_REVIEW, None, "Needs checking"),
        (DocState.IN_BIN, None, "In bin"),
        (DocState.GROUPED, None, "Not read yet"),
        (DocState.GROUPED, "Couldn't read this document.", "Couldn't read"),
    ],
)
def test_every_state_shows_its_own_label(client, make_document, state, error, label):
    document = make_document(state, ocr_error=error)

    assert label in text(client.get(f"/documents/{document.id}"))


def test_the_document_page_shows_the_fields_client_type_and_date(client, make_document):
    document = make_document(keep_until=date(2027, 3, 14))

    page = text(client.get(f"/documents/{document.id}"))

    assert "Invoice" in page
    assert "C-0042 Hollybrook Bakery Ltd" in page
    assert "Invoice number" in page and "INV-1043" in page
    assert "Amount due" in page and "£120.00" in page
    assert "14 Mar 2021" in page
    assert "14 Mar 2027" in page


def test_the_document_page_shows_the_letter_fields(client, make_document):
    document = make_document(
        doc_type="letter", fields={"subject": "Year end accounts reminder"}
    )

    page = text(client.get(f"/documents/{document.id}"))

    assert "Letter" in page
    assert "Subject" in page and "Year end accounts reminder" in page


def test_a_field_that_was_not_found_says_so(client, make_document):
    document = make_document(fields={"invoice_number": None, "amount_pence": None})

    page = text(client.get(f"/documents/{document.id}"))

    assert page.count("Not found") == 2


def test_the_document_page_shows_the_markers(client, make_document):
    no_date = make_document(document_date=None)
    due = make_document(keep_until=date(2026, 1, 1))
    needs = make_document(DocState.NEEDS_REVIEW, client=False)

    assert "No date" in text(client.get(f"/documents/{no_date.id}"))
    assert "Due" in text(client.get(f"/documents/{due.id}"))
    assert "Needs checking" in text(client.get(f"/documents/{needs.id}"))


def test_an_unclassified_document_with_no_client_says_so(client, make_document):
    document = make_document(
        DocState.NEEDS_REVIEW, doc_type=None, client=False, fields={}
    )

    page = text(client.get(f"/documents/{document.id}"))

    assert "Unclassified" in page
    assert "No client" in page


def test_an_unknown_document_shows_the_friendly_404(client):
    assert client.get("/documents/999").status_code == 404
    assert client.get("/documents/999/pdf").status_code == 404


# --- The PDF, and N5 ---


def test_the_pdf_is_shown_in_an_iframe_and_served_by_the_pdf_route(
    client, make_document
):
    document = make_document()

    page = client.get(f"/documents/{document.id}").get_data(as_text=True)
    pdf = client.get(f"/documents/{document.id}/pdf")

    assert f'<iframe src="/documents/{document.id}/pdf"' in page
    assert "The PDF file is missing" not in page
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"
    assert pdf.data == PDF_BYTES
    assert "attachment" not in pdf.headers.get("Content-Disposition", "")


def test_n5_a_missing_pdf_file_is_reported_not_a_crash(client, make_document, data_dir):
    document = make_document()
    (data_dir / FILED_PATH).unlink()

    response = client.get(f"/documents/{document.id}")

    assert response.status_code == 200
    page = text(response)
    assert "The PDF file is missing" in page
    assert "<iframe" not in page
    assert "Filed" in page  # the rest of the page still works
    assert client.get(f"/documents/{document.id}/pdf").status_code == 404


def test_a_document_with_no_pdf_yet_says_so(client, make_document):
    document = make_document(
        DocState.GROUPED, client=False, doc_type=None, fields={}, pdf_path=None
    )

    page = text(client.get(f"/documents/{document.id}"))

    assert "There is no PDF for this document yet" in page
    assert "<iframe" not in page
    assert client.get(f"/documents/{document.id}/pdf").status_code == 404


def test_a_path_that_climbs_out_of_the_data_folder_is_never_served(
    client, make_document, data_dir
):
    (data_dir.parent / "outside.pdf").write_bytes(b"secret")
    document = make_document(pdf_path="../outside.pdf", write_pdf=False)

    page = text(client.get(f"/documents/{document.id}"))

    assert "The PDF file is missing" in page
    assert client.get(f"/documents/{document.id}/pdf").status_code == 404


# --- Only the allowed buttons ---


def test_no_buttons_are_offered_until_their_actions_exist(client, make_document):
    # The Move to bin, Restore and File it buttons arrive in tasks 17 and 22.
    assert routes.ACTION_BUTTONS == {}
    document = make_document()

    assert "<button" not in client.get(f"/documents/{document.id}").get_data(
        as_text=True
    )


def test_a_button_is_shown_only_for_an_action_the_lifecycle_allows(
    client, make_document, monkeypatch
):
    monkeypatch.setitem(routes.ACTION_BUTTONS, "dispose", ("Move to bin", "main.home"))
    monkeypatch.setitem(routes.ACTION_BUTTONS, "restore", ("Restore", "main.home"))
    filed = make_document(DocState.FILED)
    binned = make_document(DocState.IN_BIN)
    unread = make_document(DocState.GROUPED)

    filed_page = text(client.get(f"/documents/{filed.id}"))
    binned_page = text(client.get(f"/documents/{binned.id}"))
    unread_page = text(client.get(f"/documents/{unread.id}"))

    assert "Move to bin" in filed_page and "Restore" not in filed_page
    assert "Restore" in binned_page and "Move to bin" not in binned_page
    assert "<button" not in unread_page


def test_the_buttons_come_from_the_documents_own_allowed_actions(make_document):
    assert make_document(DocState.FILED).allowed_actions() == ["dispose"]
    assert make_document(DocState.IN_BIN).allowed_actions() == ["restore", "destroy"]


# --- The markers on the model ---


def test_the_marker_helpers_on_the_document(make_document):
    today = date(2026, 10, 27)
    plain = make_document(keep_until=date(2030, 1, 1))
    no_date = make_document(document_date=None)
    due = make_document(keep_until=date(2026, 10, 26))
    needs = make_document(DocState.NEEDS_REVIEW)

    assert plain.markers(today) == []
    assert no_date.markers(today) == ["No date"]
    assert due.markers(today) == ["Due"]
    assert needs.markers(today) == ["Needs checking"]
    assert needs.needs_checking and not plain.needs_checking
    assert no_date.has_no_date and not plain.has_no_date


def test_a_document_that_is_not_filed_never_has_the_no_date_marker(make_document):
    unread = make_document(DocState.GROUPED, document_date=None)
    binned = make_document(DocState.IN_BIN, document_date=None)

    assert not unread.has_no_date and not binned.has_no_date
