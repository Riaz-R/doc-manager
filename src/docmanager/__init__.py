import logging
import secrets
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, flash, redirect, render_template, request

from docmanager import config
from docmanager.db import init_db
from docmanager.errors import UserFacingError
from docmanager.rules.dates import format_date
from docmanager.services import ocr


def create_app(overrides: dict | None = None) -> Flask:
    """Build the app. `overrides` can set DATA_DIR and CLOCK (tests use both)."""
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    # Flashed messages live in a cookie that needs a key. A new key each start is
    # fine here: it only means a message pending across a restart is lost.
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    app.config["CLOCK"] = datetime.now
    app.config["OCR_RUNNER"] = ocr.run_ocrmypdf  # tests swap in a fake
    app.config["MAX_CONTENT_LENGTH"] = (
        config.MAX_UPLOAD_BYTES
    )  # Flask answers 413 above it
    app.config.update(overrides or {})

    paths = (
        config.Paths(Path(app.config["DATA_DIR"]))
        if "DATA_DIR" in app.config
        else config.Paths.from_env()
    )
    app.config["PATHS"] = paths
    paths.make_folders()

    _log_to_file(app, paths.logs / "app.log")
    init_db(app, paths.db)

    from docmanager.web.routes import bp

    app.register_blueprint(bp)
    app.jinja_env.filters["format_date"] = format_date
    _register_error_pages(app)
    return app


def _log_to_file(app: Flask, log_file: Path) -> None:
    # app.logger is shared by every app made in this process, so drop the
    # handler an earlier create_app added before adding this one.
    for old in [h for h in app.logger.handlers if getattr(h, "docmanager", False)]:
        app.logger.removeHandler(old)
        old.close()
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    handler.docmanager = True
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def _register_error_pages(app: Flask) -> None:
    @app.errorhandler(UserFacingError)
    def show_refusal(error):
        flash(str(error))
        # Go back to the page the user came from, but only by its path, so a
        # crafted Referer can never send them to another website.
        referrer = urlsplit(request.referrer or "")
        target = referrer.path or "/"
        if referrer.query:
            target += "?" + referrer.query
        return redirect(target)

    from docmanager.web.routes import too_big

    app.register_error_handler(413, too_big)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("500.html"), 500
