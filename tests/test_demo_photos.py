import hashlib
import io
import re

import pytest
from PIL import Image
from sqlalchemy import select

from docmanager import cli
from docmanager.demo import photos
from docmanager.models.box import Batch, Box
from docmanager.models.page import Page
from docmanager.services import ocr

NAMES = [f"IMG_{n:04d}.jpg" for n in range(1, 8)]
LENS_COVERS = ["IMG_0003.jpg", "IMG_0005.jpg"]
INVOICE_PAGES = ["IMG_0001.jpg", "IMG_0002.jpg"]
LETTER_PAGES = ["IMG_0004.jpg"]
UNCLEAR_PAGES = ["IMG_0006.jpg", "IMG_0007.jpg"]


@pytest.fixture
def box_dir(tmp_path):
    photos.write_demo_box(tmp_path / "demo-box")
    return tmp_path / "demo-box"


def word_count(text):
    return sum(1 for piece in text.split() if any(ch.isalnum() for ch in piece))


# --- The files ---


def test_the_expected_file_names_are_written(box_dir):
    assert sorted(p.name for p in box_dir.iterdir()) == NAMES


def test_write_demo_box_returns_the_paths_in_order(tmp_path):
    written = photos.write_demo_box(tmp_path / "out")

    assert [p.name for p in written] == NAMES
    assert all(p.is_file() for p in written)


def test_the_folder_is_made_if_it_is_missing(tmp_path):
    photos.write_demo_box(tmp_path / "a" / "b" / "demo-box")

    assert (tmp_path / "a" / "b" / "demo-box" / "IMG_0001.jpg").is_file()


def test_writing_twice_gives_the_same_files(tmp_path):
    out = tmp_path / "demo-box"
    photos.write_demo_box(out)
    first = {p.name: p.read_bytes() for p in out.iterdir()}

    photos.write_demo_box(out)

    assert {p.name: p.read_bytes() for p in out.iterdir()} == first


def test_every_file_is_a_jpeg_page_of_1240_by_1754_at_150_dpi(box_dir):
    for name in NAMES:
        with Image.open(box_dir / name) as image:
            assert image.format == "JPEG"
            assert image.size == (1240, 1754)
            assert tuple(round(d) for d in image.info["dpi"]) == (150, 150)


# --- Lens covers and pages ---


def test_the_lens_covers_are_pure_black(box_dir):
    for name in LENS_COVERS:
        with Image.open(box_dir / name) as image:
            assert image.convert("RGB").getextrema() == ((0, 0), (0, 0), (0, 0))


def test_the_text_pages_are_mostly_white_with_some_text(box_dir):
    for name in set(NAMES) - set(LENS_COVERS):
        with Image.open(box_dir / name) as image:
            grey = image.convert("L")
            low, high = grey.getextrema()
            assert high == 255  # white paper
            assert low < 80  # dark text
            assert sum(grey.histogram()[200:]) > 0.9 * 1240 * 1754  # mostly white


def test_every_file_is_different(box_dir):
    # Different bytes matter most: the Upload page skips a file it has seen before.
    hashes = {hashlib.sha256((box_dir / n).read_bytes()).hexdigest() for n in NAMES}
    assert len(hashes) == len(NAMES)


def test_every_page_image_is_different_too(box_dir):
    pages = []
    for name in set(NAMES) - set(LENS_COVERS):
        with Image.open(box_dir / name) as image:
            pages.append(image.convert("L").tobytes())
    assert len(set(pages)) == len(pages)


def test_a_line_too_long_for_the_page_is_wrapped_inside_the_margin():
    long_line = "word " * 80
    image = photos.render_page([long_line])

    right_edge = image.crop((1240 - photos.MARGIN + 10, 0, 1240, 1754))
    assert right_edge.convert("L").getextrema() == (255, 255)


def test_too_much_text_for_one_page_is_an_error():
    with pytest.raises(ValueError, match="Too much text"):
        photos.render_page(["a line"] * 100)


# --- The three made-up documents ---


def test_there_are_three_documents_each_with_well_over_20_words():
    assert [d.name for d in photos.DEMO_DOCUMENTS] == ["invoice", "letter", "unclear"]
    for document in photos.DEMO_DOCUMENTS:
        assert word_count(document.text) > 40, document.name


def test_every_text_page_has_at_least_20_words():
    for document in photos.DEMO_DOCUMENTS:
        for page in document.pages:
            assert word_count("\n".join(page)) >= 20, document.name


def test_the_pages_of_each_document_follow_the_file_layout():
    # Invoice 1-2, lens cover 3, letter 4, lens cover 5, unclear 6-7.
    assert [len(d.pages) for d in photos.DEMO_DOCUMENTS] == [2, 1, 2]


def test_the_invoice_is_for_c_0042_hollybrook_bakery_with_number_and_date():
    text = photos.DEMO_DOCUMENTS[0].text

    assert "INVOICE" in text
    assert "Invoice number INV-1043" in text
    assert "Invoice date 14/03/2026" in text
    assert "Amount due 120.00" in text
    assert "C-0042" in text
    assert "Hollybrook Bakery Ltd" in text
    assert set(re.findall(r"C-\d{4}", text)) == {"C-0042"}


def test_the_letter_has_a_re_line_a_date_and_the_same_client():
    text = photos.DEMO_DOCUMENTS[1].text

    assert re.search(r"^Re: .+", text, re.MULTILINE)
    assert "Dear" in text
    assert "5 May 2026" in text
    assert set(re.findall(r"C-\d{4}", text)) == {"C-0042"}
    assert "invoice" not in text.lower()


def test_the_unclear_document_has_no_client_and_no_type_words():
    text = photos.DEMO_DOCUMENTS[2].text.lower()
    tokens = set(re.findall(r"[a-z0-9£/:\-]+", text))

    assert not re.search(r"c-\d{4}", text)
    assert "hollybrook" not in text
    for giveaway in (
        "invoice",
        "amount",
        "due",
        "payment",
        "total",
        "vat",
        "dear",
        "sincerely",
        "regards",
        "please",
        "re:",
        "subject",
        "yours",
    ):
        assert giveaway not in tokens, giveaway


def test_every_character_in_the_demo_text_can_be_drawn():
    # Pillow's built-in font draws a character it lacks (like the pound sign) as the
    # same blank box, so a missing glyph would be silently unreadable to OCR.
    from PIL import ImageDraw, ImageFont

    font = ImageFont.load_default(size=photos.FONT_SIZE)

    def drawn(char):
        image = Image.new("L", (80, 80), 255)
        ImageDraw.Draw(image).text((10, 10), char, fill=0, font=font)
        return image.tobytes()

    missing = drawn("\ufffd")
    assert (
        drawn("£") == missing
    )  # the check itself works: this glyph is known to be absent
    text = " ".join(d.text for d in photos.DEMO_DOCUMENTS)
    for char in sorted(set(text) - {" ", "\n"}):
        assert drawn(char) != missing, repr(char)


def test_no_real_organisations_are_named():
    # Only the invented names appear (SPEC 8: no real data, no real branding).
    text = " ".join(d.text for d in photos.DEMO_DOCUMENTS)
    capitalised = set(re.findall(r"\b[A-Z][a-z]+\b", text))
    assert {"Hollybrook", "Brightwell", "Fernwood"} <= capitalised
    for real in ("Amazon", "Google", "HMRC", "Barclays", "Microsoft", "Tesco"):
        assert real not in text


# --- Uploading the folder ---


def test_the_folder_uploads_through_the_upload_page_with_every_photo_added(
    client, app, box_dir
):
    files = [(io.BytesIO((box_dir / n).read_bytes()), n) for n in NAMES]

    response = client.post(
        "/upload",
        data={"choice": "new", "new_box_name": "Interview box", "photos": files},
        follow_redirects=True,
    )

    assert "7 photos added." in response.text
    assert "skipped" not in response.text
    assert "refused" not in response.text
    with app.extensions["docmanager_sessions"]() as session:
        box = session.scalars(select(Box)).one()
        batch = session.scalars(select(Batch)).one()
        assert (batch.added_count, batch.skipped_count, batch.refused_count) == (
            7,
            0,
            0,
        )
        assert [p.original_filename for _, p in box.ordered_pages()] == NAMES
        assert len(session.scalars(select(Page)).all()) == 7


# --- The command ---


def test_make_photos_command_writes_the_box_and_says_so(tmp_path, capsys):
    out = tmp_path / "demo-box"

    cli.main(["make-photos", str(out)])

    assert sorted(p.name for p in out.iterdir()) == NAMES
    assert f"Wrote 7 photos to {out}" in capsys.readouterr().out


def test_make_photos_needs_a_folder(capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(["make-photos"])

    assert stop.value.code == 2
    assert "OUT_DIR" in capsys.readouterr().err


def test_make_photos_does_not_start_the_server(tmp_path, monkeypatch):
    from flask import Flask

    monkeypatch.setattr(Flask, "run", lambda *a, **k: pytest.fail("server started"))

    cli.main(["make-photos", str(tmp_path / "demo-box")])


def test_the_command_with_no_arguments_still_serves_on_127_0_0_1(monkeypatch):
    from flask import Flask

    calls = []
    monkeypatch.setattr(Flask, "run", lambda self, *a, **k: calls.append(k))

    monkeypatch.setattr(ocr, "check_ocr_tools", list)
    cli.main([])

    assert calls == [{"host": "127.0.0.1", "port": 5000, "debug": False}]
