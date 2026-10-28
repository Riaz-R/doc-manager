"""Grouping photos into documents: pick the first and last photo, press Make document.

Nothing here commits: the route does, once the whole grouping has worked.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from docmanager.errors import UserFacingError
from docmanager.models.box import Box
from docmanager.models.document import Document
from docmanager.models.page import Page, PageState


class GroupingError(UserFacingError):
    """A grouping the app won't do. The message is plain words."""


@dataclass
class MadeDocument:
    """The new document, and which inbox numbers its range ran from and to."""

    document: Document
    first_number: int
    last_number: int

    def message(self) -> str:
        if self.first_number == self.last_number:
            return f"Document made from photo {self.first_number}"
        return f"Document made from photos {self.first_number} to {self.last_number}"


def make_document(
    session: Session,
    box: Box,
    first_page_id: int | None,
    last_page_id: int | None,
    *,
    now: datetime,
) -> MadeDocument:
    """Group the inbox photos from `first_page_id` to `last_page_id` into a new document."""
    if first_page_id is None or last_page_id is None:
        raise GroupingError("Pick both the first and the last page")

    numbers = {page.id: number for number, page in box.ordered_pages()}
    if first_page_id not in numbers or last_page_id not in numbers:
        raise GroupingError("That photo isn't in this box")
    # If the two are the wrong way round, swap them.
    first, last = sorted((numbers[first_page_id], numbers[last_page_id]))

    in_range = [
        (number, page)
        for number, page in box.ordered_pages()
        if first <= number <= last
    ]
    if any(page.state == PageState.GROUPED for _, page in in_range):
        raise GroupingError(
            f"Photos {first} to {last} include a photo that is already in a document"
        )
    for number in (first, last):
        page = dict(in_range)[number]
        if page.state == PageState.DISCARDED:
            raise GroupingError(f"Photo {number} is marked as not a page")

    # A "Not a page" photo inside the range stays where it is.
    pages = [page for _, page in in_range if page.state == PageState.INBOX]

    document = Document(box=box, created_at=now)
    session.add(document)
    document.apply("group", now=now)
    for position, page in enumerate(pages, start=1):
        page.document = document
        page.position = position
        page.apply("group", now=now)
    return MadeDocument(document, first, last)


def discard_pages(
    session: Session, box: Box, page_ids: list[int], *, now: datetime
) -> int:
    """Mark the photos with these ids "Not a page": they leave the inbox for the Bin.

    Returns how many photos were marked. If any one is refused, none are.
    """
    ids = set(page_ids)
    if not ids:
        raise GroupingError("Tick the photos that are not pages")
    pages = {page.id: page for page in box.pages}
    if not ids <= pages.keys():
        raise GroupingError("That photo isn't in this box")
    for page_id in sorted(ids):
        pages[page_id].apply("discard", now=now)
    return len(ids)


def restore_page(session: Session, page_id: int, *, now: datetime) -> Page:
    """Take a "Not a page" photo out of the Bin and back into its box's inbox."""
    page = session.get(Page, page_id)
    if page is None:
        raise GroupingError("That photo isn't in the Bin")
    page.apply("restore", now=now)
    return page


def binned_pages(session: Session) -> list[Page]:
    """Every "Not a page" photo, grouped by box and in filename order."""
    pages = session.scalars(
        select(Page).where(Page._state == PageState.DISCARDED.value)
    ).all()
    return sorted(pages, key=lambda page: (page.box_id, *page.order_key))


def bin_count(session: Session) -> int:
    """How many items are in the Bin. Only photos so far; documents join in Task 22."""
    return session.scalar(
        select(func.count(Page.id)).where(Page._state == PageState.DISCARDED.value)
    )
