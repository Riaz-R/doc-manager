import json
import os
import sys
import textwrap
import time

import pikepdf
import pytest
from conftest import FakeOcr
from PIL import Image

from docmanager import cli, config, create_app
from docmanager.demo import photos
from docmanager.services import ocr
from docmanager.services.ocr import OcrFailed

# A stand-in for the OCR program: a tiny Python script run the same way as the real one.
FAKE_PROGRAM = textwrap.dedent(
    """
    import json, shutil, sys
    args = sys.argv[1:]
    sidecar = args[args.index("--sidecar") + 1]
    source, target = args[-2], args[-1]
    shutil.copyfile(source, target)
    open(sidecar, "w").write(json.dumps(args))
    """
)


@pytest.fixture
def paths(tmp_path):
    source = tmp_path / "in.pdf"
    source.write_bytes(b"%PDF-1.4 pretend")
    return source, tmp_path / "out.pdf", tmp_path / "out.txt"


def run_with(code, paths, **kwargs):
    """Run `ocr.run_ocrmypdf` with a stand-in program made from `code`."""
    return ocr.run_ocrmypdf(*paths, command=[sys.executable, "-c", code], **kwargs)


def write_photo(path, size=(600, 800), fmt="JPEG", mode="RGB"):
    Image.new(mode, size, "white").save(path, format=fmt)
    return path


# --- combine_photos ---


def test_photos_become_one_pdf_with_a_page_each_in_order(tmp_path):
    first = write_photo(tmp_path / "a.jpg", (600, 800))  # portrait
    second = write_photo(tmp_path / "b.jpg", (800, 600))  # landscape
    third = write_photo(tmp_path / "c.png", (600, 600), "PNG")

    ocr.combine_photos([first, second, third], tmp_path / "out.pdf")

    with pikepdf.open(tmp_path / "out.pdf") as pdf:
        assert len(pdf.pages) == 3
        shapes = [
            float(p.mediabox[2] - p.mediabox[0]) / float(p.mediabox[3] - p.mediabox[1])
            for p in pdf.pages
        ]
    assert shapes[0] < 1 < shapes[1]  # the order was kept
    assert shapes[2] == pytest.approx(1)


@pytest.mark.parametrize("mode", ["RGBA", "LA", "P", "I;16"])
def test_png_photos_that_img2pdf_would_refuse_are_flattened_first(tmp_path, mode):
    png = tmp_path / "a.png"
    Image.new(mode, (200, 300)).save(png, format="PNG")

    ocr.combine_photos([png], tmp_path / "out.pdf")

    with pikepdf.open(tmp_path / "out.pdf") as pdf:
        assert len(pdf.pages) == 1


def test_a_photo_the_pdf_maker_cannot_read_raises_ocr_failed(tmp_path):
    broken = tmp_path / "a.jpg"
    broken.write_bytes(b"not a picture")

    with pytest.raises(OcrFailed) as problem:
        ocr.combine_photos([broken], tmp_path / "out.pdf")

    assert "combine the photos" in problem.value.detail


def test_no_photos_raises_ocr_failed(tmp_path):
    with pytest.raises(OcrFailed):
        ocr.combine_photos([], tmp_path / "out.pdf")


def test_ocr_failed_carries_its_detail_and_prints_it():
    error = OcrFailed("exit code 3: boom")

    assert error.detail == "exit code 3: boom"
    assert str(error) == "exit code 3: boom"


# --- run_ocrmypdf: the subprocess ---


def test_the_command_is_ocrmypdf_run_as_a_module_of_this_python():
    assert ocr.OCR_COMMAND == [sys.executable, "-m", "ocrmypdf"]


def test_ocrmypdf_is_run_with_the_documented_options(paths):
    source, target, sidecar = paths

    ocr.run_ocrmypdf(
        source, target, sidecar, command=[sys.executable, "-c", FAKE_PROGRAM]
    )

    assert json.loads(sidecar.read_text()) == [
        "-l",
        "eng",
        "--rotate-pages",
        "--deskew",
        "--sidecar",
        str(sidecar),
        str(source),
        str(target),
    ]
    assert target.read_bytes() == source.read_bytes()


def test_a_non_zero_exit_becomes_ocr_failed_with_the_detail(paths):
    code = "import sys; sys.stderr.write('Ghostscript went wrong'); sys.exit(3)"

    with pytest.raises(OcrFailed) as problem:
        run_with(code, paths)

    assert "exit code 3" in problem.value.detail
    assert "Ghostscript went wrong" in problem.value.detail


def test_only_the_end_of_a_very_long_error_is_kept(paths):
    code = "import sys; sys.stderr.write('x' * 50000 + 'THE END'); sys.exit(1)"

    with pytest.raises(OcrFailed) as problem:
        run_with(code, paths)

    assert "THE END" in problem.value.detail
    assert len(problem.value.detail) < 5000


def test_a_program_that_makes_no_output_file_is_a_failure(paths):
    with pytest.raises(OcrFailed) as problem:
        run_with("pass", paths)  # exits 0 but writes nothing

    assert "no output" in problem.value.detail.lower()


def test_a_missing_sidecar_is_a_failure_too(paths):
    _, target, sidecar = paths
    code = "import shutil, sys; shutil.copyfile(sys.argv[-2], sys.argv[-1])"

    with pytest.raises(OcrFailed) as problem:
        run_with(code, paths)

    assert "no output" in problem.value.detail.lower()
    assert target.exists() and not sidecar.exists()


def test_a_real_timeout_becomes_ocr_failed_and_returns_promptly(paths):
    started = time.monotonic()

    with pytest.raises(OcrFailed) as problem:
        run_with("import time; time.sleep(60)", paths, timeout=1)

    assert time.monotonic() - started < 10
    assert "timed out after 1 second" in problem.value.detail


def test_a_timeout_kills_the_programs_children_too(paths, tmp_path):
    pid_file = tmp_path / "child.pid"
    code = textwrap.dedent(
        f"""
        import subprocess, sys, time
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        open({str(pid_file)!r}, "w").write(str(child.pid))
        time.sleep(60)
        """
    )

    started = time.monotonic()
    with pytest.raises(OcrFailed):
        run_with(code, paths, timeout=2)
    # If the child were left running it would hold the output open, and we'd wait for it.
    assert time.monotonic() - started < 15

    child = int(pid_file.read_text())
    for _ in range(50):  # give the system a moment to clear it away
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    pytest.fail("the child process was left running")


def test_the_timeout_defaults_to_the_config_value(paths, monkeypatch):
    monkeypatch.setattr(config, "OCR_TIMEOUT_SECONDS", 1)

    with pytest.raises(OcrFailed) as problem:
        run_with("import time; time.sleep(60)", paths)

    assert "timed out after 1 second" in problem.value.detail


# --- The app setting, and the fake used by the other tests ---


def test_the_real_runner_is_the_default_ocr_setting(data_dir):
    assert create_app({"DATA_DIR": data_dir}).config["OCR_RUNNER"] is ocr.run_ocrmypdf


def test_the_ocr_setting_can_be_replaced(data_dir):
    fake = FakeOcr("hello")

    app = create_app({"DATA_DIR": data_dir, "OCR_RUNNER": fake})

    assert app.config["OCR_RUNNER"] is fake


def test_the_fake_copies_the_pdf_and_writes_the_text(paths):
    source, target, sidecar = paths
    fake = FakeOcr("some words")

    fake(source, target, sidecar)

    assert target.read_bytes() == source.read_bytes()
    assert sidecar.read_text() == "some words"
    assert fake.calls == [(source, target, sidecar)]


def test_the_fake_can_fail_and_then_recover(paths):
    source, target, sidecar = paths
    fake = FakeOcr("text", fail="boom")

    with pytest.raises(OcrFailed) as problem:
        fake(source, target, sidecar)
    assert problem.value.detail == "boom"
    assert not target.exists()

    fake.fail = None
    fake(source, target, sidecar)
    assert sidecar.read_text() == "text"
    assert len(fake.calls) == 2


# --- W5: the start-up check ---

EVERYTHING = {"tesseract": "/usr/bin/tesseract", "gs": "/usr/bin/gs"}


def check(missing_programs=(), languages=("eng", "osd")):
    return ocr.check_ocr_tools(
        which=lambda name: None if name in missing_programs else EVERYTHING[name],
        list_languages=lambda: list(languages),
    )


def test_w5_nothing_is_reported_when_everything_is_installed():
    assert check() == []


def test_w5_a_missing_tesseract_is_reported():
    problems = check(missing_programs=["tesseract"])

    assert len(problems) == 1
    assert "Tesseract" in problems[0] and "isn't installed" in problems[0]


def test_w5_a_missing_ghostscript_is_reported():
    problems = check(missing_programs=["gs"])

    assert len(problems) == 1
    assert "Ghostscript" in problems[0] and "isn't installed" in problems[0]


def test_w5_missing_osd_data_is_reported():
    problems = check(languages=["eng"])

    assert len(problems) == 1
    assert "osd" in problems[0] and "Tesseract" in problems[0]


def test_w5_missing_english_data_is_reported():
    problems = check(languages=["osd"])

    assert len(problems) == 1
    assert "eng" in problems[0]


def test_w5_every_problem_is_listed_together():
    problems = check(missing_programs=["gs"], languages=[])

    assert len(problems) == 3  # Ghostscript, eng, osd


def test_w5_language_data_is_not_checked_when_tesseract_itself_is_missing():
    def boom():
        raise AssertionError("must not ask a missing program for its languages")

    problems = ocr.check_ocr_tools(
        which=lambda name: None if name == "tesseract" else "/usr/bin/gs",
        list_languages=boom,
    )

    assert len(problems) == 1


def test_w5_a_tesseract_that_cannot_list_its_languages_is_reported():
    def broken():
        raise OSError("no")

    problems = ocr.check_ocr_tools(which=EVERYTHING.get, list_languages=broken)

    assert len(problems) == 1
    assert "Tesseract" in problems[0]


def test_the_apt_command_installs_everything_needed():
    for package in (
        "tesseract-ocr",
        "tesseract-ocr-eng",
        "tesseract-ocr-osd",
        "ghostscript",
    ):
        assert package in ocr.APT_COMMAND
    assert ocr.APT_COMMAND.startswith("sudo apt install")


def test_w5_the_command_prints_what_is_missing_and_how_to_fix_it_then_exits(
    monkeypatch, capsys
):
    from flask import Flask

    monkeypatch.setattr(Flask, "run", lambda *a, **k: pytest.fail("server started"))
    monkeypatch.setattr(
        ocr,
        "check_ocr_tools",
        lambda: ["Tesseract isn't installed.", "Ghostscript isn't installed."],
    )

    with pytest.raises(SystemExit) as stop:
        cli.main([])

    assert stop.value.code == 1
    shown = capsys.readouterr().err
    assert "Tesseract isn't installed." in shown
    assert "Ghostscript isn't installed." in shown
    assert ocr.APT_COMMAND in shown


def test_the_command_serves_when_the_check_passes(monkeypatch):
    from flask import Flask

    served = []
    monkeypatch.setattr(Flask, "run", lambda self, *a, **k: served.append(k))
    monkeypatch.setattr(ocr, "check_ocr_tools", list)

    cli.main([])

    assert served == [{"host": "127.0.0.1", "port": 5000, "debug": False}]


def test_making_demo_photos_does_not_need_the_ocr_tools(monkeypatch, tmp_path):
    monkeypatch.setattr(ocr, "check_ocr_tools", lambda: ["Tesseract isn't installed."])

    cli.main(["make-photos", str(tmp_path / "box")])

    assert (tmp_path / "box" / "IMG_0001.jpg").is_file()


# --- The real thing (slow) ---


@pytest.mark.ocr
def test_the_real_tools_pass_the_start_up_check():
    assert ocr.check_ocr_tools() == []


@pytest.mark.ocr
def test_real_ocrmypdf_reads_a_generated_page(tmp_path):
    invoice_page = tmp_path / "page.jpg"
    photos.render_page(photos.INVOICE.pages[0]).save(invoice_page, dpi=(150, 150))
    combined, searchable, sidecar = (
        tmp_path / "images.pdf",
        tmp_path / "searchable.pdf",
        tmp_path / "text.txt",
    )

    ocr.combine_photos([invoice_page], combined)
    ocr.run_ocrmypdf(combined, searchable, sidecar)

    text = sidecar.read_text()
    assert "INVOICE" in text
    assert "INV-1043" in text
    assert "C-0042" in text
    assert "14/03/2026" in text
    with pikepdf.open(searchable) as pdf:
        assert len(pdf.pages) == 1
