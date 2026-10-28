from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from docmanager.db import get_session
from docmanager.models.box import Box
from docmanager.models.page import Page
from docmanager.services import grouping, upload

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    boxes = upload.boxes_with_inbox_counts(get_session())
    return render_template("home.html", boxes=boxes)


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
    session.commit()
    flash(made.message())
    return redirect(url_for("main.inbox", box_id=box.id))


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
