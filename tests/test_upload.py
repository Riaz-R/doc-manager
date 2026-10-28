import html
import io

import pytest
from conftest import FIXED_NOW, photo_bytes
from PIL import Image
from sqlalchemy import select

from docmanager import create_app
from docmanager.models.box import Batch, Box
from docmanager.models.page import Page, PageState
from docmanager.models.records import StateChange
from docmanager.services.upload import UploadResult

HEIC_SENTENCE = (
    "iPhone HEIC photos aren't supported yet. "
    "On the iPhone: Settings → Camera → Formats → Most Compatible."
)


@pytest.fixture
def db(app):
    """A session on the test app's database, for checking what an upload stored."""
    with app.extensions["docmanager_sessions"]() as session:
        yield session


def photo(name: str, label: str | None = None, fmt: str = "JPEG"):
    """One file for a test upload: (data, filename)."""
    return (io.BytesIO(photo_bytes(label or name, fmt)), name)


def upload(client, files, *, new_box=None, box_id=None, **extra):
    """Post an upload. `extra` adds or overrides form fields (to test a crafted form)."""
    data = {"photos": files}
    if new_box is not None:
        data.update({"choice": "new", "new_box_name": new_box})
    else:
        data.update({"choice": "existing", "box": str(box_id)})
    data.update(extra)
    return client.post("/upload", data=data, follow_redirects=True)


def numbered(count, start=1):
    return [photo(f"IMG_{n:04d}.jpg") for n in range(start, start + count)]


# --- B1 to B4: boxes, batches and duplicates ---


def test_b1_new_box_gets_one_batch_of_inbox_pages(client, db):
    response = upload(client, numbered(40), new_box="Box 1")

    assert "40 photos added." in html.unescape(response.text)
    box = db.scalars(select(Box)).one()
    assert box.name == "Box 1"
    assert box.created_at == FIXED_NOW
    batch = db.scalars(select(Batch)).one()
    assert (batch.added_count, batch.skipped_count, batch.refused_count) == (40, 0, 0)
    pages = db.scalars(select(Page)).all()
    assert len(pages) == 40
    assert {p.state for p in pages} == {PageState.INBOX}
    assert {p.batch_id for p in pages} == {batch.id}


def test_b2_adding_to_an_existing_box_makes_a_second_batch(client, db):
    upload(client, numbered(40), new_box="Box 1")
    box = db.scalars(select(Box)).one()

    response = upload(client, numbered(25, start=41), box_id=box.id)

    assert "25 photos added." in html.unescape(response.text)
    assert db.scalars(select(Box)).all() == [box]
    assert len(db.scalars(select(Batch)).all()) == 2
    assert len(db.scalars(select(Page).where(Page.box_id == box.id)).all()) == 65


def test_b3_a_photo_already_in_the_app_is_skipped_in_any_box(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")

    response = upload(client, [photo("IMG_0001.jpg")], new_box="Box 2")

    assert "1 skipped – already uploaded" in html.unescape(response.text)
    assert "photo added" not in html.unescape(response.text)
    assert len(db.scalars(select(Page)).all()) == 1
    second_batch = db.scalars(select(Batch).order_by(Batch.id)).all()[1]
    assert (second_batch.added_count, second_batch.skipped_count) == (0, 1)


def test_b4_the_same_file_twice_in_one_upload_makes_one_page(client, db):
    files = [photo("IMG_0001.jpg", "same"), photo("IMG_0002.jpg", "same")]

    response = upload(client, files, new_box="Box 1")

    assert "1 photo added. 1 skipped – already uploaded." in html.unescape(
        response.text
    )
    assert len(db.scalars(select(Page)).all()) == 1


# --- B6: files that aren't photos ---


def test_b6_a_text_file_and_a_corrupt_jpeg_are_refused_by_name(client, db):
    corrupt = (io.BytesIO(b"\xff\xd8\xff\xe0 not really a jpeg"), "broken.jpg")
    files = [
        photo("IMG_0001.jpg"),
        (io.BytesIO(b"hello"), "notes.txt"),
        corrupt,
        photo("IMG_0002.jpg"),
    ]

    response = upload(client, files, new_box="Box 1")

    assert (
        "2 photos added. 2 refused – not a photo (notes.txt, broken.jpg)."
        in html.unescape(response.text)
    )
    assert len(db.scalars(select(Page)).all()) == 2
    assert db.scalars(select(Batch)).one().refused_count == 2


def test_a_truncated_jpeg_is_refused_because_photos_are_fully_decoded(client, db):
    data = photo_bytes("cut short")
    truncated = (io.BytesIO(data[: len(data) // 2]), "IMG_0009.jpg")

    response = upload(client, [truncated, photo("IMG_0001.jpg")], new_box="Box 1")

    assert "1 photo added. 1 refused – not a photo (IMG_0009.jpg)." in html.unescape(
        response.text
    )
    assert len(db.scalars(select(Page)).all()) == 1


def test_a_photo_is_judged_by_its_content_not_its_filename(client, db):
    png_named_jpg = (io.BytesIO(photo_bytes("png", "PNG")), "scan.jpg")

    response = upload(client, [png_named_jpg], new_box="Box 1")

    assert "1 photo added." in html.unescape(response.text)
    assert db.scalars(select(Page)).one().photo_path.endswith(".png")


# --- B7: HEIC ---


def test_b7_heic_is_refused_with_the_iphone_instructions(client, db):
    heic = (io.BytesIO(b"\x00\x00\x00\x18ftypheic"), "IMG_0007.HEIC")

    response = upload(client, [heic, photo("IMG_0001.jpg")], new_box="Box 1")

    assert (
        f"1 photo added. 1 refused – iPhone HEIC photo (IMG_0007.HEIC). {HEIC_SENTENCE}"
        in html.unescape(response.text)
    )
    assert len(db.scalars(select(Page)).all()) == 1


# --- B8 and the box-name rules ---


def test_b8_a_duplicate_box_name_is_refused(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")

    response = upload(client, [photo("IMG_0002.jpg")], new_box="Box 1")

    assert "There is already a box called Box 1" in html.unescape(response.text)
    assert len(db.scalars(select(Box)).all()) == 1
    assert len(db.scalars(select(Page)).all()) == 1


@pytest.mark.parametrize("name", ["", "   "])
def test_a_new_box_needs_a_name(client, db, name):
    response = upload(client, [photo("IMG_0001.jpg")], new_box=name)

    assert "Give the new box a name" in html.unescape(response.text)
    assert db.scalars(select(Box)).all() == []


def test_box_names_can_be_at_most_60_characters(client, db):
    too_long = upload(client, [photo("IMG_0001.jpg")], new_box="x" * 61)
    assert "Box names can be at most 60 characters" in too_long.text
    assert db.scalars(select(Box)).all() == []

    exactly_60 = upload(client, [photo("IMG_0001.jpg")], new_box="y" * 60)
    assert "1 photo added." in exactly_60.text


def test_box_names_are_trimmed(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="  Box 3 – 2017–2019  ")

    assert db.scalars(select(Box)).one().name == "Box 3 – 2017–2019"


def test_uploading_into_a_box_that_does_not_exist_is_refused(client, db):
    response = upload(client, [photo("IMG_0001.jpg")], box_id=999)

    assert "That box doesn't exist" in html.unescape(response.text)
    assert db.scalars(select(Page)).all() == []


def test_choosing_no_photos_is_refused_and_makes_no_box(client, db):
    response = client.post(
        "/upload",
        data={
            "choice": "new",
            "new_box_name": "Box 1",
            "photos": (io.BytesIO(b""), ""),
        },
        follow_redirects=True,
    )

    assert "Choose at least one photo" in html.unescape(response.text)
    assert db.scalars(select(Box)).all() == []


# --- What is stored ---


def test_originals_and_thumbnails_are_stored_by_sha256(client, db, data_dir):
    import hashlib

    data = photo_bytes("IMG_0001")
    upload(client, [(io.BytesIO(data), "IMG_0001.jpg")], new_box="Box 1")

    page = db.scalars(select(Page)).one()
    sha = hashlib.sha256(data).hexdigest()
    assert page.sha256 == sha
    assert page.photo_path == f"photos/{page.box_id}/{sha}.jpg"
    assert page.thumb_path == f"thumbs/{page.box_id}/{sha}.jpg"
    assert (data_dir / page.photo_path).read_bytes() == data
    with Image.open(data_dir / page.thumb_path) as thumb:
        assert thumb.format == "JPEG"
        assert max(thumb.size) == 400


def test_a_png_keeps_its_extension_and_gets_a_jpeg_thumbnail(client, db, data_dir):
    upload(client, [photo("scan.png", fmt="PNG")], new_box="Box 1")

    page = db.scalars(select(Page)).one()
    assert page.photo_path.endswith(".png")
    assert page.thumb_path.endswith(".jpg")
    with Image.open(data_dir / page.thumb_path) as thumb:
        assert thumb.format == "JPEG"


def test_the_uploaded_filename_is_kept_for_display_but_never_makes_a_path(
    client, db, data_dir
):
    upload(client, [photo("../../etc/evil.jpg", "evil")], new_box="Box 1")

    page = db.scalars(select(Page)).one()
    assert page.original_filename == "evil.jpg"
    assert "evil" not in page.photo_path
    assert (data_dir / page.photo_path).is_file()


def test_each_page_goes_through_apply_upload(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")

    page = db.scalars(select(Page)).one()
    change = db.scalars(select(StateChange)).one()
    assert (change.object_kind, change.object_id) == ("page", page.id)
    assert (change.action, change.from_state, change.to_state) == (
        "upload",
        None,
        "inbox",
    )
    assert change.at == FIXED_NOW


# --- Messages ---


def test_the_message_follows_the_spec_wording():
    result = UploadResult(added=38, skipped=2, refused=["notes.txt"], refused_heic=[])
    assert result.message() == (
        "38 photos added. 2 skipped – already uploaded. "
        "1 refused – not a photo (notes.txt)."
    )


def test_parts_with_a_zero_count_are_left_out():
    assert UploadResult(added=1, skipped=0, refused=[], refused_heic=[]).message() == (
        "1 photo added."
    )
    assert UploadResult(added=0, skipped=3, refused=[], refused_heic=[]).message() == (
        "3 skipped – already uploaded."
    )


def test_heic_files_are_listed_with_the_b7_sentence_after_other_parts():
    result = UploadResult(
        added=0, skipped=0, refused=["a.txt"], refused_heic=["x.heic", "y.heif"]
    )
    assert result.message() == (
        "1 refused – not a photo (a.txt). "
        f"2 refused – iPhone HEIC photo (x.heic, y.heif). {HEIC_SENTENCE}"
    )


# --- Screens ---


def test_upload_screen_offers_boxes_new_box_and_a_multiple_file_picker(client):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")

    page = client.get("/upload").text

    assert "Box 1" in page
    assert 'name="choice" value="new"' in page
    assert 'name="choice" value="existing"' in page
    assert 'name="new_box_name"' in page
    assert 'type="file"' in page
    assert "multiple" in page
    assert 'accept="image/jpeg,image/png"' in page
    assert 'enctype="multipart/form-data"' in page


def test_home_lists_boxes_with_photos_to_sort(client):
    upload(client, numbered(3), new_box="Box 1")
    upload(client, numbered(1, start=10), new_box="Box 2")

    home = client.get("/").text

    assert "Box 1" in home
    assert "3 photos to sort" in home
    assert "Box 2" in home
    assert "1 photo to sort" in home
    assert 'href="/upload"' in home


def test_an_upload_over_the_size_limit_says_to_upload_in_parts(data_dir):
    small = create_app(
        {"DATA_DIR": data_dir, "CLOCK": lambda: FIXED_NOW, "MAX_CONTENT_LENGTH": 2000}
    )
    client = small.test_client()
    big = (io.BytesIO(b"x" * 5000), "IMG_0001.jpg")

    response = client.post(
        "/upload",
        data={"choice": "new", "new_box_name": "Box 1", "photos": big},
        follow_redirects=True,
    )

    assert "upload in parts" in html.unescape(response.text).lower()
    assert response.status_code == 200
    with small.extensions["docmanager_sessions"]() as session:
        assert session.scalars(select(Box)).all() == []


def test_the_size_limit_defaults_to_the_config_value(app):
    from docmanager import config

    assert app.config["MAX_CONTENT_LENGTH"] == config.MAX_UPLOAD_BYTES


# --- The box choice: only the selected option is used ---


def test_existing_box_chosen_with_a_name_typed_adds_to_the_existing_box(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")
    box = db.scalars(select(Box)).one()

    response = upload(
        client, [photo("IMG_0002.jpg")], box_id=box.id, new_box_name="Typed name"
    )

    assert "1 photo added." in html.unescape(response.text)
    assert db.scalars(select(Box)).all() == [box]
    assert len(db.scalars(select(Page).where(Page.box_id == box.id)).all()) == 2


def test_new_box_chosen_with_a_dropdown_value_set_makes_the_new_box(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")
    old_box = db.scalars(select(Box)).one()

    upload(client, [photo("IMG_0002.jpg")], new_box="Box 2", box=str(old_box.id))

    boxes = db.scalars(select(Box).order_by(Box.id)).all()
    assert [b.name for b in boxes] == ["Box 1", "Box 2"]
    assert len(db.scalars(select(Page).where(Page.box_id == old_box.id)).all()) == 1
    assert len(db.scalars(select(Page).where(Page.box_id == boxes[1].id)).all()) == 1


def test_new_box_chosen_with_an_empty_name_is_refused_even_if_a_box_is_selected(
    client, db
):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")
    box = db.scalars(select(Box)).one()

    response = upload(client, [photo("IMG_0002.jpg")], new_box="", box=str(box.id))

    assert "Give the new box a name" in html.unescape(response.text)
    assert len(db.scalars(select(Page)).all()) == 1


def test_new_box_chosen_with_a_duplicate_name_gives_the_b8_message(client, db):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")

    response = upload(client, [photo("IMG_0002.jpg")], new_box="Box 1")

    assert "There is already a box called Box 1" in html.unescape(response.text)
    assert len(db.scalars(select(Box)).all()) == 1


@pytest.mark.parametrize("extra", [{"choice": "bogus"}, {"choice": ""}])
def test_an_unknown_choice_is_refused(client, db, extra):
    response = upload(client, [photo("IMG_0001.jpg")], new_box="Box 1", **extra)

    assert "Choose whether to add to an existing box or make a new one" in (
        html.unescape(response.text)
    )
    assert db.scalars(select(Box)).all() == []


def test_existing_chosen_without_a_box_selected_is_refused(client, db):
    response = upload(client, [photo("IMG_0001.jpg")], box_id="")

    assert "Choose a box to add the photos to" in html.unescape(response.text)
    assert db.scalars(select(Page)).all() == []


def test_with_no_boxes_new_box_is_selected_by_default(client):
    page = client.get("/upload").text

    assert 'name="choice" value="new" checked' in page
    assert 'name="choice" value="existing" checked' not in page
    assert 'name="choice" value="existing" disabled' in page


def test_with_boxes_add_to_an_existing_box_is_selected_by_default(client):
    upload(client, [photo("IMG_0001.jpg")], new_box="Box 1")

    page = client.get("/upload").text

    assert 'name="choice" value="existing" checked' in page
    assert 'name="choice" value="new" checked' not in page
    assert '<option value="new"' not in page  # no "New box" entry in the dropdown
