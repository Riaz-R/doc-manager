import re
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from docmanager import cli
from docmanager.demo import seed
from docmanager.models.client import Client
from docmanager.services import ocr

NOW = datetime(2026, 10, 27, 12, 0)


def clients_in(data_dir):
    """Every client row in the database inside `data_dir`, as (id, ref, name)."""
    engine = create_engine(f"sqlite:///{data_dir / 'app.db'}")
    with Session(engine) as session:
        rows = session.scalars(select(Client).order_by(Client.id)).all()
        return [(c.id, c.ref, c.name) for c in rows]


def contents(folder):
    """Every file under `folder` with its bytes, to show nothing was touched."""
    return {
        str(p.relative_to(folder)): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


@pytest.fixture
def data(tmp_path):
    return tmp_path / "data"


# --- The demo clients ---


def test_seeding_creates_the_demo_clients_including_hollybrook(data):
    result = seed.seed(data, now=NOW)

    clients = clients_in(data)
    assert (result.added, result.skipped) == (len(seed.DEMO_CLIENTS), 0)
    assert len(clients) == len(seed.DEMO_CLIENTS)
    assert (clients[0][1], clients[0][2]) == ("C-0042", "Hollybrook Bakery Ltd")
    assert len(clients) >= 6


def test_the_demo_clients_have_unique_refs_and_names_in_the_right_format():
    refs = [ref for ref, _ in seed.DEMO_CLIENTS]
    names = [name for _, name in seed.DEMO_CLIENTS]

    assert all(re.fullmatch(r"C-\d{4}", ref) for ref in refs)
    assert len(set(refs)) == len(refs)
    assert len({n.lower() for n in names}) == len(names)


def test_clients_get_the_time_they_were_made(data):
    seed.seed(data, now=NOW)

    engine = create_engine(f"sqlite:///{data / 'app.db'}")
    with Session(engine) as session:
        assert {c.created_at for c in session.scalars(select(Client))} == {NOW}


def test_seeding_twice_gives_the_same_clients(data):
    seed.seed(data, now=NOW)
    first = clients_in(data)

    again = seed.seed(data, now=NOW)

    assert clients_in(data) == first  # same rows, same ids
    assert (again.added, again.skipped) == (0, len(seed.DEMO_CLIENTS))


def test_a_client_that_already_exists_is_left_alone_and_the_rest_are_added(data):
    seed.seed(data, now=NOW)  # makes the folder and tables
    engine = create_engine(f"sqlite:///{data / 'app.db'}")
    with Session(engine) as session:
        session.query(Client).delete()
        session.add(
            Client(ref="C-0042", name="Hollybrook (my own spelling)", created_at=NOW)
        )
        session.commit()

    result = seed.seed(data, now=NOW)

    clients = {ref: name for _, ref, name in clients_in(data)}
    assert clients["C-0042"] == "Hollybrook (my own spelling)"
    assert (result.added, result.skipped) == (len(seed.DEMO_CLIENTS) - 1, 1)


def test_a_demo_name_that_exists_under_another_ref_is_skipped_not_a_crash(data):
    seed.seed(data, now=NOW)
    engine = create_engine(f"sqlite:///{data / 'app.db'}")
    with Session(engine) as session:
        session.query(Client).delete()
        session.add(Client(ref="C-9999", name="Hollybrook Bakery Ltd", created_at=NOW))
        session.commit()

    result = seed.seed(data, now=NOW)

    assert result.skipped == 1
    assert [r for _, r, n in clients_in(data) if n == "Hollybrook Bakery Ltd"] == [
        "C-9999"
    ]


def test_seeding_makes_the_data_folder_ready_to_use(data):
    seed.seed(data, now=NOW)

    for name in ("photos", "thumbs", "work", "archive", "bin", "logs"):
        assert (data / name).is_dir()
    assert (data / "app.db").is_file()


def test_seeding_leaves_everything_else_in_a_folder_alone(data):
    seed.seed(data, now=NOW)
    (data / "archive").joinpath("keep.pdf").write_bytes(b"precious")

    seed.seed(data, now=NOW)

    assert (data / "archive" / "keep.pdf").read_bytes() == b"precious"


# --- The marker ---


def test_seeding_a_new_or_empty_folder_marks_it_as_made_by_the_seed_script(tmp_path):
    new = tmp_path / "new"
    empty = tmp_path / "empty"
    empty.mkdir()

    first = seed.seed(new, now=NOW)
    second = seed.seed(empty, now=NOW)

    for folder in (new, empty):
        assert (folder / ".demo-data").is_file()
        assert "seed" in (folder / ".demo-data").read_text()
    assert first.marked and second.marked


def test_seeding_a_folder_that_already_has_things_in_it_does_not_mark_it(data):
    data.mkdir()
    (data / "my-real-work.txt").write_text("hello")

    result = seed.seed(data, now=NOW)

    assert len(clients_in(data)) == len(seed.DEMO_CLIENTS)  # the clients were added
    assert not (data / ".demo-data").exists()  # but the folder is still not "ours"
    assert not result.marked


def test_the_marker_name_is_the_one_the_plan_names():
    assert seed.MARKER == ".demo-data"


# --- --reset (plan decision 16) ---


def test_reset_empties_a_folder_the_seed_script_made(data):
    seed.seed(data, now=NOW)
    (data / "photos" / "1").mkdir()
    (data / "photos" / "1" / "x.jpg").write_bytes(b"photo")
    (data / "archive" / "C-0042 Hollybrook Bakery Ltd").mkdir()
    (data / "archive" / "C-0042 Hollybrook Bakery Ltd" / "a.pdf").write_bytes(b"pdf")
    (data / "stray.txt").write_text("stray")

    result = seed.seed(data, reset=True, now=NOW)

    assert result.emptied
    files = contents(data)
    assert not any(name.startswith(("photos/1", "archive/C-0042")) for name in files)
    assert "stray.txt" not in files
    assert len(clients_in(data)) == len(seed.DEMO_CLIENTS)
    assert (data / ".demo-data").is_file()  # still ours afterwards


def test_reset_really_removes_old_database_rows(data):
    seed.seed(data, now=NOW)
    engine = create_engine(f"sqlite:///{data / 'app.db'}")
    with Session(engine) as session:
        session.add(Client(ref="C-9999", name="Left over", created_at=NOW))
        session.commit()

    seed.seed(data, reset=True, now=NOW)

    assert "C-9999" not in [ref for _, ref, _ in clients_in(data)]


def test_reset_on_a_folder_that_does_not_exist_or_is_empty_is_fine(tmp_path):
    missing = tmp_path / "missing"
    empty = tmp_path / "empty"
    empty.mkdir()

    first = seed.seed(missing, reset=True, now=NOW)
    second = seed.seed(empty, reset=True, now=NOW)

    assert not first.emptied and not second.emptied  # nothing was there to empty
    assert len(clients_in(missing)) == len(clients_in(empty)) == len(seed.DEMO_CLIENTS)


def test_reset_refuses_a_folder_the_seed_script_did_not_make_and_touches_nothing(data):
    (data / "archive").mkdir(parents=True)
    (data / "archive" / "real client file.pdf").write_bytes(b"real")
    (data / "app.db").write_bytes(b"not really a database")
    before = contents(data)

    with pytest.raises(seed.SeedRefused) as refusal:
        seed.seed(data, reset=True, now=NOW)

    assert contents(data) == before
    assert not (data / ".demo-data").exists()
    message = str(refusal.value)
    assert str(data) in message
    assert "didn't make" in message
    assert "DOCMANAGER_DATA" in message  # it says what to do instead


def test_reset_refuses_even_a_folder_with_only_a_single_unmarked_file(data):
    data.mkdir()
    (data / "notes.txt").write_text("mine")

    with pytest.raises(seed.SeedRefused):
        seed.seed(data, reset=True, now=NOW)

    assert (data / "notes.txt").read_text() == "mine"


def test_reset_refuses_a_path_that_is_a_file(tmp_path):
    path = tmp_path / "data"
    path.write_text("I am a file")

    with pytest.raises(seed.SeedRefused) as refusal:
        seed.seed(path, reset=True, now=NOW)

    assert "is a file" in str(refusal.value)
    assert path.read_text() == "I am a file"


def test_reset_removes_a_link_but_never_what_it_points_at(data, tmp_path):
    seed.seed(data, now=NOW)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "important.txt").write_text("keep me")
    (data / "link").symlink_to(outside, target_is_directory=True)

    seed.seed(data, reset=True, now=NOW)

    assert not (data / "link").exists()
    assert (outside / "important.txt").read_text() == "keep me"


def test_a_plain_seed_never_empties_anything(data):
    seed.seed(data, now=NOW)
    (data / "stray.txt").write_text("stray")

    result = seed.seed(data, now=NOW)

    assert not result.emptied
    assert (data / "stray.txt").exists()


# --- The messages ---


def test_the_messages_say_what_happened():
    fresh = seed.SeedResult(added=8, skipped=0, emptied=False, marked=True)
    again = seed.SeedResult(added=0, skipped=8, emptied=False, marked=False)
    reset = seed.SeedResult(added=8, skipped=0, emptied=True, marked=True)
    one = seed.SeedResult(added=1, skipped=0, emptied=False, marked=False)

    assert fresh.message() == "Added 8 clients."
    assert again.message() == "Added 0 clients. 8 already there."
    assert reset.message() == "Emptied the data folder first. Added 8 clients."
    assert one.message() == "Added 1 client."


# --- The command ---


def test_the_seed_command_seeds_the_data_folder_from_the_environment(
    monkeypatch, tmp_path, capsys
):
    folder = tmp_path / "somewhere"
    monkeypatch.setenv("DOCMANAGER_DATA", str(folder))

    cli.main(["seed"])

    assert len(clients_in(folder)) == len(seed.DEMO_CLIENTS)
    assert f"Added {len(seed.DEMO_CLIENTS)} clients." in capsys.readouterr().out


def test_the_seed_command_with_reset_empties_a_seeded_folder(monkeypatch, tmp_path):
    folder = tmp_path / "somewhere"
    monkeypatch.setenv("DOCMANAGER_DATA", str(folder))
    cli.main(["seed"])
    (folder / "stray.txt").write_text("stray")

    cli.main(["seed", "--reset"])

    assert not (folder / "stray.txt").exists()


def test_the_seed_command_refuses_an_unmarked_folder_with_a_message_and_an_exit(
    monkeypatch, tmp_path, capsys
):
    folder = tmp_path / "real"
    folder.mkdir()
    (folder / "work.txt").write_text("real work")
    monkeypatch.setenv("DOCMANAGER_DATA", str(folder))

    with pytest.raises(SystemExit) as stop:
        cli.main(["seed", "--reset"])

    assert stop.value.code == 1
    assert "didn't make" in capsys.readouterr().err
    assert (folder / "work.txt").read_text() == "real work"
    assert not (folder / "app.db").exists()


def test_the_seed_command_does_not_start_the_server_or_need_the_ocr_tools(
    monkeypatch, tmp_path
):
    from flask import Flask

    monkeypatch.setenv("DOCMANAGER_DATA", str(tmp_path / "somewhere"))
    monkeypatch.setattr(Flask, "run", lambda *a, **k: pytest.fail("server started"))
    monkeypatch.setattr(ocr, "check_ocr_tools", lambda: ["Tesseract isn't installed."])

    cli.main(["seed"])


def test_the_seed_command_takes_no_other_options(capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(["seed", "--everything"])

    assert stop.value.code == 2
