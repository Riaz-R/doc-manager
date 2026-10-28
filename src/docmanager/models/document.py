from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docmanager import config
from docmanager.db import Base
from docmanager.lifecycle import Lifecycle, Stateful
from docmanager.models.box import Box
from docmanager.models.client import Client
from docmanager.models.document_types import DOCUMENT_TYPES, DocumentType
from docmanager.models.page import Page
from docmanager.rules.classify import LOW_TEXT_REASON, count_words
from docmanager.rules.dates import format_date


class DocState(StrEnum):
    GROUPED = "grouped"
    NEEDS_REVIEW = "needs_review"
    FILED = "filed"
    IN_BIN = "in_bin"

    @property
    def label(self) -> str:
        return {
            DocState.GROUPED: "Not read yet",
            DocState.NEEDS_REVIEW: "Needs checking",
            DocState.FILED: "Filed",
            DocState.IN_BIN: "In bin",
        }[self]


# SPEC 3.4. None on the left is "(new)"; None on the right is "(row deleted)".
DOC_LIFECYCLE = Lifecycle(
    noun="document",
    state_type=DocState,
    transitions={
        (None, "group"): DocState.GROUPED,
        (DocState.GROUPED, "file"): DocState.FILED,
        (DocState.GROUPED, "flag"): DocState.NEEDS_REVIEW,
        (DocState.NEEDS_REVIEW, "confirm"): DocState.FILED,
        (DocState.FILED, "dispose"): DocState.IN_BIN,
        (DocState.IN_BIN, "restore"): DocState.FILED,
        (DocState.IN_BIN, "destroy"): None,
    },
    phrases={
        "group": "made",
        "file": "filed",
        "flag": "flagged for checking",
        "confirm": "confirmed",
        "dispose": "moved to the bin",
        "restore": "restored",
        "destroy": "destroyed",
    },
)


class Document(Stateful, Base):
    """Pages that belong together, read and filed as one searchable PDF."""

    __tablename__ = "documents"
    kind = "document"
    lifecycle = DOC_LIFECYCLE

    id: Mapped[int] = mapped_column(primary_key=True)
    box_id: Mapped[int] = mapped_column(ForeignKey("boxes.id"))
    doc_type: Mapped[str | None]  # the key of a DocumentType; None means "Unclassified"
    # JSON columns: always assign a new dict or list, because SQLAlchemy can't see
    # changes made inside the old one.
    fields: Mapped[dict] = mapped_column(JSON, default=dict)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    document_date: Mapped[date | None]  # the date that starts the retention clock
    keep_until: Mapped[date | None]
    ocr_text: Mapped[str | None] = mapped_column(Text)
    ocr_error: Mapped[str | None] = mapped_column(Text)
    type_score: Mapped[int | None]
    runner_up_score: Mapped[int | None]
    review_reasons: Mapped[list] = mapped_column(JSON, default=list)
    pdf_path: Mapped[str | None]  # relative to the data folder
    filed_name: Mapped[str | None]  # the archive filename, including any " (2)" suffix
    created_at: Mapped[datetime | None]
    filed_at: Mapped[datetime | None]
    binned_at: Mapped[datetime | None]

    box: Mapped[Box] = relationship(back_populates="documents")
    client: Mapped[Client | None] = relationship()
    pages: Mapped[list[Page]] = relationship(
        back_populates="document", order_by=Page.position
    )

    @property
    def type(self) -> DocumentType | None:
        """The DocumentType this document holds, or None while it is "Unclassified"."""
        return DOCUMENT_TYPES.get(self.doc_type)

    def change_type(self, new_type: DocumentType, *, today: date) -> None:
        """Swap this document's type, and read its fields and date again for the new type.

        The row, its id, its pages and its state stay as they are (SPEC 3.4).
        """
        found = new_type.extract(self.ocr_text or "", today)
        self.doc_type = new_type.key
        self.document_date = found.pop("document_date")
        self.fields = (
            found  # a new dict: SQLAlchemy can't see changes inside the old one
        )

    @property
    def state_label(self) -> str:
        """What to show the user. A grouped document that failed to read says so."""
        if self.state is None:
            return "New"
        if self.state == DocState.GROUPED and self.ocr_error:
            return "Couldn't read"
        return self.state.label

    def is_due(self, today: date) -> bool:
        """Filed, with a keep-until date that is already behind us."""
        return (
            self.state == DocState.FILED
            and self.keep_until is not None
            and today > self.keep_until
        )

    # Guards. Each returns a plain-words reason to refuse, or None to allow.

    def _filing_problem(self, *, needs_enough_text: bool) -> str | None:
        if self.ocr_text is None:
            return "This document hasn't been read yet"
        if needs_enough_text and count_words(self.ocr_text) < config.MIN_OCR_WORDS:
            return LOW_TEXT_REASON
        if self.doc_type is None:
            return "Choose a type before filing"
        if self.client_id is None and self.client is None:
            return "Choose a client before filing"
        return None

    def guard_file(self, now: datetime) -> str | None:
        # Filing happens without a person looking, so the text must be enough to trust.
        return self._filing_problem(needs_enough_text=True)

    def guard_confirm(self, now: datetime) -> str | None:
        # A person has looked at the document in review, so little text is fine.
        return self._filing_problem(needs_enough_text=False)

    def guard_flag(self, now: datetime) -> str | None:
        if self.ocr_text is None:
            return "This document hasn't been read yet"
        return None

    def guard_dispose(self, now: datetime) -> str | None:
        if self.is_due(now.date()):
            return None
        if self.keep_until is None:
            return "Keep-until not set – add the document's date"
        return f"This document must be kept until {format_date(self.keep_until)}"
