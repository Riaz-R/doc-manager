"""Putting photos into a box: checking each file, storing it and recording the upload.

Nothing here commits to the database: the route does that once the whole upload
has worked, so a refusal never leaves half a box behind.
"""

import hashlib
import io
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from PIL import Image
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from docmanager import config
from docmanager.errors import UserFacingError
from docmanager.models.box import Batch, Box
from docmanager.models.page import Page, PageState

MAX_BOX_NAME_LENGTH = 60
HEIC_EXTENSIONS = (".heic", ".heif")
HEIC_ADVICE = (
    "iPhone HEIC photos aren't supported yet. "
    "On the iPhone: Settings → Camera → Formats → Most Compatible."
)
# What Pillow calls each format we accept, and the extension we store it under.
EXTENSIONS = {"JPEG": "jpg", "PNG": "png"}


class UploadRefused(UserFacingError):
    """An upload (or a new box name) the app won't accept. The message is plain words."""


@dataclass
class UploadResult:
    """What an upload did, so the user can be told in one message."""

    added: int = 0
    skipped: int = 0
    refused: list[str] = field(
        default_factory=list
    )  # names of files that aren't photos
    refused_heic: list[str] = field(default_factory=list)

    def message(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{self.added} {_photos(self.added)} added.")
        if self.skipped:
            parts.append(f"{self.skipped} skipped – already uploaded.")
        if self.refused:
            parts.append(
                f"{len(self.refused)} refused – not a photo ({_names(self.refused)})."
            )
        if self.refused_heic:
            parts.append(
                f"{len(self.refused_heic)} refused – iPhone HEIC photo "
                f"({_names(self.refused_heic)}). {HEIC_ADVICE}"
            )
        return " ".join(parts)

    @property
    def refused_count(self) -> int:
        return len(self.refused) + len(self.refused_heic)


def _photos(count: int) -> str:
    return "photo" if count == 1 else "photos"


def _names(names: list[str]) -> str:
    return ", ".join(names)


def find_or_create_box(
    session: Session, *, box_id: int | None, new_name: str, now: datetime
) -> Box:
    """The existing box with `box_id`, or, when `box_id` is None, a new box called `new_name`."""
    if box_id is not None:
        box = session.get(Box, box_id)
        if box is None:
            raise UploadRefused("That box doesn't exist")
        return box

    name = new_name.strip()
    if not name:
        raise UploadRefused("Give the new box a name")
    if len(name) > MAX_BOX_NAME_LENGTH:
        raise UploadRefused(
            f"Box names can be at most {MAX_BOX_NAME_LENGTH} characters"
        )
    if session.scalar(select(Box).where(Box.name == name)) is not None:
        raise UploadRefused(f"There is already a box called {name}")

    box = Box(name=name, created_at=now)
    session.add(box)
    session.flush()  # the database gives the box its id
    return box


def upload_photos(
    session: Session,
    box: Box,
    files: Iterable[tuple[str, bytes]],
    *,
    data_dir,
    now: datetime,
) -> UploadResult:
    """Check, store and record each (filename, content) pair as a page in `box`.

    `files` can be a generator, so only one file's bytes are held at a time.
    """
    batch = Batch(
        box=box, uploaded_at=now, added_count=0, skipped_count=0, refused_count=0
    )
    session.add(batch)
    session.flush()

    result = UploadResult()
    seen: set[str] = set()  # fingerprints already handled in this upload
    for raw_name, data in files:
        name = _display_name(raw_name)
        if name.lower().endswith(HEIC_EXTENSIONS):
            result.refused_heic.append(name)
            continue
        extension = _photo_extension(data)
        if extension is None:
            result.refused.append(name)
            continue

        sha256 = hashlib.sha256(data).hexdigest()
        if sha256 in seen or _is_in_the_app(session, sha256):
            result.skipped += 1
            continue
        seen.add(sha256)

        photo_path = f"photos/{box.id}/{sha256}.{extension}"
        thumb_path = f"thumbs/{box.id}/{sha256}.jpg"
        _write(data_dir / photo_path, data)
        _write_thumbnail(data, data_dir / thumb_path)

        page = Page(
            box=box,
            batch=batch,
            sha256=sha256,
            original_filename=name,
            photo_path=photo_path,
            thumb_path=thumb_path,
        )
        session.add(page)
        page.apply("upload", now=now)
        result.added += 1

    batch.added_count = result.added
    batch.skipped_count = result.skipped
    batch.refused_count = result.refused_count
    return result


def boxes_with_inbox_counts(session: Session) -> list[tuple[Box, int]]:
    """Every box with the number of its photos still to sort, for Home."""
    inbox = and_(Page.box_id == Box.id, Page._state == PageState.INBOX.value)
    rows = session.execute(
        select(Box, func.count(Page.id))
        .outerjoin(Page, inbox)
        .group_by(Box.id)
        .order_by(Box.id)
    )
    return [(box, count) for box, count in rows]


def _display_name(raw_name: str) -> str:
    """The bare filename: some browsers send a whole path. Used for display only."""
    return raw_name.replace("\\", "/").rsplit("/", 1)[-1]


def _photo_extension(data: bytes) -> str | None:
    """ "jpg" or "png" when the bytes decode fully as that kind of photo, else None."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            extension = EXTENSIONS.get(image.format)
            if extension is None:
                return None
            image.load()  # decoding every pixel is what catches a cut-off file
            return extension
    except Exception:  # noqa: BLE001  (Pillow raises many kinds of error for damaged files)
        return None


def _is_in_the_app(session: Session, sha256: str) -> bool:
    return session.scalar(select(Page.id).where(Page.sha256 == sha256)) is not None


def _write(path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _write_thumbnail(data: bytes, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(data)) as image:
        thumb = image.convert("RGB")
    thumb.thumbnail((config.THUMB_SIZE, config.THUMB_SIZE))
    thumb.save(path, format="JPEG")
