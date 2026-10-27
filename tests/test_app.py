from flask import Flask

from docmanager import cli, config


def test_home_page_answers_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_command_serves_only_on_127_0_0_1(monkeypatch):
    # AT-21: Flask.run is replaced by a recorder, so no real server starts.
    calls = []

    def record_run(self, *args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(Flask, "run", record_run)

    cli.main()

    assert calls == [((), {"host": "127.0.0.1", "port": 5000, "debug": False})]


def test_host_and_port_are_fixed_in_config():
    assert config.HOST == "127.0.0.1"
    assert config.PORT == 5000
