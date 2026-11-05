"""What kind of document something is. Plain Python, not stored in the database.

A Document keeps only the `key` of its type; changing the type swaps which of
these objects the document looks up (SPEC 3.4).
"""

import re
from datetime import date
from decimal import Decimal

from docmanager.rules.dates import add_years, find_dated_spans, find_dates

# What each type listens for, and how loudly (decision 143). A word or phrase
# counts once however often it appears.
INVOICE_WEIGHTS = {
    "invoice": 4,
    "invoice number": 3,
    "invoice date": 2,
    "amount due": 3,
    "balance due": 2,
    "vat": 1,
    "total": 1,
}
LETTER_WEIGHTS = {
    "dear": 3,
    "yours sincerely": 3,
    "yours faithfully": 3,
    "kind regards": 2,
    "best regards": 2,
    "re:": 2,
    "enclosed": 1,
}

_INVOICE_NUMBER = re.compile(
    r"invoice\s*(?:number|no\.?|#)(?![A-Za-z])\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9/\-]*)",
    re.IGNORECASE,
)
# The pound sign is optional: the demo font can't draw it and OCR often misreads it.
_AMOUNT_DUE = re.compile(
    r"amount\s+due\s*[:\-]?\s*£?\s*(\d[\d,]*(?:\.\d{1,2})?)(?![\d/])", re.IGNORECASE
)
_INVOICE_DATE_LABEL = re.compile(r"invoice\s+date|date\s+of\s+invoice", re.IGNORECASE)
_RE_LINE = re.compile(
    r"^[ \t]*re[ \t]*:[ \t]*(.+?)[ \t]*$", re.IGNORECASE | re.MULTILINE
)
# What may sit between a label and its date: spaces, a colon, a dash, a line break.
_LABEL_GAP = " \t\r\n:-.#"


class DocumentType:
    """One kind of document. Each subclass says how to recognise and read its own."""

    key: str  # stored in Document.doc_type
    label: str  # "Invoice"
    plural_label: str  # "Invoices", used as the folder name
    retention_years: int
    # (field, how it is named on screen), in the order shown.
    field_labels: tuple[tuple[str, str], ...] = ()

    @staticmethod
    def keyword_score(text: str, weights: dict[str, int]) -> int:
        """Add up the weight of every keyword found in `text`.

        A keyword counts once however often it appears, whatever its case, and
        only as a whole word or phrase ("alpha" is not found in "alphabet").
        """
        total = 0
        for keyword, weight in weights.items():
            body = r"\s+".join(re.escape(word) for word in keyword.split())
            # Word edges only where the keyword itself starts or ends with a letter.
            before = r"(?<!\w)" if keyword[0].isalnum() else ""
            after = r"(?!\w)" if keyword[-1].isalnum() else ""
            if re.search(before + body + after, text, re.IGNORECASE):
                total += weight
        return total

    def score(self, text: str) -> int:
        raise NotImplementedError

    def extract(self, text: str, today: date) -> dict:
        """This type's fields, plus "document_date" (a date, or None).

        Every field is always present, with None when it wasn't found. A date
        after `today` is ignored as a misread.
        """
        raise NotImplementedError

    def filename_key(self, fields: dict) -> str:
        """The part of the filename that tells documents of this type apart."""
        raise NotImplementedError

    def keep_until(self, document_date: date | None) -> date | None:
        """The last day the record must be kept: the document's date plus this type's years.

        None when there is no date. It is counted from the document's own date, not
        from the day it was uploaded (SPEC 2, changes from the brief).
        """
        if document_date is None:
            return None
        return add_years(document_date, self.retention_years)

    def describe_fields(self, fields: dict) -> list[tuple[str, str | None]]:
        """(label, text) for each field of this type, for showing on screen.

        The text is None when the field wasn't found.
        """
        return [
            (label, self.format_field(name, fields.get(name)))
            for name, label in self.field_labels
        ]

    def format_field(self, name: str, value) -> str | None:
        return None if value in (None, "") else str(value)


class InvoiceType(DocumentType):
    key = "invoice"
    label = "Invoice"
    plural_label = "Invoices"
    retention_years = 6
    field_labels = (
        ("invoice_number", "Invoice number"),
        ("amount_pence", "Amount due"),
    )

    def score(self, text: str) -> int:
        return self.keyword_score(text, INVOICE_WEIGHTS)

    def extract(self, text: str, today: date) -> dict:
        return {
            "invoice_number": self._invoice_number(text),
            "amount_pence": self._amount_pence(text),
            "document_date": self._invoice_date(text, today),
        }

    def filename_key(self, fields: dict) -> str:
        return fields.get("invoice_number") or "no number"

    def format_field(self, name: str, value) -> str | None:
        if name == "amount_pence" and value is not None:
            return f"£{value // 100:,}.{value % 100:02d}"
        return super().format_field(name, value)

    @staticmethod
    def _invoice_number(text: str) -> str | None:
        for match in _INVOICE_NUMBER.finditer(text):
            if any(
                ch.isdigit() for ch in match.group(1)
            ):  # "Invoice number is..." isn't one
                return match.group(1)
        return None

    @staticmethod
    def _amount_pence(text: str) -> int | None:
        match = _AMOUNT_DUE.search(text)
        if match is None:
            return None
        pounds = Decimal(match.group(1).replace(",", ""))
        return int((pounds * 100).to_integral_value())

    @staticmethod
    def _invoice_date(text: str, today: date) -> date | None:
        """The date written right after an "Invoice date" label, else the first date."""
        spans = find_dated_spans(text, today)
        for label in _INVOICE_DATE_LABEL.finditer(text):
            for start, _, when in spans:
                if start >= label.end() and not text[label.end() : start].strip(
                    _LABEL_GAP
                ):
                    return when
        return spans[0][2] if spans else None


class LetterType(DocumentType):
    key = "letter"
    label = "Letter"
    plural_label = "Letters"
    retention_years = 3
    field_labels = (("subject", "Subject"),)

    def score(self, text: str) -> int:
        return self.keyword_score(text, LETTER_WEIGHTS)

    def extract(self, text: str, today: date) -> dict:
        subject = _RE_LINE.search(text)
        dates = find_dates(text, today)
        return {
            "subject": subject.group(1) if subject else None,
            "document_date": dates[0] if dates else None,
        }

    def filename_key(self, fields: dict) -> str:
        return (fields.get("subject") or "")[:40].strip() or "letter"


DOCUMENT_TYPES = {t.key: t for t in (InvoiceType(), LetterType())}
