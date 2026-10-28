import html
from datetime import date

import pytest
import texts
from conftest import FIXED_NOW
from sqlalchemy import select

from docmanager.errors import UserFacingError
from docmanager.lifecycle import InvalidTransition
from docmanager.models.box import Batch, Box
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.models.page import Page
from docmanager.models.records import StateChange
from docmanager.services import filing
from docmanager.services.filing import FilingError

INVOICE_PATH = "C-0042 Hollybrook Bakery Ltd/Invoices/2021-03-14 Invoice INV-2222.pdf"
LETTER_PATH = (
    "C-0042 Hollybrook Bakery Ltd/Letters/2022-05-05 Letter Year end paperwork.pdf"
)
PDF_BYTES = b"%PDF-1.4 the work copy"


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


@pytest.fixture
def paths(app):
    return app.config["PATHS"]


@pytest.fixture
def hollybrook(db):
    client = Client(ref="C-0042", name="Hollybrook Bakery Ltd", created_at=FIXED_NOW)
    db.add(client)
    db.commit()
    return client


@pytest.fixture
def other_client(db):
    client = Client(ref="C-0007", name="Ashgrove Dental Practice", created_at=FIXED_NOW)
    db.add(client)
    db.commit()
    return client


@pytest.fixture
def make_flagged(db, data_dir):
    """A document in Needs checking, built the way the app builds one (group, then flag)."""

    def make(
        *,
        doc_id=17,
        doc_type=None,
        fields=None,
        document_date=None,
        client=None,
        text=texts.REVIEW_TEXT,
        box=None,
    ):
        box = (
            box
            or db.scalars(select(Box)).first()
            or Box(name="Box 1", created_at=FIXED_NOW)
        )
        document = Document(
            id=doc_id,
            box=box,
            ocr_text=text,
            doc_type=doc_type,
            fields=fields or {},
            document_date=document_date,
            client=client,
            review_reasons=["Couldn't tell what type this is"],
            pdf_path=f"work/{doc_id}.pdf",
            created_at=FIXED_NOW,
        )
        batch = Batch(
            box=box,
            uploaded_at=FIXED_NOW,
            added_count=2,
            skipped_count=0,
            refused_count=0,
        )
        db.add_all([document, batch])
        document.apply("group", now=FIXED_NOW)
        for position, name in enumerate(("a.jpg", "b.jpg"), start=1):
            page = Page(
                box=box,
                batch=batch,
                sha256=f"sha-{doc_id}-{position}",
                original_filename=name,
                photo_path="photos/x.jpg",
                thumb_path="thumbs/x.jpg",
                document=document,
                position=position,
            )
            page._state = "grouped"  # tests may set the state directly
            db.add(page)
        document.apply("flag", now=FIXED_NOW)
        db.commit()
        work = data_dir / f"work/{doc_id}.pdf"
        work.parent.mkdir(parents=True, exist_ok=True)
        work.write_bytes(PDF_BYTES)
        return document

    return make


def confirm(
    db, paths, document, *, type_key=None, client=None, posted=None, shown=None, **kw
):
    """Call confirm_document the way the Check screen does: shown values, then edits."""
    shown = filing.shown_values(document) if shown is None else shown
    posted = {**shown, **(posted or {})}
    result = filing.confirm_document(
        db,
        document,
        type_key=type_key,
        client_id=client.id if client else None,
        posted=posted,
        shown=shown,
        paths=paths,
        now=FIXED_NOW,
        **kw,
    )
    db.commit()
    return result


def history(db, document):
    rows = db.scalars(
        select(StateChange)
        .where(
            StateChange.object_kind == "document", StateChange.object_id == document.id
        )
        .order_by(StateChange.id)
    ).all()
    return [(r.action, r.from_state, r.to_state) for r in rows]


# --- C8: confirm in review ---


def test_c8_picking_a_type_and_client_files_the_document(
    db, paths, data_dir, hollybrook, make_flagged
):
    document = make_flagged()  # no type, no client: it was flagged

    result = confirm(db, paths, document, type_key="invoice", client=hollybrook)

    assert result.message() == "Filed as 2021-03-14 Invoice INV-2222"
    db.expire_all()
    assert document.state == DocState.FILED
    assert document.doc_type == "invoice"
    assert document.client.ref == "C-0042"
    # change_type read the invoice fields and date again from the text.
    assert document.fields == {"invoice_number": "INV-2222", "amount_pence": 4550}
    assert document.document_date == date(2021, 3, 14)
    assert document.filed_name == "2021-03-14 Invoice INV-2222.pdf"
    assert document.filed_at == FIXED_NOW
    assert document.pdf_path == f"archive/{INVOICE_PATH}"
    assert (data_dir / "archive" / INVOICE_PATH).read_bytes() == PDF_BYTES
    assert not (data_dir / "work" / "17.pdf").exists()  # moved, not copied


def test_c8_the_documents_history_gains_one_confirm(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged()

    confirm(db, paths, document, type_key="invoice", client=hollybrook)

    assert history(db, document) == [
        ("group", None, "grouped"),
        ("flag", "grouped", "needs_review"),
        ("confirm", "needs_review", "filed"),
    ]


def test_the_stored_type_and_client_are_used_when_none_are_posted(
    db, paths, hollybrook, make_flagged
):
    # A document flagged only for too little text already has its type and client.
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )

    confirm(db, paths, document)  # no type, no client posted

    assert document.state == DocState.FILED


# --- C9: swapping the type keeps the document ---


def test_c9_changing_the_type_to_letter_keeps_id_pages_and_history(
    db, paths, data_dir, hollybrook, make_flagged
):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )
    page_ids = [p.id for p in document.pages]

    confirm(db, paths, document, type_key="letter", client=hollybrook)

    db.expire_all()
    same = db.get(Document, 17)
    assert same is document and same.id == 17
    assert [p.id for p in same.pages] == page_ids
    assert history(db, same) == [
        ("group", None, "grouped"),
        ("flag", "grouped", "needs_review"),
        ("confirm", "needs_review", "filed"),
    ]
    # The fields are now the letter's, and none of the invoice's are left behind.
    assert same.doc_type == "letter"
    assert same.fields == {"subject": "Year end paperwork"}
    assert same.document_date == date(2022, 5, 5)
    assert (data_dir / "archive" / LETTER_PATH).is_file()


# --- Decision 13: which values win ---


def test_changing_the_type_with_a_typed_subject_keeps_the_typed_subject(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )

    confirm(
        db,
        paths,
        document,
        type_key="letter",
        client=hollybrook,
        posted={"subject": "My own subject"},
    )

    assert document.fields == {
        "subject": "My own subject"
    }  # typed, not "Year end paperwork"
    assert document.document_date == date(2022, 5, 5)  # not typed: read again
    assert document.filed_name == "2022-05-05 Letter My own subject.pdf"


def test_changing_the_type_with_a_typed_date_keeps_the_typed_date(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )

    confirm(
        db,
        paths,
        document,
        type_key="letter",
        client=hollybrook,
        posted={"date": "01/02/2020"},
    )

    assert document.document_date == date(2020, 2, 1)  # typed
    assert document.fields == {"subject": "Year end paperwork"}  # not typed: read again


def test_with_no_type_change_the_typed_values_are_saved(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )

    confirm(
        db,
        paths,
        document,
        type_key="invoice",
        client=hollybrook,
        posted={
            "invoice_number": "INV-9999",
            "amount_pence": "£99.99",
            "date": "2 February 2021",
        },
    )

    assert document.fields == {"invoice_number": "INV-9999", "amount_pence": 9999}
    assert document.document_date == date(2021, 2, 2)
    assert document.filed_name == "2021-02-02 Invoice INV-9999.pdf"


def test_values_that_were_not_changed_keep_their_stored_values_not_a_fresh_reading(
    db, paths, hollybrook, make_flagged
):
    # The stored value differs from what the text says; the person left it alone.
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "STORED-1", "amount_pence": 100},
        document_date=date(2020, 1, 1),
    )

    confirm(db, paths, document, type_key="invoice", client=hollybrook)

    assert document.fields == {"invoice_number": "STORED-1", "amount_pence": 100}
    assert document.document_date == date(2020, 1, 1)


def test_clearing_a_value_removes_it(db, paths, hollybrook, make_flagged):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )

    confirm(
        db,
        paths,
        document,
        type_key="invoice",
        client=hollybrook,
        posted={"invoice_number": "", "date": ""},
    )

    assert document.fields == {"invoice_number": None, "amount_pence": 4550}
    assert document.document_date is None
    assert document.filed_name == "undated Invoice no number.pdf"


def test_typed_values_for_another_types_fields_are_ignored(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged()

    confirm(
        db,
        paths,
        document,
        type_key="invoice",
        client=hollybrook,
        posted={"subject": "typed in the wrong box"},
    )

    assert "subject" not in document.fields


def test_a_missing_posted_value_counts_as_not_changed(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )
    shown = filing.shown_values(document)

    filing.confirm_document(
        db,
        document,
        type_key="invoice",
        client_id=hollybrook.id,
        posted={},  # a crafted form with nothing in it
        shown=shown,
        paths=paths,
        now=FIXED_NOW,
    )

    assert document.fields == {"invoice_number": "INV-2222", "amount_pence": 4550}


def test_the_client_can_be_changed_in_review(
    db, paths, hollybrook, other_client, make_flagged
):
    document = make_flagged(doc_type="invoice", client=hollybrook)

    confirm(db, paths, document, type_key="invoice", client=other_client)

    assert document.client.ref == "C-0007"
    assert document.pdf_path.startswith("archive/C-0007 Ashgrove Dental Practice/")


# --- C10 and the other refusals ---


def refusal(db, paths, document, **kw):
    with pytest.raises(UserFacingError) as problem:
        confirm(db, paths, document, **kw)
    return str(problem.value)


def test_c10_no_client_is_refused_with_the_guard_wording(db, paths, make_flagged):
    document = make_flagged()

    message = refusal(db, paths, document, type_key="invoice")

    assert message == "Choose a client before filing"


def test_no_type_is_refused_with_the_guard_wording(db, paths, hollybrook, make_flagged):
    document = make_flagged()

    assert (
        refusal(db, paths, document, client=hollybrook) == "Choose a type before filing"
    )


def test_the_type_is_reported_before_the_client(db, paths, make_flagged):
    assert refusal(db, paths, make_flagged()) == "Choose a type before filing"


def test_a_refusal_changes_nothing(db, paths, data_dir, make_flagged):
    document = make_flagged()
    before_changes = len(history(db, document))

    refusal(db, paths, document, type_key="invoice", posted={"invoice_number": "X-1"})

    assert document.state == DocState.NEEDS_REVIEW
    assert document.doc_type is None  # the swap was undone
    assert document.fields == {}
    assert document.document_date is None
    assert document.client is None
    assert len(history(db, document)) == before_changes
    assert (data_dir / "work" / "17.pdf").exists()
    assert not (data_dir / "archive").exists() or not any(
        (data_dir / "archive").iterdir()
    )


def test_a_type_that_does_not_exist_is_refused_as_no_type(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged()

    message = refusal(db, paths, document, type_key="payslip", client=hollybrook)

    assert message == "Choose a type before filing"


def test_a_client_that_does_not_exist_is_refused(db, paths, make_flagged):
    document = make_flagged()
    shown = filing.shown_values(document)

    with pytest.raises(FilingError) as problem:
        filing.confirm_document(
            db,
            document,
            type_key="invoice",
            client_id=999,
            posted=shown,
            shown=shown,
            paths=paths,
            now=FIXED_NOW,
        )

    assert str(problem.value) == "That client isn't in your client list"


@pytest.mark.parametrize(
    "posted,message",
    [
        (
            {"date": "banana"},
            'Couldn\'t read the date "banana". Write it like 14/03/2021',
        ),
        (
            {"date": "14/03/2021 and more"},
            'Couldn\'t read the date "14/03/2021 and more". Write it like 14/03/2021',
        ),
        ({"date": "14/03/2031"}, "The date can't be after today"),
        ({"amount_pence": "lots"}, "Amount due must be a number like 120.00"),
        ({"amount_pence": "-5"}, "Amount due must be a number like 120.00"),
    ],
)
def test_a_typed_value_that_cannot_be_read_is_refused_and_nothing_changes(
    db, paths, hollybrook, make_flagged, posted, message
):
    document = make_flagged()

    assert (
        refusal(
            db, paths, document, type_key="invoice", client=hollybrook, posted=posted
        )
        == message
    )
    assert document.state == DocState.NEEDS_REVIEW
    assert document.doc_type is None


@pytest.mark.parametrize("state", [DocState.FILED, DocState.GROUPED, DocState.IN_BIN])
def test_only_a_document_in_review_can_be_confirmed(
    db, paths, hollybrook, make_flagged, state
):
    document = make_flagged()
    document._state = state.value  # tests may set the state directly
    db.commit()

    message = refusal(db, paths, document, type_key="invoice", client=hollybrook)

    assert message == f'This document can\'t be confirmed while it is "{state.label}"'


def test_a_missing_work_pdf_is_refused_politely(
    db, paths, data_dir, hollybrook, make_flagged
):
    document = make_flagged()
    (data_dir / "work" / "17.pdf").unlink()

    message = refusal(db, paths, document, type_key="invoice", client=hollybrook)

    assert message == "The PDF file is missing, so this document can't be filed"
    assert document.state == DocState.NEEDS_REVIEW


def test_an_error_is_both_a_filing_error_and_an_invalid_transition_for_the_guards():
    assert issubclass(FilingError, UserFacingError)
    assert issubclass(InvalidTransition, UserFacingError)


# --- A name clash while confirming ---


def test_confirming_into_an_existing_name_gets_a_2_suffix(
    db, paths, data_dir, hollybrook, make_flagged
):
    first = make_flagged(doc_id=17)
    second = make_flagged(doc_id=18)
    confirm(db, paths, first, type_key="invoice", client=hollybrook)

    confirm(db, paths, second, type_key="invoice", client=hollybrook)

    assert second.filed_name == "2021-03-14 Invoice INV-2222 (2).pdf"
    assert (data_dir / "archive" / INVOICE_PATH.replace(".pdf", " (2).pdf")).is_file()


# --- What the screen shows (the values the form carries as "shown") ---


def test_shown_values_are_the_stored_values_as_a_person_would_type_them(
    hollybrook, make_flagged
):
    document = make_flagged(
        doc_type="invoice",
        client=hollybrook,
        fields={"invoice_number": "INV-2222", "amount_pence": 4550},
        document_date=date(2021, 3, 14),
    )

    assert filing.shown_values(document) == {
        "date": "14/03/2021",
        "invoice_number": "INV-2222",
        "amount_pence": "45.50",
        "subject": "",  # another type's field: shown empty
    }


def test_shown_values_for_a_document_with_nothing_are_all_empty(make_flagged):
    document = make_flagged()

    assert filing.shown_values(document) == {
        "date": "",
        "invoice_number": "",
        "amount_pence": "",
        "subject": "",
    }


def test_the_result_message_for_a_confirmed_document(
    db, paths, hollybrook, make_flagged
):
    document = make_flagged()

    result = confirm(db, paths, document, type_key="invoice", client=hollybrook)

    assert result.outcome == "filed"
    assert html.unescape(result.message()).startswith("Filed as ")
    assert db.scalars(select(Page).where(Page.document_id == 17)).all()
