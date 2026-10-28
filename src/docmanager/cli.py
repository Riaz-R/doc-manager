import argparse
from pathlib import Path

from docmanager import config, create_app
from docmanager.demo import photos


def main(argv: list[str] | None = None) -> None:
    """`docmanager` serves the app; `docmanager make-photos OUT_DIR` writes demo photos."""
    parser = argparse.ArgumentParser(prog="docmanager")
    commands = parser.add_subparsers(dest="command")
    make_photos = commands.add_parser(
        "make-photos", help="write a small box of made-up demo photos"
    )
    make_photos.add_argument("out_dir", metavar="OUT_DIR", help="folder to write into")
    args = parser.parse_args(argv)

    if args.command == "make-photos":
        written = photos.write_demo_box(Path(args.out_dir).expanduser())
        print(f"Wrote {len(written)} photos to {args.out_dir}")
        return

    # Debug mode stays off: it would let anyone who can reach the page run code.
    create_app().run(host=config.HOST, port=config.PORT, debug=False)
