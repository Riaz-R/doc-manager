"""The Page and Document lifecycles (AT-01 to AT-04) and their guards."""

from datetime import date
from itertools import count, product

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from docmanager.lifecycle import InvalidTransition
from docmanager.models.box import Batch, Box
from docmanager.models.client import Client
from docmanager.models.document import DOC_LIFECYCLE, DocState, Document
from docmanager.models.page import PAGE_LIFECYCLE, Page, PageState
from docmanager.models.records import StateChange
from docmanager.rules.dates import format_date

# The spec's lifecycle tables, written out as plain text (SPEC 3.3 and 3.4).
# None on the left is "(new)"; None on the right is "(row deleted)".
SPEC_PAGE_ROWS = {
    (None, "upload"): "inbox",
    ("inbox", "group"): "grouped",
    ("inbox", "discard"): "discarded",
    ("discarded", "restore"): "inbox",
    ("grouped", "destroy"): None,
    ("discarded", "destroy"): None,
}
SPEC_DOC_ROWS = {
    (None, "group"): "grouped",
    ("grouped", "file"): "filed",
    ("grouped", "flag"): "needs_review",
    ("needs_review", "confirm"): "filed",
    ("filed", "dispose"): "in_bin",
    ("in_bin", "restore"): "filed",
    ("in_bin", "destroy"): None,
}

PAGE_PAIRS = list(
    product([None, *PageState], ["upload", "group", "discard", "restore", "destroy"])
)
DOC_PAIRS = list(
    product(
        [None, *DocState],
        ["group", "file", "flag", "confirm", "dispose", "restore", "destroy"],
    )
)

_numbers = count(1)


def plain(table):
    """A lifecycle's table with the enums turned back into plain text."""
    return {
        (s.value if s else None, action): (t.value if t else None)
        for (s, action), t in table.items()
    }


def make_box(session, now):
    box = Box(name=f"Box {next(_numbers)}", created_at=now)
    session.add(box)
    session.flush()
    return box


def make_page(session, now, state=None):
    box = make_box(session, now)
    batch = Batch(
        box=box, uploaded_at=now, added_count=1, skipped_count=0, refused_count=0
    )
    n = next(_numbers)
    page = Page(
        box=box,
        batch=batch,
        sha256=f"{n:064d}",
        original_filename=f"IMG_{n:04d}.jpg",
        photo_path=f"photos/{box.id}/{n}.jpg",
        thumb_path=f"thumbs/{box.id}/{n}.jpg",
    )
    if state:
        page._state = state.value  # tests may set the state directly
    session.add(page)
    return page


def make_document(session, now, state=None, **overrides):
    """A document that satisfies every guard unless an override says otherwise."""
    box = make_box(session, now)
    client = Client(
        ref=f"C-{next(_numbers):04d}", name=f"Client {next(_numbers)}", created_at=now
    )
    fields = {
        "box": box,
        "client": client,
        "doc_type": "invoice",
        "ocr_text": "some words that were read from the photos",
        "keep_until": date(2026, 10, 26),  # the day before the fixed "today"
    }
    fields.update(overrides)
    document = Document(**fields)
    if state:
        document._state = state.value
    session.add(document)
    return document


def count_changes(session):
    return session.scalar(select(func.count()).select_from(StateChange))


# --- AT-01: the tables match the spec, and every other pair is refused --------


def test_page_table_is_copied_exactly_from_the_spec():
    assert plain(PAGE_LIFECYCLE.transitions) == SPEC_PAGE_ROWS


def test_document_table_is_copied_exactly_from_the_spec():
    assert plain(DOC_LIFECYCLE.transitions) == SPEC_DOC_ROWS


@pytest.mark.parametrize("state, action", PAGE_PAIRS, ids=lambda v: str(v))
def test_every_page_state_and_action_pair(session, now, state, action):
    page = make_page(session, now, state)
    before = count_changes(session)
    key = (state.value if state else None, action)

    if key in SPEC_PAGE_ROWS:
        page.apply(action, now=now)
        expected = SPEC_PAGE_ROWS[key]
        # A move to "(row deleted)" leaves the state as it was.
        assert page.state.value == (expected or state.value)
        assert count_changes(session) == before + 1
    else:
        with pytest.raises(InvalidTransition):
            page.apply(action, now=now)
        assert count_changes(session) == before


@pytest.mark.parametrize("state, action", DOC_PAIRS, ids=lambda v: str(v))
def test_every_document_state_and_action_pair(session, now, state, action):
    document = make_document(session, now, state)
    before = count_changes(session)
    key = (state.value if state else None, action)

    if key in SPEC_DOC_ROWS:
        document.apply(action, now=now)
        expected = SPEC_DOC_ROWS[key]
        assert document.state.value == (expected or state.value)
        assert count_changes(session) == before + 1
    else:
        with pytest.raises(InvalidTransition):
            document.apply(action, now=now)
        assert count_changes(session) == before


def test_the_plans_own_example_message_for_a_document_that_cannot_be_binned(
    session, now
):
    document = make_document(session, now, DocState.NEEDS_REVIEW)

    with pytest.raises(InvalidTransition) as problem:
        document.apply("dispose", now=now)

    assert (
        str(problem.value)
        == 'This document can\'t be moved to the bin while it is "Needs checking"'
    )


# --- AT-02: every guard, word for word ----------------------------------------


@pytest.mark.parametrize(
    "state, action", [(DocState.GROUPED, "file"), (DocState.NEEDS_REVIEW, "confirm")]
)
class TestFilingGuards:
    def refusal(self, session, now, state, action, **overrides):
        document = make_document(session, now, state, **overrides)
        with pytest.raises(InvalidTransition) as problem:
            document.apply(action, now=now)
        assert document.state == state  # nothing changed
        return str(problem.value)

    def test_not_read_yet(self, session, now, state, action):
        message = self.refusal(session, now, state, action, ocr_text=None)
        assert message == "This document hasn't been read yet"

    def test_no_type(self, session, now, state, action):
        message = self.refusal(session, now, state, action, doc_type=None)
        assert message == "Choose a type before filing"

    def test_no_client(self, session, now, state, action):
        message = self.refusal(session, now, state, action, client=None)
        assert message == "Choose a client before filing"

    def test_not_read_is_reported_before_type_and_client(
        self, session, now, state, action
    ):
        message = self.refusal(
            session, now, state, action, ocr_text=None, doc_type=None, client=None
        )
        assert message == "This document hasn't been read yet"

    def test_type_is_reported_before_client(self, session, now, state, action):
        message = self.refusal(session, now, state, action, doc_type=None, client=None)
        assert message == "Choose a type before filing"

    def test_read_with_type_and_client_goes_through(self, session, now, state, action):
        document = make_document(session, now, state)
        document.apply(action, now=now)
        assert document.state == DocState.FILED


def test_read_text_that_is_empty_still_counts_as_read(session, now):
    # "Very little text" is a separate check (Task 11); the guard only asks whether OCR ran.
    document = make_document(session, now, DocState.GROUPED, ocr_text="")
    document.apply("file", now=now)
    assert document.state == DocState.FILED


def test_flag_guard_refuses_an_unread_document(session, now):
    document = make_document(session, now, DocState.GROUPED, ocr_text=None)

    with pytest.raises(InvalidTransition) as problem:
        document.apply("flag", now=now)

    assert str(problem.value) == "This document hasn't been read yet"


def test_flag_guard_accepts_a_read_document_even_without_type_or_client(session, now):
    document = make_document(session, now, DocState.GROUPED, doc_type=None, client=None)
    document.apply("flag", now=now)
    assert document.state == DocState.NEEDS_REVIEW


def test_dispose_guard_names_the_keep_until_date(session, now):
    document = make_document(session, now, DocState.FILED, keep_until=date(2027, 3, 14))

    with pytest.raises(InvalidTransition) as problem:
        document.apply("dispose", now=now)

    assert str(problem.value) == "This document must be kept until 14 Mar 2027"
    assert document.state == DocState.FILED


def test_dispose_guard_with_no_keep_until(session, now):
    document = make_document(session, now, DocState.FILED, keep_until=None)

    with pytest.raises(InvalidTransition) as problem:
        document.apply("dispose", now=now)

    assert str(problem.value) == "Keep-until not set – add the document's date"


def test_a_document_is_kept_through_its_keep_until_day(session, now):
    # now is 2026-10-27, so keep_until of today is still "kept"; yesterday is due.
    on_the_day = make_document(
        session, now, DocState.FILED, keep_until=date(2026, 10, 27)
    )
    with pytest.raises(InvalidTransition):
        on_the_day.apply("dispose", now=now)

    day_after = make_document(
        session, now, DocState.FILED, keep_until=date(2026, 10, 26)
    )
    day_after.apply("dispose", now=now)
    assert day_after.state == DocState.IN_BIN


def test_is_due_follows_the_same_rule(session, now):
    today = now.date()
    due = make_document(session, now, DocState.FILED, keep_until=date(2026, 10, 26))
    kept = make_document(session, now, DocState.FILED, keep_until=date(2026, 10, 27))
    undated = make_document(session, now, DocState.FILED, keep_until=None)
    not_filed = make_document(
        session, now, DocState.IN_BIN, keep_until=date(2020, 1, 1)
    )

    assert due.is_due(today)
    assert not kept.is_due(today)
    assert not undated.is_due(today)
    assert not not_filed.is_due(today)


def test_allowed_actions_ignore_guards(session, now):
    # A document that isn't due still lists the action, so the button shows and then refuses.
    document = make_document(session, now, DocState.FILED, keep_until=date(2030, 1, 1))
    assert document.allowed_actions() == ["dispose"]


def test_format_date_uses_day_short_month_year():
    assert format_date(date(2027, 3, 14)) == "14 Mar 2027"
    assert format_date(date(2026, 1, 5)) == "5 Jan 2026"
    assert format_date(date(2026, 12, 31)) == "31 Dec 2026"


# --- AT-03: exactly one StateChange per transition ----------------------------


def history(session, kind, object_id):
    rows = session.scalars(
        select(StateChange)
        .where(StateChange.object_kind == kind, StateChange.object_id == object_id)
        .order_by(StateChange.id)
    ).all()
    return [(r.action, r.from_state, r.to_state) for r in rows]


def test_a_document_writes_one_state_change_per_move(session, now):
    document = make_document(session, now)
    for action in ["group", "flag", "confirm", "dispose", "restore"]:
        before = count_changes(session)
        document.apply(action, now=now)
        assert count_changes(session) == before + 1

    # Move to the bin again and destroy it: the last move is recorded as "(row deleted)".
    document.apply("dispose", now=now)
    document.apply("destroy", now=now)

    assert history(session, "document", document.id) == [
        ("group", None, "grouped"),
        ("flag", "grouped", "needs_review"),
        ("confirm", "needs_review", "filed"),
        ("dispose", "filed", "in_bin"),
        ("restore", "in_bin", "filed"),
        ("dispose", "filed", "in_bin"),
        ("destroy", "in_bin", None),
    ]


def test_a_page_writes_one_state_change_per_move(session, now):
    page = make_page(session, now)
    for action in ["upload", "discard", "restore", "group", "destroy"]:
        before = count_changes(session)
        page.apply(action, now=now)
        assert count_changes(session) == before + 1

    assert history(session, "page", page.id) == [
        ("upload", None, "inbox"),
        ("discard", "inbox", "discarded"),
        ("restore", "discarded", "inbox"),
        ("group", "inbox", "grouped"),
        ("destroy", "grouped", None),
    ]


def test_a_refused_move_writes_nothing(session, now):
    document = make_document(session, now, DocState.FILED, keep_until=date(2030, 1, 1))
    before = count_changes(session)

    with pytest.raises(InvalidTransition):
        document.apply("dispose", now=now)

    assert count_changes(session) == before


# --- AT-04: no setter ----------------------------------------------------------


def test_page_state_cannot_be_set(session, now):
    page = make_page(session, now, PageState.INBOX)
    with pytest.raises(AttributeError):
        page.state = PageState.GROUPED
    assert page.state == PageState.INBOX


def test_document_state_cannot_be_set(session, now):
    document = make_document(session, now, DocState.GROUPED)
    with pytest.raises(AttributeError):
        document.state = DocState.FILED
    assert document.state == DocState.GROUPED


# --- Labels --------------------------------------------------------------------


def test_page_state_labels():
    assert {s.value: s.label for s in PageState} == {
        "inbox": "To sort",
        "grouped": "In a document",
        "discarded": "Not a page (in bin)",
    }


def test_document_state_labels(session, now):
    labels = {}
    for state in DocState:
        labels[state.value] = make_document(session, now, state).state_label
    assert labels == {
        "grouped": "Not read yet",
        "needs_review": "Needs checking",
        "filed": "Filed",
        "in_bin": "In bin",
    }


def test_a_grouped_document_with_an_ocr_error_says_it_couldnt_be_read(session, now):
    document = make_document(
        session,
        now,
        DocState.GROUPED,
        ocr_text=None,
        ocr_error="Couldn't read this document. Try again, or retake the photos.",
    )
    assert document.state_label == "Couldn't read"


# --- The models hold every field in the spec ----------------------------------


def test_a_document_round_trips_every_field(session, now):
    document = make_document(
        session,
        now,
        DocState.FILED,
        fields={"invoice_number": "INV-1043", "amount_pence": 12000},
        document_date=date(2021, 3, 14),
        type_score=9,
        runner_up_score=2,
        review_reasons=["Couldn't tell what type this is"],
        pdf_path="archive/x.pdf",
        filed_name="2021-03-14 Invoice INV-1043.pdf",
        created_at=now,
        filed_at=now,
        binned_at=None,
    )
    session.commit()
    session.expire_all()

    loaded = session.get(Document, document.id)
    assert loaded.fields == {"invoice_number": "INV-1043", "amount_pence": 12000}
    assert loaded.document_date == date(2021, 3, 14)
    assert loaded.keep_until == date(2026, 10, 26)
    assert loaded.type_score == 9
    assert loaded.runner_up_score == 2
    assert loaded.review_reasons == ["Couldn't tell what type this is"]
    assert loaded.pdf_path == "archive/x.pdf"
    assert loaded.filed_name == "2021-03-14 Invoice INV-1043.pdf"
    assert loaded.created_at == now
    assert loaded.binned_at is None
    assert loaded.client.name.startswith("Client")
    assert loaded.box.id == loaded.box_id


def test_a_new_document_starts_with_empty_fields_and_reasons(session, now):
    document = Document(box=make_box(session, now))
    session.add(document)
    session.commit()
    assert document.fields == {}
    assert document.review_reasons == []
    assert document.doc_type is None
    assert document.state is None


def test_a_page_round_trips_every_field(session, now):
    page = make_page(session, now, PageState.INBOX)
    session.commit()
    session.expire_all()

    loaded = session.get(Page, page.id)
    assert loaded.state == PageState.INBOX
    assert loaded.document_id is None
    assert loaded.position is None
    assert loaded.batch.box_id == loaded.box_id
    assert loaded.original_filename.startswith("IMG_")


def test_pages_of_a_document_come_back_in_position_order(session, now):
    document = make_document(session, now, DocState.GROUPED)
    pages = [make_page(session, now, PageState.GROUPED) for _ in range(3)]
    for position, page in zip([3, 1, 2], pages):
        page.document = document
        page.position = position
    session.commit()
    session.expire_all()

    assert [p.position for p in session.get(Document, document.id).pages] == [1, 2, 3]


def test_box_batch_and_client_fields(session, now):
    box = make_box(session, now)
    batch = Batch(
        box=box, uploaded_at=now, added_count=38, skipped_count=2, refused_count=1
    )
    client = Client(ref="C-0042", name="Hollybrook Bakery Ltd", created_at=now)
    session.add_all([batch, client])
    session.commit()

    assert (batch.added_count, batch.skipped_count, batch.refused_count) == (38, 2, 1)
    assert box.batches == [batch]
    assert (client.ref, client.name, client.created_at) == (
        "C-0042",
        "Hollybrook Bakery Ltd",
        now,
    )


def test_names_refs_and_fingerprints_must_be_unique(session, now):
    session.add(Box(name="Box 1", created_at=now))
    session.commit()
    session.add(Box(name="Box 1", created_at=now))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(Client(ref="C-0001", name="A Ltd", created_at=now))
    session.commit()
    session.add(Client(ref="C-0001", name="B Ltd", created_at=now))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(Client(ref="C-0002", name="A Ltd", created_at=now))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    first = make_page(session, now)
    session.commit()
    twin = make_page(session, now)
    twin.sha256 = first.sha256
    with pytest.raises(IntegrityError):
        session.commit()


def test_the_app_creates_every_table(app):
    from sqlalchemy import inspect

    tables = set(inspect(app.extensions["docmanager_engine"]).get_table_names())
    assert {
        "boxes",
        "batches",
        "clients",
        "pages",
        "documents",
        "state_changes",
    } <= tables
