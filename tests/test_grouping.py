import io

import pytest
from conftest import FIXED_NOW, photo_bytes
from sqlalchemy import func, select

from docmanager.models.box import Box
from docmanager.models.document import DocState, Document
from docmanager.models.page import PageState
from docmanager.models.records import StateChange


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


def upload(client, count, box_name="Box 1"):
    """Upload IMG_0001.jpg ... into a new box, so photo N is the Nth in filename order."""
    files = [
        (io.BytesIO(photo_bytes(f"IMG_{n:04d}")), f"IMG_{n:04d}.jpg")
        for n in range(1, count + 1)
    ]
    client.post(
        "/upload",
        data={"choice": "new", "new_box_name": box_name, "photos": files},
    )


def box_of(db, name="Box 1"):
    return db.scalars(select(Box).where(Box.name == name)).one()


def page_id(db, number, box_name="Box 1"):
    """The id of the photo with this inbox number (its place in filename order)."""
    return dict(box_of(db, box_name).ordered_pages())[number].id


def make_document(client, db, first, last, box_name="Box 1"):
    """Press Make document with the photos at inbox numbers `first` and `last`."""
    data = {}
    if first is not None:
        data["first"] = str(page_id(db, first, box_name))
    if last is not None:
        data["last"] = str(page_id(db, last, box_name))
    box = box_of(db, box_name)
    return client.post(
        f"/boxes/{box.id}/make-document", data=data, follow_redirects=True
    )


def numbers_in_state(db, state, box_name="Box 1"):
    db.expire_all()
    return [n for n, p in box_of(db, box_name).ordered_pages() if p.state == state]


def message(response):
    import html

    return html.unescape(response.text)


# --- AT-07: G1 to G5 ---


def test_g1_pages_3_to_6_become_a_grouped_document_and_leave_the_inbox(client, db):
    upload(client, 10)

    response = make_document(client, db, 3, 6)

    assert "Document made from photos 3 to 6" in message(response)
    document = db.scalars(select(Document)).one()
    assert document.state == DocState.GROUPED
    assert document.box_id == box_of(db).id
    assert document.created_at == FIXED_NOW
    assert [(p.position, p.state) for p in document.pages] == [
        (1, PageState.GROUPED),
        (2, PageState.GROUPED),
        (3, PageState.GROUPED),
        (4, PageState.GROUPED),
    ]
    assert numbers_in_state(db, PageState.GROUPED) == [3, 4, 5, 6]
    assert numbers_in_state(db, PageState.INBOX) == [1, 2, 7, 8, 9, 10]
    # The pages are in filename order, so position 1 is photo 3.
    assert [p.original_filename for p in document.pages] == [
        f"IMG_{n:04d}.jpg" for n in (3, 4, 5, 6)
    ]


def test_g1_the_inbox_shows_the_rest_and_lists_the_document_as_not_read_yet(client, db):
    upload(client, 10)
    make_document(client, db, 3, 6)
    document = db.scalars(select(Document)).one()

    html = client.get(f"/boxes/{box_of(db).id}/inbox").text

    for number in (1, 2, 7, 8, 9, 10):
        assert f'<span class="photo-number">{number}</span>' in html
    for number in (3, 4, 5, 6):
        assert f'<span class="photo-number">{number}</span>' not in html
    assert "Not read yet" in html
    assert f"Document {document.id}" in html
    assert "4 pages" in html


def test_a_document_is_listed_as_not_read_yet_even_when_the_inbox_is_empty(client, db):
    upload(client, 2)
    make_document(client, db, 1, 2)

    html = client.get(f"/boxes/{box_of(db).id}/inbox").text

    assert "No photos to sort in this box" in html
    assert "Not read yet" in html


def test_g2_one_page_document(client, db):
    upload(client, 10)

    response = make_document(client, db, 7, 7)

    assert "Document made from photo 7" in message(response)
    document = db.scalars(select(Document)).one()
    assert [(p.position, p.original_filename) for p in document.pages] == [
        (1, "IMG_0007.jpg")
    ]
    assert numbers_in_state(db, PageState.INBOX) == [1, 2, 3, 4, 5, 6, 8, 9, 10]


def test_g3_first_after_last_is_swapped(client, db):
    upload(client, 10)

    response = make_document(client, db, 6, 3)

    assert "Document made from photos 3 to 6" in message(response)
    assert numbers_in_state(db, PageState.GROUPED) == [3, 4, 5, 6]


def test_g4_a_range_that_includes_a_grouped_photo_is_refused(client, db):
    upload(client, 10)
    make_document(client, db, 5, 5)

    response = make_document(client, db, 3, 7)

    assert "Photos 3 to 7 include a photo that is already in a document" in message(
        response
    )
    assert db.scalars(select(func.count(Document.id))).one() == 1
    assert numbers_in_state(db, PageState.GROUPED) == [5]  # nothing else moved
    assert numbers_in_state(db, PageState.INBOX) == [1, 2, 3, 4, 6, 7, 8, 9, 10]


def test_g4_the_swapped_range_is_the_one_named_in_the_refusal(client, db):
    upload(client, 10)
    make_document(client, db, 5, 5)

    response = make_document(client, db, 7, 3)

    assert "Photos 3 to 7 include a photo that is already in a document" in message(
        response
    )


@pytest.mark.parametrize("first,last", [(3, None), (None, 6), (None, None)])
def test_g5_both_ends_must_be_picked(client, db, first, last):
    upload(client, 10)

    response = make_document(client, db, first, last)

    assert "Pick both the first and the last page" in message(response)
    assert db.scalars(select(Document)).all() == []
    assert numbers_in_state(db, PageState.INBOX) == list(range(1, 11))


def test_g5_a_value_that_is_not_a_number_counts_as_not_picked(client, db):
    upload(client, 3)
    box = box_of(db)

    response = client.post(
        f"/boxes/{box.id}/make-document",
        data={"first": "abc", "last": str(page_id(db, 2))},
        follow_redirects=True,
    )

    assert "Pick both the first and the last page" in message(response)


# --- G7: a Not a page photo inside the range stays out ---


def test_g7_a_discarded_photo_inside_the_range_is_skipped(client, db):
    upload(client, 10)
    dict(box_of(db).ordered_pages())[4]._state = "discarded"  # tests may set it
    db.commit()

    response = make_document(client, db, 3, 6)

    assert "Document made from photos 3 to 6" in message(response)
    document = db.scalars(select(Document)).one()
    assert [(p.position, p.original_filename) for p in document.pages] == [
        (1, "IMG_0003.jpg"),
        (2, "IMG_0005.jpg"),
        (3, "IMG_0006.jpg"),
    ]
    assert numbers_in_state(db, PageState.DISCARDED) == [4]
    assert dict(box_of(db).ordered_pages())[4].document_id is None


def test_a_discarded_photo_cannot_be_an_end_of_the_range(client, db):
    upload(client, 10)
    dict(box_of(db).ordered_pages())[3]._state = "discarded"
    db.commit()

    response = make_document(client, db, 3, 6)

    assert "Photo 3 is marked as not a page" in message(response)
    assert db.scalars(select(Document)).all() == []


# --- Crafted requests ---


def test_a_photo_from_another_box_is_refused(client, db):
    upload(client, 3, box_name="Box 1")
    # A second box with a photo of its own.
    client.post(
        "/upload",
        data={
            "choice": "new",
            "new_box_name": "Box 2",
            "photos": [(io.BytesIO(photo_bytes("other")), "other.jpg")],
        },
    )
    other = page_id(db, 1, box_name="Box 2")
    mine = page_id(db, 1, box_name="Box 1")

    response = client.post(
        f"/boxes/{box_of(db).id}/make-document",
        data={"first": str(mine), "last": str(other)},
        follow_redirects=True,
    )

    assert "That photo isn't in this box" in message(response)
    assert db.scalars(select(Document)).all() == []


def test_a_photo_that_does_not_exist_is_refused(client, db):
    upload(client, 3)

    response = client.post(
        f"/boxes/{box_of(db).id}/make-document",
        data={"first": "999", "last": "998"},
        follow_redirects=True,
    )

    assert "That photo isn't in this box" in message(response)


def test_make_document_in_an_unknown_box_is_a_404(client):
    assert client.post("/boxes/999/make-document", data={}).status_code == 404


def test_a_refusal_sends_the_user_back_to_the_inbox(client, db):
    upload(client, 3)
    inbox = f"/boxes/{box_of(db).id}/inbox"

    response = client.post(
        f"/boxes/{box_of(db).id}/make-document",
        data={},
        headers={"Referer": f"http://127.0.0.1:5000{inbox}"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == inbox


# --- Every change goes through apply("group") ---


def test_every_change_is_recorded_by_apply_group(client, db):
    upload(client, 6)
    make_document(client, db, 2, 4)

    document = db.scalars(select(Document)).one()
    changes = db.scalars(select(StateChange).where(StateChange.action == "group")).all()
    page_changes = [c for c in changes if c.object_kind == "page"]
    doc_changes = [c for c in changes if c.object_kind == "document"]
    assert sorted(c.object_id for c in page_changes) == sorted(
        p.id for p in document.pages
    )
    assert all((c.from_state, c.to_state) == ("inbox", "grouped") for c in page_changes)
    assert [(c.object_id, c.from_state, c.to_state) for c in doc_changes] == [
        (document.id, None, "grouped")
    ]
    assert all(c.at == FIXED_NOW for c in changes)


# --- The Make document button ---


def test_the_inbox_has_a_make_document_button_that_says_it_takes_a_while(client, db):
    upload(client, 2)
    box = box_of(db)

    html = client.get(f"/boxes/{box.id}/inbox").text

    assert f'action="/boxes/{box.id}/make-document"' in html
    assert "Make document" in html
    assert "takes up to a minute" in html
