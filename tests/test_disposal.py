"""AT-19 (first half): Due for disposal, Move to bin and restore. D1 to D3 and R4."""

import html
from datetime import date

import pytest
from conftest import FIXED_NOW
from sqlalchemy import select

from docmanager.config import LEGAL_NOTE
from docmanager.models.box import Box
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.models.records import StateChange

PDF_BYTES = b"%PDF-1.4 pretend this is a PDF"
ARCHIVE = "C-0042 Hollybrook Bakery Ltd/Invoices"


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


@pytest.fixture
def make_document(db, data_dir):
    """A Filed document with its PDF in the archive, kept until `keep_until`."""

    def make(
        keep_until=date(2026, 10, 26),  # the day before the fixed "today"
        *,
        number="INV-1043",
        document_date=date(2021, 3, 14),
        write_pdf=True,
    ):
        hollybrook = db.scalars(select(Client)).first() or Client(
            ref="C-0042", name="Hollybrook Bakery Ltd", created_at=FIXED_NOW
        )
        box = db.scalars(select(Box)).first() or Box(name="Box 1", created_at=FIXED_NOW)
        name = f"{document_date} Invoice {number}.pdf"
        document = Document(
            box=box,
            doc_type="invoice",
            client=hollybrook,
            fields={"invoice_number": number, "amount_pence": 12000},
            document_date=document_date,
            keep_until=keep_until,
            pdf_path=f"archive/{ARCHIVE}/{name}",
            filed_name=name,
            filed_at=FIXED_NOW,
            ocr_text="some text",
        )
        document._state = DocState.FILED.value
        db.add(document)
        db.commit()
        if write_pdf:
            target = data_dir / document.pdf_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(PDF_BYTES)
        return document

    return make


def text(response):
    return html.unescape(response.get_data(as_text=True))


def flashed(response):
    return text(response)


def move(client, *documents, follow=True):
    return client.post(
        "/due/bin",
        data={"document": [str(d.id) for d in documents]},
        follow_redirects=follow,
    )


def history(db, document):
    return [
        (r.action, r.from_state, r.to_state)
        for r in db.scalars(
            select(StateChange)
            .where(
                StateChange.object_kind == "document",
                StateChange.object_id == document.id,
            )
            .order_by(StateChange.id)
        )
    ]


# --- R4 at the list level ---


def test_r4_a_document_a_day_past_keep_until_is_listed_but_one_kept_through_today_is_not(
    client, make_document
):
    due = make_document(date(2026, 10, 26), number="INV-1")
    kept = make_document(date(2026, 10, 27), number="INV-2")

    page = text(client.get("/due"))

    assert f'value="{due.id}"' in page
    assert f'value="{kept.id}"' not in page


def test_r5_a_document_with_no_date_is_never_listed(client, make_document):
    undated = make_document(None, document_date=None)

    assert f'value="{undated.id}"' not in text(client.get("/due"))


def test_the_due_list_says_so_when_nothing_is_due(client, make_document):
    make_document(date(2030, 1, 1))

    assert "Nothing is due for disposal" in text(client.get("/due"))


def test_the_due_list_shows_a_tick_box_and_the_details_for_each_document(
    client, make_document
):
    make_document(date(2026, 10, 26))

    page = text(client.get("/due"))

    assert 'type="checkbox"' in page and 'name="document"' in page
    assert "C-0042 Hollybrook Bakery Ltd" in page
    assert "26 Oct 2026" in page
    assert "Move ticked to bin" in page


def test_the_due_list_only_lists_filed_documents(client, make_document, db):
    binned = make_document(date(2026, 10, 26))
    binned._state = DocState.IN_BIN.value
    db.commit()

    assert f'value="{binned.id}"' not in text(client.get("/due"))


def test_the_legal_note_is_shown_on_the_due_list_and_the_bin(client):
    assert LEGAL_NOTE.startswith("These keep-until dates come from example rules.")
    assert LEGAL_NOTE in text(client.get("/due"))
    assert LEGAL_NOTE in text(client.get("/bin"))


# --- D1: move to bin ---


def test_d1_two_ticked_due_documents_go_to_the_bin(client, db, data_dir, make_document):
    first = make_document(number="INV-1")
    second = make_document(number="INV-2")
    original = first.pdf_path

    response = move(client, first, second)

    assert "2 documents moved to the bin" in flashed(response)
    db.expire_all()
    for document in (first, second):
        assert document.state == DocState.IN_BIN
        assert document.binned_at == FIXED_NOW
        assert document.pdf_path == f"bin/{document.id}.pdf"
        assert (data_dir / document.pdf_path).read_bytes() == PDF_BYTES
    assert not (data_dir / original).exists()
    assert history(db, first)[-1] == ("dispose", "filed", "in_bin")


def test_one_document_is_worded_in_the_singular(client, make_document):
    only = make_document()

    assert "1 document moved to the bin" in flashed(move(client, only))


def test_a_document_page_move_to_bin_button_works_for_a_due_document(
    client, db, data_dir, make_document
):
    document = make_document()

    page = text(client.get(f"/documents/{document.id}"))
    assert f'action="/documents/{document.id}/bin"' in page
    assert "Move to bin" in page

    client.post(f"/documents/{document.id}/bin")
    db.expire_all()
    assert document.state == DocState.IN_BIN


def test_a_post_with_nothing_ticked_says_so(client, make_document):
    make_document()

    response = client.post("/due/bin", follow_redirects=True)

    assert "Tick the documents to move to the bin" in flashed(response)


# --- D2: not yet due ---


def test_d2_a_crafted_post_for_a_document_that_is_not_due_is_refused(
    client, db, data_dir, make_document
):
    document = make_document(date(2027, 3, 14))

    response = move(client, document)

    assert "This document must be kept until 14 Mar 2027" in flashed(response)
    db.expire_all()
    assert document.state == DocState.FILED
    assert document.binned_at is None
    assert (data_dir / document.pdf_path).is_file()


def test_the_document_page_offers_move_to_bin_even_when_not_due_and_refuses_it(
    client, db, make_document
):
    document = make_document(date(2027, 3, 14))

    assert "Move to bin" in text(client.get(f"/documents/{document.id}"))

    response = client.post(f"/documents/{document.id}/bin", follow_redirects=True)
    assert "This document must be kept until 14 Mar 2027" in flashed(response)


def test_one_refused_document_stops_the_whole_move(client, db, data_dir, make_document):
    due = make_document(number="INV-1")
    not_due = make_document(date(2030, 1, 1), number="INV-2")

    move(client, due, not_due)

    db.expire_all()
    assert due.state == DocState.FILED  # nothing moved
    assert (data_dir / due.pdf_path).is_file()


def test_a_document_with_no_keep_until_is_refused_with_its_own_reason(
    client, make_document
):
    undated = make_document(None, document_date=None)

    response = move(client, undated)

    assert "Keep-until not set – add the document's date" in flashed(response)


def test_an_unknown_document_id_is_refused(client, make_document):
    make_document()

    response = client.post("/due/bin", data={"document": "999"}, follow_redirects=True)

    assert "That document can't be found" in flashed(response)


def test_a_document_whose_pdf_has_gone_can_still_be_binned(client, db, make_document):
    document = make_document(write_pdf=False)

    move(client, document)

    db.expire_all()
    assert document.state == DocState.IN_BIN


# --- The Bin lists documents ---


def test_the_bin_lists_documents_with_a_restore_button(client, db, make_document):
    document = make_document()
    move(client, document)

    page = text(client.get("/bin"))

    assert "2021-03-14 Invoice INV-1043.pdf" in page
    assert "C-0042 Hollybrook Bakery Ltd" in page
    assert f'action="/documents/{document.id}/restore"' in page


def test_home_tiles_show_the_due_count_and_count_documents_in_the_bin(
    client, make_document
):
    first = make_document(number="INV-1")
    make_document(number="INV-2")

    page = text(client.get("/"))
    assert 'href="/due"' in page
    assert "Due for disposal: 2 documents" in page
    assert "Bin: 0 items" in page

    move(client, first)
    page = text(client.get("/"))
    assert "Due for disposal: 1 document" in page
    assert "Bin: 1 item" in page


# --- D3: restore ---


def test_d3_restore_puts_the_document_back_at_its_calculated_path(
    client, db, data_dir, make_document
):
    document = make_document()
    original = document.pdf_path
    move(client, document)

    response = client.post(f"/documents/{document.id}/restore", follow_redirects=True)

    assert "restored" in flashed(response).lower()
    db.expire_all()
    assert document.state == DocState.FILED
    assert document.pdf_path == original
    assert document.filed_name == "2021-03-14 Invoice INV-1043.pdf"
    assert document.binned_at is None
    assert (data_dir / original).read_bytes() == PDF_BYTES
    assert not (data_dir / "bin" / f"{document.id}.pdf").exists()
    assert history(db, document)[-1] == ("restore", "in_bin", "filed")


def test_d3_a_name_clash_on_restore_gets_a_2_suffix(
    client, db, data_dir, make_document
):
    document = make_document()
    move(client, document)
    # Another document has since been filed under the same name.
    taken = data_dir / "archive" / ARCHIVE / "2021-03-14 Invoice INV-1043.pdf"
    taken.parent.mkdir(parents=True, exist_ok=True)
    taken.write_bytes(b"someone else")

    client.post(f"/documents/{document.id}/restore")

    db.expire_all()
    assert document.filed_name == "2021-03-14 Invoice INV-1043 (2).pdf"
    assert document.pdf_path == f"archive/{ARCHIVE}/{document.filed_name}"
    assert taken.read_bytes() == b"someone else"  # not overwritten
    assert (data_dir / document.pdf_path).read_bytes() == PDF_BYTES


def test_restore_is_refused_for_a_filed_document(client, db, make_document):
    document = make_document()

    response = client.post(f"/documents/{document.id}/restore", follow_redirects=True)

    assert "can't be restored" in flashed(response)
    db.expire_all()
    assert document.state == DocState.FILED


def test_restore_with_the_pdf_missing_from_the_bin_is_refused(
    client, db, data_dir, make_document
):
    document = make_document()
    move(client, document)
    (data_dir / "bin" / f"{document.id}.pdf").unlink()

    response = client.post(f"/documents/{document.id}/restore", follow_redirects=True)

    assert "The PDF file is missing" in flashed(response)
    db.expire_all()
    assert document.state == DocState.IN_BIN


def test_the_document_page_of_a_binned_document_offers_restore_not_move(
    client, db, make_document
):
    document = make_document()
    move(client, document)

    page = text(client.get(f"/documents/{document.id}"))

    assert f'action="/documents/{document.id}/restore"' in page
    assert "Move to bin" not in page
