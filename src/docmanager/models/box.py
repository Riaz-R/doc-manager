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
