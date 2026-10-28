import html

import pytest
from conftest import FIXED_NOW

from docmanager.models.box import Batch, Box
from docmanager.models.document import DocState, Document
from docmanager.models.page import Page, PageState

CAN_GO = "Paper can go"
SUFFIX = "before this paper can go"


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


@pytest.fixture
def make_box(db):
    """A box, filled by naming how many photos and documents it holds, and their states."""

    def make(name="Box 1", *, photos=(), documents=()):
        """`photos`: page states. `documents`: DocStates, or (DocState, ocr_error) pairs."""
        box = Box(name=name, created_at=FIXED_NOW)
        batch = Batch(
            box=box,
            uploaded_at=FIXED_NOW,
            added_count=0,
            skipped_count=0,
            refused_count=0,
        )
        db.add_all([box, batch])
        for number, state in enumerate(photos, start=1):
            page = Page(
                box=box,
                batch=batch,
                sha256=f"{name}-photo-{number}",
                original_filename=f"IMG_{number:04d}.jpg",
                photo_path="photos/x.jpg",
                thumb_path="thumbs/x.jpg",
            )
            page._state = state.value  # tests may set the state directly
            db.add(page)
        for item in documents:
            state, error = item if isinstance(item, tuple) else (item, None)
            document = Document(box=box, ocr_error=error, created_at=FIXED_NOW)
            document._state = state.value
            db.add(document)
        db.commit()
        return box

    return make


def home_text(client):
    return html.unescape(client.get("/").get_data(as_text=True))


# --- The rule, on the model ---


def test_p1_all_filed_and_nothing_in_the_inbox_means_paper_can_go(make_box):
    box = make_box(documents=[DocState.FILED, DocState.FILED])

    assert box.paper_can_go()
    assert box.paper_blockers() == []


def test_p5_not_a_page_photos_do_not_block(make_box):
    box = make_box(
        photos=[PageState.DISCARDED, PageState.GROUPED, PageState.GROUPED],
        documents=[DocState.FILED],
    )

    assert box.paper_can_go()


def test_documents_later_moved_to_the_bin_still_count_as_filed(make_box):
    box = make_box(documents=[DocState.FILED, DocState.IN_BIN])

    assert box.paper_can_go()


def test_p6_keep_until_is_never_asked_about(make_box, db):
    box = make_box(documents=[DocState.FILED])
    for document in box.documents:
        document.keep_until = FIXED_NOW.date().replace(year=2031)
    db.commit()

    assert box.paper_can_go()


def test_p2_a_photo_in_the_inbox_blocks(make_box):
    box = make_box(photos=[PageState.INBOX], documents=[DocState.FILED])

    assert not box.paper_can_go()
    assert box.paper_blockers() == [f"1 photo to sort {SUFFIX}"]


def test_p2_the_photo_line_is_plural_for_several(make_box):
    box = make_box(photos=[PageState.INBOX] * 3, documents=[DocState.FILED])

    assert box.paper_blockers() == [f"3 photos to sort {SUFFIX}"]


def test_p3_a_document_needing_checking_blocks(make_box):
    box = make_box(documents=[DocState.FILED, DocState.NEEDS_REVIEW])

    assert not box.paper_can_go()
    assert box.paper_blockers() == [f"1 document needs checking {SUFFIX}"]


def test_p3_the_checking_line_is_plural_for_several(make_box):
    box = make_box(documents=[DocState.NEEDS_REVIEW, DocState.NEEDS_REVIEW])

    assert box.paper_blockers() == [f"2 documents need checking {SUFFIX}"]


def test_p4_a_document_with_an_ocr_error_blocks(make_box):
    box = make_box(
        documents=[DocState.FILED, (DocState.GROUPED, "Couldn't read this document.")]
    )

    assert not box.paper_can_go()
    assert box.paper_blockers() == [f"1 document couldn't be read {SUFFIX}"]


def test_p4_the_couldnt_read_line_is_plural_for_several(make_box):
    box = make_box(documents=[(DocState.GROUPED, "x"), (DocState.GROUPED, "y")])

    assert box.paper_blockers() == [f"2 documents couldn't be read {SUFFIX}"]


def test_a_grouped_document_with_no_error_has_not_been_read_yet(make_box):
    box = make_box(documents=[DocState.FILED, DocState.GROUPED])

    assert box.paper_blockers() == [f"1 document hasn't been read yet {SUFFIX}"]


def test_the_not_read_yet_line_is_plural_for_several(make_box):
    box = make_box(documents=[DocState.GROUPED, DocState.GROUPED])

    assert box.paper_blockers() == [f"2 documents haven't been read yet {SUFFIX}"]


def test_p7_a_box_with_photos_but_no_documents_is_blocked(make_box):
    box = make_box(photos=[PageState.INBOX, PageState.INBOX])

    assert not box.paper_can_go()
    assert box.paper_blockers() == [
        f"2 photos to sort {SUFFIX}",
        "Nothing filed from this box yet",
    ]


def test_p7_a_box_whose_photos_are_all_not_a_page_has_nothing_filed(make_box):
    box = make_box(photos=[PageState.DISCARDED])

    assert not box.paper_can_go()
    assert box.paper_blockers() == ["Nothing filed from this box yet"]


def test_an_empty_box_has_nothing_filed(make_box):
    box = make_box()

    assert not box.paper_can_go()
    assert box.paper_blockers() == ["Nothing filed from this box yet"]


def test_every_blocker_is_listed_in_a_fixed_order(make_box):
    box = make_box(
        photos=[PageState.INBOX],
        documents=[
            DocState.GROUPED,
            (DocState.GROUPED, "error"),
            DocState.NEEDS_REVIEW,
            DocState.FILED,
        ],
    )

    assert box.paper_blockers() == [
        f"1 photo to sort {SUFFIX}",
        f"1 document needs checking {SUFFIX}",
        f"1 document couldn't be read {SUFFIX}",
        f"1 document hasn't been read yet {SUFFIX}",
    ]


def test_nothing_in_the_bin_or_other_boxes_changes_a_boxs_answer(make_box):
    ready = make_box("Box 1", documents=[DocState.FILED])
    make_box("Box 2", photos=[PageState.INBOX], documents=[DocState.NEEDS_REVIEW])

    assert ready.paper_can_go()


# --- Home ---


def test_p1_home_shows_paper_can_go_beside_the_box(client, make_box):
    make_box("Box 1", documents=[DocState.FILED])

    body = home_text(client)

    assert CAN_GO in body
    assert "Box 1" in body
    assert SUFFIX not in body


def test_p5_p6_home_shows_paper_can_go_for_a_box_with_only_not_a_page_photos_left(
    client, make_box
):
    make_box("Box 1", photos=[PageState.DISCARDED], documents=[DocState.FILED])

    assert CAN_GO in home_text(client)


def test_p2_home_says_what_blocks_the_paper(client, make_box):
    make_box("Box 1", photos=[PageState.INBOX], documents=[DocState.FILED])

    body = home_text(client)

    assert CAN_GO not in body
    assert f"1 photo to sort {SUFFIX}" in body


def test_p3_home_says_a_document_needs_checking(client, make_box):
    make_box("Box 1", documents=[DocState.NEEDS_REVIEW])

    body = home_text(client)

    assert CAN_GO not in body
    assert f"1 document needs checking {SUFFIX}" in body


def test_p4_home_says_a_document_couldnt_be_read(client, make_box):
    make_box("Box 1", documents=[(DocState.GROUPED, "error")])

    body = home_text(client)

    assert CAN_GO not in body
    assert f"1 document couldn't be read {SUFFIX}" in body


def test_p7_home_says_nothing_is_filed_yet(client, make_box):
    make_box("Box 1", photos=[PageState.INBOX])

    body = home_text(client)

    assert CAN_GO not in body
    assert "Nothing filed from this box yet" in body
    assert f"1 photo to sort {SUFFIX}" in body


def test_home_shows_each_boxs_own_answer(client, make_box):
    make_box("Box 1", documents=[DocState.FILED])
    make_box("Box 2", documents=[DocState.NEEDS_REVIEW])

    body = home_text(client)
    box_1, box_2 = body.index("Box 1"), body.index("Box 2")

    assert CAN_GO in body[box_1:box_2]
    assert CAN_GO not in body[box_2:]
    assert f"1 document needs checking {SUFFIX}" in body[box_2:]
