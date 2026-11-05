"""The seed script: made-up clients, two demo boxes, and a safe way to start over.

Clients only come from here until the should tier (SPEC 3.5). Everything is invented.
The boxes are filled by drawing photos and running them through the same services
and OCR program the app itself uses.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from docmanager import create_app
from docmanager.demo import photos
from docmanager.errors import UserFacingError
from docmanager.models.box import Box
from docmanager.models.client import Client
from docmanager.models.document import DocState
from docmanager.services import disposal, filing, grouping, ocr, upload

# The marker the seed script leaves in a data folder it made. `--reset` empties a
# folder only if it has this marker or has nothing in it (plan decision 16).
MARKER = ".demo-data"

# (ref, name). C-0042 is the client the demo photos belong to.
DEMO_CLIENTS = (
    ("C-0042", "Hollybrook Bakery Ltd"),
    ("C-0007", "Ashgrove Dental Practice"),
    ("C-0013", "Birchfield Garden Centre"),
    ("C-0021", "Kestrel Print & Design"),
    ("C-0034", "Larkspur Tea Rooms"),
    ("C-0051", "Marlowe Joinery Ltd"),
    ("C-0066", "Quayside Bike Repairs"),
    ("C-0078", "Thornbury Plumbing Services"),
)


class SeedRefused(UserFacingError):
    """The seed script won't do what was asked. The message says why, in plain words."""


@dataclass
class SeedResult:
    added: int
    skipped: int  # demo clients that were already there
    emptied: bool  # the data folder was emptied first (--reset)
    marked: bool  # the folder was left marked as made by the seed script

    def message(self) -> str:
        text = f"Added {self.added} {'client' if self.added == 1 else 'clients'}."
        if self.skipped:
            text += f" {self.skipped} already there."
        if self.emptied:
            text = "Emptied the data folder first. " + text
        return text


def seed(data_dir, *, reset: bool = False, now: datetime | None = None) -> SeedResult:
    """Add the demo clients to the data folder, skipping any that already exist.

    With `reset`, the folder is emptied first, but only if it is empty already or the
    seed script made it (it has the marker). Anything else is refused and left
    untouched, because it may hold real work.
    """
    data_dir = Path(data_dir)
    if data_dir.exists() and not data_dir.is_dir():
        raise SeedRefused(f"{data_dir} is a file, not a folder.")

    was_empty = not data_dir.exists() or not any(data_dir.iterdir())
    emptied = False
    if reset and not was_empty:
        if not (data_dir / MARKER).is_file():
            raise SeedRefused(
                f"The data folder ({data_dir}) already has things in it that the seed "
                "script didn't make, so --reset won't empty it. To start the demo from "
                "scratch, move or delete that folder yourself, or set DOCMANAGER_DATA "
                "to a new folder."
            )
        _empty(data_dir)
        emptied, was_empty = True, True

    clock = (lambda: now) if now else datetime.now
    app = create_app({"DATA_DIR": data_dir, "CLOCK": clock})
    with app.extensions["docmanager_sessions"]() as session:
        have = session.scalars(select(Client)).all()
        refs = {client.ref for client in have}
        names = {client.name.lower() for client in have}
        added = 0
        for ref, name in DEMO_CLIENTS:
            if ref in refs or name.lower() in names:
                continue
            session.add(Client(ref=ref, name=name, created_at=clock()))
            added += 1
        session.commit()

    # Mark only a folder that had nothing else in it: marking one that holds someone's
    # real work would let a later --reset delete it.
    if was_empty:
        (data_dir / MARKER).write_text(
            "Made by `docmanager seed`. `docmanager seed --reset` may empty this folder.\n"
        )
    return SeedResult(
        added=added,
        skipped=len(DEMO_CLIENTS) - added,
        emptied=emptied,
        marked=was_empty,
    )


def _empty(folder: Path) -> None:
    """Delete everything inside `folder`. A link is removed, never followed."""
    for child in folder.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)


BOX_ONE = "Box 1 – 2016–2019"
BOX_TWO = "Box 2 – 2020–2022"


@dataclass
class FillResult:
    filled: bool
    reason: str = ""  # why nothing was added, when `filled` is False

    def message(self) -> str:
        if self.filled:
            return f'Filled "{BOX_ONE}" (paper can go) and "{BOX_TWO}" (still blocked).'
        return f"Left the boxes alone: {self.reason}"


def fill_demo_boxes(
    data_dir, *, now: datetime | None = None, ocr_runner=None
) -> FillResult:
    """Fill two demo boxes with made-up documents, through the real services and OCR.

    Box 1 can have its paper shredded: one Filed document, one with No date, two that
    are Due, and one that is In bin. Box 2 is blocked: photos still to sort, one
    document that Needs checking, and "Not a page" photos in the Bin.

    Only a folder the seed script made (it has the marker) is filled, and only once:
    the boxes would otherwise be added to someone's real work, or twice. If a demo
    document doesn't come out as planned (OCR misread it), it stops and says so.
    `ocr_runner` is for tests; the default is the real OCR program.
    """
    data_dir = Path(data_dir)
    if not (data_dir / MARKER).is_file():
        return FillResult(
            False,
            "this data folder wasn't made by the seed script. Use `--reset` on an "
            "empty or seeded folder to get the demo boxes.",
        )
    if ocr_runner is None and (problems := ocr.check_ocr_tools()):
        raise SeedRefused(
            "The demo boxes need the OCR programs: "
            + " ".join(problems)
            + f" Install them with: {ocr.APT_COMMAND}"
        )
    clock = datetime.now if now is None else (lambda: now)
    overrides = {"DATA_DIR": data_dir, "CLOCK": clock}
    if ocr_runner is not None:
        overrides["OCR_RUNNER"] = ocr_runner
    app = create_app(overrides)
    runner, paths = app.config["OCR_RUNNER"], app.config["PATHS"]
    moment = clock()

    with app.extensions["docmanager_sessions"]() as session:
        taken = session.scalars(
            select(Box.name).where(Box.name.in_((BOX_ONE, BOX_TWO)))
        ).all()
        if taken:
            return FillResult(False, "the demo boxes are already there.")

        def read(box, first, last, expected):
            """Group photos `first` to `last` (inbox numbers) and read the document."""
            numbered = dict(box.ordered_pages())
            made = grouping.make_document(
                session, box, numbered[first].id, numbered[last].id, now=moment
            )
            result = filing.read_document(
                session, made.document, paths=paths, ocr_runner=runner, now=moment
            )
            session.commit()
            if result.outcome != expected:
                raise SeedRefused(
                    f"Demo document {made.document.id} didn't come out as planned: "
                    f"{result.message()}"
                )
            return made.document

        # Box 1: five documents, one page each, no gaps.
        box = _upload(
            session,
            BOX_ONE,
            paths,
            moment,
            _pages(
                photos.SEED_FILED,
                photos.SEED_NO_DATE,
                photos.SEED_DUE_INVOICE,
                photos.SEED_DUE_LETTER,
                photos.SEED_BIN_INVOICE,
            ),
        )
        documents = [read(box, n, n, "filed") for n in range(1, 6)]
        disposal.move_to_bin(session, [documents[4].id], paths=paths, now=moment)
        session.commit()

        # Box 2: a document that needs checking, lens covers, and three loose photos.
        box = _upload(
            session,
            BOX_TWO,
            paths,
            moment,
            [
                *_pages(photos.SEED_UNCLEAR),
                photos.render_lens_cover(),
                *_pages(*photos.SEED_LOOSE_PAGES),
                photos.render_lens_cover(),
            ],
        )
        numbered = dict(box.ordered_pages())
        grouping.discard_pages(
            session, box, [numbered[3].id, numbered[7].id], now=moment
        )
        session.commit()
        read(box, 1, 2, "flagged")

        if documents[4].state != DocState.IN_BIN:  # pragma: no cover - a safety net
            raise SeedRefused("The demo document didn't reach the bin")
    return FillResult(True)


def _pages(*documents):
    return [photos.render_page(page) for doc in documents for page in doc.pages]


def _upload(session, name, paths, moment, images) -> Box:
    """Make the box and upload one photo per image, named IMG_0001.jpg and so on."""
    box = upload.find_or_create_box(session, box_id=None, new_name=name, now=moment)
    files = [
        (f"IMG_{number:04d}.jpg", photos.jpeg_bytes(image, f"{name} photo {number}"))
        for number, image in enumerate(images, start=1)
    ]
    upload.upload_photos(session, box, files, data_dir=paths.root, now=moment)
    session.commit()
    return box
