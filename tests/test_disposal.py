"""AT-19: Due for disposal, Move to bin, restore, Empty bin and disposal records (D1 to D6, R4, B5)."""

import html
import io
import re
from datetime import date
from pathlib import Path

import pytest
from conftest import FIXED_NOW, photo_bytes
from sqlalchemy import select

from docmanager.config import LEGAL_NOTE, Paths
from docmanager.models.box import Batch, Box
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.models.page import Page
from docmanager.models.records import DisposalRecord, StateChange
from docmanager.services import disposal

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


# --- Task 23: Empty bin and disposal records (AT-19 second half: D4 to D6, B5) ---

SPEC_RECORD_FIELDS = {
    "id",
    "filed_name",
    "doc_type_label",
    "client_ref",
    "client_name",
    "document_date",
    "keep_until",
    "page_count",
    "binned_at",
    "destroyed_at",
}


@pytest.fixture
def paths(app):
    return app.config["PATHS"]


@pytest.fixture
def binned(db, data_dir, make_document):
    """A document in the bin with two grouped pages, all with real files on disk."""

    def make(number="INV-1043", *, clash=False):
        document = make_document(number=number)
        box = document.box
        batch = db.scalars(select(Batch)).first() or Batch(
            box=box,
            uploaded_at=FIXED_NOW,
            added_count=0,
            skipped_count=0,
            refused_count=0,
        )
        for position in (1, 2):
            sha = f"sha-{document.id}-{position}"
            page = Page(
                box=box,
                batch=batch,
                sha256=sha,
                original_filename=f"IMG_{document.id}{position}.jpg",
                photo_path=f"photos/{box.id}/{sha}.jpg",
                thumb_path=f"thumbs/{box.id}/{sha}.jpg",
                document=document,
                position=position,
            )
            page._state = "grouped"
            db.add(page)
            for rel in (page.photo_path, page.thumb_path):
                (data_dir / rel).parent.mkdir(parents=True, exist_ok=True)
                (data_dir / rel).write_bytes(b"jpeg")
        db.commit()
        if clash:
            taken = data_dir / document.pdf_path
            taken.parent.mkdir(parents=True, exist_ok=True)
            taken.write_bytes(b"x")
            document.pdf_path = document.pdf_path.replace(".pdf", " (2).pdf")
            document.filed_name = document.filed_name.replace(".pdf", " (2).pdf")
            (data_dir / document.pdf_path).write_bytes(PDF_BYTES)
            db.commit()
        (data_dir / "work").mkdir(exist_ok=True)
        (data_dir / "work" / f"{document.id}.txt").write_text("ocr text")
        # keep_until is behind "today", so it can be binned the normal way.
        disposal.move_to_bin(db, [document.id], paths=Paths(data_dir), now=FIXED_NOW)
        db.commit()
        return document

    return make


@pytest.fixture
def lone_photos(client, db):
    """Upload three photos and mark two of them "Not a page"."""
    client.post(
        "/upload",
        data={
            "choice": "new",
            "new_box_name": "Box 9",
            "photos": [
                (io.BytesIO(photo_bytes(f"P{n}")), f"IMG_000{n}.jpg") for n in (1, 2, 3)
            ],
        },
        content_type="multipart/form-data",
    )
    box = db.scalars(select(Box).where(Box.name == "Box 9")).one()
    pages = db.scalars(
        select(Page).where(Page.box_id == box.id).order_by(Page.id)
    ).all()
    client.post(
        f"/boxes/{box.id}/discard",
        data={"discard": [str(pages[0].id), str(pages[1].id)]},
    )
    db.expire_all()
    return pages


def confirm_form(page):
    """The ids the confirmation page carries in its hidden fields."""
    return {
        "document": re.findall(r'name="document" value="(\d+)"', page),
        "page": re.findall(r'name="page" value="(\d+)"', page),
    }


def all_files(data_dir):
    return {p.relative_to(data_dir) for p in data_dir.rglob("*") if p.is_file()}


# --- D4: the confirmation page deletes nothing ---


def test_d4_empty_bin_asks_first_and_lists_every_item(
    client, db, data_dir, binned, lone_photos
):
    documents = [binned(f"INV-{n}") for n in (1, 2, 3)]
    before = all_files(data_dir)

    page = text(client.get("/bin/empty"))

    assert "This cannot be undone" in page
    assert LEGAL_NOTE in page
    assert "Yes, destroy these 5 items permanently" in page
    assert "Cancel" in page
    for document in documents:
        assert document.filed_name in page
    assert lone_photos[0].original_filename in page
    assert lone_photos[1].original_filename in page
    assert lone_photos[2].original_filename not in page  # still in the inbox
    ids = confirm_form(html.unescape(client.get("/bin/empty").get_data(as_text=True)))
    assert len(ids["document"]) == 3 and len(ids["page"]) == 2
    # Nothing was deleted.
    assert all_files(data_dir) == before
    assert db.scalars(select(DisposalRecord)).all() == []
    assert len(db.scalars(select(Document)).all()) == 3


def test_the_bin_offers_empty_bin_only_when_it_holds_something(client, binned):
    assert "Empty bin" not in text(client.get("/bin"))

    binned()

    assert 'href="/bin/empty"' in text(client.get("/bin"))
    assert "Empty bin…" in text(client.get("/bin"))


def test_the_confirmation_page_for_an_empty_bin_goes_back_to_the_bin(client):
    response = client.get("/bin/empty", follow_redirects=True)

    assert "The Bin is empty" in text(response)


def test_the_confirmation_is_worded_in_the_singular_for_one_item(client, binned):
    binned()

    assert "Yes, destroy this item permanently" in text(client.get("/bin/empty"))


# --- D5: confirm ---


def test_d5_confirming_destroys_everything_but_a_record_per_document(
    client, db, data_dir, paths, binned, lone_photos
):
    documents = [binned(f"INV-{n}") for n in (1, 2, 3)]
    kept_photo = lone_photos[2]
    kept_files = {Path(kept_photo.photo_path), Path(kept_photo.thumb_path)}
    form = confirm_form(text(client.get("/bin/empty")))

    response = client.post("/bin/empty", data=form, follow_redirects=True)

    assert (
        "3 documents and 2 photos destroyed. "
        "A disposal record was kept for each document." in text(response)
    )
    db.expire_all()
    # No Document, StateChange rows for them, and Page rows only for the kept photo.
    assert db.scalars(select(Document)).all() == []
    assert [p.id for p in db.scalars(select(Page))] == [kept_photo.id]
    remaining = db.scalars(select(StateChange)).all()
    assert {(r.object_kind, r.object_id) for r in remaining} == {
        ("page", kept_photo.id)
    }
    # No files except the photo that was never in the bin.
    left = {p for p in all_files(data_dir) if p.parts[0] not in ("logs",)}
    left.discard(Path("app.db"))
    assert left == kept_files
    assert len(db.scalars(select(DisposalRecord)).all()) == 3
    assert documents  # ids were real


def test_each_record_has_exactly_the_spec_fields_and_the_documents_values(
    client, db, binned
):
    document = binned("INV-1043")
    page_count = len(document.pages)
    client.post("/bin/empty", data=confirm_form(text(client.get("/bin/empty"))))

    columns = {c.name for c in DisposalRecord.__table__.columns}
    assert columns == SPEC_RECORD_FIELDS
    (record,) = db.scalars(select(DisposalRecord)).all()
    assert record.filed_name == "2021-03-14 Invoice INV-1043.pdf"
    assert record.doc_type_label == "Invoice"
    assert (record.client_ref, record.client_name) == (
        "C-0042",
        "Hollybrook Bakery Ltd",
    )
    assert record.document_date == date(2021, 3, 14)
    assert record.keep_until == date(2026, 10, 26)
    assert record.page_count == page_count == 2
    assert record.binned_at == FIXED_NOW
    assert record.destroyed_at == FIXED_NOW


def test_a_document_filed_with_a_2_suffix_keeps_it_in_its_record(client, db, binned):
    binned(clash=True)
    client.post("/bin/empty", data=confirm_form(text(client.get("/bin/empty"))))

    (record,) = db.scalars(select(DisposalRecord)).all()

    assert record.filed_name == "2021-03-14 Invoice INV-1043 (2).pdf"


def test_there_are_no_records_for_photos(client, db, lone_photos):
    client.post("/bin/empty", data=confirm_form(text(client.get("/bin/empty"))))

    assert db.scalars(select(DisposalRecord)).all() == []
    assert [p.id for p in db.scalars(select(Page))] == [lone_photos[2].id]


def test_the_message_is_worded_for_one_photo_and_for_documents_only(
    client, db, binned, lone_photos
):
    # Two photos and no documents: no sentence about records.
    response = client.post(
        "/bin/empty",
        data=confirm_form(text(client.get("/bin/empty"))),
        follow_redirects=True,
    )
    page = text(response)
    assert "2 photos destroyed." in page
    assert "disposal record" not in page

    binned()
    response = client.post(
        "/bin/empty",
        data=confirm_form(text(client.get("/bin/empty"))),
        follow_redirects=True,
    )
    assert (
        "1 document destroyed. A disposal record was kept for each document."
        in text(response)
    )


def test_destroying_the_documents_writes_nothing_to_disk_before_the_rows_go(
    client, db, data_dir, binned
):
    """The files are deleted after the commit, so a failed commit loses no files."""
    document = binned()
    form = confirm_form(text(client.get("/bin/empty")))
    assert (data_dir / "bin" / f"{document.id}.pdf").is_file()

    client.post("/bin/empty", data=form)

    assert not (data_dir / "bin" / f"{document.id}.pdf").exists()
    assert not (data_dir / "work" / f"{document.id}.txt").exists()


# --- B5: a destroyed photo can be uploaded again ---


def test_b5_a_destroyed_photo_can_be_uploaded_again(client, db, lone_photos):
    client.post("/bin/empty", data=confirm_form(text(client.get("/bin/empty"))))

    response = client.post(
        "/upload",
        data={
            "choice": "new",
            "new_box_name": "Box 10",
            "photos": [(io.BytesIO(photo_bytes("P1")), "IMG_0001.jpg")],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert "1 photo added" in text(response)
    assert "skipped" not in text(response)


# --- D6: only what was confirmed ---


def test_d6_an_item_binned_after_the_page_was_opened_is_not_destroyed(
    client, db, data_dir, binned
):
    first_id = binned("INV-1").id
    form = confirm_form(text(client.get("/bin/empty")))
    second = binned("INV-2")  # binned after the confirmation page was opened

    response = client.post("/bin/empty", data=form, follow_redirects=True)

    assert "1 document destroyed" in text(response)
    db.expire_all()
    assert db.get(Document, first_id) is None
    assert db.get(Document, second.id).state == DocState.IN_BIN
    assert (data_dir / "bin" / f"{second.id}.pdf").is_file()
    assert len(db.scalars(select(DisposalRecord)).all()) == 1


def test_d6_an_item_restored_after_the_page_was_opened_is_not_destroyed(
    client, db, data_dir, binned
):
    document = binned()
    form = confirm_form(text(client.get("/bin/empty")))
    client.post(f"/documents/{document.id}/restore")

    response = client.post("/bin/empty", data=form, follow_redirects=True)

    assert "Nothing to destroy" in text(response)
    db.expire_all()
    assert db.get(Document, document.id).state == DocState.FILED
    assert db.scalars(select(DisposalRecord)).all() == []


def test_a_post_with_no_ids_destroys_nothing(client, binned, db):
    binned()

    response = client.post("/bin/empty", follow_redirects=True)

    assert "Nothing to destroy" in text(response)
    assert len(db.scalars(select(Document)).all()) == 1


def test_a_crafted_post_naming_a_filed_document_does_not_destroy_it(
    client, db, make_document
):
    document = make_document()

    response = client.post(
        "/bin/empty", data={"document": str(document.id)}, follow_redirects=True
    )

    assert "Nothing to destroy" in text(response)
    db.expire_all()
    assert db.get(Document, document.id).state == DocState.FILED
