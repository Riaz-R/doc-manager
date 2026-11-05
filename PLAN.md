# Doc Manager: build plan

## Progress
**Sitting (a) Foundation**
- [x] Task 1: Project skeleton and a first page on 127.0.0.1
- [x] Task 2: Settings, database and page frame
- [x] Task 3: Lifecycle engine
- [x] Task 4: Models with the Page and Document lifecycles

**Sitting (b) Upload, inbox, grouping, Not a page**
- [x] Task 5: Upload into a box
- [x] Task 6: Inbox in filename order
- [x] Task 7: Make document
- [x] Task 8: Not a page, restore and the Bin
- [x] Task 9: Demo photo generator

**Sitting (c) OCR, classification, filing**
- [x] Task 10: Document types and dates
- [x] Task 11: Classification, with the low-text check
- [x] Task 12: Naming rules
- [x] Task 13: OCR runner and start-up check
- [x] Task 14: Read and file on Make document, with Retry
- [x] Task 15: Filed documents and the Document page
- [x] Task 16: Seed creates the demo clients

**Sitting (d) Review, Paper can go**
- [x] Task 17: Confirming a document in review
- [x] Task 18: Needs checking and Check document screens
- [x] Task 19: Paper can go
- [x] Task 20: End-to-end OCR test and demo-line check

**——— DEMO LINE: demo script steps 1–7 (§9) work ———**

**Sitting (e) Retention and destruction**
- [x] Task 21: Retention
- [ ] Task 22: Due for disposal, Move to bin, restore
- [ ] Task 23: Empty bin and disposal records

**Sitting (f) Seed script and README**
- [ ] Task 24: Seed fills boxes and documents
- [ ] Task 25: README and manual checks

**Gate.** Every task ends with its Done-when command passing and this gate green:
`uv run ruff format --check && uv run ruff check && uv run pytest`

**Tests:**
- Tests make their own made-up photos with Pillow, never real documents.
- Tests never touch the network.
- Web pages are tested with Flask's test client.
- Each test gets its own data folder (pytest's `tmp_path`) and a fixed clock.

---

## Class design

```
Box 1──* Batch 1──* Page *──0..1 Document *──0..1 Client
Box 1──* Page,  Box 1──* Document
Document.doc_type (a key) ──> DOCUMENT_TYPES[key] : InvoiceType | LetterType   (both DocumentType)
Page, Document ── Stateful mixin ── Lifecycle table; every apply() writes exactly one StateChange
Document ──destroy──> DisposalRecord (a snapshot; the only thing that remains)
```

| Where | Class | Job |
|---|---|---|
| `lifecycle.py` | `InvalidTransition` | An exception carrying a plain-words reason for the user. |
| | `Lifecycle` | Holds the transition table `{(from_state, action): to_state}`. `None` stands for "(new)" as a from-state and "(row deleted)" as a to-state. `target(state, action)` raises `InvalidTransition` with a message like "This document can't be moved to the bin while it is "Needs checking"". `actions_from(state)` lists the actions. |
| | `Stateful` (mixin) | Stores the `_state` column (database name `state`). `state` is a read-only property returning the enum. Also gives `allowed_actions()` and `apply(action, *, now, note=None)`. |
| `models/page.py` | `PageState` (StrEnum with `.label`), `Page`, `PAGE_LIFECYCLE` | One photo. Order key is `(original_filename, id)`. |
| `models/document.py` | `DocState`, `Document`, `DOC_LIFECYCLE` | Has the guards `guard_file`, `guard_flag`, `guard_confirm` and `guard_dispose`. `type` returns the `DocumentType` or `None`. `change_type(new_type, *, today)`. `state_label`. `filed_name`. Markers: `needs_checking`, `has_no_date`, `is_due(today)`. |
| `models/document_types.py` | `DocumentType`, `InvoiceType`, `LetterType`, `DOCUMENT_TYPES` | Plain Python, not stored. Each has `key`, `label`, `plural_label`, `retention_years`, `score(text)`, `extract(text, today)`, `filename_key(fields)`, `keep_until(date)` and the helper `keyword_score(text, weights)`. |
| `models/box.py` | `Box`, `Batch` | `Box` has `ordered_pages()`, `inbox_pages()`, `paper_blockers()` and `paper_can_go()`. |
| `models/client.py` | `Client` | `ref` (C-0000) and `name`, both unique. |
| `models/records.py` | `StateChange`, `DisposalRecord` | Append-only history, and the destruction snapshot. |
| `rules/` | `dates.py`, `classify.py` (`Classification`, `count_words`), `naming.py` | Pure functions with no database, so they are fast and easy to unit-test. |
| `services/` | `upload.py` (`UploadRefused`, `UploadResult`), `grouping.py` (`GroupingError`), `ocr.py` (`OcrFailed`), `filing.py`, `disposal.py` | Each function takes a session and `now`. This is where the database and files change. |
| `web/routes.py` | One Flask blueprint | Kept thin: read the form, call one service, commit, then redirect with a `flash` message. |

**How `apply()` works.**
1. It looks up `(state, action)` in the table.
2. If a `guard_<action>(now)` method exists and returns a reason, it raises `InvalidTransition(reason)`.
3. It sets `_state`.
4. If the row has no id yet, it flushes the session so the database assigns one.
5. It adds one `StateChange` row, using the session that `object_session(self)` returns.

**Rules for code and tests:**
- **The clock and the OCR program are app settings** (`CLOCK` and `OCR_RUNNER`), so tests can fix the date and swap OCR for a fake.
- **Replace JSON columns with a new value.** Always assign a new dict or list to `fields` and `review_reasons`, because SQLAlchemy doesn't notice in-place changes to JSON.
- **Tests may set `_state` directly** to put an object in a given state. App code never does.

## Decisions this plan makes (beyond the spec)

| # | Decision |
|---|---|
| 1 | Task 1 adds Flask and a first page, so the app runs, and the 127.0.0.1 binding is tested, from the start. Debug mode always stays off. |
| 2 | `NAMING_TEMPLATE` lives in `config.py` with the other tunable values. §5.6 says `rules/naming.py`; §7 says `config.py`. |
| 3 | `allowed_actions()` lists the table's actions for the current state and doesn't run guards. A not-yet-Due document therefore shows **Move to bin**, and pressing it gives the refusal reason. Demo step 8 needs this. |
| 4 | `extract()` and `change_type()` take `today`, so future dates can be ignored (following the §3.7 rule). |
| 5 | Make document commits the new Grouped document before OCR starts. W4 depends on this, and it keeps SQLite unlocked during the long read. |
| 6 | Paths stored in the database are relative to the data folder, so `DOCMANAGER_DATA` can move it. |
| 7 | Originals keep their real extension (`.jpg` or `.png`). Thumbnails are always 400px JPEGs. |
| 8 | Photos are checked by fully decoding them with Pillow, which catches truncated JPEGs. HEIC is recognised by its `.heic` or `.heif` extension. |
| 9 | Inbox numbers count every photo in the box in filename order. They don't shift as photos leave the inbox, so "Photos 3 to 7" stays meaningful. |
| 10 | `keyword_score` counts each keyword once, ignoring case and matching whole words. The keyword weights are chosen in task 10 and logged in DECISIONS.md. |
| 11 | New wordings. **Reasons:** "Couldn't tell which client this is for" and "More than one client reference found: C-0042, C-0043". **Guards:** "This document hasn't been read yet", "Choose a type before filing" and "Choose a client before filing". **Box names:** "Give the new box a name" and "Box names can be at most 60 characters". **Blocking lines:** plural forms such as "2 documents need checking before this paper can go". "Nothing filed from this box yet" is shown when the box has no documents. A flagged document's message lists all its reasons, joined with "; ". |
| 12 | **Upload message.** Parts with a zero count are left out. HEIC files are listed as "N refused – iPhone HEIC photo (names)", followed by the B7 sentence. |
| 13 | **Review values.** When you press File it, the app starts from the stored values. If you changed the type, it starts instead from the new type's fields and date, read again from the OCR text. Any value you changed on the form then replaces the starting value. "Changed" means different from what the screen showed: the form carries the shown values in hidden fields. The Check document screen shows the date and the fields for every type (Invoice: number and amount; Letter: subject), so you can type a value for the new type in the same step. **Later** on the inbox banner hides the banner for that visit. |
| 14 | `Document.filed_name` is the archive filename, including any clash suffix such as " (2)". It is set each time the document is filed or restored, and copied into the DisposalRecord. Restoring from the bin clears `binned_at`. |
| 15 | Emptying the bin deletes the database rows in one transaction, then deletes the files after the commit. |
| 16 | `seed --reset` only empties a data folder that the seed script made (it carries a `.demo-data` marker) or one that is empty. Otherwise it refuses and says why. |
| 17 | `pdfminer.six` is added as a dev-only dependency, so the end-to-end test can read the PDF's text layer. |
| 18 | **Low-text check.** A word is a whitespace-separated piece of text containing a letter or digit. The check runs first, and the type and client checks still run, so every reason is recorded. `guard_file` also refuses when there is too little text, so the lifecycle enforces it. Confirming in review doesn't need it. Every test fixture, demo document and seeded document has at least 20 words, except the C11 fixture. |

---

## Sitting (a) Foundation: 65 min (§10: 55). Done when AT-01–AT-04, AT-21 and AT-22 pass

### Task 1: Project skeleton and a first page on 127.0.0.1 (15 min)
- **Builds:**
  - `uv init --package docmanager` with the src layout, and Python 3.13 in `.python-version`.
  - Dependencies: `uv add flask` and `uv add --dev pytest ruff`.
  - Settings in `pyproject.toml`:
    - Ruff: the default rules plus `I` (import sorting).
    - pytest: `testpaths` and the `ocr` marker.
  - `.gitignore`, covering:
    - `.venv/`, `data/`, `*.db`, `__pycache__/`, `.pytest_cache/` and `.ruff_cache/`;
    - generated test files (`tests/**/*.jpg|png|pdf`);
    - `demo-box/`.
  - `config.py` with `HOST = "127.0.0.1"` and `PORT = 5000`.
  - `create_app()` with a one-line Home page.
  - The `docmanager` command (`[project.scripts]`), which serves the app on HOST:PORT with no option to change the host.
- **Files:** `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `src/docmanager/{__init__,cli,config}.py`, `tests/conftest.py`, `tests/test_app.py`
- **Tests:**
  - AT-21: the command calls `app.run(host="127.0.0.1", port=5000)`. `Flask.run` is replaced by a recorder.
  - Home answers 200 through the test client.
- **Done when:** `uv sync && uv run pytest -v && uv run ruff check && uv run ruff format --check`

### Task 2: Settings, database and page frame (20 min)
- **Builds:**
  - `uv add sqlalchemy`.
  - `config.py` gets all the constants:
    - `MIN_TYPE_SCORE` 6, `MIN_TYPE_MARGIN` 3 and **`MIN_OCR_WORDS` 20**;
    - `NAMING_TEMPLATE`;
    - `OCR_TIMEOUT_SECONDS` 300;
    - `THUMB_SIZE` 400;
    - `MAX_UPLOAD_BYTES` 500 MB.
  - `config.Paths`: the data folder from `DOCMANAGER_DATA` (default `./data`), with photos, thumbs, work, archive, bin, logs and `app.db`.
  - `db.py`:
    - `Base` and the engine;
    - `create_all` at start-up;
    - one session per request, through `get_session()` on `flask.g` and closed at teardown.
  - `create_app(overrides)` accepts `DATA_DIR` and `CLOCK`.
  - Templates and style:
    - `base.html` with the flash banner and navigation;
    - `style.css`: 20px base font, buttons at least 48px tall, high contrast.
  - Error handling:
    - friendly 404 and 500 pages;
    - a rotating log at `data/logs/app.log`;
    - one handler that flashes plain-words domain errors and redirects back.
- **Files:** `config.py`, `db.py`, `__init__.py`, `web/routes.py`, `web/templates/{base,home,404,500}.html`, `web/static/style.css`, `tests/conftest.py` (app, client and fixed-clock fixtures), `tests/test_app.py`, `tests/test_no_urls.py`
- **Tests:**
  - AT-22: no `http(s)://` in templates or static files.
  - `DOCMANAGER_DATA` moves the database.
  - An unknown URL shows the friendly 404.
  - A failing route shows the 500 page and writes to the log.
- **Done when:** `uv run pytest tests/test_app.py tests/test_no_urls.py -v`

### Task 3: Lifecycle engine (15 min)
- **Builds:** `InvalidTransition`, `Lifecycle` and `Stateful` in `lifecycle.py`, and `StateChange` in `models/records.py`.
- **Files:** `lifecycle.py`, `models/__init__.py`, `models/records.py`, `tests/test_lifecycle.py`
- **Tests:** these use a tiny model defined only in the test, a lamp that goes Off ⇄ On with one guard:
  - an allowed move changes the state and writes one StateChange;
  - an unknown pair raises with plain words;
  - a guard's reason is raised;
  - `state` has no setter.
- **Done when:** `uv run pytest tests/test_lifecycle.py -v`

### Task 4: Models with the Page and Document lifecycles (15 min)
- **Builds:**
  - `Box`, `Batch`, `Client`, `Page` and `Document`, with every field in §3, including `filed_name`.
  - The `PAGE_LIFECYCLE` and `DOC_LIFECYCLE` tables, copied exactly from §3.3 and §3.4.
  - Document guards:
    - **file / confirm:** the document has been read, and has a type and a client;
    - **flag:** the document has been read;
    - **dispose:** the document is Due, otherwise "This document must be kept until 14 Mar 2027". With no keep-until the reason is "Keep-until not set – add the document's date".
  - `state_label`, and `format_date()` in `rules/dates.py`.
- **Files:** `models/{box,page,document,client}.py`, `rules/dates.py`, `tests/test_lifecycles.py`
- **Tests:**
  - AT-01: table-driven over every (state, action) pair, including "(new)".
  - AT-02: every guard reason, word for word.
  - AT-03: exactly one StateChange per transition.
  - AT-04: `page.state = …` raises `AttributeError`.
- **Done when:** `uv run pytest tests/test_lifecycles.py -v`

---

## Sitting (b) Upload, inbox, grouping, Not a page: 90 min (§10: 90). Done when AT-05 (except B5) and AT-06–AT-09 pass

### Task 5: Upload into a box (25 min)
- **Builds:**
  - `uv add pillow`.
  - `services/upload.py`:
    - `find_or_create_box()`, which refuses a duplicate name (B8) and checks the 1–60 character rule;
    - `upload_photos()`, which returns an `UploadResult` whose `.message()` uses the §4 wording.
  - File checks:
    - JPEG and PNG only, judged by decoding the content;
    - a corrupt file is refused by name;
    - HEIC gets the B7 sentence.
  - Duplicate check: sha256 against the database and within the same upload.
  - Storage: originals at `photos/<box-id>/<sha256>.<ext>`, and thumbnails.
  - A Batch with its counts. Each page goes through `apply("upload")`.
  - Screens:
    - Upload screen: pick a box or "New box", and a `multiple` file input;
    - Home lists boxes with "N photos to sort".
  - An over-500 MB upload shows "upload in parts" (a 413 handler).
- **Files:** `services/upload.py`, `web/routes.py`, `templates/{upload,home}.html`, `tests/conftest.py` (`photo_bytes(label)`: draws a label on white with Pillow), `tests/test_upload.py`
- **Tests:**
  - AT-05: B1–B4 and B6–B8.
  - The over-size message, with the limit lowered in the test app.
- **Done when:** `uv run pytest tests/test_upload.py -v`

### Task 6: Inbox in filename order (15 min)
- **Builds:**
  - Page order by filename.
  - `Box.ordered_pages()` with fixed numbers for each photo.
  - The Inbox screen shows, for each photo:
    - a large numbered thumbnail and its filename;
    - **First** and **Last** radio buttons;
    - a **Not a page** tick box.
  - A thumbnail route.
- **Files:** `models/{box,page}.py`, `web/routes.py`, `templates/inbox.html`, `tests/test_inbox.py`
- **Tests:**
  - AT-06: O1 as a unit test.
  - The inbox page lists photos in filename order with their numbers.
  - The thumbnail route serves a JPEG.
- **Done when:** `uv run pytest tests/test_inbox.py -v`

### Task 7: Make document (20 min)
- **Builds:** `services/grouping.py` with `GroupingError` and `make_document()`:
  - it swaps First and Last if they're reversed (G3);
  - it needs both ends picked (G5);
  - it refuses a range that includes a Grouped photo, with the G4 wording;
  - it skips "Not a page" photos (G7);
  - it gives the photos positions 1..n;
  - every change goes through `apply("group")`.

  Until task 14:
  - the message is "Document made from photos 3 to 6";
  - the inbox lists unread documents as "Not read yet".
- **Files:** `services/grouping.py`, `web/routes.py`, `templates/inbox.html`, `tests/test_grouping.py`
- **Tests:** AT-07: G1 (without OCR) and G2–G5.
- **Done when:** `uv run pytest tests/test_grouping.py -v`

### Task 8: Not a page, restore and the Bin (15 min)
- **Builds:**
  - `discard_pages()` and `restore_page()`.
  - A "Mark ticked as not a page" button.
  - A Bin screen listing the photos, each with a **Restore** button.
  - A Bin tile on Home.
- **Files:** `services/grouping.py`, `web/routes.py`, `templates/{bin,home}.html`, `tests/test_not_a_page.py`
- **Tests:** AT-08 (G6 and G7) and AT-09 (G8).
- **Done when:** `uv run pytest tests/test_not_a_page.py -v`

### Task 9: Demo photo generator (15 min)
- **Builds:** `demo/photos.py`, and the command `docmanager make-photos OUT_DIR`.
  - **Pages:** typed text on white images, 1240×1754 at 150 dpi, using Pillow's built-in scalable font.
  - **Lens covers:** plain black images.
  - **`write_demo_box(out_dir)`** writes three made-up documents, each well over 20 words, as `IMG_0001.jpg`…, with a lens cover between documents:
    - an invoice for C-0042 Hollybrook Bakery Ltd, INV-1043, dated 14/03/2026;
    - a letter;
    - a deliberately unclear document with no client, for the review step.
- **Files:** `demo/{__init__,photos}.py`, `cli.py`, `tests/test_demo_photos.py`
- **Tests:**
  - The expected file names are written.
  - The lens covers are pure black.
  - Every page is different.
  - The folder uploads through the Upload page with every photo added.
- **Done when:** `uv run pytest tests/test_demo_photos.py -v && uv run docmanager make-photos ~/demo-box && ls ~/demo-box`

---

## Sitting (c) OCR, classification, filing: 110 min (§10: 90). Done when AT-10, AT-11 (except the keep-until checks) and AT-13 pass

### Task 10: Document types and dates (20 min)
- **Builds:**
  - `DocumentType` and `keyword_score`.
  - `InvoiceType`:
    - `invoice_number`;
    - `amount_pence`, from "Amount due £120.00";
    - the invoice date: a labelled date first, otherwise the first date.
  - `LetterType`:
    - `subject`, from a "Re:" line;
    - the first date as the letter date.
  - The `DOCUMENT_TYPES` registry and `Document.type`.
  - `find_dates(text, today)`:
    - reads `14/03/2021`, `14 March 2021` and `2021-03-14`;
    - ignores dates after today.
  - `keep_until` waits for task 21.
- **Files:** `models/{document_types,document}.py`, `rules/dates.py`, `tests/texts.py` (made-up OCR texts of at least 20 words each), `tests/test_document_types.py`, `tests/test_dates.py`
- **Tests:** AT-11 parts:
  - each type's `score()`;
  - every extracted field;
  - each date format, including a future date being ignored;
  - the filename keys, including "no number" and "letter".
- **Done when:** `uv run pytest tests/test_document_types.py tests/test_dates.py -v`

### Task 11: Classification, with the low-text check (20 min)
- **Builds:** `rules/classify.py`, with `count_words()` and `classify(text, clients, today)` returning a `Classification`. The checks run in this order:
  - **Check 1, text:** at least `MIN_OCR_WORDS` words.
  - **Check 2, type:** a minimum score and a margin over the runner-up.
  - **Check 3, client:** a single C-0000 ref, otherwise an exact name (whole phrase, case ignored).

  Reasons use the §5.5 wording, plus the two wordings in decision 11. `guard_file` also refuses when there is too little text.
- **Files:** `rules/classify.py`, `models/document.py`, `tests/texts.py`, `tests/test_classify.py`, `tests/test_lifecycles.py`
- **Tests:**
  - AT-11: C1–C6 and **C11** on text fixtures, with exact wording.
  - C11: a confident 11-word invoice text is flagged with the low-text reason.
  - `guard_file` refuses when there is too little text.
- **Done when:** `uv run pytest tests/test_classify.py tests/test_lifecycles.py -v`

### Task 12: Naming rules (15 min)
- **Builds:** `rules/naming.py` builds the path from the template:
  - `undated` when there's no date;
  - unsafe characters become `-`;
  - trailing dots and spaces are trimmed;
  - a clash adds ` (2)`, then ` (3)`.
- **Files:** `rules/naming.py`, `tests/test_naming.py`
- **Tests:** AT-13: N1–N4.
- **Done when:** `uv run pytest tests/test_naming.py -v`

### Task 13: OCR runner and start-up check (15 min)
- **Builds:**
  - `uv add ocrmypdf img2pdf`.
  - `combine_photos()` uses img2pdf.
  - `run_ocrmypdf()` runs `python -m ocrmypdf -l eng --rotate-pages --deskew --sidecar` as a subprocess with a timeout. A non-zero exit or a timeout becomes `OcrFailed`, carrying the technical detail.
  - `check_ocr_tools()`: `docmanager` prints what is missing and the apt command, then exits.
  - In `conftest`:
    - `FakeOcr` copies the PDF and writes the given text, or fails;
    - `ocr` tests are skipped with a clear message if the tools are missing.
- **Files:** `services/ocr.py`, `cli.py`, `tests/conftest.py`, `tests/test_ocr.py`
- **Tests:**
  - AT-10 W5: a missing Tesseract and missing `osd` data each give a message and an exit.
  - A real timeout becomes `OcrFailed`. The test swaps in a sleeping command with a 1-second limit.
  - A non-zero exit becomes `OcrFailed`.
  - One `ocr` test runs real OCRmyPDF on a generated page.
- **Done when:** `uv run pytest tests/test_ocr.py -v`

### Task 14: Read and file on Make document, with Retry (20 min)
- **Builds:**
  - `Document.change_type()`: sets the key, then reads fields and date again from the text.
  - `filing.read_document()`:
    - commits the Grouped document first;
    - runs `OCR_RUNNER`;
    - stores `ocr_text`, or stores `ocr_error` and writes the detail to the log;
    - after a success, classifies the document, then sets its type, client and reasons;
    - files it (moving the PDF to its archive path and setting `filed_name`) or flags it.
  - After Make document, the message is one of:
    - "Filed as …";
    - "Needs checking: …";
    - the W2 wording.
  - A **Retry** button for documents that couldn't be read or haven't been read yet.
  - The images PDF is deleted after each attempt. The sidecar `.txt` stays in `work/`.
- **Files:** `services/{filing,ocr}.py`, `models/document.py`, `web/routes.py`, `templates/inbox.html`, `tests/test_reading.py`
- **Tests** (all with `FakeOcr`):
  - W1: filed at the N1 path with `filed_name` set, and C1 end to end.
  - W2: an OCR failure leaves the document Grouped, with the exact error, the detail in the log, and Retry shown.
  - W3: Retry clears the error and files the document.
  - W4: a Grouped document with no text is listed with Retry.
  - C6: the path uses "undated".
  - A clash gives `filed_name` the " (2)" suffix.
- **Done when:** `uv run pytest tests/test_reading.py -v`

### Task 15: Filed documents and the Document page (10 min)
- **Builds:**
  - **Filed documents table:** client, type, date, keep-until and markers.
  - **Document page:**
    - the PDF in an iframe, served by a PDF route;
    - the fields, markers and state label;
    - only the allowed buttons;
    - "The PDF file is missing" when the file isn't on disk (N5).
- **Files:** `web/routes.py`, `templates/{filed,document}.html`, `tests/test_document_pages.py`
- **Tests:**
  - N5.
  - The list shows a filed document with its "No date" marker.
  - The document page shows its state label.
- **Done when:** `uv run pytest tests/test_document_pages.py -v`

### Task 16: Seed creates the demo clients (10 min)
- **Builds:** `demo/seed.py` and `docmanager seed [--reset]`.
  - Seeding adds made-up clients, including C-0042 Hollybrook Bakery Ltd, and skips any that already exist.
  - `--reset` follows decision 16.
- **Files:** `demo/seed.py`, `cli.py`, `tests/test_seed.py`
- **Tests:**
  - Seeding twice gives the same clients.
  - `--reset` empties a seeded folder.
  - `--reset` refuses an unmarked folder and leaves it untouched.
- **Done when:** `uv run pytest tests/test_seed.py -v`

---

## Sitting (d) Review, Paper can go: 60 min (§10: 40). Done when AT-12 (except the keep-until checks), AT-14–AT-17 and AT-20 pass

### Task 17: Confirming a document in review (15 min)
- **Builds:** `filing.confirm_document()`:
  - takes the posted values together with the values the screen showed;
  - works out the final values by the decision 13 rule;
  - sets the client;
  - runs `apply("confirm")`;
  - files the document and sets `filed_name`.
- **Files:** `services/filing.py`, `tests/test_review.py`
- **Tests:**
  - C8.
  - C9: same id 17, same pages, history kept, letter fields.
  - Changing the type with a typed subject keeps the typed subject, and the date is read again.
  - Changing the type with a typed date keeps the typed date.
  - With no type change, the typed values are saved.
  - C10's guard, at the service level.
- **Done when:** `uv run pytest tests/test_review.py -v`

### Task 18: Needs checking and Check document screens (20 min)
- **Builds:**
  - **Needs checking list:** oldest first, with reasons.
  - **Check document screen:**
    - the PDF on the left;
    - on the right: the reasons, a type dropdown and a client dropdown;
    - the date and every type's fields, with the shown values in hidden inputs;
    - the filename that will be used;
    - the **File it** button.
  - A refusal shows the form again with your choices kept.
  - The inbox banner "N documents need checking – Check now / Later", and a Home tile.
- **Files:** `web/routes.py`, `templates/{needs_checking,check,inbox,home}.html`, `tests/test_review.py`
- **Tests:** AT-12:
  - C7: grouping isn't blocked, and the banner and tile show the counts.
  - C8 through the screen.
  - C10: the message, with your choices kept.
- **Done when:** `uv run pytest tests/test_review.py -v`

### Task 19: Paper can go (15 min)
- **Builds:**
  - `Box.paper_blockers()` and `paper_can_go()`.
  - Home shows **Paper can go**, or the blocking lines in the decision 11 wording.
- **Files:** `models/box.py`, `templates/home.html`, `tests/test_paper_can_go.py`
- **Tests:**
  - AT-14: P1, P5 and P6.
  - AT-15: P2.
  - AT-16: P3.
  - AT-17: P4 and P7.
  - Every line is checked word for word.
- **Done when:** `uv run pytest tests/test_paper_can_go.py -v`

### Task 20: End-to-end OCR test and demo-line check (10 min)
- **Builds:**
  - `uv add --dev pdfminer.six`.
  - A test marked `ocr`, using real OCR:
    - Step 1: generate the demo photos.
    - Step 2: upload them.
    - Step 3: mark the lens covers "Not a page".
    - Step 4: group each document.
    - Step 5: check the invoice is filed at `archive/C-0042 Hollybrook Bakery Ltd/Invoices/2026-03-14 Invoice INV-1043.pdf`, with its text searchable.
    - Step 6: review the unclear document.
    - Step 7: check the box shows **Paper can go**.
  - If Tesseract misreads, adjust the demo photos' font.
- **Files:** `tests/test_end_to_end.py`, `demo/photos.py` (only if the font needs adjusting)
- **Tests:** AT-20.
- **Done when:** `uv run pytest -m ocr -v`, then run demo script steps 1–7 (§9) by hand.

## ——— DEMO LINE ——— Running total 325 min (§10: 275). Demo script steps 1–7 work.

---

## Sitting (e) Retention and destruction: 50 min (§10: 45). Done when AT-18, AT-19 and the keep-until checks in AT-11 and AT-12 pass

### Task 21: Retention (10 min)
- **Builds:**
  - `add_years()`, where 29 Feb becomes 28 Feb.
  - `DocumentType.keep_until()`.
  - `change_type()` and confirming both set keep-until.
  - `is_due(today)` and the **Due** marker.
  - The document page shows keep-until, or "Keep-until not set – add the document's date".
  - Keep-until checks are added to C1, C8 and C9.
- **Files:** `rules/dates.py`, `models/{document_types,document}.py`, `templates/document.html`, `tests/test_retention.py`, `tests/test_reading.py`, `tests/test_review.py`
- **Tests:** AT-18: R1–R5. R4 includes the "kept through that day" boundary.
- **Done when:** `uv run pytest tests/test_retention.py tests/test_reading.py tests/test_review.py -v`

### Task 22: Due for disposal, Move to bin, restore (20 min)
- **Builds:**
  - `services/disposal.py`:
    - `due_documents(today)`;
    - `move_to_bin()`, which moves the PDF to `bin/<doc-id>.pdf` and sets `binned_at`;
    - `restore_document()`, back to the calculated path with the N3 clash rule, updating `filed_name` and clearing `binned_at`.
  - Screens:
    - Due for disposal, with tick boxes;
    - **Move to bin** on the Document page;
    - the Bin lists documents too.
  - The legal note on Due for disposal and the Bin.
  - Home tiles for Due for disposal and the Bin.
- **Files:** `services/disposal.py`, `web/routes.py`, `templates/{due,bin,document,home}.html`, `tests/test_disposal.py`
- **Tests:**
  - AT-19: D1–D3.
  - R4 at the list level.
  - The legal note is shown.
- **Done when:** `uv run pytest tests/test_disposal.py -v`

### Task 23: Empty bin and disposal records (20 min)
- **Builds:**
  - `DisposalRecord`, with the §3.6 fields; `filed_name` is copied from the document.
  - The **Empty bin…** confirmation page lists the exact items, with their ids in hidden fields.
  - `empty_bin()`:
    - writes one record per document;
    - applies `destroy`;
    - deletes the Document, Page and StateChange rows, then deletes the files after the commit;
    - shows the D5 message.
- **Files:** `models/records.py`, `services/disposal.py`, `web/routes.py`, `templates/empty_bin.html`, `tests/test_disposal.py`
- **Tests:** AT-19: D4–D6 and B5:
  - no files or rows are left;
  - each record has exactly the §3.6 fields;
  - a document filed with " (2)" keeps that suffix in its record;
  - there are no records for photos.
- **Done when:** `uv run pytest tests/test_disposal.py -v`

---

## Sitting (f) Seed script and README: 25 min (§10: 20). Done when AT-23–AT-25 pass

### Task 24: Seed fills boxes and documents (15 min)
- **Builds:** seed draws photos (every document at least 20 words) with `demo/photos.py` and runs them through the real services and OCR:
  - **"Box 1 – 2016–2019"** shows Paper can go. It holds documents that are Filed, No date, two Due, and one In bin.
  - **"Box 2 – 2020–2022"** shows blocking lines. It has photos to sort, one Needs checking document, and "Not a page" photos in the bin.
- **Files:** `demo/{seed,photos}.py`, `tests/test_seed.py`
- **Tests:** AT-23 (`ocr`).
- **Done when:** `uv run pytest -m ocr tests/test_seed.py -v`

### Task 25: README and manual checks (10 min)
- **Builds:** `README.md` covers:
  - setup: uv, then `sudo apt install tesseract-ocr ghostscript`;
  - running the app;
  - the §1 workflow;
  - the demo commands;
  - the legal note;
  - the known limitations.
- **Files:** `README.md`
- **Tests:** AT-24 and AT-25 are manual.
- **Done when:** `git clone . /tmp/dm-fresh && cd /tmp/dm-fresh && uv sync && uv run pytest` passes. Then, using that clone, run the demo script following only the README (AT-24), and check every screen at 200% zoom (AT-25).
