from datetime import date, datetime

from sqlalchemy.orm import Mapped, mapped_column

from docmanager.db import Base


class StateChange(Base):
    """One row of history for every move a Page or Document makes. Never edited."""

    __tablename__ = "state_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_kind: Mapped[str]  # "page" or "document"
    object_id: Mapped[int]
    action: Mapped[str]
    from_state: Mapped[str | None]  # None for "(new)"
    to_state: Mapped[str | None]  # None for "(row deleted)"
    at: Mapped[datetime]
    note: Mapped[str | None]


class DisposalRecord(Base):
    """Proof that a digital record was destroyed. A snapshot, never edited.

    It is the only thing left of a document once the bin is emptied (SPEC 3.6),
    so it holds plain values, not links to rows that no longer exist.
    """

    __tablename__ = "disposal_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    filed_name: Mapped[str]  # the filename it was last filed under, with any " (2)"
    doc_type_label: Mapped[str]  # for example "Invoice"
    client_ref: Mapped[str]
    client_name: Mapped[str]
    document_date: Mapped[date | None]
    keep_until: Mapped[date | None]
    page_count: Mapped[int]
    binned_at: Mapped[datetime | None]
    destroyed_at: Mapped[datetime]
