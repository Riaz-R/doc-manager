"""Moving documents to the bin and back. (Emptying the bin joins in task 23.)

The database is changed first and the files after, so a refusal never leaves a
file moved. Nothing here commits; the route does.
"""

import shutil
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from docmanager.config import Paths
from docmanager.errors import UserFacingError
from docmanager.lifecycle import InvalidTransition
from docmanager.models.document import DocState, Document
from docmanager.rules.naming import free_path, relative_path


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
