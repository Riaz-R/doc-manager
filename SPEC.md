# Doc Manager: Specification

A small local document manager (ECM) that turns boxes of paper client files into
named, searchable PDFs. Paper can be shredded as soon as it has been digitised;
each digital record is kept until its retention period ends, then destroyed.

Status: agreed spec, ready to build. Last updated 2026-10-26.

---

## 1. Purpose and users

### Problem
Small businesses keep boxes of paper client files because record-keeping rules
say the records must be kept for a number of years. The boxes take up space,
and nobody can find anything in them.

### Goal
Photograph a box of paper with a phone, and let the app:
1. turn the photos into one searchable PDF per document,
2. work out what each document is and which client it belongs to,
3. file it under a predictable name,
4. work out how long each digital record must be kept,
5. tell the user when a box's paper can be shredded (as soon as everything in it is filed), and, separately, when each digital record can be destroyed (when its keep-until date has passed).

Shredding the paper and destroying the digital record are two separate events.
The paper never waits for keep-until.

### Users
| User | Who | What they need |
|---|---|---|
| Primary | A retired or semi-retired professional (the author's dad) with boxes of client files | Plain words, large buttons, one obvious next step, nothing destroyed by accident |
| Similar | A small local business owner | The same, plus confidence that disposal follows the rules and leaves proof |
| Demo audience | Interviewers for roles that configure object models, lifecycles and workflows | A clear object model, enforced lifecycles, rules they can read, and an honest build story |

### Typical workflow
1. Take a box off the shelf and give it a name in the app, for example "Box 3 – 2017–2019".
2. Photograph each document's pages in order with the phone. **Tip:** cover the lens for one photo between documents. The dark photos make the gaps easy to see in the inbox.
3. Upload the photos into that box. A big box may take several uploads.
4. In the inbox, mark the lens-cover photos and any bad shots "Not a page". Then, for each document, pick its first and last photo and press "Make document". The app reads the document while the page waits, then files it or marks it "Needs checking".
5. Check flagged documents now or later.
6. When Home shows "Paper can go" beside the box, shred that box's paper.
7. Later, as a separate step: when records pass their keep-until date, open "Due for disposal", move them to the bin, and empty the bin with a separate confirmation. This destroys the digital records.

Dark-photo detection (should tier) will later suggest groupings from the lens-cover photos.

---

## 2. Scope

### Must (this build)
- **Upload into a box:** create a named box or pick an existing one; upload many photos at once (each upload is a batch); JPEG and PNG only; duplicate check (§3.3).
- **Inbox:** shows a box's unsorted photos, ordered by filename.
- **Not a page:** marked photos leave the inbox and go to the bin. They can be restored from the bin, and are deleted when the bin is emptied, with no DisposalRecord.
- **Grouping:** group consecutive photos into a document by picking its first and last photo. Grouped photos leave the inbox.
- **OCR on "Make document":** OCRmyPDF and Tesseract run while the page waits, entirely on this computer. If OCR fails, the document stays grouped with an error and a Retry button.
- **Classification:** each document type scores the text; the client is matched against a client register. No AI at runtime.
- **Review:** documents that fail a check get a "Needs checking" marker with the reasons in plain words. The user can check them now or later.
- **Naming and filing:** documents are named and filed by the default naming template.
- **Paper can go:** a marker on each box, shown on Home. When it isn't shown, Home says what is blocking it (§3.1).
- **Retention:** keep-until is calculated from the document's own date and its type's `retention_years` (§3.4).
- **Disposal of digital records:** a "Due for disposal" list; "Move to bin"; a bin with restore; "Empty bin" needs a separate confirmation and keeps only a disposal record per document (§3.6).
- **Lifecycles:** enforced in code for Page and Document (§3.7).
- **Seed script and README:** the seed script creates made-up clients, boxes and documents. The README explains setup, running and the workflow in §1.
- **Localhost only:** the app listens on 127.0.0.1 (§8).

Known limitations until the should tier is built:
- A document from a client who isn't in the register can't be filed, because clients only come from the seed script.
- A phone counter rollover (IMG_9999 → IMG_0001) puts photos in the wrong order.
- A long document holds the browser page until OCR finishes (up to the 5-minute timeout).

### Should
See §11. Should-tier work starts after the must tier works.

### Stretch (not this build)
- **QR separator sheets:** printable sheets for "end of document" and "end of box", detected during upload.
- **Settings page:** edit the naming template, with placeholders validated; applies to newly filed documents only.
- **Client import:** import clients from a CSV file.
- **Event-based retention:** for example a "Client agreement" type kept 6 years after the client leaves, which needs a "left on" date on Client.

### Roadmap only
- Sorting loose pages that are neither grouped nor in order (page-level classification and reassembly).
- A Windows desktop shortcut or installer for non-technical users.
- Backups and export.
- Multiple users, logins and sign-off on disposal.
- Requiring the user to check each document's PDF before a box's paper can go.

### Out of scope
- Network access at runtime (see §8).
- AI or machine learning at runtime.
- Real client data in the repo, tests or demo.
- Logins and user accounts.
- JavaScript (see §8).
- Editing PDF contents, annotations and versioning.
- Legal accuracy of the retention rules (see §8).

### Changes from the original brief, and why
| Original leaning | Changed to | Reason |
|---|---|---|
| One upload batch = one box | A box holds many batches | A real box often needs more than one upload (phone storage, upload limits, breaks). |
| Order "as captured" | Filename order in must; EXIF date taken in should | Filename order is quick to build; EXIF fixes counter rollover later. |
| Black-photo detection in should | Plus a "Not a page" button in must | Lens-cover photos and bad shots would otherwise stop a box ever reaching "Paper can go". |
| A Document base class with one subclass per type | A Document holds a swappable `DocumentType` object; one `DocumentType` subclass per type | Changing a document's type in review is a swap on the same document, not a new object. |
| Keep-until from the type's rule (trigger unspecified) | Counted from the document's own date | Counting from upload day gives wrong dates for every old document. |
| Low confidence goes to review | Review is a non-blocking marker; filing rule in §3.4 | Keeps capture fast; a missing date is handled by the "No date" marker (§3.4). |
| Disposing moves to a bin | Emptying the bin deletes everything except a disposal record | Proof of timely, proper destruction is a record-keeping requirement; nothing else should outlive the record. |
| (Not in the brief) | "Paper can go" marker on each box; shredding paper is separate from destroying the digital record | The point is to clear space as soon as papers are digitised; retention applies to the digital record. |

---

## 3. Objects, fields and lifecycles

All objects are SQLAlchemy models stored in SQLite. State fields are never set
directly. Every change goes through `obj.apply(action)` (see §3.7).

### 3.1 Box
A physical box of paper: a named container for batches and pages, with no
lifecycle in the must tier.

| Field | Type | Notes |
|---|---|---|
| id | int | |
| name | text, unique, 1–60 chars | for example "Box 3 – 2017–2019" |
| created_at | datetime | |

**Paper can go** (a marker, worked out rather than stored, like Due): shown when
the box has at least one Document, no Page in Inbox, and every Document has been
filed (none is Grouped and none is NeedsReview). Documents later moved to the bin
still count as filed. "Not a page" photos don't block it. It never depends on
keep-until.

When it isn't shown, `box.paper_blockers()` returns one plain-words line per
blocker, shown on Home beside the box:
- "3 photos to sort before this paper can go"
- "1 document needs checking before this paper can go"
- "1 document couldn't be read before this paper can go" (Grouped with `ocr_error`)
- "1 document hasn't been read yet before this paper can go" (Grouped, no text, no error)
- "Nothing filed from this box yet"

Should tier: the box lifecycle, PaperDestroyed state and box screens (§11.2).

### 3.2 Batch
One upload into a box.

| Field | Type | Notes |
|---|---|---|
| id | int | |
| box_id | FK Box | |
| uploaded_at | datetime | |
| added_count, skipped_count, refused_count | int | shown to the user after upload |

No lifecycle; batches are a record of each upload.

### 3.3 Page
One photo.

**Duplicate rule:** `sha256` is unique among the pages currently in the app,
including "Not a page" photos still in the bin. An upload whose bytes match an
existing page is skipped and reported. Emptying the bin deletes Page rows (§3.6),
so a destroyed photo can be uploaded again.

| Field | Type | Notes |
|---|---|---|
| id | int | |
| box_id, batch_id | FK | |
| sha256 | text, unique | of the uploaded bytes; the duplicate check |
| original_filename | text | display and ordering only; never used to build a path |
| state | PageState | Inbox, Grouped, Discarded |
| document_id | FK Document, nullable | set while Grouped |
| position | int, nullable | page number within its document |
| photo_path, thumb_path | text | under `data/photos/` and `data/thumbs/`, named by sha256 |

**Order** (computed, not stored): a box's pages sort by `(original_filename, id)`.

**Lifecycle**

| From | Action | To | Guard |
|---|---|---|---|
| (new) | upload | Inbox | not a duplicate (§3.3); a readable JPEG/PNG |
| Inbox | group | Grouped | part of a valid range (§5.3) |
| Inbox | discard | Discarded | none ("Not a page") |
| Discarded | restore | Inbox | none |
| Grouped | destroy | (row deleted) | only as part of destroying its document |
| Discarded | destroy | (row deleted) | only through the "Empty bin" confirmation; no DisposalRecord |

Display labels: Inbox = "To sort", Grouped = "In a document",
Discarded = "Not a page (in bin)".

Should tier: EXIF order, ungroup, dark-photo fields (§11).

### 3.4 Document and document types
A Document is one SQLAlchemy class. What kind of document it is lives in a
separate `DocumentType` object that the document holds. Changing the type swaps
that object; the document keeps its id, pages and history.

**`Document` fields**

| Field | Type | Notes |
|---|---|---|
| id | int | |
| box_id | FK Box | |
| state | DocState | see below |
| doc_type | text, nullable | the key of its `DocumentType` (`invoice`, `letter`); null = "Unclassified" |
| fields | JSON | values extracted by the type, for example `{"invoice_number": "INV-1043", "amount_pence": 12000}` |
| client_id | FK Client, nullable | |
| document_date | date, nullable | the retention trigger date (each type says which date that is) |
| keep_until | date, nullable | calculated; null when the date is missing (see Markers) |
| ocr_text | text, nullable | from the OCR sidecar file |
| ocr_error | text, nullable | plain words; set when OCR failed, cleared on success |
| type_score, runner_up_score | int, nullable | kept to explain the decision |
| review_reasons | JSON list of text | plain words, for example "More than one client matched: Smith Ltd, J Smith & Co" |
| pdf_path | text, nullable | the current location (work, archive or bin) |
| created_at, filed_at, binned_at | datetime, nullable | |

`document.type` returns the `DocumentType` instance for `doc_type` from a
registry, or `None`. `document.change_type(new_type)` swaps the type:
1. it sets `doc_type` to the new type's key,
2. it re-extracts `fields` and `document_date` from `ocr_text` using the new type,
3. it recalculates `keep_until`.

The row, its id, its pages and its state stay the same.

**`DocumentType` classes** (plain Python, in `models/document_types.py`)

```python
class DocumentType:
    key: str                    # stored in Document.doc_type
    label: str                  # "Invoice"
    plural_label: str           # "Invoices", used as the folder name
    retention_years: int        # overridden by each subclass

    def score(self, text: str) -> int: ...           # overridden by each subclass
    def extract(self, text: str) -> dict: ...        # fields + "document_date"
    def filename_key(self, fields: dict) -> str: ...
    def keep_until(self, document_date: date | None) -> date | None:
        # document_date + retention_years; None if no date; 29 Feb -> 28 Feb

class InvoiceType(DocumentType): ...
class LetterType(DocumentType): ...

DOCUMENT_TYPES = {t.key: t for t in (InvoiceType(), LetterType())}
```

Each subclass overrides `score(text)` and `retention_years`. The base class gives
a `keyword_score(text, weights)` helper that the overrides can use.

| Type | Key | Fields | `document_date` is | Filename key | `retention_years` (illustrative) |
|---|---|---|---|---|---|
| `InvoiceType` | `invoice` | invoice_number, amount_pence | invoice date | invoice number, or "no number" | 6 |
| `LetterType` | `letter` | subject (from a "Re:" line) | letter date | subject (first 40 chars), or "letter" | 3 |

A document with no type (`doc_type` null) shows as "Unclassified" and can't be filed.

**Lifecycle**

| From | Action | To | Guard |
|---|---|---|---|
| (new) | group | Grouped | made by "Make document"; OCR runs straight after |
| Grouped | file | Filed | OCR succeeded and classification met the confirm conditions (§5.5) |
| Grouped | flag | NeedsReview | OCR succeeded and a check failed; records review_reasons |
| NeedsReview | confirm | Filed | a type is chosen and a client is set |
| Filed | dispose | InBin | the document is Due (see Markers) |
| InBin | restore | Filed | none |
| InBin | destroy | (row deleted) | only through the "Empty bin" confirmation; writes a DisposalRecord |

If OCR fails, there is no transition: the document stays Grouped with
`ocr_error` set, and Retry runs OCR again. A Grouped document with no OCR text
and no error (for example, the app was stopped mid-read) is shown with Retry too.

Display labels: Grouped = "Not read yet" (or "Couldn't read" when `ocr_error` is set),
NeedsReview = "Needs checking", Filed = "Filed", InBin = "In bin".

**Markers** (shown as badges; derived from fields, not states):
- **Needs checking:** state is NeedsReview.
- **No date:** Filed and `document_date` is null. Its keep-until isn't set, so it is never Due.
- **Due:** Filed and today is after `keep_until`.

Should tier: ungroup, save for later, correct after filing, background worker states, legal hold (§11).

### 3.5 Client
| Field | Type | Notes |
|---|---|---|
| id | int | |
| ref | text, unique, format `C-0000` | set by the seed script |
| name | text, unique | for example "Hollybrook Bakery Ltd" |
| created_at | datetime | |

No lifecycle. In the must tier, clients are created only by the seed script.
Should tier: clients screen and aliases (§11.5).

### 3.6 Records that support the lifecycles
**`StateChange`**: an append-only history row for every transition. Its rows are
deleted together with their page or document on destruction. Should tier: shown
on the document page (§11.9).

| Field | Notes |
|---|---|
| object_kind, object_id | `page` / `document`, id |
| action, from_state, to_state | |
| at | datetime |
| note | optional plain-words note |

**Destruction** of a digital record. This is separate from shredding the paper,
which has usually happened long before. Emptying the bin deletes, for each
document:
- its PDF,
- its page photos and thumbnails,
- its OCR text (sidecar file and `ocr_text`),
- its fingerprints (the Page rows and their `sha256`),
- its database entries (the Document, Page and StateChange rows).

Only a `DisposalRecord` remains. "Not a page" photos in the bin are deleted the
same way, with no record.

**`DisposalRecord`**: an immutable snapshot written when a document is destroyed.

| Field | Notes |
|---|---|
| id | |
| filed_name | the filename it was filed under |
| doc_type_label | for example "Invoice" |
| client_ref, client_name | snapshot |
| document_date, keep_until | snapshot |
| page_count | |
| binned_at, destroyed_at | |

### 3.7 How lifecycles are enforced in code
A small hand-written state machine in `lifecycle.py`, with no third-party library,
so that it is easy to explain:

```python
class InvalidTransition(Exception):
    """Carries a plain-words reason for the user."""

class Lifecycle:
    # (from_state, action) -> to_state
    transitions: dict[tuple[State, str], State]

class Stateful:                      # mixin for Page and Document
    _state: Mapped[str]              # stored column
    @property
    def state(self): ...             # read-only
    def allowed_actions(self) -> list[str]: ...
    def apply(self, action: str, *, now: datetime, note: str | None = None) -> None:
        # 1. look up (state, action) in the table, or raise InvalidTransition
        # 2. call guard_<action>() if defined; if it returns a reason, raise InvalidTransition(reason)
        # 3. set _state, write a StateChange row
```

- `destroy` is checked against the table like any other action; the disposal service then deletes the rows in the same transaction.
- Templates only show buttons for `allowed_actions()`, but the server still checks every POST. A forbidden POST is refused with a friendly message.
- Functions take `now` / `today` as arguments instead of reading the clock, so tests can fix the date.

---

## 4. Screens

All pages are rendered on the server with Jinja2 templates and one stylesheet
(no JavaScript, see §8). The design follows these rules:
- Base font 20px, buttons at least 48px tall, high contrast.
- One main action per screen, as the biggest button.
- Plain words throughout.
- Destructive actions always go through a separate confirmation page.

| # | Screen | Shows | Main actions |
|---|---|---|---|
| 1 | **Home** | Each box with "N photos to sort", and either **Paper can go** or its blocking lines (§3.1); tiles with counts: Needs checking, Due for disposal, Bin | Upload photos; open a box's inbox; Filed documents |
| 2 | **Upload** | Box picker: existing boxes, or "New box" with a name field; file picker (`multiple`, `accept="image/jpeg,image/png"`) | Upload. Result: "38 photos added. 2 skipped – already uploaded. 1 refused – not a photo (notes.txt)." |
| 3 | **Inbox (per box)** | Large thumbnails in filename order, numbered, with filename; on each, **First** / **Last** radio buttons and a **Not a page** tick box. A "Couldn't read" section listing Grouped documents with their error. Banner: "2 documents need checking – Check now / Later" | **Make document** (labelled "takes up to a minute"); Mark ticked as not a page; Retry on each "Couldn't read" document |
| 4 | **Needs checking** | List of flagged documents, oldest first, with their reasons | Open a document to check |
| 5 | **Check document** | The PDF on the left (browser's built-in viewer in an `<iframe>`); on the right, the reasons in plain words, type dropdown (Invoice, Letter), client dropdown, date, type fields; the filename that will be used | **File it** |
| 6 | **Document** | PDF, fields, markers, state label, keep-until | Only the allowed actions: Move to bin, Restore |
| 7 | **Filed documents** | Table: client, type, date, keep-until, markers | Open |
| 8 | **Due for disposal** | Filed documents that are Due, with tick boxes; the legal note (§8) | Move ticked to bin |
| 9 | **Bin** | Documents in the bin and "Not a page" photos; the legal note (§8) | Restore (each); **Empty bin…** |
| 10 | **Empty bin – confirm** | The exact list that will be destroyed, the count, the warning "This cannot be undone", and the legal note (§8) | "Yes, destroy these N items permanently"; Cancel |

Plain-word messages for errors and refusals appear in a banner at the top of
the next page (Flask `flash`).

Should-tier screens and additions: §11.

---

## 5. Behaviours (given / when / then)

### 5.1 Boxes and upload
- **B1 New box:** **Given** no box named "Box 1", **when** the user uploads 40 photos choosing "New box: Box 1", **then** box "Box 1" is created, one batch holds 40 Inbox pages, and the result says "40 photos added".
- **B2 Add to an existing box:** **Given** box "Box 1" with 40 pages, **when** the user uploads 25 more photos into "Box 1", **then** a second batch is created and the inbox shows all 65 in filename order.
- **B3 Duplicate in a later upload:** **Given** photo P is in the app, **when** the same file is uploaded again into any box, **then** it is skipped and the result says "1 skipped – already uploaded".
- **B4 Duplicate in the same upload:** **Given** an upload containing the same file twice, **when** it is processed, **then** one page is created and one is reported as skipped.
- **B5 Photo of a destroyed record:** **Given** a photo deleted by emptying the bin, **when** it is uploaded again, **then** it is added as a new Inbox page.
- **B6 Not a photo:** **Given** an upload containing `notes.txt` or a corrupt JPEG, **when** it is processed, **then** that file is refused by name, and the other photos are still added.
- **B7 HEIC:** **Given** an iPhone `.heic` photo, **when** it is uploaded, **then** it is refused with "iPhone HEIC photos aren't supported yet. On the iPhone: Settings → Camera → Formats → Most Compatible."
- **B8 Duplicate box name:** **Given** box "Box 1" exists, **when** the user creates a new box named "Box 1", **then** it is refused with "There is already a box called Box 1".

Should tier: turning rotated photos the right way up (§11.9).

### 5.2 Order
- **O1 Filename order:** **Given** photos named IMG_0003.jpg, IMG_0001.jpg and IMG_0002.jpg uploaded in that order, **when** the inbox is shown, **then** they appear as IMG_0001, IMG_0002, IMG_0003.

Should tier: EXIF capture order (§11.6).

### 5.3 Grouping and Not a page
- **G1 Make document:** **Given** Inbox pages 1–10 in a box, **when** the user picks First = 3 and Last = 6 and presses Make document, **then**:
  - a Document is created in Grouped, with pages 3–6 as positions 1–4;
  - those pages become Grouped and leave the inbox;
  - OCR runs while the page waits (§5.4);
  - the user returns to the inbox, which shows 1, 2, 7–10, with a message such as "Filed as 2021-03-14 Invoice INV-1043" or "Needs checking: Couldn't tell what type this is".
- **G2 One-page document:** **Given** First = Last = page 7, **then** a one-page document is created.
- **G3 First after Last:** **Given** First = 6 and Last = 3, **then** the app swaps them and groups pages 3–6.
- **G4 Range would swallow a grouped page:** **Given** page 5 is already Grouped (because the user grouped 5–5 earlier) and the user picks 3–7, **then** it is refused with "Photos 3 to 7 include a photo that is already in a document".
- **G5 Only one end picked:** **Given** First is picked but not Last, **then** it is refused with "Pick both the first and the last page".
- **G6 Not a page:** **Given** pages 2 and 9 are ticked, **when** the user presses Mark as not a page, **then** both become Discarded, leave the inbox and appear in the Bin.
- **G7 Not a page inside a range:** **Given** page 4 is Discarded and the user groups 3–6, **then** the document contains pages 3, 5, 6, and page 4 stays Discarded.
- **G8 Restore a photo:** **Given** a Discarded page in the Bin, **when** the user presses Restore, **then** it leaves the Bin and returns to the inbox in its filename position.

Should tier: ungroup (§11.3).

### 5.4 OCR
- **W1 Happy path:** **Given** a new Grouped document, **when** OCR runs during the "Make document" request, **then** the photos are combined into a PDF, OCRmyPDF writes a searchable PDF and a text file to `data/work/`, and classification runs (§5.5).
- **W2 Failure:** **Given** OCRmyPDF exits with an error or exceeds the 5-minute timeout, **then**:
  - the document stays Grouped with `ocr_error` "Couldn't read this document. Try again, or retake the photos.";
  - the technical detail is written to `data/logs/app.log`;
  - the document is listed under "Couldn't read" in the inbox with a Retry button.
- **W3 Retry:** **Given** a Grouped document with an error, **when** the user presses Retry, **then** OCR runs again while the page waits; on success it continues as W1 and the error is cleared.
- **W4 Interrupted:** **Given** the app was stopped during OCR, **when** it starts again, **then** the document is still Grouped with no text and is listed with a Retry button.
- **W5 Missing OCR tools:** **Given** Tesseract or Ghostscript is missing, **when** the app starts, **then** it prints which program is missing and how to install it, and exits.

Should tier: background worker (§11.1).

### 5.5 Classification and review
Checks, in order. All reasons that fail are recorded.
1. **Type check:** each `DocumentType` scores the text with its `score(text)`. The type passes when the top score is at least `MIN_TYPE_SCORE` (default 6) and beats the runner-up by at least `MIN_TYPE_MARGIN` (default 3). Otherwise the document has no type ("Unclassified").
2. **Client check:** if exactly one `C-0000` reference is found and it exists in the register, it matches. If no reference is found, the client matches when exactly one client's exact name appears (case-insensitive, whole phrase). Otherwise there is no match.
3. **Date** (does not block filing): the type's `extract` finds its date in UK day-first formats (`14/03/2021`, `14 March 2021`, `2021-03-14`). Dates after today are ignored as misreads.

When checks 1 and 2 pass, the document is filed automatically (the `confirm`
conditions in §3.4); otherwise it is flagged.

- **C1 Confident:** **Given** text containing "INVOICE", "Invoice number INV-1043", "Amount due", "C-0042" and "Invoice date 14/03/2021", **then** the type is Invoice, the client is C-0042, document_date is 2021-03-14, keep_until is 2027-03-14, and the document is Filed with no marker.
- **C2 Unclear type:** **Given** text scoring Invoice 7 and Letter 5, **then** it is flagged with "Not sure what type this is (Invoice or Letter?)" and shown as Unclassified.
- **C3 No keywords:** **Given** text that every type scores 0, **then** it is flagged with "Couldn't tell what type this is".
- **C4 Two clients:** **Given** text containing no reference but the names of two clients, "Smith Ltd" and "J Smith & Co", **then** it is flagged with "More than one client matched: Smith Ltd, J Smith & Co".
- **C5 Unknown reference:** **Given** text containing "C-0099" and no such client, **then** it is flagged with "Client C-0099 isn't in your client list".
- **C6 No date:** **Given** a confident type and client but no date found, **then** it is Filed with the "No date" marker and the filename uses "undated".
- **C7 Check now or later:** **Given** a flagged document, **when** the user groups more documents, **then** nothing blocks them, and the inbox banner and Home tile show the "Needs checking" count.
- **C8 Confirm in review:** **Given** a flagged document, **when** the user picks type Invoice and client C-0042 and presses File it, **then** `change_type(InvoiceType())` swaps its type, its fields are re-extracted, and it is Filed with a calculated keep-until.
- **C9 Type swap keeps the document:** **Given** a flagged document with id 17 shown as Invoice, **when** the user changes the type to Letter, **then** it is still document 17 with the same pages and history, its fields are the letter fields, and its keep-until uses `LetterType.retention_years`.
- **C10 Review guard:** **Given** the client is still empty, **when** File it is pressed, **then** it is refused with "Choose a client before filing", and the form is shown again with the user's choices.

Should tier: add a client from review, save for later (§11.4).

### 5.6 Naming and filing
Default template, a constant in `rules/naming.py`:
`{client_ref} {client_name}/{type_plural}/{date} {type_label} {key}.pdf`

- **N1 Invoice:** **Given** an Invoice for C-0042 Hollybrook Bakery Ltd, dated 2021-03-14, number INV-1043, **then** it is filed at `data/archive/C-0042 Hollybrook Bakery Ltd/Invoices/2021-03-14 Invoice INV-1043.pdf`.
- **N2 No date:** **Given** no date, **then** the date part is `undated`.
- **N3 Name clash:** **Given** a file already exists at the target path, **then** the new file gets ` (2)` (then ` (3)` …) before `.pdf`.
- **N4 Unsafe characters:** **Given** a client name containing `/ \ : * ? " < > |` or trailing dots or spaces, **then** those characters are replaced with `-` or trimmed, so the path works on Windows too.
- **N5 Database is the source of truth:** the database records `pdf_path`. If a file is missing from disk, the document page says "The PDF file is missing" instead of crashing.

Should tier: correcting after filing (§11.4).

### 5.7 Paper can go
- **P1 All filed:** **Given** box "Box 1" whose documents are all Filed and whose inbox is empty, **then** Home shows "Paper can go" beside it.
- **P2 Photo still to sort:** **Given** the same box with one photo in its inbox, **then** "Paper can go" is not shown, and Home says "1 photo to sort before this paper can go".
- **P3 Needs checking:** **Given** one document in the box is NeedsReview, **then** "Paper can go" is not shown, and Home says "1 document needs checking before this paper can go".
- **P4 OCR error:** **Given** one document in the box is Grouped with an OCR error, **then** "Paper can go" is not shown, and Home says "1 document couldn't be read before this paper can go".
- **P5 Not a page doesn't block:** **Given** a box whose remaining photos are all marked "Not a page" and whose documents are all Filed, **then** "Paper can go" is shown.
- **P6 Doesn't wait for keep-until:** **Given** a box whose documents are all Filed with keep-until dates in 2031, **then** "Paper can go" is shown today.
- **P7 Empty box:** **Given** a box with photos but no documents yet, **then** "Paper can go" is not shown.

### 5.8 Retention
- **R1 Invoice:** **Given** an Invoice dated 2021-03-14, **then** keep_until is 2027-03-14 (6 years).
- **R2 Letter:** **Given** a Letter dated 2022-05-10, **then** keep_until is 2025-05-10 (3 years).
- **R3 Leap day:** **Given** a Letter dated 2020-02-29, **then** keep_until is 2023-02-28.
- **R4 Due:** **Given** today is 2026-10-25 and keep_until is 2026-10-24, **then** the document is listed in Due for disposal. **Given** keep_until is 2026-10-25, **then** it is not listed (it is kept through that day).
- **R5 No date:** **Given** a Filed document with no date, **then** it never appears in Due for disposal, and its page says "Keep-until not set – add the document's date".

### 5.9 Destroying digital records
- **D1 Move to bin:** **Given** two Due documents ticked, **when** the user presses Move to bin, **then** both become InBin, their PDFs move to `data/bin/`, and binned_at is set.
- **D2 Not yet due:** **Given** a document that isn't Due, **when** a crafted POST tries to move it to the bin, **then** it is refused with "This document must be kept until 14 Mar 2027".
- **D3 Restore:** **Given** a document in the bin, **when** the user presses Restore, **then** it becomes Filed again at its calculated path (clash rule N3 applies).
- **D4 Empty bin needs a second step:** **Given** a bin with 3 documents and 2 "Not a page" photos, **when** the user presses Empty bin…, **then** a confirmation page lists those 5 items, and nothing is deleted yet.
- **D5 Confirm:** **Given** the confirmation page, **when** the user presses "Yes, destroy these 5 items permanently", **then**:
  - for each document, everything listed under Destruction in §3.6 is deleted and one DisposalRecord is written;
  - the 2 photos' files and Page rows are deleted, with no DisposalRecord.

  The message says "3 documents and 2 photos destroyed. A disposal record was kept for each document."
- **D6 Only what was confirmed:** **Given** an item was moved to the bin after the confirmation page was opened, **when** the user confirms, **then** only the items listed on that page are destroyed (the form carries their ids).

Should tier: legal hold, disposal log screen (§11.9).

---

## 6. Acceptance tests

Automated tests use pytest in `tests/` and run with `uv run pytest`. Tests
marked `ocr` run real Tesseract/OCRmyPDF on generated photos and are skipped with
a clear message if the tools are missing. All others use stored text fixtures
and run in seconds. Dates are fixed as described in §3.7.

Each test passes only when every stated condition holds; otherwise it fails.

| ID | Check | Type |
|---|---|---|
| AT-01 | Every row of the Page and Document lifecycle tables (§3) is allowed, and every other (state, action) pair raises `InvalidTransition` | unit, table-driven |
| AT-02 | Each guard refuses with the plain-words reason given in §5 | unit |
| AT-03 | Every transition writes exactly one StateChange row | unit |
| AT-04 | Setting `state` directly is impossible (no setter) | unit |
| AT-05 | Upload: B1–B8 (B5 is checked in AT-19) | integration (Flask test client) |
| AT-06 | Order: O1 | unit |
| AT-07 | Grouping: G1–G5 | integration |
| AT-08 | Not a page (G6, G7): ticked photos are Discarded, absent from the inbox, listed in the Bin, and skipped when inside a grouped range | integration |
| AT-09 | Restore (G8): the photo is Inbox again, absent from the Bin, and shown in its filename position | integration |
| AT-10 | OCR: W2–W4 with OCR replaced by a fake that fails or hangs; W5 start-up check | integration |
| AT-11 | Classification: C1–C6 on text fixtures, including each type's `score()` and the reasons' exact wording | unit |
| AT-12 | Review: C7–C10, including `change_type()` keeping the same id, pages and history | integration |
| AT-13 | Naming: N1–N5 | unit |
| AT-14 | Paper can go is shown: P1, P5, P6 | integration |
| AT-15 | Paper can go is not shown with a photo in the inbox: P2, with its exact blocking line | integration |
| AT-16 | Paper can go is not shown with a document needing checking: P3, with its exact blocking line | integration |
| AT-17 | Paper can go is not shown with an OCR error: P4, with its exact blocking line; and not shown for P7 | integration |
| AT-18 | Retention: R1–R5, including each type's `retention_years`, the leap day and the "kept through that day" boundary | unit |
| AT-19 | Destruction: D1–D6. After D5: no files, Page, Document or StateChange rows remain for the destroyed items; each DisposalRecord has exactly the §3.6 fields; no DisposalRecord exists for the photos; re-uploading a destroyed photo succeeds (B5) | integration |
| AT-20 | End to end: generate photos → upload → mark lens-cover photos Not a page → group → OCR → Invoice filed at the expected path, with text searchable in the PDF, and the box shows "Paper can go" | `ocr` |
| AT-21 | The app binds only to 127.0.0.1 | unit |
| AT-22 | No template or static file references an `http(s)://` URL | unit (scan files) |
| AT-23 | Seed: `uv run docmanager seed --reset` on an empty data folder produces clients, one box showing "Paper can go", one box with blocking lines, inbox photos, "Not a page" photos in the bin, and documents that are Filed, Needs checking, No date, Due and In bin | `ocr` |
| AT-24 | Manual: the demo script (§9) runs on a fresh clone following README steps only | manual |
| AT-25 | Manual: every screen is usable at 200% browser zoom, and every action button is at least 48px tall | manual |

`uv run pytest` must pass, and `uv run ruff check` and `uv run ruff format --check` must be clean, before each commit.

Should-tier tests: §11.10.

---

## 7. Technical decisions

| Area | Decision | Why (one line) |
|---|---|---|
| Language | Python 3.13, pinned in `.python-version` | Recent and widely supported by the libraries; uv installs it. |
| Web framework | Flask + Jinja2 templates | Smallest thing to learn: one function per URL returning HTML. |
| Database | SQLite file + SQLAlchemy 2.0 ORM, default settings, one session per request | No server; Box, Batch, Page, Document, Client and the records map straight to tables. |
| Document types | `DocumentType` base class with `InvoiceType` and `LetterType`; a Document holds one, stored by key | Changing type swaps one object; the document keeps its id, pages and history. |
| Lifecycles | Hand-written `Lifecycle` + `Stateful` mixin | Easy to read and explain; transition tables are plain data. |
| OCR | OCRmyPDF (pinned Python package) run as a subprocess (`python -m ocrmypdf` in the uv environment) with `-l eng --rotate-pages --deskew --sidecar`, during the "Make document" request; photos combined first with `img2pdf` | Simplest flow to build; a subprocess can be timed out and can't crash the web app. |
| Images | Pillow: thumbnails (400px), demo photo drawing | One library for all image work. |
| Dependencies | uv: `pyproject.toml` lists dependencies; `uv.lock` (committed) pins exact versions; `uv sync` installs them; every command runs with `uv run` (the app, seed, pytest, ruff) | One tool, the same versions everywhere, no virtual environment to activate by hand. |
| Formatting and linting | Ruff (format + check), default rules plus import sorting | One tool, fast, settings live in `pyproject.toml`. |
| Tests | pytest; `ocr` marker for slow tests | Standard and simple; slow tests can be skipped. |
| Error handling | Domain exceptions (`InvalidTransition`, `UploadRefused`, `GroupingError`) carry plain-words messages, shown with `flash`; custom 404/500 pages; OCR errors are kept on the document (`ocr_error`) with Retry; technical detail goes to a rotating log at `data/logs/app.log` | The user never sees a stack trace; the developer can still find out what went wrong. |
| File storage | Everything in `data/` (gitignored), location overridable with `DOCMANAGER_DATA`. Uploaded files are named by sha256, never by their uploaded name | Code and data stay separate; no path tricks from filenames. |
| Run | `uv run docmanager` serves the app (address in §8); `uv run docmanager seed [--reset]`; `uv run docmanager make-photos OUT_DIR` writes a small box of demo photos (3 documents, a lens-cover photo between each). One generator draws plain typed text on white images, with a plain black image for each lens cover; the seed script reuses it | One command each. |
| Config | `config.py` constants: thresholds, naming template, OCR timeout | Every tunable value lives in one place. |
| System programs | Tesseract (with `eng` and `osd` data), Ghostscript, from apt. Checked at start-up | OCRmyPDF needs them; a clear message beats a cryptic failure. |

Should-tier technical additions: §11.

### Project layout
```
doc-manager/
  pyproject.toml  uv.lock  .python-version  README.md  SPEC.md  CLAUDE.md
  src/docmanager/
    __init__.py          create_app()
    cli.py               run | seed | make-photos
    config.py
    db.py                engine, session
    lifecycle.py         Lifecycle, Stateful, InvalidTransition
    models/              box.py page.py document.py document_types.py client.py records.py
    rules/               classify.py naming.py dates.py
    services/            upload.py grouping.py ocr.py filing.py disposal.py
    web/                 routes.py templates/ static/style.css
    demo/                photos.py (plain typed text on white; plain black lens covers) seed.py (reuses photos.py)
  tests/
  data/                  (gitignored) app.db photos/ thumbs/ work/ archive/ bin/ logs/
```

### Data folder
| Path | Contents |
|---|---|
| `data/app.db` | SQLite database |
| `data/photos/<box-id>/<sha256>.jpg` | uploaded originals |
| `data/thumbs/<box-id>/<sha256>.jpg` | 400px thumbnails |
| `data/work/<doc-id>.pdf`, `.txt` | OCR output before filing |
| `data/archive/<client>/<type>/<name>.pdf` | filed documents |
| `data/bin/<doc-id>.pdf` | documents in the bin |
| `data/logs/app.log` | technical log |

---

## 8. Constraints

- **Localhost only:** the server binds `127.0.0.1:5000`, with the host fixed in code. Until the cross-site protections (§11.8) are built, a malicious web page open in the same browser could submit the app's forms.
- **No network:** no outbound requests at runtime; no CDN fonts, scripts or styles; Tesseract language data is local.
- **No real data:** all documents are generated by `demo/` code, using made-up names, fictional banks and senders, and `C-0000` refs. No real organisation's name or branding is imitated. The repo never contains a `data/` folder.
- **No AI at runtime:** classification is each type's `score()` and regexes only.
- **No JavaScript:** only HTML forms.
- **Accessibility:** see the design rules in §4.
- **Legal note:** the retention rules are illustrative. The Due for disposal, Bin and Empty bin screens and the README say "These keep-until dates come from example rules. Check the rules that apply to you, including whether a digital copy may replace the paper."
- **Time:** see §10. Should-tier work starts only after AT-01–AT-23 pass.
- **Upload size:** up to 500 MB per upload; above that, the user is told to upload in parts into the same box.

---

## 9. Demo script (about 5 minutes)
Steps 1–7 work at the demo line (§10). Steps 8–9 need sittings (e) and (f).

Beforehand: `uv run docmanager seed --reset` (creates the demo clients; from
sitting (f) it also fills boxes and documents) and `uv run docmanager make-photos ~/demo-box`.

1. `uv run docmanager`, and open http://127.0.0.1:5000.
2. **Live upload:** upload `~/demo-box` into a new box "Interview box". Upload one photo twice to show the duplicate skip.
3. **Inbox:** point out the black lens-cover photos marking the gaps between documents; tick them and press Mark as not a page. Pick First and Last for each document and press Make document. While it reads, show `lifecycle.py` and the `DocumentType` classes.
4. **Refusal:** press Make document with only First picked and show the plain-words refusal.
5. **Filed documents:** show the filed documents and their filenames on disk.
6. **Needs checking:** open the flagged document, read out its reasons, change its type (same document, new type object), pick the client and file it.
7. **Paper can go:** back on Home, "Interview box" now shows "Paper can go". The paper can be shredded today.

— demo line —

8. **Needs (e):** open a filed document and show its keep-until: the paper went today, but the record is kept until 2032. Try to move it to the bin and show the refusal. Then, separately: Due for disposal → Move to bin → Empty bin → confirm. The digital records are destroyed and only the disposal records remain.
9. **Needs (f):** on Home, a seeded box shows what is blocking its paper. Close with the test run: `uv run pytest -m "not ocr"`.

---

## 10. Build order (must tier)

Ordered by priority, so the app's main purpose works first.

Budget: about 3.5 hours (210 min). Estimate: **340 min in total; 275 min at
the demo line**, so even the demo line is 65 min over budget.

| Sitting | Work | Estimate | Running total | Done when |
|---|---|---|---|---|
| (a) Foundation | uv project, ruff, pytest, `config`, `db`, base template and style (25); `lifecycle.py`, models, Page and Document tables (25); localhost binding and the no-URL scan (5) | 55 min | 55 min | AT-01–AT-04, AT-21, AT-22 pass |
| (b) Upload, inbox, grouping, Not a page | Upload into a box with file checks and thumbnails (20); duplicate check (5); Home with the box list (5); inbox in filename order and grouping (30); Not a page, restore, and the Bin listing photos (15); demo photo generator (15) | 90 min | 145 min | AT-05 (except B5), AT-06–AT-09 pass |
| (c) OCR, classification, filing | OCR on Make document with error and Retry (25); `InvoiceType`, `LetterType` and classification (30); naming and filing (20); Filed documents list and Document page (10); `seed` creates the demo clients (5) | 90 min | 235 min | AT-10, AT-11 (except keep-until checks), AT-13 pass |
| (d) Review, Paper can go | Review with `change_type()` (25); Paper can go marker and blocking lines on Home (15) | 40 min | 275 min | AT-12 (except keep-until checks), AT-14–AT-17, AT-20 pass |
| **Demo line** | If time runs out here, the app already shows photos becoming filed documents and the box showing "Paper can go". | | **275 min** | Demo script steps 1–7 (§9) work |
| (e) Retention and destruction | Retention (10); due list, documents in the bin, restore, empty-bin confirmation, destruction and DisposalRecord (35) | 45 min | 320 min | AT-18, AT-19, and the keep-until checks in AT-11 and AT-12 pass |
| (f) Seed script and README | Seed script fills boxes and documents, reusing the photo generator (10); README (10) | 20 min | 340 min | AT-23–AT-25 pass |

Commit at the end of each sitting with the tests green.

---

## 11. Should tier

Built only after the must tier works (§8 Time).

### 11.1 Background OCR worker
"Make document" returns at once, and a worker thread reads the document. A new
state, Processing ("Being read"), is added to the Document lifecycle:

| From | Action | To | Guard |
|---|---|---|---|
| Grouped | start | Processing | worker only |
| Processing | file / flag | Filed / NeedsReview | as the Grouped rows in §3.4 |
| Processing | fail | Grouped | records ocr_error |
| Processing | requeue | Grouped | only at app start-up, for work left unfinished by a crash |

Pages showing work in progress refresh every 5 seconds with
`<meta http-equiv="refresh">`. SQLite runs in WAL mode so the worker and the web
pages don't lock each other out. Adds `services/worker.py`. Paper can go also
treats Processing as a blocker.

### 11.2 Box lifecycle and paper-destroyed confirmation
Adds Box fields `state` (Open, Complete, PaperDestroyed), `completed_at` and
`paper_destroyed_at`.

| From | Action | To | Guard |
|---|---|---|---|
| (new) | create | Open | name unique and not blank |
| Open | complete | Complete | Paper can go is shown (§3.1); applied automatically |
| Complete | reopen | Open | Paper can go stops showing (new upload or restored photo); applied automatically |
| Complete | confirm_paper_destroyed | PaperDestroyed | user confirms on a separate screen |

Display labels: Open = "In progress", Complete = "Paper can go",
PaperDestroyed = "Paper destroyed".

A PaperDestroyed box accepts no new uploads. Pages already in it can still be
restored and grouped, because the photo may now be the only copy.

New screens:
- **Boxes / Box detail:** state, counts, documents with markers, "Not a page" photos; actions are Go to inbox and "I have destroyed the paper" (only when Complete).
- **Paper destroyed – confirm:** box summary and thumbnails of any "Not a page" photos for a last look; "Yes, I have destroyed the paper for this box" or Cancel.

Behaviours:
- **X1 Complete:** a box becomes Complete when Paper can go shows.
- **X2 Reopen:** a Complete box becomes Open when more photos are uploaded into it.
- **X3 Confirm:** confirming on a Complete box makes it PaperDestroyed, with the date recorded.
- **X4 Not yet:** an Open box doesn't offer "I have destroyed the paper", and a crafted POST is refused.
- **X5 No uploads:** a PaperDestroyed box isn't offered on Upload, and a crafted POST to it is refused.

### 11.3 Ungroup
- Document `ungroup`: Grouped or NeedsReview → row deleted; pages go back to the inbox; work files are deleted.
- Page `ungroup`: Grouped → Inbox.
- **G9:** ungrouping a Needs checking document returns its pages to the inbox.
- **G10:** a Filed document doesn't offer Ungroup, and a crafted POST is refused with "Filed documents can't be ungrouped".

### 11.4 Review extras
- **Save for later:** NeedsReview `save` → NeedsReview stores the user's edits (C12).
- **Add a client from review:** creates a client with the next free `C-0000` ref and selects it (C11).
- **Correcting after filing:** Filed `correct` → Filed, with the same guard as confirm. Changing the type, client or date moves the file to its newly calculated path, recalculates keep-until, and removes empty old folders (N6).

### 11.5 Clients screen and aliases
- **Aliases:** adds the Client field `aliases`, a JSON list of other names that appear on documents. The client check also matches when exactly one client's name or alias appears.
- **Clients screen:** lists each client's ref, name, aliases and document count, with an Add client action. New refs are the next free number.

### 11.6 EXIF capture order
Adds the Page field `taken_at` (EXIF `DateTimeOriginal` + `SubSecTimeOriginal`).
Order becomes `(taken_at is None, taken_at, original_filename, id)`.
- **O2:** photos are shown in EXIF time order, whatever their filenames.
- **O3:** within the same second, fractions of a second decide, then filename.
- **O4:** photos with no EXIF time come after timed ones, with a "No time" label.

### 11.7 Dark-photo proposals
Adds Page fields `is_dark` and `discard_reason` (`not_a_page`, `separator`).
Adds `services/darkness.py`.
- **S1 Detection:** a photo whose downscaled greyscale mean is below 25/255 and whose standard deviation is below 12 is dark. Both values are config constants.
- **S2 Proposals:** for inbox photos `D a b c D d e D` (D = dark), a "Suggested documents" panel proposes a–c and d–e, with First and Last pre-filled.
- **S3 Confirm:** a confirmed proposal creates the document as in G1, and the dark photos around it become Discarded with reason `separator`.
- **S4 Adjust:** the user can change First and Last before confirming, or ignore the proposal and group manually.
- **S5 Dark page:** a genuinely dark page can be grouped manually. Nothing is discarded without confirmation.

### 11.8 Cross-site form protections
- **F1:** a POST without the per-session form token is refused.
- **F2:** a request whose `Host` header isn't `127.0.0.1:5000` or `localhost:5000` is refused.

Together these stop a malicious web page in the same browser from submitting the
app's forms, for example to empty the bin (CSRF and DNS rebinding).

### 11.9 Smaller items
- **List filters and text search** on Filed documents (client, type, OCR text).
- **History display:** a document's StateChange rows on its page.
- **Disposal log screen:** DisposalRecords, newest first, read-only.
- **Legal hold:**
  - a `legal_hold` field and an "On hold" marker;
  - Filed `dispose` also requires "not on legal hold";
  - **D7:** a Due document on hold is shown with "On hold", and Move to bin refuses it.
- **HEIC support** via `pillow-heif`, replacing the B7 refusal.
- **Rotated photos:**
  - **B9:** given a photo whose EXIF orientation says it is rotated, its thumbnail and PDF page are shown the right way up;
  - this needs Pillow orientation handling before `img2pdf`.
- **`BankStatementType`:**
  - key `bank_statement`;
  - fields account_last4 and period_end;
  - `document_date` is the period end;
  - filename key `acct-1234`;
  - `retention_years` 6.

  **R6:** a Bank statement with period end 2018-06-30 is kept until 2024-06-30.

### 11.10 Should-tier tests
These are written when each item is built: worker failure, requeue and refresh;
X1–X5; G9–G10; C11, C12 and N6; O2–O4; S1–S5; F1–F2; D7; B9; R6; alias matching.
