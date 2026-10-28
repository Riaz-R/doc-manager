"""Grouping photos into documents: pick the first and last photo, press Make document.

Nothing here commits: the route does, once the whole grouping has worked.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from docmanager.errors import UserFacingError
from docmanager.models.box import Box
from docmanager.models.document import Document
from docmanager.models.page import PageState


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
