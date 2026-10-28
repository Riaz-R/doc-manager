"""Reading a document with OCR, then filing it or flagging it for a person to check.

Nothing here commits except `read_document`, which has to commit before the slow
OCR step (see its docstring); the route commits the result afterwards.
"""

import logging
import re
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from docmanager.config import Paths
from docmanager.errors import UserFacingError
from docmanager.lifecycle import InvalidTransition
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.models.document_types import DOCUMENT_TYPES
from docmanager.rules.classify import classify
from docmanager.rules.dates import parse_date
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
        _file(document, paths, searchable, now, action="file")
        return ReadResult(document, "filed")
    document.apply("flag", now=now)
    return ReadResult(document, "flagged")


def _file(
    document: Document, paths: Paths, searchable, now: datetime, *, action: str
) -> None:
    """Move the searchable PDF to its archive path and mark the document Filed.

    `action` is "file" (the app decided) or "confirm" (a person did, in review).
    """
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
    document.apply(action, now=now)  # the guards have the last word
    target = paths.archive / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(searchable, target)
    document.pdf_path = f"archive/{path.as_posix()}"
    document.filed_name = path.name
    document.filed_at = now


# The values the Check document screen can show, in the order it shows them: the
# date, then the fields of every type (decision 13).
_DATE = "date"
_ALL_FIELDS = tuple(
    dict.fromkeys(name for t in DOCUMENT_TYPES.values() for name, _ in t.field_labels)
)
_AMOUNT = re.compile(r"\d+(?:\.\d{1,2})?")


def shown_values(document: Document) -> dict[str, str]:
    """The date and every type's fields as the Check screen shows them, as text.

    A field that belongs to some other type than the document's is shown empty.
    These are what the form carries in its hidden inputs, so the next step can tell
    what the person changed.
    """
    shown = {_DATE: _date_text(document.document_date)}
    for name in _ALL_FIELDS:
        value = document.fields.get(name) if document.type else None
        shown[name] = _field_text(name, value)
    return shown


def _date_text(day: date | None) -> str:
    return day.strftime("%d/%m/%Y") if day else ""


def _field_text(name: str, value) -> str:
    if value is None:
        return ""
    if name == "amount_pence":
        return f"{value // 100}.{value % 100:02d}"
    return str(value)


def _read_field(name: str, text: str):
    """What a typed field means: its stored value, or None if it was left blank."""
    text = text.strip()
    if not text:
        return None
    if name != "amount_pence":
        return text
    cleaned = text.replace("£", "").replace(",", "").strip()
    if not _AMOUNT.fullmatch(cleaned):
        raise FilingError("Amount due must be a number like 120.00")
    return int((Decimal(cleaned) * 100).to_integral_value())


def _read_date(text: str, today: date) -> date | None:
    text = text.strip()
    if not text:
        return None
    when = parse_date(text)
    if when is None:
        raise FilingError(f'Couldn\'t read the date "{text}". Write it like 14/03/2021')
    if when > today:
        raise FilingError("The date can't be after today")
    return when


def confirm_document(
    session: Session,
    document: Document,
    *,
    type_key: str | None,
    client_id: int | None,
    posted: dict[str, str],
    shown: dict[str, str],
    paths: Paths,
    now: datetime,
) -> ReadResult:
    """File a document that was Needs checking, using what the person chose and typed.

    `type_key` and `client_id` of None mean "keep what the document has". The final
    values follow decision 13: start from the stored values, or, if the type was
    changed, from a fresh reading of the OCR text for the new type; then any value
    whose posted text differs from the `shown` text (the person typed it) replaces
    the starting value. A refusal changes nothing. The caller commits.
    """
    document.lifecycle.target(document.state, "confirm")  # only from Needs checking

    chosen = document.type if type_key is None else DOCUMENT_TYPES.get(type_key)
    if client_id is None:
        client = document.client
    else:
        client = session.get(Client, client_id)
        if client is None:
            raise FilingError("That client isn't in your client list")

    # The final values, worked out before anything on the document changes.
    names = [name for name, _ in chosen.field_labels] if chosen else []
    fields: dict = {}
    when = None
    if chosen is not None:
        if chosen.key != document.doc_type:
            fresh = chosen.extract(document.ocr_text or "", now.date())
            when = fresh.pop("document_date")
            fields = {name: fresh.get(name) for name in names}
        else:
            when = document.document_date
            fields = {name: document.fields.get(name) for name in names}
        if _changed(_DATE, posted, shown):
            when = _read_date(posted[_DATE], now.date())
        for name in names:
            if _changed(name, posted, shown):
                fields[name] = _read_field(name, posted[name])

    before = (
        document.doc_type,
        document.fields,
        document.document_date,
        document.client,
    )
    document.doc_type = chosen.key if chosen else None
    document.fields = (
        fields  # a new dict: SQLAlchemy can't see changes inside the old one
    )
    document.document_date = when
    document.client = client
    try:
        reason = document.guard_confirm(now)
        if reason:
            raise InvalidTransition(reason)
        work = paths.root / (document.pdf_path or "")
        if not document.pdf_path or not work.is_file():
            raise FilingError(
                "The PDF file is missing, so this document can't be filed"
            )
        _file(document, paths, work, now, action="confirm")
    except UserFacingError:
        document.doc_type, document.fields, document.document_date, document.client = (
            before
        )
        raise
    return ReadResult(document, "filed")


def documents_needing_check(session: Session) -> list[Document]:
    """Every document in Needs checking, oldest first."""
    return list(
        session.scalars(
            select(Document)
            .where(Document._state == DocState.NEEDS_REVIEW.value)
            .order_by(Document.created_at, Document.id)
        )
    )


def planned_filename(document: Document, paths: Paths) -> str | None:
    """The filename the document would be filed under now, or None without a type and client."""
    if document.type is None or document.client is None:
        return None
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
    return path.name


def _changed(name: str, posted: dict[str, str], shown: dict[str, str]) -> bool:
    """Did the person type something different from what the screen showed?"""
    return name in posted and posted[name].strip() != shown.get(name, "").strip()
