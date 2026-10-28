import io

import pytest
from conftest import FIXED_NOW, photo_bytes
from PIL import Image
from sqlalchemy import select

from docmanager.models.box import Batch, Box
from docmanager.models.page import Page


def make_box_with_pages(session, filenames):
    """A box whose pages were 'uploaded' in the order given (so ids follow that order)."""
    box = Box(name="Box 1", created_at=FIXED_NOW)
    batch = Batch(
        box=box,
        uploaded_at=FIXED_NOW,
        added_count=len(filenames),
        skipped_count=0,
        refused_count=0,
    )
    for n, filename in enumerate(filenames):
        session.add(
            Page(
                box=box,
                batch=batch,
                sha256=f"sha{n}",
                original_filename=filename,
                photo_path=f"photos/1/sha{n}.jpg",
                thumb_path=f"thumbs/1/sha{n}.jpg",
            )
        )
    session.add(box)
    session.flush()
    for page in box.pages:
        page._state = "inbox"  # tests may set the state directly
    return box


def names(numbered_pages):
    return [(number, page.original_filename) for number, page in numbered_pages]


# --- AT-06: order ---


def test_o1_pages_come_back_in_filename_order(session):
    box = make_box_with_pages(session, ["IMG_0003.jpg", "IMG_0001.jpg", "IMG_0002.jpg"])

    assert names(box.ordered_pages()) == [
        (1, "IMG_0001.jpg"),
        (2, "IMG_0002.jpg"),
        (3, "IMG_0003.jpg"),
    ]


def test_the_same_filename_is_ordered_by_id(session):
    box = make_box_with_pages(session, ["IMG_0002.jpg", "IMG_0001.jpg", "IMG_0001.jpg"])

    ordered = [page for _, page in box.ordered_pages()]

    assert [p.original_filename for p in ordered] == [
        "IMG_0001.jpg",
        "IMG_0001.jpg",
        "IMG_0002.jpg",
    ]
    assert ordered[0].id < ordered[1].id


def test_numbers_count_every_photo_and_do_not_shift_as_photos_leave(session):
    box = make_box_with_pages(session, ["A.jpg", "B.jpg", "C.jpg", "D.jpg"])
    box.pages[1]._state = "discarded"  # B
    box.pages[2]._state = "grouped"  # C

    assert names(box.inbox_pages()) == [(1, "A.jpg"), (4, "D.jpg")]
    assert [n for n, _ in box.ordered_pages()] == [1, 2, 3, 4]


def test_an_empty_box_has_no_pages(session):
    box = make_box_with_pages(session, [])

    assert box.ordered_pages() == []
    assert box.inbox_pages() == []


# --- The Inbox screen ---


@pytest.fixture
def db(app):
    with app.extensions["docmanager_sessions"]() as session:
        yield session


def upload(client, filenames, new_box="Box 1"):
    files = [(io.BytesIO(photo_bytes(name)), name) for name in filenames]
    client.post(
        "/upload",
        data={"box": "new", "new_box_name": new_box, "photos": files},
    )


def inbox_url(db, name="Box 1"):
    return f"/boxes/{db.scalars(select(Box).where(Box.name == name)).one().id}/inbox"


def test_the_inbox_lists_photos_in_filename_order_with_their_numbers(client, db):
    upload(client, ["IMG_0003.jpg", "IMG_0001.jpg", "IMG_0002.jpg"])

    page = client.get(inbox_url(db)).text

    positions = [page.index(f"IMG_000{n}.jpg") for n in (1, 2, 3)]
    assert positions == sorted(positions)
    for number, filename in enumerate(["IMG_0001", "IMG_0002", "IMG_0003"], start=1):
        assert f'<span class="photo-number">{number}</span>' in page
        assert filename in page


def test_each_photo_has_first_last_and_not_a_page_controls(client, db):
    upload(client, ["IMG_0001.jpg", "IMG_0002.jpg"])
    pages = db.scalars(select(Page).order_by(Page.id)).all()

    html = client.get(inbox_url(db)).text

    for page in pages:
        assert f'type="radio" name="first" value="{page.id}"' in html
        assert f'type="radio" name="last" value="{page.id}"' in html
        assert f'type="checkbox" name="discard" value="{page.id}"' in html
        assert f'src="/pages/{page.id}/thumb"' in html
    assert "First" in html and "Last" in html and "Not a page" in html


def test_the_inbox_shows_only_photos_still_to_sort_but_keeps_their_numbers(client, db):
    upload(client, ["A.jpg", "B.jpg", "C.jpg"])
    for page in db.scalars(select(Page)):
        if page.original_filename == "B.jpg":
            page._state = "discarded"
    db.commit()

    html = client.get(inbox_url(db)).text

    assert "A.jpg" in html and "C.jpg" in html
    assert "B.jpg" not in html
    assert '<span class="photo-number">3</span>' in html
    assert '<span class="photo-number">2</span>' not in html


def test_an_empty_inbox_says_so(client, db):
    upload(client, ["A.jpg"])
    db.scalars(select(Page)).one()._state = "grouped"
    db.commit()

    assert "No photos to sort in this box" in client.get(inbox_url(db)).text


def test_an_unknown_box_shows_the_friendly_404(client):
    response = client.get("/boxes/999/inbox")

    assert response.status_code == 404


def test_home_links_each_box_to_its_inbox(client, db):
    upload(client, ["A.jpg"])

    assert f'href="{inbox_url(db)}"' in client.get("/").text


# --- The thumbnail route ---


def test_the_thumbnail_route_serves_a_jpeg(client, db):
    upload(client, ["A.jpg"])
    page = db.scalars(select(Page)).one()

    response = client.get(f"/pages/{page.id}/thumb")

    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    with Image.open(io.BytesIO(response.data)) as image:
        assert image.format == "JPEG"
        assert max(image.size) == 400


def test_an_unknown_thumbnail_is_a_404(client):
    assert client.get("/pages/999/thumb").status_code == 404


def test_a_missing_thumbnail_file_is_a_404_not_a_crash(client, db, data_dir):
    upload(client, ["A.jpg"])
    page = db.scalars(select(Page)).one()
    (data_dir / page.thumb_path).unlink()

    assert client.get(f"/pages/{page.id}/thumb").status_code == 404
