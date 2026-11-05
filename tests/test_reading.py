import html
import io
from datetime import date

import pikepdf
import pytest
import texts
from conftest import FIXED_NOW, FakeOcr, photo_bytes
from sqlalchemy import select

from docmanager.models.box import Box
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.models.document_types import DOCUMENT_TYPES
from docmanager.models.page import PageState
from docmanager.models.records import StateChange
from docmanager.services import grouping

W2 = "Couldn't read this document. Try again, or retake the photos."
INVOICE_PATH = "C-0042 Hollybrook Bakery Ltd/Invoices/2021-03-14 Invoice INV-1043.pdf"


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


@pytest.fixture(autouse=True)
def hollybrook(db):
    """The one client every test here needs (the seed script makes it for real)."""
    db.add(Client(ref="C-0042", name="Hollybrook Bakery Ltd", created_at=FIXED_NOW))
    db.commit()


def upload(client, count, box_name="Box 1", prefix="IMG"):
    files = [
        (io.BytesIO(photo_bytes(f"{prefix}{n}")), f"{prefix}_{n:04d}.jpg")
        for n in range(1, count + 1)
    ]
    client.post(
        "/upload", data={"choice": "new", "new_box_name": box_name, "photos": files}
    )


def box_of(db, name="Box 1"):
    return db.scalars(select(Box).where(Box.name == name)).one()


def page_id(db, number, box_name="Box 1"):
    return dict(box_of(db, box_name).ordered_pages())[number].id


def group(client, db, first, last, box_name="Box 1"):
    return client.post(
        f"/boxes/{box_of(db, box_name).id}/make-document",
        data={
            "first": str(page_id(db, first, box_name)),
            "last": str(page_id(db, last, box_name)),
        },
        follow_redirects=True,
    )


def retry(client, document_id):
    return client.post(f"/documents/{document_id}/retry", follow_redirects=True)


def message(response):
    return html.unescape(response.text)


def documents(db):
    db.expire_all()
    return db.scalars(select(Document).order_by(Document.id)).all()


def only_document(db):
    (document,) = documents(db)
    return document


def log_text(data_dir):
    return (data_dir / "logs" / "app.log").read_text()


# --- W1: the happy path ---


def test_w1_a_confident_invoice_is_filed_at_the_n1_path(client, db, fake_ocr, data_dir):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 4)

    response = group(client, db, 1, 2)

    assert "Filed as 2021-03-14 Invoice INV-1043" in message(response)
    document = only_document(db)
    assert document.state == DocState.FILED
    assert document.pdf_path == f"archive/{INVOICE_PATH}"
    assert document.filed_name == "2021-03-14 Invoice INV-1043.pdf"
    assert document.filed_at == FIXED_NOW
    assert (data_dir / "archive" / INVOICE_PATH).is_file()


def test_c1_end_to_end_every_field_is_stored(client, db, fake_ocr):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 2)

    group(client, db, 1, 2)

    document = only_document(db)
    assert document.doc_type == "invoice"
    assert document.type is DOCUMENT_TYPES["invoice"]
    assert document.client.ref == "C-0042"
    assert document.fields == {"invoice_number": "INV-1043", "amount_pence": 12000}
    assert document.document_date == date(2021, 3, 14)
    assert document.keep_until == date(2027, 3, 14)
    assert (document.type_score, document.runner_up_score) == (12, 0)
    assert document.review_reasons == []
    assert document.ocr_text == texts.INVOICE_C1
    assert document.ocr_error is None


def test_the_filed_pdf_has_a_page_for_each_photo_in_order(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 3)

    group(client, db, 1, 3)

    with pikepdf.open(data_dir / "archive" / INVOICE_PATH) as pdf:
        assert len(pdf.pages) == 3


def test_the_sidecar_text_stays_in_work_and_the_images_pdf_is_deleted(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 2)

    group(client, db, 1, 2)

    document = only_document(db)
    images_pdf, searchable, sidecar = fake_ocr.calls[0]
    assert not images_pdf.exists()  # deleted after the attempt
    assert sidecar == data_dir / "work" / f"{document.id}.txt"
    assert sidecar.read_text() == texts.INVOICE_C1
    assert not searchable.exists()  # moved into the archive
    assert [p.name for p in (data_dir / "work").iterdir()] == [f"{document.id}.txt"]


def test_the_document_goes_through_group_then_file_and_the_pages_stay_grouped(
    client, db, fake_ocr
):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 4)
    group(client, db, 2, 3)

    document = only_document(db)
    moves = db.scalars(
        select(StateChange).where(
            StateChange.object_kind == "document", StateChange.object_id == document.id
        )
    ).all()
    assert [(m.action, m.from_state, m.to_state) for m in moves] == [
        ("group", None, "grouped"),
        ("file", "grouped", "filed"),
    ]
    assert [p.state for p in document.pages] == [PageState.GROUPED] * 2


def test_the_document_is_committed_before_the_ocr_starts(app, client, db):
    seen = []

    class Peeking(FakeOcr):
        def __call__(self, pdf_in, pdf_out, sidecar):
            # A second connection sees only what has been committed.
            with app.extensions["docmanager_sessions"]() as other:
                rows = other.scalars(select(Document)).all()
                seen.append([(d.id, d.state, d.ocr_text) for d in rows])
            return super().__call__(pdf_in, pdf_out, sidecar)

    app.config["OCR_RUNNER"] = Peeking(texts.INVOICE_C1)
    upload(client, 2)

    group(client, db, 1, 2)

    assert seen == [[(1, DocState.GROUPED, None)]]


def test_stale_files_from_an_earlier_attempt_are_cleared_before_the_ocr_runs(
    client, db, fake_ocr, data_dir
):
    seen = []

    class Checking(FakeOcr):
        def __call__(self, pdf_in, pdf_out, sidecar):
            seen.append((pdf_out.exists(), sidecar.exists()))
            return super().__call__(pdf_in, pdf_out, sidecar)

    upload(client, 2)
    fake_ocr.fail = "first attempt fails"
    group(client, db, 1, 2)
    document = only_document(db)
    (data_dir / "work" / f"{document.id}.txt").write_text("stale")
    (data_dir / "work" / f"{document.id}.pdf").write_bytes(b"stale")
    checking = Checking(texts.INVOICE_C1)
    client.application.config["OCR_RUNNER"] = checking

    retry(client, document.id)

    assert seen == [(False, False)]


# --- Needs checking ---


def test_a_document_that_fails_a_check_is_flagged_with_all_its_reasons(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail, fake_ocr.text = None, texts.NO_KEYWORDS
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert (
        "Needs checking: Couldn't tell what type this is; "
        "Couldn't tell which client this is for"
    ) in message(response)
    document = only_document(db)
    assert document.state == DocState.NEEDS_REVIEW
    assert document.state_label == "Needs checking"
    assert document.review_reasons == [
        "Couldn't tell what type this is",
        "Couldn't tell which client this is for",
    ]
    assert document.doc_type is None
    assert document.ocr_text == texts.NO_KEYWORDS
    assert document.pdf_path == f"work/{document.id}.pdf"
    assert (data_dir / document.pdf_path).is_file()
    assert document.filed_name is None


def test_a_flagged_document_keeps_the_client_that_was_found(client, db, fake_ocr):
    fake_ocr.fail, fake_ocr.text = (
        None,
        texts.NO_KEYWORDS + "\nClient reference C-0042\n",
    )
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert "Needs checking: Couldn't tell what type this is" in message(response)
    assert "which client" not in message(response)
    document = only_document(db)
    assert document.client.ref == "C-0042"
    assert (document.type_score, document.runner_up_score) == (0, 0)


def test_c11_too_little_text_is_flagged_even_with_a_confident_type_and_client(
    client, db, fake_ocr
):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_ELEVEN_WORDS
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert (
        "Needs checking: Very little text was read. Check the photos are clear "
        "before shredding the paper."
    ) in message(response)
    document = only_document(db)
    assert document.state == DocState.NEEDS_REVIEW
    assert document.doc_type == "invoice"  # the type was still found
    assert document.client.ref == "C-0042"


def test_empty_ocr_text_counts_as_read_and_is_flagged_with_every_reason(
    client, db, fake_ocr
):
    fake_ocr.fail, fake_ocr.text = None, ""
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert "Needs checking: Very little text was read." in message(response)
    document = only_document(db)
    assert document.state == DocState.NEEDS_REVIEW
    assert document.ocr_text == ""
    assert len(document.review_reasons) == 3


def test_an_unknown_client_reference_is_flagged(client, db, fake_ocr):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_UNKNOWN_REF
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert "Needs checking: Client C-0099 isn't in your client list" in message(
        response
    )


# --- C6 and the clash rule ---


def test_c6_no_date_files_as_undated(client, db, fake_ocr, data_dir):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_NO_DATE
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert "Filed as undated Invoice INV-7000" in message(response)
    document = only_document(db)
    assert document.state == DocState.FILED
    assert document.document_date is None
    assert document.filed_name == "undated Invoice INV-7000.pdf"
    assert (
        data_dir
        / "archive"
        / "C-0042 Hollybrook Bakery Ltd"
        / "Invoices"
        / "undated Invoice INV-7000.pdf"
    ).is_file()


def test_a_name_clash_gives_the_second_file_a_2_suffix(client, db, fake_ocr, data_dir):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 4)
    group(client, db, 1, 2)

    response = group(client, db, 3, 4)

    assert "Filed as 2021-03-14 Invoice INV-1043 (2)" in message(response)
    first, second = documents(db)
    assert first.filed_name == "2021-03-14 Invoice INV-1043.pdf"
    assert second.filed_name == "2021-03-14 Invoice INV-1043 (2).pdf"
    folder = data_dir / "archive" / "C-0042 Hollybrook Bakery Ltd" / "Invoices"
    assert sorted(p.name for p in folder.iterdir()) == [
        "2021-03-14 Invoice INV-1043 (2).pdf",
        "2021-03-14 Invoice INV-1043.pdf",
    ]
    assert second.pdf_path == f"archive/{INVOICE_PATH.replace('.pdf', ' (2).pdf')}"


# --- W2: OCR fails ---


def test_w2_an_ocr_failure_leaves_the_document_grouped_with_the_exact_error(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail = "Ghostscript exploded: error 42"
    upload(client, 4)

    response = group(client, db, 1, 2)

    assert W2 in message(response)
    document = only_document(db)
    assert document.state == DocState.GROUPED
    assert document.ocr_error == W2
    assert document.ocr_text is None
    assert document.state_label == "Couldn't read"
    assert document.pdf_path is None
    actions = db.scalars(select(StateChange.action)).all()
    assert "file" not in actions and "flag" not in actions
    assert not any((data_dir / "work").glob("*-images.pdf"))  # images pdf deleted


def test_w2_the_technical_detail_goes_to_the_log_not_to_the_user(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail = "Ghostscript exploded: error 42"
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert "Ghostscript exploded" not in message(response)
    document = only_document(db)
    assert "Ghostscript exploded: error 42" in log_text(data_dir)
    assert f"document {document.id}" in log_text(data_dir)


def test_w2_the_inbox_lists_the_document_as_couldnt_read_with_a_retry_button(
    client, db, fake_ocr
):
    fake_ocr.fail = "boom"
    upload(client, 4)
    group(client, db, 1, 2)
    document = only_document(db)

    page = client.get(f"/boxes/{box_of(db).id}/inbox").text

    assert f"Document {document.id}" in page
    assert "Couldn&#39;t read" in page
    assert html.unescape(page).count(W2) == 1
    assert f'action="/documents/{document.id}/retry"' in page
    assert "Retry" in page


def test_a_photo_that_cannot_be_combined_is_a_read_failure_too(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 2)
    for page in box_of(db).pages:
        (data_dir / page.photo_path).unlink()

    response = group(client, db, 1, 2)

    assert W2 in message(response)
    assert only_document(db).state == DocState.GROUPED
    assert "Could not combine the photos" in log_text(data_dir)


# --- W3: Retry ---


def test_w3_retry_clears_the_error_and_files_the_document(client, db, fake_ocr):
    fake_ocr.fail = "boom"
    upload(client, 2)
    group(client, db, 1, 2)
    document = only_document(db)
    assert document.ocr_error == W2
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1

    response = retry(client, document.id)

    assert "Filed as 2021-03-14 Invoice INV-1043" in message(response)
    document = only_document(db)
    assert document.state == DocState.FILED
    assert document.ocr_error is None
    assert document.ocr_text == texts.INVOICE_C1
    assert [p.state for p in document.pages] == [PageState.GROUPED] * 2


def test_w3_a_retry_that_fails_again_keeps_the_error_and_the_retry_button(
    client, db, fake_ocr, data_dir
):
    fake_ocr.fail = "first failure"
    upload(client, 2)
    group(client, db, 1, 2)
    document = only_document(db)
    fake_ocr.fail = "second failure"

    response = retry(client, document.id)

    assert W2 in message(response)
    assert only_document(db).ocr_error == W2
    assert "second failure" in log_text(data_dir)
    assert f"/documents/{document.id}/retry" in response.text


def test_w3_a_retry_can_end_in_needs_checking(client, db, fake_ocr):
    fake_ocr.fail = "boom"
    upload(client, 2)
    group(client, db, 1, 2)
    fake_ocr.fail, fake_ocr.text = None, texts.NO_KEYWORDS

    response = retry(client, only_document(db).id)

    assert "Needs checking: Couldn't tell what type this is" in message(response)
    assert only_document(db).ocr_error is None


def test_retry_sends_the_user_back_to_the_inbox_of_the_documents_box(
    client, db, fake_ocr
):
    fake_ocr.fail = "boom"
    upload(client, 2)
    group(client, db, 1, 2)

    response = client.post(f"/documents/{only_document(db).id}/retry")

    assert response.status_code == 302
    assert response.headers["Location"] == f"/boxes/{box_of(db).id}/inbox"


@pytest.mark.parametrize("text", [texts.INVOICE_C1, texts.NO_KEYWORDS])
def test_retry_on_a_document_that_has_been_read_is_refused(client, db, fake_ocr, text):
    fake_ocr.fail, fake_ocr.text = None, text
    upload(client, 2)
    group(client, db, 1, 2)  # filed or flagged: either way it has been read
    calls_before = len(fake_ocr.calls)

    response = retry(client, only_document(db).id)

    assert "This document has already been read" in message(response)
    assert len(fake_ocr.calls) == calls_before


def test_retry_on_a_document_that_does_not_exist_is_a_404(client):
    assert client.post("/documents/999/retry").status_code == 404


# --- W4: interrupted ---


def make_unread_document(app, db):
    """A Grouped document with no text and no error, as if the app stopped mid-read."""
    box = box_of(db)
    pages = [p for _, p in box.ordered_pages()]
    with app.extensions["docmanager_sessions"]() as session:
        made = grouping.make_document(
            session, session.get(Box, box.id), pages[0].id, pages[1].id, now=FIXED_NOW
        )
        session.commit()
        return made.document.id


def test_w4_a_grouped_document_with_no_text_is_listed_with_a_retry_button(
    app, client, db
):
    upload(client, 4)
    document_id = make_unread_document(app, db)

    page = client.get(f"/boxes/{box_of(db).id}/inbox").text

    assert f"Document {document_id}" in page
    assert "Not read yet" in page
    assert f'action="/documents/{document_id}/retry"' in page


def test_w4_retry_reads_the_interrupted_document(app, client, db, fake_ocr):
    upload(client, 4)
    document_id = make_unread_document(app, db)
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1

    response = retry(client, document_id)

    assert "Filed as 2021-03-14 Invoice INV-1043" in message(response)
    assert only_document(db).state == DocState.FILED


def test_w4_an_unexpected_crash_during_ocr_leaves_a_committed_unread_document(
    app, client, db
):
    class Crashing(FakeOcr):
        def __call__(self, pdf_in, pdf_out, sidecar):
            raise RuntimeError("the power went out")

    app.config["OCR_RUNNER"] = Crashing()
    upload(client, 2)

    response = group(client, db, 1, 2)

    assert response.status_code == 500
    document = only_document(db)
    assert (document.state, document.ocr_text, document.ocr_error) == (
        DocState.GROUPED,
        None,
        None,
    )
    page = client.get(f"/boxes/{box_of(db).id}/inbox").text
    assert "Not read yet" in page and f"/documents/{document.id}/retry" in page


def test_a_document_that_is_filed_or_flagged_is_not_listed_as_unread(
    client, db, fake_ocr
):
    fake_ocr.fail, fake_ocr.text = None, texts.INVOICE_C1
    upload(client, 4)
    group(client, db, 1, 2)

    page = client.get(f"/boxes/{box_of(db).id}/inbox").text

    assert "/retry" not in page
    assert "not read yet" not in page.lower()


# --- change_type ---


def make_document_with_text(session, text):
    box = Box(name="Box 1", created_at=FIXED_NOW)
    document = Document(box=box, ocr_text=text, doc_type="letter")
    session.add(document)
    session.flush()
    return document


TODAY = date(2026, 10, 27)


def test_change_type_sets_the_key_and_reads_the_new_types_fields_and_date(session):
    document = make_document_with_text(session, texts.INVOICE_C1)
    document.fields = {"subject": "old"}

    document.change_type(DOCUMENT_TYPES["invoice"], today=TODAY)

    assert document.doc_type == "invoice"
    assert document.type is DOCUMENT_TYPES["invoice"]
    assert document.fields == {"invoice_number": "INV-1043", "amount_pence": 12000}
    assert document.document_date == date(2021, 3, 14)


def test_change_type_to_letter_gives_the_letter_fields(session):
    document = make_document_with_text(session, texts.LETTER)
    document.doc_type = "invoice"

    document.change_type(DOCUMENT_TYPES["letter"], today=TODAY)

    assert document.doc_type == "letter"
    assert document.fields == {"subject": "Year end accounts reminder"}
    assert document.document_date == date(2022, 5, 10)


def test_change_type_keeps_the_id_the_state_and_the_pages(session):
    document = make_document_with_text(session, texts.LETTER)
    document._state = "needs_review"
    ident = document.id

    document.change_type(DOCUMENT_TYPES["invoice"], today=TODAY)

    assert document.id == ident
    assert document.state == DocState.NEEDS_REVIEW


def test_change_type_replaces_the_fields_dict_so_the_database_notices(session):
    document = make_document_with_text(session, texts.LETTER)
    before = document.fields = {"subject": "x"}

    document.change_type(DOCUMENT_TYPES["letter"], today=TODAY)

    assert document.fields is not before
    assert before == {"subject": "x"}  # the old dict was left alone


def test_change_type_ignores_a_date_after_today(session):
    document = make_document_with_text(session, "Dear Sir\nRe: Hello\n14/03/2031")

    document.change_type(DOCUMENT_TYPES["letter"], today=TODAY)

    assert document.document_date is None


def test_change_type_on_a_document_with_no_text_gives_empty_fields(session):
    document = make_document_with_text(session, None)

    document.change_type(DOCUMENT_TYPES["invoice"], today=TODAY)

    assert document.doc_type == "invoice"
    assert document.fields == {"invoice_number": None, "amount_pence": None}
    assert document.document_date is None
