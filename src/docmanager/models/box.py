from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docmanager.db import Base

if TYPE_CHECKING:  # only for the type names below; the real import would be circular
    from docmanager.models.document import Document
    from docmanager.models.page import Page


class Box(Base):
    """A physical box of paper: a named container for batches, pages and documents."""

    __tablename__ = "boxes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        unique=True
    )  # 1 to 60 characters, checked on upload
    created_at: Mapped[datetime]

    batches: Mapped[list["Batch"]] = relationship(back_populates="box")
    pages: Mapped[list["Page"]] = relationship(back_populates="box")
    documents: Mapped[list["Document"]] = relationship(back_populates="box")

    def ordered_pages(self) -> list[tuple[int, "Page"]]:
        """Every photo in the box as (number, page), in filename order.

        The number counts all the box's photos, whatever state they are in, so a
        photo keeps its number as others leave the inbox ("Photos 3 to 7" stays
        meaningful).
        """
        ordered = sorted(self.pages, key=lambda page: page.order_key)
        return list(enumerate(ordered, start=1))

    def inbox_pages(self) -> list[tuple[int, "Page"]]:
        """The photos still to sort, with the numbers they have in the whole box."""
        from docmanager.models.page import PageState  # page.py imports this file

        return [
            (number, page)
            for number, page in self.ordered_pages()
            if page.state == PageState.INBOX
        ]

    def unread_documents(self) -> list["Document"]:
        """Documents that were made from photos but not read yet, oldest first."""
        from docmanager.models.document import DocState  # document.py imports this file

        return sorted(
            (d for d in self.documents if d.state == DocState.GROUPED),
            key=lambda d: d.id,
        )

    def paper_blockers(self) -> list[str]:
        """One plain-words line for each thing stopping this box's paper from going.

        The paper can go once the box has at least one document, no photo is still
        to sort and every document has been filed (SPEC 3.1). A document moved to the
        bin still counts as filed, "Not a page" photos don't count, and keep-until
        isn't looked at. An empty list means the paper can go.
        """
        from docmanager.models.document import DocState  # document.py imports this file

        to_sort = len(self.inbox_pages())
        needs_checking = unreadable = unread = 0
        for document in self.documents:
            if document.state == DocState.NEEDS_REVIEW:
                needs_checking += 1
            elif document.state == DocState.GROUPED:
                if document.ocr_error:
                    unreadable += 1
                else:
                    unread += 1

        end = "before this paper can go"
        lines = []
        if to_sort:
            lines.append(f"{to_sort} {_plural(to_sort, 'photo')} to sort {end}")
        if needs_checking:
            verb = "needs" if needs_checking == 1 else "need"
            lines.append(
                f"{needs_checking} {_plural(needs_checking, 'document')} {verb} checking {end}"
            )
        if unreadable:
            lines.append(
                f"{unreadable} {_plural(unreadable, 'document')} couldn't be read {end}"
            )
        if unread:
            verb = "hasn't" if unread == 1 else "haven't"
            lines.append(
                f"{unread} {_plural(unread, 'document')} {verb} been read yet {end}"
            )
        if not self.documents:
            lines.append("Nothing filed from this box yet")
        return lines

    def paper_can_go(self) -> bool:
        """The "Paper can go" marker: worked out each time, never stored."""
        return not self.paper_blockers()


def _plural(count: int, noun: str) -> str:
    return noun if count == 1 else f"{noun}s"


class Batch(Base):
    """One upload into a box, kept as a record of what was added, skipped and refused."""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    box_id: Mapped[int] = mapped_column(ForeignKey("boxes.id"))
    uploaded_at: Mapped[datetime]
    added_count: Mapped[int]
    skipped_count: Mapped[int]
    refused_count: Mapped[int]

    box: Mapped[Box] = relationship(back_populates="batches")
    pages: Mapped[list["Page"]] = relationship(back_populates="batch")
