from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from docmanager.db import get_session
from docmanager.models.box import Box
from docmanager.services import upload

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    boxes = upload.boxes_with_inbox_counts(get_session())
    return render_template("home.html", boxes=boxes)


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

    choice = request.form.get("box", "new")
    box = upload.find_or_create_box(
        session,
        box_id=int(choice) if choice.isdigit() else None,
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
