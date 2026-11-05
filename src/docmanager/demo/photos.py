"""Made-up photos for the demo: typed text on white pages, black lens covers.

Everything written here is invented (names, numbers, addresses). No real document
is ever used.
"""

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAGE_SIZE = (1240, 1754)  # A4 at 150 dpi
DPI = 150
MARGIN = 100
FONT_SIZE = 40
LINE_HEIGHT = 56


@dataclass(frozen=True)
class DemoDocument:
    """One made-up document: a name and its pages, each a list of lines of text."""

    name: str
    pages: tuple[tuple[str, ...], ...]

    @property
    def text(self) -> str:
        return "\n".join(line for page in self.pages for line in page)


INVOICE = DemoDocument(
    "invoice",
    (
        (
            "INVOICE",
            "",
            "Brightwell Flour Mills",
            "Invoice number INV-1043",
            "Invoice date 14/03/2026",
            "",
            "Client reference C-0042",
            "Hollybrook Bakery Ltd",
            "12 Mill Lane, Daleford",
            "",
            "All prices in pounds",
            "Flour, 16kg sacks x 6    72.00",
            "Yeast, 500g tubs x 4    28.00",
            "Delivery    20.00",
            "",
            "Amount due 120.00",
        ),
        (
            "Payment terms",
            "",
            (
                "Please pay within 30 days of the date of this invoice by bank transfer, "
                "quoting the invoice number. Thank you for your custom, and we look "
                "forward to supplying your bakery again soon."
            ),
            "",
            "Brightwell Flour Mills, Unit 3, Mill Road, Daleford",
        ),
    ),
)

LETTER = DemoDocument(
    "letter",
    (
        (
            "Fernwood Accountancy Services",
            "4 Orchard Court, Daleford",
            "",
            "5 May 2026",
            "",
            "Our ref: C-0042",
            "Hollybrook Bakery Ltd",
            "12 Mill Lane",
            "Daleford",
            "",
            "Dear Mr Hartley,",
            "",
            "Re: Year end accounts reminder",
            "",
            (
                "We are writing to tell you that your year end records are now ready "
                "for your review. Please look over the enclosed figures and let us "
                "know if anything looks wrong before the end of the month."
            ),
            "",
            "Yours sincerely,",
            "A. Whitcombe",
            "Fernwood Accountancy Services",
        ),
    ),
)

# Deliberately unclear: no client and none of the words either type looks for, so
# it ends up in Needs checking.
UNCLEAR = DemoDocument(
    "unclear",
    (
        (
            "Things to sort out",
            "",
            (
                "The kettle in the back office needs descaling. Ask about the spare "
                "keys for the side door. The shelf above the sink is loose and the "
                "blue folder has gone missing again. Check the cupboard by the "
                "window for old boxes."
            ),
            "",
            (
                "Don't forget to ring the plumber about the tap, and put the ladder "
                "back in the shed."
            ),
        ),
        (
            "More notes",
            "",
            (
                "Bring tea bags and biscuits on Friday. The heating timer is wrong "
                "by an hour. Someone left an umbrella by the door; it is green with "
                "a wooden handle. Water the plant on the desk twice a week."
            ),
        ),
    ),
)

DEMO_DOCUMENTS = (INVOICE, LETTER, UNCLEAR)


def _invoice(name, supplier, number, date, ref, client, street, items, amount):
    """A one-page made-up invoice. `items` are (description, price) pairs."""
    lines = [
        "INVOICE",
        "",
        supplier,
        f"Invoice number {number}",
        f"Invoice date {date}",
        "",
        f"Client reference {ref}",
        client,
        street,
        "",
        "All prices in pounds",
    ]
    lines += [f"{what}    {price}" for what, price in items]
    lines += [
        "",
        f"Amount due {amount}",
        "",
        "Please pay by bank transfer within 30 days, quoting the invoice number.",
    ]
    return DemoDocument(name, (tuple(lines),))


def _letter(name, ref, greeting, subject, date, body):
    lines = ["Fernwood Accountancy Services", "4 Orchard Court, Daleford", ""]
    if date:
        lines += [date, ""]
    lines += [f"Our ref: {ref}", "", greeting, "", f"Re: {subject}", "", body, ""]
    lines += ["Yours sincerely,", "A. Whitcombe", "Fernwood Accountancy Services"]
    return DemoDocument(name, (tuple(lines),))


# The documents the seed script puts in the demo boxes. They are different from the
# `make-photos` ones on purpose: the app skips a photo it has already seen, so
# sharing a photo would break the live upload in the demo script.
SEED_FILED = _invoice(
    "seed filed invoice",
    "Pennine Dental Supplies",
    "INV-2207",
    "10/06/2025",
    "C-0007",
    "Ashgrove Dental Practice",
    "8 Chapel Street, Daleford",
    [("Examination gloves, boxes x 10", "64.00"), ("Paper bibs, packs x 5", "31.00")],
    "95.00",
)
SEED_NO_DATE = _letter(
    "seed letter without a date",
    "C-0013",
    "Dear Mr Lindqvist,",
    "Greenhouse delivery query",
    None,
    (
        "Thank you for your question about the greenhouse panels. We have "
        "checked our records and can confirm the panels were sent to your "
        "garden centre last season. Please let us know if any are missing."
    ),
)
SEED_DUE_INVOICE = _invoice(
    "seed due invoice",
    "Brightwell Flour Mills",
    "INV-0388",
    "12/04/2016",
    "C-0042",
    "Hollybrook Bakery Ltd",
    "12 Mill Lane, Daleford",
    [("Flour, 16kg sacks x 4", "48.00"), ("Sugar, 25kg sacks x 2", "36.00")],
    "84.00",
)
SEED_DUE_LETTER = _letter(
    "seed due letter",
    "C-0034",
    "Dear Ms Okafor,",
    "Quarterly tax figures",
    "20 September 2017",
    (
        "We are writing to confirm that the figures for the quarter have been "
        "sent to the tax office on time. Nothing more is needed from you, and "
        "we will write again when the next quarter is due."
    ),
)
SEED_BIN_INVOICE = _invoice(
    "seed binned invoice",
    "Tarn Timber Merchants",
    "INV-0912",
    "02/11/2016",
    "C-0051",
    "Marlowe Joinery Ltd",
    "Unit 9, Canal Yard, Daleford",
    [("Oak boards, 2.4m x 12", "220.00"), ("Wood glue, 5 litre x 2", "90.00")],
    "310.00",
)
SEED_UNCLEAR = DemoDocument(
    "seed unclear",
    (
        (
            "Jobs for the week",
            "",
            (
                "Move the old filing trolley into the cellar. Ring about the "
                "broken gate latch. Find the box of spare light bulbs, which "
                "was last seen on the landing."
            ),
        ),
        (
            "More jobs",
            "",
            (
                "Sweep the yard on Thursday. Take the glass to the recycling "
                "bank. Ask the neighbours whether the skip is still wanted "
                "and move the bikes out of the hall."
            ),
        ),
    ),
)
SEED_LOOSE_PAGES = tuple(
    DemoDocument(
        f"seed loose page {number}",
        (
            (
                f"Loose page {number}",
                "",
                (
                    f"This page, number {number} of the pile, has not been put in a "
                    "document yet. It is waiting in the inbox to be sorted, "
                    "and nobody has read it."
                ),
            ),
        ),
    )
    for number in (1, 2, 3)
)


def render_page(lines) -> Image.Image:
    """Typed text on a white page. Long lines wrap inside the margins."""
    image = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=FONT_SIZE)
    y = MARGIN
    for line in lines:
        for wrapped in _wrap(line, font, PAGE_SIZE[0] - 2 * MARGIN):
            if y + LINE_HEIGHT > PAGE_SIZE[1] - MARGIN:
                raise ValueError("Too much text for one page")
            draw.text((MARGIN, y), wrapped, fill="black", font=font)
            y += LINE_HEIGHT
    return image


def render_lens_cover() -> Image.Image:
    """The photo taken with a hand over the lens: plain black."""
    return Image.new("RGB", PAGE_SIZE, "black")


def _wrap(line: str, font, max_width: int) -> list[str]:
    """Split `line` into pieces that each fit in `max_width` pixels. A blank line stays blank."""
    if not line:
        return [""]
    pieces, current = [], ""
    for word in line.split(" "):
        trial = f"{current} {word}" if current else word
        if current and font.getlength(trial) > max_width:
            pieces.append(current)
            current = word
        else:
            current = trial
    pieces.append(current)
    return pieces


def jpeg_bytes(image: Image.Image, comment: str) -> bytes:
    """The photo as JPEG bytes. The comment keeps two black lens covers from being identical."""
    buffer = io.BytesIO()
    image.save(
        buffer, format="JPEG", quality=90, dpi=(DPI, DPI), comment=comment.encode()
    )
    return buffer.getvalue()


def write_demo_box(out_dir) -> list[Path]:
    """Write the demo box as IMG_0001.jpg ... and return the paths in order.

    Three documents with a lens cover between them. Every file's bytes differ, even
    the two black lens covers (each carries its own JPEG comment), because the app
    skips a photo whose bytes it has already seen.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    photos = []  # (image, comment)
    for number, document in enumerate(DEMO_DOCUMENTS):
        if number:
            photos.append((render_lens_cover(), f"lens cover {number}"))
        for page_number, page in enumerate(document.pages, start=1):
            photos.append((render_page(page), f"{document.name} page {page_number}"))

    paths = []
    for number, (image, comment) in enumerate(photos, start=1):
        path = out_dir / f"IMG_{number:04d}.jpg"
        path.write_bytes(jpeg_bytes(image, comment))
        paths.append(path)
    return paths
