import argparse
import sys
from pathlib import Path

from docmanager import config, create_app
from docmanager.demo import photos
from docmanager.services import ocr


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

    problems = ocr.check_ocr_tools()
    if problems:
        print("Doc Manager can't start yet:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(f"\nTo fix this, run:\n  {ocr.APT_COMMAND}", file=sys.stderr)
        raise SystemExit(1)

    # Debug mode stays off: it would let anyone who can reach the page run code.
    create_app().run(host=config.HOST, port=config.PORT, debug=False)
