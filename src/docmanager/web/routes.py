from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from sqlalchemy import select

from docmanager.db import get_session
from docmanager.models.box import Box
from docmanager.models.document import DocState, Document
from docmanager.models.page import Page
from docmanager.services import filing, grouping, upload

bp = Blueprint("main", __name__)

# A button on the Document page for each lifecycle action that has a screen:
# {action: (label, endpoint)}. The page shows a button only when the document's
# lifecycle allows the action. Move to bin and Restore join this in task 22.
ACTION_BUTTONS: dict[str, tuple[str, str]] = {}


@bp.get("/")
def home():
    session = get_session()
    return render_template(
        "home.html",
        boxes=upload.boxes_with_inbox_counts(session),
        bin_count=grouping.bin_count(session),
    )


@bp.get("/documents")
def filed_documents():
    documents = (
        get_session()
        .scalars(
            select(Document)
            .where(Document._state == DocState.FILED.value)
            .order_by(Document.filed_at.desc(), Document.id.desc())
        )
        .all()
    )
    return render_template("filed.html", documents=documents, today=_today())


@bp.get("/documents/<int:document_id>")
def document_page(document_id):
    document = _document_or_404(document_id)
    today = _today()
    buttons = [
        (label, url_for(endpoint, document_id=document.id))
        for action in document.allowed_actions()
        if action in ACTION_BUTTONS
        for label, endpoint in [ACTION_BUTTONS[action]]
    ]
    if not document.pdf_path:
        pdf_state = "none"
    elif _pdf_file(document) is None:
        pdf_state = "missing"
    else:
        pdf_state = "ok"
    return render_template(
        "document.html",
        document=document,
        markers=document.markers(today),
        fields=document.type.describe_fields(document.fields) if document.type else [],
        buttons=buttons,
        pdf_state=pdf_state,
    )


@bp.get("/documents/<int:document_id>/pdf")
def document_pdf(document_id):
    path = _pdf_file(_document_or_404(document_id))
    if path is None:
        abort(404)
    return send_file(path, mimetype="application/pdf")


@bp.get("/boxes/<int:box_id>/inbox")
def inbox(box_id):
    box = get_session().get(Box, box_id)
    if box is None:
        abort(404)
    return render_template(
        "inbox.html",
        box=box,
        pages=box.inbox_pages(),
        unread=box.unread_documents(),
    )


@bp.post("/boxes/<int:box_id>/make-document")
def make_document(box_id):
    session = get_session()
    box = session.get(Box, box_id)
    if box is None:
        abort(404)
    made = grouping.make_document(
        session,
        box,
        _page_id(request.form.get("first")),
        _page_id(request.form.get("last")),
        now=current_app.config["CLOCK"](),
    )
    _read_and_flash(made.document)  # this commits the new document first
    return redirect(url_for("main.inbox", box_id=box.id))


@bp.post("/documents/<int:document_id>/retry")
def retry_document(document_id):
    document = get_session().get(Document, document_id)
    if document is None:
        abort(404)
    box_id = document.box_id
    _read_and_flash(document)
    return redirect(url_for("main.inbox", box_id=box_id))


def _read_and_flash(document):
    """Read the document (OCR runs while the page waits), keep the outcome, tell the user."""
    session = get_session()
    result = filing.read_document(
        session,
        document,
        paths=current_app.config["PATHS"],
        ocr_runner=current_app.config["OCR_RUNNER"],
        now=current_app.config["CLOCK"](),
    )
    session.commit()
    flash(result.message())


@bp.post("/boxes/<int:box_id>/discard")
def discard(box_id):
    session = get_session()
    box = session.get(Box, box_id)
    if box is None:
        abort(404)
    count = grouping.discard_pages(
        session,
        box,
        [int(raw) for raw in request.form.getlist("discard") if raw.isdigit()],
        now=current_app.config["CLOCK"](),
    )
    session.commit()
    flash(f"{count} {'photo' if count == 1 else 'photos'} marked as not a page")
    return redirect(url_for("main.inbox", box_id=box.id))


@bp.get("/bin")
def bin_screen():
    return render_template("bin.html", pages=grouping.binned_pages(get_session()))


@bp.post("/pages/<int:page_id>/restore")
def restore_page(page_id):
    session = get_session()
    page = grouping.restore_page(session, page_id, now=current_app.config["CLOCK"]())
    session.commit()
    flash(f"Restored {page.original_filename} to the inbox of {page.box.name}")
    return redirect(url_for("main.bin_screen"))


@bp.get("/pages/<int:page_id>/thumb")
def thumbnail(page_id):
    page = get_session().get(Page, page_id)
    if page is None:
        abort(404)
    # send_from_directory refuses any path that climbs out of the data folder,
    # and answers 404 itself when the file is missing.
    return send_from_directory(current_app.config["PATHS"].root, page.thumb_path)


@bp.get("/upload")
def upload_form():
    boxes = get_session().query(Box).order_by(Box.name).all()
    return render_template("upload.html", boxes=boxes)


@bp.post("/upload")
def upload_photos():
    session = get_session()
    files = [f for f in request.files.getlist("photos") if f.filename]
    if not files:
        raise upload.UploadRefused("Choose at least one photo")

    # Only the chosen option is used; the other field is ignored.
    choice = request.form.get("choice")
    if choice == "new":
        box_id = None
    elif choice == "existing":
        box_id = request.form.get("box", "")
        if not box_id.isdigit():
            raise upload.UploadRefused("Choose a box to add the photos to")
        box_id = int(box_id)
    else:
        raise upload.UploadRefused(
            "Choose whether to add to an existing box or make a new one"
        )
    box = upload.find_or_create_box(
        session,
        box_id=box_id,
        new_name=request.form.get("new_box_name", ""),
        now=current_app.config["CLOCK"](),
    )
    result = upload.upload_photos(
        session,
        box,
        ((f.filename, f.read()) for f in files),
        data_dir=current_app.config["PATHS"].root,
        now=current_app.config["CLOCK"](),
    )
    session.commit()
    flash(result.message())
    return redirect(url_for("main.home"))


def too_big(_error) -> object:
    """A 413: the browser sent more than MAX_CONTENT_LENGTH."""
    flash(
        "That upload is too big for one go. Upload in parts: choose some of the "
        "photos, then the rest, into the same box."
    )
    return redirect(url_for("main.upload_form"))


def _page_id(raw: str | None) -> int | None:
    """A form value as a page id; anything that isn't a number counts as not picked."""
    return int(raw) if raw and raw.isdigit() else None


def _today():
    return current_app.config["CLOCK"]().date()


def _document_or_404(document_id: int) -> Document:
    document = get_session().get(Document, document_id)
    if document is None:
        abort(404)
    return document


def _pdf_file(document: Document) -> Path | None:
    """The document's PDF on disk, or None if it has none or the file is missing.

    The database holds the path (SPEC N5), but only a file inside the data folder
    is ever served, whatever the path says.
    """
    if not document.pdf_path:
        return None
    root = current_app.config["PATHS"].root.resolve()
    path = (root / document.pdf_path).resolve()
    return path if path.is_relative_to(root) and path.is_file() else None
