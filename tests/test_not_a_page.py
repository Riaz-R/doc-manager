import html
import io

import pytest
from conftest import FIXED_NOW, photo_bytes
from sqlalchemy import select

from docmanager.models.box import Box
from docmanager.models.document import Document
from docmanager.models.page import Page, PageState
from docmanager.models.records import StateChange


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


def upload(client, count, box_name="Box 1", prefix="IMG"):
    """Upload PREFIX_0001.jpg ... into a new box, so photo N is the Nth in filename order."""
    files = [
        (io.BytesIO(photo_bytes(f"{prefix}_{n:04d}")), f"{prefix}_{n:04d}.jpg")
        for n in range(1, count + 1)
    ]
    client.post(
        "/upload",
        data={"choice": "new", "new_box_name": box_name, "photos": files},
    )


def box_of(db, name="Box 1"):
    return db.scalars(select(Box).where(Box.name == name)).one()


def page_id(db, number, box_name="Box 1"):
    return dict(box_of(db, box_name).ordered_pages())[number].id


def mark_not_a_page(client, db, numbers, box_name="Box 1", extra_ids=()):
    ids = [str(page_id(db, n, box_name)) for n in numbers] + list(extra_ids)
    return client.post(
        f"/boxes/{box_of(db, box_name).id}/discard",
        data={"discard": ids},
        follow_redirects=True,
    )


def make_document(client, db, first, last):
    return client.post(
        f"/boxes/{box_of(db).id}/make-document",
        data={"first": str(page_id(db, first)), "last": str(page_id(db, last))},
        follow_redirects=True,
    )


def restore(client, page):
    return client.post(f"/pages/{page}/restore", follow_redirects=True)


def numbers_in_state(db, state, box_name="Box 1"):
    db.expire_all()
    return [n for n, p in box_of(db, box_name).ordered_pages() if p.state == state]


def text(response):
    return html.unescape(response.text)


def inbox_numbers(client, db, box_name="Box 1"):
    page = client.get(f"/boxes/{box_of(db, box_name).id}/inbox").text
    return [n for n in range(1, 40) if f'<span class="photo-number">{n}</span>' in page]


# --- AT-08: G6 and G7 ---


def test_g6_ticked_photos_become_discarded_leave_the_inbox_and_appear_in_the_bin(
    client, db
):
    upload(client, 10)

    response = mark_not_a_page(client, db, [2, 9])

    assert "2 photos marked as not a page" in text(response)
    assert numbers_in_state(db, PageState.DISCARDED) == [2, 9]
    assert inbox_numbers(client, db) == [1, 3, 4, 5, 6, 7, 8, 10]  # numbers don't shift
    bin_page = client.get("/bin").text
    assert "IMG_0002.jpg" in bin_page and "IMG_0009.jpg" in bin_page
    assert "IMG_0003.jpg" not in bin_page


def test_one_photo_message_is_singular(client, db):
    upload(client, 3)

    response = mark_not_a_page(client, db, [2])

    assert "1 photo marked as not a page" in text(response)


def test_discarding_goes_through_apply_discard(client, db):
    upload(client, 4)
    mark_not_a_page(client, db, [2, 3])

    changes = db.scalars(
        select(StateChange).where(StateChange.action == "discard")
    ).all()

    assert sorted(c.object_id for c in changes) == sorted(
        [page_id(db, 2), page_id(db, 3)]
    )
    assert all(c.object_kind == "page" for c in changes)
    assert all((c.from_state, c.to_state) == ("inbox", "discarded") for c in changes)
    assert all(c.at == FIXED_NOW for c in changes)


def test_the_same_photo_ticked_twice_counts_once(client, db):
    upload(client, 3)

    response = mark_not_a_page(client, db, [2, 2])

    assert "1 photo marked as not a page" in text(response)


def test_g7_a_not_a_page_photo_is_skipped_when_grouping_through_the_screens(client, db):
    upload(client, 10)
    mark_not_a_page(client, db, [4])

    response = make_document(client, db, 3, 6)

    assert "Document made from photos 3 to 6" in text(response)
    document = db.scalars(select(Document)).one()
    assert [p.original_filename for p in document.pages] == [
        "IMG_0003.jpg",
        "IMG_0005.jpg",
        "IMG_0006.jpg",
    ]
    assert numbers_in_state(db, PageState.DISCARDED) == [4]
    assert "IMG_0004.jpg" in client.get("/bin").text


def test_nothing_ticked_is_refused(client, db):
    upload(client, 3)

    response = client.post(
        f"/boxes/{box_of(db).id}/discard", data={}, follow_redirects=True
    )

    assert "Tick the photos that are not pages" in text(response)


def test_a_value_that_is_not_a_number_counts_as_not_ticked(client, db):
    upload(client, 3)

    response = client.post(
        f"/boxes/{box_of(db).id}/discard",
        data={"discard": ["abc"]},
        follow_redirects=True,
    )

    assert "Tick the photos that are not pages" in text(response)


def test_a_refusal_changes_nothing_at_all(client, db):
    upload(client, 5)
    make_document(client, db, 2, 2)  # photo 2 is now in a document
    grouped = page_id(db, 2)

    response = mark_not_a_page(client, db, [4], extra_ids=[str(grouped)])

    assert "This photo can't be marked as not a page" in text(response)
    assert numbers_in_state(db, PageState.DISCARDED) == []  # photo 4 stayed too


def test_a_photo_from_another_box_is_refused(client, db):
    upload(client, 3, box_name="Box 1")
    upload(client, 3, box_name="Box 2", prefix="OTHER")
    other = str(page_id(db, 1, box_name="Box 2"))

    response = mark_not_a_page(client, db, [], extra_ids=[other])

    assert "That photo isn't in this box" in text(response)
    assert numbers_in_state(db, PageState.DISCARDED, box_name="Box 2") == []


def test_discarding_in_an_unknown_box_is_a_404(client):
    assert client.post("/boxes/999/discard", data={}).status_code == 404


def test_the_inbox_has_a_mark_ticked_as_not_a_page_button(client, db):
    upload(client, 2)
    box = box_of(db)

    page = client.get(f"/boxes/{box.id}/inbox").text

    assert "Mark ticked as not a page" in page
    assert f'formaction="/boxes/{box.id}/discard"' in page


# --- AT-09: G8 ---


def test_g8_restoring_returns_the_photo_to_the_inbox_in_its_filename_position(
    client, db
):
    upload(client, 5)
    mark_not_a_page(client, db, [2, 4])
    photo = page_id(db, 2)

    response = restore(client, photo)

    assert "IMG_0002.jpg" in text(response)
    assert "restored" in text(response).lower()
    assert numbers_in_state(db, PageState.INBOX) == [1, 2, 3, 5]
    assert inbox_numbers(client, db) == [1, 2, 3, 5]
    bin_page = client.get("/bin").text
    assert "IMG_0002.jpg" not in bin_page
    assert "IMG_0004.jpg" in bin_page
    # In filename order: photo 2 comes back between photos 1 and 3.
    inbox = client.get(f"/boxes/{box_of(db).id}/inbox").text
    assert inbox.index("IMG_0001.jpg") < inbox.index("IMG_0002.jpg")
    assert inbox.index("IMG_0002.jpg") < inbox.index("IMG_0003.jpg")


def test_restoring_goes_through_apply_restore(client, db):
    upload(client, 3)
    mark_not_a_page(client, db, [2])
    restore(client, page_id(db, 2))

    change = db.scalars(
        select(StateChange).where(StateChange.action == "restore")
    ).one()

    assert (change.object_kind, change.object_id) == ("page", page_id(db, 2))
    assert (change.from_state, change.to_state) == ("discarded", "inbox")
    assert change.at == FIXED_NOW


def test_a_restored_photo_can_be_grouped_again(client, db):
    upload(client, 4)
    mark_not_a_page(client, db, [3])
    restore(client, page_id(db, 3))

    make_document(client, db, 2, 4)

    document = db.scalars(select(Document)).one()
    assert [p.original_filename for p in document.pages] == [
        "IMG_0002.jpg",
        "IMG_0003.jpg",
        "IMG_0004.jpg",
    ]


def test_restoring_a_photo_that_is_not_in_the_bin_is_refused(client, db):
    upload(client, 2)

    response = restore(client, page_id(db, 1))

    assert 'This photo can\'t be restored while it is "To sort"' in text(response)


def test_restoring_a_photo_that_does_not_exist_is_refused(client):
    assert "That photo isn't in the Bin" in text(restore(client, 999))


# --- The Bin screen and Home tile ---


def test_an_empty_bin_says_so(client):
    page = client.get("/bin").text

    assert "The Bin is empty" in page


def test_the_bin_lists_photos_from_every_box_with_a_restore_button_each(client, db):
    upload(client, 3, box_name="Box 1")
    upload(client, 3, box_name="Box 2", prefix="OTHER")
    mark_not_a_page(client, db, [1], box_name="Box 1")
    mark_not_a_page(client, db, [2], box_name="Box 2")
    first, second = page_id(db, 1), page_id(db, 2, box_name="Box 2")

    page = client.get("/bin").text

    assert "Box 1" in page and "IMG_0001.jpg" in page
    assert "Box 2" in page and "OTHER_0002.jpg" in page
    for photo in (first, second):
        assert f'src="/pages/{photo}/thumb"' in page
        assert f'action="/pages/{photo}/restore"' in page
    assert page.count("Restore") == 2


def test_home_has_a_bin_tile_with_the_count(client, db):
    upload(client, 4)
    assert 'href="/bin"' in client.get("/").text
    assert "Bin: 0 items" in client.get("/").text

    mark_not_a_page(client, db, [1, 2])
    assert "Bin: 2 items" in client.get("/").text

    mark_not_a_page(client, db, [3])
    restore(client, page_id(db, 1))
    assert "Bin: 2 items" in client.get("/").text


def test_the_bin_count_is_singular_for_one(client, db):
    upload(client, 2)
    mark_not_a_page(client, db, [1])

    assert "Bin: 1 item" in client.get("/").text
    assert "Bin: 1 items" not in client.get("/").text


def test_discarded_photos_are_not_counted_as_photos_to_sort(client, db):
    upload(client, 3)
    mark_not_a_page(client, db, [1])

    assert "2 photos to sort" in client.get("/").text
    assert db.scalars(select(Page).where(Page._state == "discarded")).all()
