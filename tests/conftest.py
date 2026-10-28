import io
import shutil
from datetime import datetime

import pytest
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import docmanager.models  # noqa: F401  (registers every table with Base)
from docmanager import create_app
from docmanager.db import Base
from docmanager.services import ocr
from docmanager.services.ocr import OcrFailed

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


class FakeOcr:
    """Stands in for OCRmyPDF in tests: copies the PDF and writes `text` as the sidecar.

    Set `fail` to a technical message and the next calls raise OcrFailed instead.
    Every call is recorded in `calls` as (input pdf, output pdf, sidecar).
    """

    def __init__(self, text: str = "", fail: str | None = None):
        self.text = text
        self.fail = fail
        self.calls = []

    def __call__(self, pdf_in, pdf_out, sidecar):
        self.calls.append((pdf_in, pdf_out, sidecar))
        if self.fail:
            raise OcrFailed(self.fail)
        shutil.copyfile(pdf_in, pdf_out)
        sidecar.write_text(self.text)


@pytest.fixture
def fake_ocr():
    """A FakeOcr that fails until a test gives it some text (`fake_ocr.fail = None`)."""
    return FakeOcr(fail="fake OCR: not set up for this test")


@pytest.fixture
def app(data_dir, fake_ocr):
    # Tests never run the real OCR program, unless they are marked "ocr".
    return create_app(
        {"DATA_DIR": data_dir, "CLOCK": lambda: FIXED_NOW, "OCR_RUNNER": fake_ocr}
    )


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


def pytest_collection_modifyitems(config, items):
    """Skip the slow "ocr" tests, with a clear reason, if the OCR programs are missing."""
    problems = ocr.check_ocr_tools()
    if not problems:
        return
    reason = "OCR tools missing: " + " ".join(problems) + f" Install: {ocr.APT_COMMAND}"
    for item in items:
        if "ocr" in item.keywords:
            item.add_marker(pytest.mark.skip(reason=reason))
