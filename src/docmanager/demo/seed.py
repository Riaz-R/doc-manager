"""The seed script: made-up clients for the demo, and a safe way to start over.

Clients only come from here until the should tier (SPEC 3.5). Everything is invented.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from docmanager import create_app
from docmanager.errors import UserFacingError
from docmanager.models.client import Client

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
