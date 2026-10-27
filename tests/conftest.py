from datetime import datetime

import pytest

from docmanager import create_app

# Every test sees the same "now", so dates never depend on the real clock.
FIXED_NOW = datetime(2026, 10, 27, 12, 0)


@pytest.fixture(autouse=True)
def isolated_data_folder(tmp_path, monkeypatch):
    """Point DOCMANAGER_DATA at a private folder so no test writes to ./data."""
    monkeypatch.setenv("DOCMANAGER_DATA", str(tmp_path / "env-data"))


@pytest.fixture
def now():
    return FIXED_NOW


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


@pytest.fixture
def app(data_dir):
    return create_app({"DATA_DIR": data_dir, "CLOCK": lambda: FIXED_NOW})


@pytest.fixture
def client(app):
    return app.test_client()
