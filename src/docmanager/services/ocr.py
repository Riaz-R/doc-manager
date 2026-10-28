"""Turning photos into a searchable PDF: combine them, then run OCRmyPDF on the result.

OCRmyPDF runs as a separate program, so a crash or a hang in it can never take the
web app down, and a timeout can stop it (SPEC 7).
"""

import io
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import img2pdf
from PIL import Image

from docmanager import config

# What the user sees on a document when reading it failed (SPEC W2).
OCR_ERROR_MESSAGE = "Couldn't read this document. Try again, or retake the photos."

# The program to run: OCRmyPDF as a module of this same Python, so it is always the
# version `uv sync` installed.
OCR_COMMAND = [sys.executable, "-m", "ocrmypdf"]

APT_COMMAND = (
    "sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd ghostscript"
)

_KEEP_OF_ERROR = 2000  # characters of the program's error output kept in the detail


class OcrFailed(Exception):
    """Reading a document failed. `detail` is technical: it goes to the log, not the user."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def combine_photos(photo_paths: list[Path], pdf_path: Path) -> None:
    """Write one PDF with a page for each photo, in the order given."""
    try:
        pdf_path.write_bytes(
            img2pdf.convert([_pdf_ready(path) for path in photo_paths])
        )
    except Exception as error:
        raise OcrFailed(f"Could not combine the photos into a PDF: {error}") from error


def _pdf_ready(path: Path) -> bytes:
    """The photo's bytes, flattened onto white if it is a PNG that img2pdf would refuse.

    img2pdf won't take a PNG with transparency or an unusual colour mode. JPEGs go
    straight in, untouched.
    """
    data = Path(path).read_bytes()
    with Image.open(io.BytesIO(data)) as image:
        if image.format != "PNG" or image.mode in ("RGB", "L"):
            return data
        rgba = image.convert("RGBA")
    flat = Image.new("RGB", rgba.size, "white")
    flat.paste(rgba, mask=rgba.split()[3])
    out = io.BytesIO()
    flat.save(out, format="PNG")
    return out.getvalue()


def run_ocrmypdf(
    pdf_in: Path,
    pdf_out: Path,
    sidecar: Path,
    *,
    timeout: float | None = None,
    command: list[str] | None = None,
) -> None:
    """Read `pdf_in` and write a searchable PDF to `pdf_out` and its text to `sidecar`.

    Raises OcrFailed if the program fails or takes longer than `timeout` seconds
    (default: `config.OCR_TIMEOUT_SECONDS`). `command` replaces the program, for tests.
    """
    timeout = config.OCR_TIMEOUT_SECONDS if timeout is None else timeout
    args = [
        *(command or OCR_COMMAND),
        "-l",
        "eng",
        "--rotate-pages",
        "--deskew",
        "--sidecar",
        str(sidecar),
        str(pdf_in),
        str(pdf_out),
    ]
    # A new session makes the program the head of its own process group, so on a
    # timeout we can stop it and the Tesseract and Ghostscript it started.
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        _, error = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise OcrFailed(
            f"OCRmyPDF timed out after {timeout:g} second{'s' if timeout != 1 else ''}"
        ) from None

    if process.returncode != 0:
        raise OcrFailed(
            f"OCRmyPDF exited with exit code {process.returncode}: "
            f"{error.strip()[-_KEEP_OF_ERROR:]}"
        )
    if not (pdf_out.exists() and sidecar.exists()):
        raise OcrFailed("OCRmyPDF finished but made no output files")


def check_ocr_tools(which=shutil.which, list_languages=None) -> list[str]:
    """Plain-words problems with the programs OCR needs. An empty list means all is well.

    `which` and `list_languages` can be replaced, so tests don't need the real programs.
    """
    problems = []
    if which("tesseract") is None:
        problems.append(
            "Tesseract (the program that reads text from photos) isn't installed."
        )
    else:
        try:
            languages = (list_languages or _tesseract_languages)()
        except (OSError, subprocess.SubprocessError):
            problems.append("Tesseract is installed but won't start.")
        else:
            for code, what in (
                ("eng", "English (eng)"),
                ("osd", "page direction (osd)"),
            ):
                if code not in languages:
                    problems.append(f"Tesseract is missing its {what} data.")
    if which("gs") is None:
        problems.append(
            "Ghostscript (the program that makes PDF files) isn't installed."
        )
    return problems


def _tesseract_languages() -> list[str]:
    result = subprocess.run(
        ["tesseract", "--list-langs"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise OSError(result.stderr)
    # The first line is a heading ("List of available languages ...").
    return result.stdout.split("\n")[1:]
