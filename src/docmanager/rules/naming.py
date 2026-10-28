"""Where a filed document goes: the archive path built from the naming template.

Pure functions: nothing here touches the disk. The caller says whether a path is
already taken, so the clash rule can be tested without files.
"""

import re
from collections.abc import Callable
from datetime import date
from pathlib import PurePosixPath

from docmanager import config
from docmanager.models.document_types import DocumentType

# Characters Windows won't allow in a file name, plus control characters.
_UNSAFE = re.compile(r'[/\\:*?"<>|\x00-\x1f]')


def clean_part(text: str) -> str:
    """Make `text` safe to use as part of one file or folder name.

    Runs of spaces and line breaks become a single space, unsafe characters become
    "-", and dots and spaces are trimmed from both ends (a trailing dot or space is
    refused by Windows, and a leading dot would hide the file or climb a folder).
    If nothing is left, the result is "-".
    """
    text = " ".join(text.split())
    text = _UNSAFE.sub("-", text)
    return text.strip(". ") or "-"


def relative_path(
    *,
    client_ref: str,
    client_name: str,
    doc_type: DocumentType,
    fields: dict,
    document_date: date | None,
    template: str | None = None,
) -> PurePosixPath:
    """The path under the archive folder for a document, built from the template.

    Every value is cleaned before it goes into the template, so a "/" in a client's
    name can never add a folder level. A document with no date gets "undated".
    """
    values = {
        "client_ref": clean_part(client_ref),
        "client_name": clean_part(client_name),
        "type_plural": clean_part(doc_type.plural_label),
        "type_label": clean_part(doc_type.label),
        "date": document_date.isoformat() if document_date else "undated",
        "key": clean_part(doc_type.filename_key(fields)),
    }
    text = (template or config.NAMING_TEMPLATE).format(**values)
    *folders, filename = text.split("/")
    # The template's own text could end a folder name with a space or dot too.
    parts = [folder.strip(". ") for folder in folders] + [filename.strip()]
    return PurePosixPath(*(part for part in parts if part))


def free_path(
    path: PurePosixPath, is_taken: Callable[[PurePosixPath], bool]
) -> PurePosixPath:
    """`path`, or the first of "name (2).pdf", "name (3).pdf" ... that isn't taken."""
    if not is_taken(path):
        return path
    number = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
        if not is_taken(candidate):
            return candidate
        number += 1
