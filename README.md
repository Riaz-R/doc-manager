# Doc Manager

Doc Manager turns photos of paper client files into named PDFs with a text layer, so you can search within each one, on your own computer, and tells you when each box's paper can be shredded and, separately, when each digital record can be destroyed.

Everything runs locally: nothing is sent over the network, and the app only listens on `127.0.0.1` (your own computer).

> **The retention rules are illustrative.** These keep-until dates come from example rules. Check the rules that apply to you, including whether a digital copy may replace the paper.

## Install

You need [uv](https://docs.astral.sh/uv/) (it installs Python 3.13 and the libraries for you) and two programs from your system's package manager. On Ubuntu or Debian (including WSL):

```
sudo apt install tesseract-ocr ghostscript
uv sync
```

Tesseract reads the text in the photos; Ghostscript is used by the PDF tools. The app checks for them when it starts and tells you what is missing.

## Run

```
uv run docmanager
```

Then open <http://127.0.0.1:5000> in your browser. Stop it with Ctrl+C.

Your files and database live in the `data/` folder next to where you run the command (it is not part of the repository).

### Advanced: keeping your data somewhere else

`DOCMANAGER_DATA` is a setting (an environment variable) that tells the app which folder to keep its files and database in, instead of `data/`. Put it in front of a command:

```
DOCMANAGER_DATA=~/my-documents uv run docmanager
```

Use the same value every time you run `docmanager` or `docmanager seed`, or you will be looking at a different, empty folder.

### The app starts empty

A new data folder has no boxes, no documents and **no clients**. In this version clients can only be added by the `seed` command, and a document can only be filed once it matches a client. So, before anything can be filed, run:

```
uv run docmanager seed
```

`seed` is an optional *demo* command, but it is the only way to get clients for now. It adds eight made-up clients (including `C-0042 Hollybrook Bakery Ltd`) and two demo boxes, "Box 1 – 2016–2019" (its paper can go) and "Box 2 – 2020–2022" (still blocked, and showing what is blocking it). Reading the demo pages takes about a minute. Running it again doesn't duplicate anything.

To start again, move the old `data/` folder aside (rename it) and run `uv run docmanager seed`. `seed --reset` only empties a folder the seed script made itself (it leaves a `.demo-data` file there), and refuses any other folder.

## How to use it

1. Take a box off the shelf and give it a name in the app, for example "Box 3 – 2017–2019".
2. Photograph each document's pages in order with your phone. **Tip:** cover the lens for one photo between documents. The dark photos make the gaps easy to see in the inbox.
3. Upload the photos into that box (JPEG or PNG; a big box may take several uploads).
4. In the inbox, first group each document: pick its first and last photo and press **Make document**, leaving the black lens-cover photos in place as visible separators between documents. The app reads the document while the page waits, then files it or marks it "Needs checking". Then tick the black photos and any bad shots and press **Mark ticked as not a page**. The lens covers must be cleared this way, or the box will never show **Paper can go**. Note that Make document ignores the ticks; the inbox ticks are only used by Mark ticked as not a page.
5. Check flagged documents now or later.
6. When Home shows **Paper can go** beside the box, you can shred that box's paper. (It doesn't wait for the keep-until date.)
7. Later, as a separate step: when records pass their keep-until date, open **Due for disposal**, move them to the bin, and empty the bin with a separate confirmation. This destroys the digital records; only a short disposal record of each one is kept.

## Try the demo

```
uv run docmanager seed --reset                # clients and two demo boxes
uv run docmanager make-photos ~/demo-box      # a folder of made-up photos to upload yourself
uv run docmanager                             # then open http://127.0.0.1:5000
```

Upload `~/demo-box` into a new box. Group each document first with First and Last, leaving the black lens-cover photos in place as visible separators. Then tick the black photos and press "Mark ticked as not a page" (the lens covers must be cleared for the box to show Paper can go; Make document ignores ticks). One document is deliberately unclear, so it lands in Needs checking. Open it, pick a type and a client, and press **File it**. Back on Home the box shows **Paper can go**.

## Tests

```
uv run pytest                  # everything (run these in a second terminal tab while the app is running)
uv run pytest -m "not ocr"     # skip the slow tests that run the real OCR program
uv run ruff format --check && uv run ruff check
```

Run the tests in a second terminal tab while the app is still running in the first; they use their own temporary data and don't touch the app's.

Tests use made-up photos drawn with Pillow and never touch the network.

## Known limitations

- A document from a client who isn't in the register can't be filed, because clients only come from the `seed` command.
- A phone counter rollover (IMG_9999 → IMG_0001) puts photos in the wrong order.
- A long document holds the browser page until OCR finishes (up to the 5-minute timeout).
- Classification is tested on generated text only; how well it does on real phone photos hasn't been measured.
- There is no search across documents yet; you can only search within a single PDF.
- iPhone HEIC photos aren't supported yet (on the iPhone: Settings → Camera → Formats → Most Compatible).
- There are no logins and no protection against other web pages in the same browser submitting the app's forms, so only run it on a computer you trust.

## More

- [SPEC.md](SPEC.md): what the app does and why, in full.
- [DECISIONS.md](DECISIONS.md): every decision made while building it.
- [PLAN.md](PLAN.md): the build plan.
