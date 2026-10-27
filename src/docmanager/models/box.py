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
