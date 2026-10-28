"""AT-20: the demo script's steps 1 to 7, with the real OCR program.

Slow (it reads several pages with Tesseract), so it is marked `ocr`.
"""

import html
import io

import pytest
from conftest import FIXED_NOW
from pdfminer.high_level import extract_text
from sqlalchemy import select

from docmanager import create_app
from docmanager.demo.photos import write_demo_box
from docmanager.models.box import Box
from docmanager.models.client import Client
from docmanager.models.document import DocState, Document
from docmanager.models.page import PageState

INVOICE_PATH = (
    "archive/C-0042 Hollybrook Bakery Ltd/Invoices/2026-03-14 Invoice INV-1043.pdf"
)


def text(response):
    return html.unescape(response.get_data(as_text=True))


@pytest.mark.ocr
def test_at20_photos_become_filed_documents_and_the_paper_can_go(tmp_path, data_dir):
    # The real OCR program: no OCR_RUNNER override.
    app = create_app({"DATA_DIR": data_dir, "CLOCK": lambda: FIXED_NOW})
    client = app.test_client()
    with app.extensions["docmanager_sessions"]() as db:
        db.add(Client(ref="C-0042", name="Hollybrook Bakery Ltd", created_at=FIXED_NOW))
        db.commit()

        # Step 1: generate the demo photos.
        photos = write_demo_box(tmp_path / "demo-box")
        assert len(photos) == 7

        # Step 2: upload them into a new box.
        files = [(io.BytesIO(p.read_bytes()), p.name) for p in photos]
        response = client.post(
            "/upload",
            data={"choice": "new", "new_box_name": "Interview box", "photos": files},
            follow_redirects=True,
        )
        assert "7 photos added" in text(response)
        box = db.scalars(select(Box)).one()
        numbered = dict(box.ordered_pages())
        assert len(numbered) == 7

        # Step 3: the lens covers (photos 3 and 5) are marked "Not a page".
        client.post(
            f"/boxes/{box.id}/discard",
            data={"discard": [str(numbered[3].id), str(numbered[5].id)]},
        )

        # Step 4: group each document and read it with real OCR.
        def make(first, last):
            return text(
                client.post(
                    f"/boxes/{box.id}/make-document",
                    data={
                        "first": str(numbered[first].id),
                        "last": str(numbered[last].id),
                    },
                    follow_redirects=True,
                )
            )

        assert "Filed as 2026-03-14 Invoice INV-1043" in make(1, 2)
        assert "Filed as 2026-05-05 Letter Year end accounts reminder" in make(4, 4)
        assert "Needs checking" in make(6, 7)

        # Step 5: the invoice is at its path, with a searchable text layer.
        db.expire_all()
        invoice = db.scalars(
            select(Document).where(Document.doc_type == "invoice")
        ).one()
        assert invoice.pdf_path == INVOICE_PATH
        assert "INV-1043" in extract_text(data_dir / INVOICE_PATH)

        # The box is not ready yet: one document still needs checking.
        home = text(client.get("/"))
        assert "Paper can go" not in home
        assert "1 document needs checking before this paper can go" in home

        # Step 6: review the unclear document.
        unclear = db.scalars(
            select(Document).where(Document._state == DocState.NEEDS_REVIEW.value)
        ).one()
        check = text(client.get(f"/documents/{unclear.id}/check"))
        assert "Couldn't tell what type this is" in check
        hollybrook = db.scalars(select(Client)).one()
        shown = {
            f"shown_{n}": ""
            for n in ("date", "invoice_number", "amount_pence", "subject")
        }
        response = client.post(
            f"/documents/{unclear.id}/check",
            data={**shown, "type": "letter", "client": str(hollybrook.id)},
            follow_redirects=True,
        )
        assert "Filed as" in text(response)

        # Step 7: Home now shows Paper can go, with every page accounted for.
        db.expire_all()
        assert {d.state for d in db.scalars(select(Document))} == {DocState.FILED}
        assert {p.state for p in box.pages} == {PageState.GROUPED, PageState.DISCARDED}
        home = text(client.get("/"))
        assert "Paper can go" in home
        assert "before this paper can go" not in home
