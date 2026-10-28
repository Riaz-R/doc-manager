"""Made-up photos for the demo: typed text on white pages, black lens covers.

Everything written here is invented (names, numbers, addresses). No real document
is ever used.
"""

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
        image.save(
            path, format="JPEG", quality=90, dpi=(DPI, DPI), comment=comment.encode()
        )
        paths.append(path)
    return paths
