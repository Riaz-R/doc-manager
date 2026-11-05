"""Moving documents to the bin and back, and destroying what is in the bin.

The database is changed first and the files after, so a refusal never leaves a
file moved. Nothing here commits, except `empty_bin`, which has to (see its
docstring); the route commits everything else.
"""

import logging
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from docmanager.config import Paths
from docmanager.errors import UserFacingError
from docmanager.lifecycle import InvalidTransition
from docmanager.models.document import DocState, Document
from docmanager.models.page import Page, PageState
from docmanager.models.records import DisposalRecord, StateChange
from docmanager.rules.naming import free_path, relative_path

logger = logging.getLogger(__name__)


class DisposalError(UserFacingError):
    """Something the user asked for that disposal can't do. The message is plain words."""


def due_documents(session: Session, today: date) -> list[Document]:
    """Filed documents whose keep-until day has passed, the oldest keep-until first.

    A document is kept through its keep-until day, and one with no keep-until is
    never listed (R4, R5).
    """
    return list(
        session.scalars(
            select(Document)
            .where(
                Document._state == DocState.FILED.value,
                Document.keep_until < today,
            )
            .order_by(Document.keep_until, Document.id)
        )
    )


def binned_documents(session: Session) -> list[Document]:
    """Every document in the bin, the longest-binned first."""
    return list(
        session.scalars(
            select(Document)
            .where(Document._state == DocState.IN_BIN.value)
            .order_by(Document.binned_at, Document.id)
        )
    )


def _documents(session: Session, ids: list[int]) -> list[Document]:
    found = []
    for document_id in dict.fromkeys(ids):  # in order, each once
        document = session.get(Document, document_id)
        if document is None:
            raise DisposalError("That document can't be found")
        found.append(document)
    return found


def move_to_bin(
    session: Session, ids: list[int], *, paths: Paths, now: datetime
) -> int:
    """Move documents to the bin: state, `binned_at`, and the PDF to bin/<id>.pdf.

    Every document is checked first (D2), so one that must still be kept stops the
    whole move and nothing changes. A document whose PDF has gone from disk is
    still binned, so it can be destroyed in the end. Returns how many were moved.
    """
    if not ids:
        raise DisposalError("Tick the documents to move to the bin")
    documents = _documents(session, ids)
    for document in documents:
        document.lifecycle.target(document.state, "dispose")
        reason = document.guard_dispose(now)
        if reason:
            raise InvalidTransition(reason)

    paths.bin.mkdir(parents=True, exist_ok=True)
    for document in documents:
        source = paths.root / (document.pdf_path or "")
        target = paths.bin / f"{document.id}.pdf"
        document.apply("dispose", now=now)
        document.binned_at = now
        if document.pdf_path and source.is_file():
            shutil.move(source, target)
        document.pdf_path = f"bin/{document.id}.pdf"
    return len(documents)


def restore_document(
    session: Session, document_id: int, *, paths: Paths, now: datetime
) -> Document:
    """Take a document out of the bin and back into the archive at its calculated path.

    A name already taken gets " (2)", " (3)" ... (N3). The document is refused, and
    stays in the bin, if its PDF is no longer there.
    """
    (document,) = _documents(session, [document_id])
    document.lifecycle.target(document.state, "restore")
    source = paths.root / (document.pdf_path or "")
    if not document.pdf_path or not source.is_file():
        raise DisposalError(
            "The PDF file is missing, so this document can't be restored"
        )

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
    document.apply("restore", now=now)
    target: Path = paths.archive / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(source, target)
    document.pdf_path = f"archive/{path.as_posix()}"
    document.filed_name = path.name
    document.binned_at = None
    return document


@dataclass
class DestroyResult:
    """What emptying the bin destroyed, in a form the route can show."""

    documents: int
    photos: int

    def message(self) -> str:
        parts = []
        if self.documents:
            parts.append(
                f"{self.documents} {'document' if self.documents == 1 else 'documents'}"
            )
        if self.photos:
            parts.append(f"{self.photos} {'photo' if self.photos == 1 else 'photos'}")
        text = " and ".join(parts) + " destroyed."
        if self.documents:
            text += " A disposal record was kept for each document."
        return text


def empty_bin(
    session: Session,
    document_ids: list[int],
    page_ids: list[int],
    *,
    paths: Paths,
    now: datetime,
) -> DestroyResult:
    """Destroy the listed documents and "Not a page" photos for good (SPEC 3.6, D5, D6).

    Only the ids the person was shown are touched, and only if they are still in
    the bin: one that was restored since is left alone. For each document one
    DisposalRecord is written and the Document, its Page and StateChange rows are
    deleted; photos are deleted the same way with no record. The rows go in one
    transaction, which this function commits, and only then are the files deleted
    (decision 15): if the commit fails, no file has been lost.
    """
    documents = [
        d
        for d in _optional(session, Document, document_ids)
        if d.state == DocState.IN_BIN
    ]
    photos = [
        p for p in _optional(session, Page, page_ids) if p.state == PageState.DISCARDED
    ]
    if not documents and not photos:
        raise DisposalError("Nothing to destroy")

    files: list[Path] = []
    for document in documents:
        session.add(
            DisposalRecord(
                filed_name=document.filed_name or "",
                doc_type_label=document.type.label if document.type else "Unclassified",
                client_ref=document.client.ref if document.client else "",
                client_name=document.client.name if document.client else "",
                document_date=document.document_date,
                keep_until=document.keep_until,
                page_count=len(document.pages),
                binned_at=document.binned_at,
                destroyed_at=now,
            )
        )
        files.append(paths.root / (document.pdf_path or "bin/none"))
        files += [paths.work / f"{document.id}.pdf", paths.work / f"{document.id}.txt"]
        document.apply("destroy", now=now)
        for page in list(document.pages):
            page.apply("destroy", now=now)
            files += [paths.root / page.photo_path, paths.root / page.thumb_path]
            _delete_rows(session, page, "page")
        _delete_rows(session, document, "document")
    for page in photos:
        page.apply("destroy", now=now)
        files += [paths.root / page.photo_path, paths.root / page.thumb_path]
        _delete_rows(session, page, "page")

    session.commit()
    for file in files:
        try:
            file.unlink(missing_ok=True)
        except OSError:
            logger.exception("Couldn't delete %s after emptying the bin", file)
    return DestroyResult(len(documents), len(photos))


def _optional(session: Session, model, ids: list[int]) -> list:
    """The rows for `ids` that exist; an id that is gone is skipped."""
    rows = (session.get(model, i) for i in dict.fromkeys(ids))
    return [row for row in rows if row is not None]


def _delete_rows(session: Session, item, kind: str) -> None:
    """Delete an object's row and all of its history."""
    for change in session.scalars(
        select(StateChange).where(
            StateChange.object_kind == kind, StateChange.object_id == item.id
        )
    ):
        session.delete(change)
    session.flush()  # the destroy StateChange added by apply() is in the database now
    session.delete(item)
