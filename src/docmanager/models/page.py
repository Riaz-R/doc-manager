from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docmanager.db import Base
from docmanager.lifecycle import Lifecycle, Stateful
from docmanager.models.box import Batch, Box

if TYPE_CHECKING:  # only for the type name below; the real import would be circular
    from docmanager.models.document import Document


class PageState(StrEnum):
    INBOX = "inbox"
    GROUPED = "grouped"
    DISCARDED = "discarded"

    @property
    def label(self) -> str:
        return {
            PageState.INBOX: "To sort",
            PageState.GROUPED: "In a document",
            PageState.DISCARDED: "Not a page (in bin)",
        }[self]


# SPEC 3.3. None on the left is "(new)"; None on the right is "(row deleted)".
PAGE_LIFECYCLE = Lifecycle(
    noun="photo",
    state_type=PageState,
    transitions={
        (None, "upload"): PageState.INBOX,
        (PageState.INBOX, "group"): PageState.GROUPED,
        (PageState.INBOX, "discard"): PageState.DISCARDED,
        (PageState.DISCARDED, "restore"): PageState.INBOX,
        (PageState.GROUPED, "destroy"): None,
        (PageState.DISCARDED, "destroy"): None,
    },
    phrases={
        "upload": "uploaded",
        "group": "put in a document",
        "discard": "marked as not a page",
        "restore": "restored",
        "destroy": "destroyed",
    },
)


class Page(Stateful, Base):
    """One photo."""

    __tablename__ = "pages"
    kind = "page"
    lifecycle = PAGE_LIFECYCLE

    id: Mapped[int] = mapped_column(primary_key=True)
    box_id: Mapped[int] = mapped_column(ForeignKey("boxes.id"))
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    sha256: Mapped[str] = mapped_column(
        unique=True
    )  # of the uploaded bytes: the duplicate check
    original_filename: Mapped[
        str
    ]  # for display and ordering only, never used to build a path
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    position: Mapped[int | None]  # page number within its document
    photo_path: Mapped[str]  # relative to the data folder
    thumb_path: Mapped[str]

    box: Mapped[Box] = relationship(back_populates="pages")
    batch: Mapped[Batch] = relationship(back_populates="pages")
    document: Mapped["Document | None"] = relationship(back_populates="pages")
