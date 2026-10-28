from pathlib import Path

from flask import Flask

from docmanager import cli, config, create_app
from docmanager.db import get_session
from docmanager.errors import UserFacingError
from docmanager.services import ocr


def test_home_page_answers_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Doc Manager" in response.data


def test_command_serves_only_on_127_0_0_1(monkeypatch):
    # AT-21: Flask.run is replaced by a recorder, so no real server starts.
    calls = []

    def record_run(self, *args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(Flask, "run", record_run)

    monkeypatch.setattr(ocr, "check_ocr_tools", list)  # not what this test is about
    cli.main([])

    assert calls == [((), {"host": "127.0.0.1", "port": 5000, "debug": False})]


def test_host_and_port_are_fixed_in_config():
    assert config.HOST == "127.0.0.1"
    assert config.PORT == 5000


def test_tunable_values_live_in_config():
    assert config.MIN_TYPE_SCORE == 6
    assert config.MIN_TYPE_MARGIN == 3
    assert config.MIN_OCR_WORDS == 20
    assert config.OCR_TIMEOUT_SECONDS == 300
    assert config.THUMB_SIZE == 400
    assert config.MAX_UPLOAD_BYTES == 500 * 1024 * 1024
    assert config.NAMING_TEMPLATE == (
        "{client_ref} {client_name}/{type_plural}/{date} {type_label} {key}.pdf"
    )


def test_paths_are_laid_out_under_the_data_folder(tmp_path):
    paths = config.Paths(tmp_path)
    assert paths.photos == tmp_path / "photos"
    assert paths.thumbs == tmp_path / "thumbs"
    assert paths.work == tmp_path / "work"
    assert paths.archive == tmp_path / "archive"
    assert paths.bin == tmp_path / "bin"
    assert paths.logs == tmp_path / "logs"
    assert paths.db == tmp_path / "app.db"


def test_data_folder_defaults_to_data(monkeypatch):
    monkeypatch.delenv("DOCMANAGER_DATA")
    assert config.Paths.from_env().root == Path("data")


def test_docmanager_data_moves_the_database(tmp_path, monkeypatch):
    moved = tmp_path / "somewhere-else"
    monkeypatch.setenv("DOCMANAGER_DATA", str(moved))

    create_app()

    assert (moved / "app.db").is_file()
    assert (moved / "logs").is_dir()


def test_data_dir_override_beats_the_environment(app, data_dir, tmp_path):
    assert (data_dir / "app.db").is_file()
    assert not (tmp_path / "env-data").exists()
    for name in ("photos", "thumbs", "work", "archive", "bin", "logs"):
        assert (data_dir / name).is_dir()


def test_clock_is_an_app_setting(app, now):
    assert app.config["CLOCK"]() == now


def test_one_session_per_request_closed_at_the_end(app):
    sessions = []

    @app.get("/two-lookups")
    def two_lookups():
        sessions.append(get_session())
        sessions.append(get_session())
        return "ok"

    app.test_client().get("/two-lookups")

    assert sessions[0] is sessions[1]
    # A closed session has handed its connection back to the pool.
    assert app.extensions["docmanager_engine"].pool.checkedout() == 0


def test_unknown_url_shows_friendly_404(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert b"couldn't find that page" in response.data
    assert b"Traceback" not in response.data


def test_failing_route_shows_500_page_and_logs(app, data_dir):
    @app.get("/boom")
    def boom():
        return 1 / 0

    response = app.test_client().get("/boom")

    assert response.status_code == 500
    assert b"Something went wrong" in response.data
    assert b"ZeroDivisionError" not in response.data
    log = (data_dir / "logs" / "app.log").read_text()
    assert "ZeroDivisionError" in log


def test_domain_error_is_flashed_and_the_user_sent_back(app):
    @app.post("/refuse")
    def refuse():
        raise UserFacingError("Pick both the first and the last page")

    client = app.test_client()
    response = client.post("/refuse", headers={"Referer": "http://localhost/"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    page = client.get("/")
    assert b"Pick both the first and the last page" in page.data


def test_domain_error_without_referer_goes_home(app):
    @app.post("/refuse")
    def refuse():
        raise UserFacingError("Nope")

    response = app.test_client().post("/refuse")
    assert response.headers["Location"] == "/"
