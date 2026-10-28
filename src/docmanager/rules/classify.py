"""Working out what a document is and whose it is (SPEC 5.5). No database, no AI.

The checks run in this order, and every one that fails adds a reason:
1. text: enough words were read;
2. type: one document type scores high enough and clearly beats the others;
3. client: exactly one client matches, by reference or by name.
The date is read too but never blocks filing.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from docmanager import config

LOW_TEXT_REASON = (
    "Very little text was read. Check the photos are clear before shredding the paper."
)

# C-0042. Not part of a longer word, so "INV-C-0042x" doesn't count.
_CLIENT_REF = re.compile(r"(?<![\w-])C-\d{4}(?!\d)", re.IGNORECASE)


@dataclass(frozen=True)
class Classification:
    """The result of reading a text: what was found, and why anything was flagged."""

    reasons: list[str] = field(default_factory=list)  # empty when every check passed
    doc_type: str | None = None  # a DocumentType key, or None for "Unclassified"
    type_score: int = 0  # the best score, kept to explain the decision
    runner_up_score: int = 0
    client: object | None = None  # one of the clients given to classify()
    fields: dict = field(default_factory=dict)  # the type's fields, without the date
    document_date: date | None = None

    @property
    def passed(self) -> bool:
        """True when the document can be filed automatically."""
        return not self.reasons


def count_words(text: str) -> int:
    """How many whitespace-separated pieces contain a letter or a digit."""
    return sum(1 for piece in text.split() if any(ch.isalnum() for ch in piece))


def classify(text: str, clients, today: date) -> Classification:
    """Run the three checks on `text`. `clients` need a `ref` and a `name` each."""
    # Imported here because the model package imports this module (for the guards).
    from docmanager.models.document_types import DOCUMENT_TYPES

    reasons = []

    # Check 1: text
    if count_words(text) < config.MIN_OCR_WORDS:
        reasons.append(LOW_TEXT_REASON)

    # Check 2: type. sorted() is stable, so a tie keeps the registry's order.
    scored = sorted(
        ((doc_type.score(text), doc_type) for doc_type in DOCUMENT_TYPES.values()),
        key=lambda pair: pair[0],
        reverse=True,
    )
    top_score, top_type = scored[0]
    runner_up_score = scored[1][0] if len(scored) > 1 else 0
    if (
        top_score >= config.MIN_TYPE_SCORE
        and top_score - runner_up_score >= config.MIN_TYPE_MARGIN
    ):
        chosen = top_type
        fields = chosen.extract(text, today)
        document_date = fields.pop("document_date")
    else:
        chosen, fields, document_date = None, {}, None
        if top_score == 0:
            reasons.append("Couldn't tell what type this is")
        else:
            maybe = [t.label for score, t in scored if score > 0][:2]
            reasons.append(f"Not sure what type this is ({' or '.join(maybe)}?)")

    # Check 3: client
    client, client_reason = _find_client(text, clients)
    if client_reason:
        reasons.append(client_reason)

    return Classification(
        reasons=reasons,
        doc_type=chosen.key if chosen else None,
        type_score=top_score,
        runner_up_score=runner_up_score,
        client=client,
        fields=fields,
        document_date=document_date,
    )


def _find_client(text: str, clients) -> tuple[object | None, str | None]:
    """The matching client, or None and the reason there isn't one."""
    refs = list(dict.fromkeys(ref.upper() for ref in _CLIENT_REF.findall(text)))
    if len(refs) > 1:
        return None, f"More than one client reference found: {', '.join(refs)}"
    if refs:  # a reference settles it: names are not looked at
        for client in clients:
            if client.ref.upper() == refs[0]:
                return client, None
        return None, f"Client {refs[0]} isn't in your client list"

    # No reference: look for a client's exact name, as a whole phrase.
    found = []
    for client in clients:
        words = r"\s+".join(re.escape(word) for word in client.name.split())
        match = re.search(rf"(?<!\w){words}(?!\w)", text, re.IGNORECASE)
        if match:
            found.append((match.start(), client))
    found.sort(key=lambda pair: pair[0])  # in the order they appear in the text
    if len(found) > 1:
        names = ", ".join(client.name for _, client in found)
        return None, f"More than one client matched: {names}"
    if found:
        return found[0][1], None
    return None, "Couldn't tell which client this is for"
