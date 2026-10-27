from docmanager import config, create_app


def main() -> None:
    # Debug mode stays off: it would let anyone who can reach the page run code.
    create_app().run(host=config.HOST, port=config.PORT, debug=False)
