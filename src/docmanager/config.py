"""Settings that never change while the app runs."""

import os
from dataclasses import dataclass
from pathlib import Path

# The app only ever listens on this computer. There is deliberately no way to change it.
HOST = "127.0.0.1"
PORT = 5000

# Classification (SPEC 5.5)
MIN_TYPE_SCORE = 6
MIN_TYPE_MARGIN = 3
MIN_OCR_WORDS = 20

# Where filed documents go (SPEC 5.6)
NAMING_TEMPLATE = (
    "{client_ref} {client_name}/{type_plural}/{date} {type_label} {key}.pdf"
)

OCR_TIMEOUT_SECONDS = 300
THUMB_SIZE = 400
MAX_UPLOAD_BYTES = 500 * 1024 * 1024


@dataclass(frozen=True)
class Paths:
    """Every place the app keeps files, all inside one data folder."""

    root: Path

    @classmethod
    def from_env(cls) -> "Paths":
        return cls(Path(os.environ.get("DOCMANAGER_DATA", "data")))

    @property
    def photos(self) -> Path:
        return self.root / "photos"

    @property
    def thumbs(self) -> Path:
        return self.root / "thumbs"

    @property
    def work(self) -> Path:
        return self.root / "work"

    @property
    def archive(self) -> Path:
        return self.root / "archive"

    @property
    def bin(self) -> Path:
        return self.root / "bin"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def db(self) -> Path:
        return self.root / "app.db"

    def make_folders(self) -> None:
        for folder in (
            self.photos,
            self.thumbs,
            self.work,
            self.archive,
            self.bin,
            self.logs,
        ):
            folder.mkdir(parents=True, exist_ok=True)
