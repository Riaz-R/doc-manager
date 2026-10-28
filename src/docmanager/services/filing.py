"""Reading a document with OCR, then filing it or flagging it for a person to check.

Nothing here commits except `read_document`, which has to commit before the slow
OCR step (see its docstring); the route commits the result afterwards.
"""

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from docmanager.config import Paths
from docmanager.errors import UserFacingError
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.rules.classify import classify
from docmanager.rules.naming import free_path, relative_path
from docmanager.services.ocr import OCR_ERROR_MESSAGE, OcrFailed, combine_photos

logger = logging.getLogger(__name__)


class FilingError(UserFacingError):
    """Something the user asked for that filing can't do. The message is plain words."""


@dataclass
class ReadResult:
    """What happened when a document was read, in a form the route can show."""

    document: Document
    outcome: str  # "filed", "flagged" or "failed"

    def message(self) -> str:
        if self.outcome == "filed":
            return f"Filed as {self.document.filed_name.removesuffix('.pdf')}"
        if self.outcome == "flagged":
            return "Needs checking: " + "; ".join(self.document.review_reasons)
        return OCR_ERROR_MESSAGE


def read_document(
    session: Session, document: Document, *, paths: Paths, ocr_runner, now: datetime
) -> ReadResult:
    """Read a Grouped document that hasn't been read, then file it or flag it.

    The document is committed first, so that if the app stops during the long OCR
    step the document is still there, Grouped, and can be read again (W4). The
    caller commits the outcome. If the OCR fails, the document stays Grouped with
    `ocr_error` set and the technical detail goes to the log (W2).
    """
    if document.state != DocState.GROUPED or document.ocr_text is not None:
        raise FilingError("This document has already been read")
    session.commit()

    images_pdf = paths.work / f"{document.id}-images.pdf"
    searchable = paths.work / f"{document.id}.pdf"
    sidecar = paths.work / f"{document.id}.txt"
    paths.work.mkdir(parents=True, exist_ok=True)
    for stale in (searchable, sidecar):  # left over from an attempt that failed
        stale.unlink(missing_ok=True)

    try:
        combine_photos(
            [paths.root / page.photo_path for page in document.pages], images_pdf
        )
        ocr_runner(images_pdf, searchable, sidecar)
        text = sidecar.read_text(encoding="utf-8", errors="replace")
    except OcrFailed as error:
        logger.error("Reading document %s failed: %s", document.id, error.detail)
        for partial in (searchable, sidecar):
            partial.unlink(missing_ok=True)
        document.ocr_error = OCR_ERROR_MESSAGE
        return ReadResult(document, "failed")
    finally:
        images_pdf.unlink(missing_ok=True)

    document.ocr_text = text
    document.ocr_error = None
    document.pdf_path = f"work/{document.id}.pdf"

    found = classify(text, session.scalars(select(Client)).all(), now.date())
    document.doc_type = found.doc_type
    document.fields = found.fields
    document.document_date = found.document_date
    document.type_score = found.type_score
    document.runner_up_score = found.runner_up_score
    document.client = found.client
    document.review_reasons = list(found.reasons)

    if found.passed:
        _file(document, paths, searchable, now)
        return ReadResult(document, "filed")
    document.apply("flag", now=now)
    return ReadResult(document, "flagged")


def _file(document: Document, paths: Paths, searchable, now: datetime) -> None:
    """Move the searchable PDF to its archive path and mark the document Filed."""
    path = free_path(
        relative_path(
            client_ref=document.client.ref,
            client_name=document.client.name,
            doc_type=document.type,
            fields=document.fields,
            document_date=document.document_date,
        ),
        lambda candidate: (paths.archive / candidate).exists(),
    )
    document.apply("file", now=now)  # the guards have the last word
    target = paths.archive / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(searchable, target)
    document.pdf_path = f"archive/{path.as_posix()}"
    document.filed_name = path.name
    document.filed_at = now
