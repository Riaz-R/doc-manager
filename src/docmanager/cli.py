import argparse
import sys
from pathlib import Path

from docmanager import config, create_app
from docmanager.demo import photos, seed
from docmanager.services import ocr


def main(argv: list[str] | None = None) -> None:
    """`docmanager` serves the app; `make-photos OUT_DIR` and `seed [--reset]` are the demo helpers."""
    parser = argparse.ArgumentParser(prog="docmanager")
    commands = parser.add_subparsers(dest="command")
    make_photos = commands.add_parser(
        "make-photos", help="write a small box of made-up demo photos"
    )
    make_photos.add_argument("out_dir", metavar="OUT_DIR", help="folder to write into")
    seed_command = commands.add_parser(
        "seed",
        help="add the made-up demo clients and two demo boxes to the data folder",
    )
    seed_command.add_argument(
        "--reset",
        action="store_true",
        help="empty the data folder first (only if the seed script made it, or it is empty)",
    )
    args = parser.parse_args(argv)

    if args.command == "make-photos":
        written = photos.write_demo_box(Path(args.out_dir).expanduser())
        print(f"Wrote {len(written)} photos to {args.out_dir}")
        return

    if args.command == "seed":
        try:
            root = config.Paths.from_env().root
            print(seed.seed(root, reset=args.reset).message())
            print("Filling the demo boxes. Each page is read with OCR: about a minute.")
            print(seed.fill_demo_boxes(root).message())
        except seed.SeedRefused as refusal:
            print(refusal, file=sys.stderr)
            raise SystemExit(1) from None
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
