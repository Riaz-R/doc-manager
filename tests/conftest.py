import io
from datetime import datetime

import pytest
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import docmanager.models  # noqa: F401  (registers every table with Base)
from docmanager import create_app
from docmanager.db import Base

# Every test sees the same "now", so dates never depend on the real clock.
FIXED_NOW = datetime(2026, 10, 27, 12, 0)


@pytest.fixture(autouse=True)
def isolated_data_folder(tmp_path, monkeypatch):
    """Point DOCMANAGER_DATA at a private folder so no test writes to ./data."""
    monkeypatch.setenv("DOCMANAGER_DATA", str(tmp_path / "env-data"))


@pytest.fixture
def now():
    return FIXED_NOW


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def app(data_dir):
    return create_app({"DATA_DIR": data_dir, "CLOCK": lambda: FIXED_NOW})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session():
    """A throwaway in-memory database with every table, for model-level tests."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def photo_bytes(label: str, fmt: str = "JPEG") -> bytes:
    """A made-up photo: the label drawn on white. Different labels give different bytes."""
    image = Image.new("RGB", (600, 800), "white")
    ImageDraw.Draw(image).text((40, 40), label, fill="black", font_size=48)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()
