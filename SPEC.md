# Doc Manager: Specification

A small local document manager (ECM) that turns boxes of paper client files into
named, searchable, retention-managed PDFs, so the paper can be shredded with confidence.

Status: agreed spec, ready to build. Last updated 2026-10-25.

---

## 1. Purpose and users

### Problem
Small businesses keep boxes of paper client files because record-keeping rules
say they must keep them for a number of years. The boxes take up space, nobody
can find anything in them, and nobody knows when each paper may legally be
thrown away.

### Goal
Photograph a box of paper with a phone, and let the app:
1. turn the photos into one searchable PDF per document,
2. work out what each document is and which client it belongs to,
3. file it under a predictable name,
4. work out how long it must be kept,
5. say when the paper box can be shredded, and later, when each record can be destroyed.

### Users
| User | Who | What they need |
|---|---|---|
| Primary | A retired or semi-retired professional (the author's dad) with boxes of client files | Plain words, large buttons, one obvious next step, nothing destroyed by accident |
| Similar | A small local business owner | The same, plus confidence that disposal follows the rules and leaves proof |
| Demo audience | Interviewers for roles that configure object models, lifecycles and workflows | A clear object model, enforced lifecycles, rules they can read, and an honest build story |

### Typical workflow
1. Take a box off the shelf and give it a name in the app, for example "Box 3 – 2017–2019".
2. Photograph every page in order with the phone. Cover the lens for one photo between documents.
3. Upload the photos into that box. A big box may take several uploads.
4. In the inbox, mark each document's first and last page, and mark lens-cover photos and bad shots as "Not a page".
5. The app reads each document in the background. Most are filed automatically; the rest get a "Needs checking" marker.
6. Check flagged documents now or later.
7. When everything in the box is filed, the app shows "All filed – paper can go". The user shreds the paper and confirms it.
8. Every so often, open "Due for disposal", move expired records to the bin, and empty the bin with a separate confirmation.

---

## 2. Scope

### Must (this build, about 3.5 hours)
- **Boxes and uploads:** create a named box; upload many photos at once into a new or open box (each upload is a batch); JPEG and PNG only.
- **Duplicate protection:** a photo with exactly the same bytes as any photo ever uploaded is skipped and reported, including photos whose records were destroyed.
- **Capture order:** photos are ordered by EXIF date taken (with fractions of a second), then by filename.
- **Inbox:** shows a box's unsorted photos in capture order. The user groups consecutive photos into a document by picking its first and last page. Grouped photos leave the inbox.
- **Not a page:** mark photos as "Not a page" (they go to the bin, and can be restored).
- **Ungroup:** undo a grouping while its document is "Needs checking" or "Couldn't read".
- **OCR:** a background worker turns each document into a searchable PDF with OCRmyPDF and Tesseract, entirely on this computer.
- **Classification:** plain rules decide the document type (Invoice, Bank statement, Tax return, or Unclassified) and match the client against a client register. No AI at runtime.
- **Review:** documents that fail a check get a "Needs checking" marker with the reasons in plain words. Review never blocks the user, who can check now or later.
- **Filing:** documents are named and filed by the default naming template.
- **Retention:** keep-until is calculated from the document's own date using its type's rule. A document with no date is filed with a "No date" marker and is never due.
- **Disposal:** a "Due for disposal" list; "Move to bin"; a bin with restore; "Empty bin" needs a separate confirmation and leaves a disposal record.
- **Box lifecycle:** Open → Complete (enforced guard) → Paper destroyed (user confirms).
- **Clients screen:** list and add clients.
- **Filed documents:** a list, filterable by client and type.
- **Lifecycles:** enforced in code for Page, Document and Box, with a state history for each object.
- **Demo data:** a demo photo generator and a seed script. Only made-up documents.

### Should (after the must tier works)
- **Dark-photo detection:** near-black photos are detected, and the app proposes groupings for the user to confirm.
- **Text search:** search across OCR text, client and type.
- **Legal hold:** a flag on a document that blocks moving it to the bin.
- **HEIC support:** accept iPhone HEIC photos (via `pillow-heif`).

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
- Requiring the user to check each document's PDF before a box can be marked Complete.

### Out of scope
- Any network access at runtime: no cloud OCR, no CDN assets, no telemetry, no updates.
- AI or machine learning at runtime.
- Real client data in the repo, tests or demo.
- Logins and user accounts, beyond the localhost-only protections in §8.
- A JavaScript framework, or any JavaScript at all in the must tier.
- Editing PDF contents, annotations and versioning.
- Legal accuracy. The retention rules are illustrative, and the app says so on the disposal screens.

### Changes from the original brief, and why
| Original leaning | Changed to | Reason |
|---|---|---|
| One upload batch = one box | A box holds many batches | A real box often needs more than one upload (phone storage, upload limits, breaks). |
| Order "as captured" | EXIF date taken + fractions of a second, then filename | Browsers don't guarantee file order, and phone counters roll over. |
| Black-photo detection only in the "should" tier | A "Not a page" button in the "must" tier | Lens-cover photos and bad shots would otherwise clog the inbox forever. |
| Keep-until from the type's rule (trigger unspecified) | Counted from the document's own date | Counting from upload day gives wrong dates for every old document. |
| Low confidence goes to review | Review is a non-blocking marker; filing needs type and client, not date | Keeps capture fast; a missing date is common and is handled safely by "No date". |
| Disposing moves to a bin | Emptying the bin also writes a disposal record | Proof of timely, proper destruction is itself a record-keeping requirement. |
| (Not in the brief) | Box lifecycle with a "safe to shred" guard | Shredding paper whose OCR failed would lose the record for good. |

---

## 3. Objects, fields and lifecycles

All objects are SQLAlchemy models stored in SQLite. State fields are never set
directly. Every change goes through `obj.apply(action)` (see §3.6).

### 3.1 Box
A physical box of paper.

| Field | Type | Notes |
|---|---|---|
| id | int | |
| name | text, unique, 1–60 chars | for example "Box 3 – 2017–2019" |
| state | BoxState | Open, Complete, PaperDestroyed |
| created_at | datetime | |
| completed_at | datetime, nullable | set on entering Complete |
| paper_destroyed_at | datetime, nullable | |

**Lifecycle**

| From | Action | To | Guard (plain-words refusal) |
|---|---|---|---|
| (new) | create | Open | name unique and not blank |
| Open | complete | Complete | at least one document exists; no pages in Inbox; no documents Waiting, Being read, Couldn't read or Needs checking. This action is applied automatically by the system. |
| Complete | reopen | Open | applied automatically when new photos are uploaded or a page is restored to the inbox |
| Complete | confirm_paper_destroyed | PaperDestroyed | user confirms on a separate screen |

Display labels: Open = "In progress", Complete = "All filed – paper can go",
PaperDestroyed = "Paper destroyed".

A PaperDestroyed box accepts no new uploads. Pages already in it can still be
restored and grouped, because the photo may now be the only copy.

### 3.2 Batch
One upload into a box.

| Field | Type | Notes |
|---|---|---|
| id | int | |
| box_id | FK Box | |
| uploaded_at | datetime | |
| added_count, skipped_count, refused_count | int | shown to the user after upload |

No lifecycle; batches are an immutable record of each upload.

### 3.3 Page
One photo. Page rows are never deleted. Destroying a page deletes its files but
keeps the row, so its hash still blocks re-uploads.

| Field | Type | Notes |
|---|---|---|
| id | int | |
| box_id, batch_id | FK | |
| sha256 | text, unique | of the uploaded bytes; the duplicate check |
| original_filename | text | display only; never used to build a path |
| taken_at | datetime, nullable | EXIF `DateTimeOriginal` + `SubSecTimeOriginal` |
| state | PageState | Inbox, Grouped, Discarded, Destroyed |
| discard_reason | enum, nullable | `not_a_page`, `separator` (should tier) |
| document_id | FK Document, nullable | set while Grouped |
| position | int, nullable | page number within its document |
| photo_path, thumb_path | text | under `data/photos/` and `data/thumbs/`, named by sha256 |
| is_dark | bool, nullable | should tier: near-black detection result |

**Capture order** (computed, not stored): sort a box's pages by
`(taken_at is None, taken_at, original_filename, id)`. Photos without an EXIF time
sort after timed ones and show a "No time" label.

**Lifecycle**

| From | Action | To | Guard |
|---|---|---|---|
| (new) | upload | Inbox | not a duplicate; a readable JPEG/PNG; box is not PaperDestroyed |
| Inbox | group | Grouped | part of a valid range (§5.3) |
| Inbox | discard | Discarded | none |
| Discarded | restore | Inbox | none |
| Grouped | ungroup | Inbox | its document is Failed or NeedsReview |
| Grouped | destroy | Destroyed | only as part of destroying its document |
| Discarded | destroy | Destroyed | only through "Empty bin" |

Display labels: Inbox = "To sort", Grouped = "In a document",
Discarded = "Not a page (in bin)", Destroyed = "Destroyed".

### 3.4 Document (base class) and subclasses
Single-table inheritance: one `documents` table with a `doc_type` column that
tells SQLAlchemy which subclass to load. Subclass-only columns are nullable.

**Base `Document` fields**

| Field | Type | Notes |
|---|---|---|
| id | int | |
| doc_type | discriminator | `invoice`, `bank_statement`, `tax_return`, `unclassified` |
| box_id | FK Box | |
| state | DocState | see below |
| client_id | FK Client, nullable | |
| document_date | date, nullable | the retention trigger date (each subclass says which date that is) |
| keep_until | date, nullable | calculated; null means "No date" |
| ocr_text | text, nullable | from the OCR sidecar file |
| type_score, runner_up_score | int, nullable | kept to explain the decision |
| review_reasons | JSON list of text | plain words, for example "More than one client matched: Smith Ltd, J Smith & Co" |
| failure_reason | text, nullable | plain words |
| pdf_path | text, nullable | the current location (work, archive or bin) |
| legal_hold | bool | should tier |
| created_at, filed_at, binned_at, destroyed_at | datetime, nullable | |

**Class-level behaviour each subclass defines**

| Member | Purpose |
|---|---|
| `label`, `plural_label` | "Invoice" / "Invoices"; the plural is used as the folder name |
| `keywords: dict[str, int]` | weighted words and phrases for scoring |
| `extract(text) -> dict` | regexes that pull out subclass fields and `document_date` |
| `retention: RetentionRule \| None` | how keep-until is calculated |
| `filename_key() -> str` | the distinguishing part of the filename |

**Subclasses**

| Subclass | Extra fields | `document_date` is | Filename key | Retention rule (illustrative) |
|---|---|---|---|---|
| `Invoice` | invoice_number, amount_pence | invoice date | invoice number, or "no number" | 6 years after the end of the financial year that contains the invoice date (financial year end is a config constant, default 31 March) |
| `BankStatement` | account_last4, period_end | period end | `acct-1234` | 6 years after the period end |
| `TaxReturn` | tax_year (for example "2021-22") | 5 April at the end of the tax year | the tax year | 6 years after the end of the tax year |
| `Unclassified` | none | none | none | none; it can't be filed |

**`RetentionRule`** is a small value object with `years` and
`roll_to` (`none` | `financial_year_end`). Its `keep_until(document_date) -> date | None`
returns `None` when the date is `None`, and turns 29 February into 28 February in
non-leap years.

**Lifecycle**

| From | Action | To | Guard |
|---|---|---|---|
| (new) | create | Queued | made by grouping |
| Queued | start | Processing | worker only |
| Processing | fail | Failed | worker only; records failure_reason |
| Processing | flag | NeedsReview | one or more checks failed (§5.5); records review_reasons |
| Processing | file | Filed | type check and client check passed |
| Processing | requeue | Queued | only at app start-up, for work left unfinished by a crash |
| Failed | retry | Queued | none |
| Failed, NeedsReview | ungroup | Dissolved | pages go back to the inbox |
| NeedsReview | save | NeedsReview | stores the user's edits ("Save for later") |
| NeedsReview | confirm | Filed | type is not Unclassified; client set |
| Filed | correct | Filed | same guard as confirm; renames and moves the file, recalculates keep-until |
| Filed | dispose | InBin | keep_until is set and today is after it; not on legal hold (should tier) |
| InBin | restore | Filed | none |
| InBin | destroy | Destroyed | only through "Empty bin" confirmation |

Dissolved and Destroyed are final states.

Display labels: Queued = "Waiting to be read", Processing = "Being read",
Failed = "Couldn't read", NeedsReview = "Needs checking", Filed = "Filed",
InBin = "In bin", Destroyed = "Destroyed", Dissolved = "Ungrouped".

**Markers** (shown as badges; derived from fields, not states):
- **Needs checking:** state is NeedsReview.
- **No date:** Filed and `document_date` is null.
- **Due:** Filed and today is after `keep_until`.
- **On hold:** `legal_hold` (should tier).

**Changing type.** When review changes the type (for example Unclassified →
Invoice), the `doc_type` column is updated and the object is reloaded as the new
subclass, then its fields are re-extracted from `ocr_text`. This is done in one
function, `retype(document, new_class)`, because SQLAlchemy can't change an
object's class in place.

### 3.5 Client
| Field | Type | Notes |
|---|---|---|
| id | int | |
| ref | text, unique, format `C-0000` | generated as the next free number |
| name | text, unique | for example "Hollybrook Bakery Ltd" |
| aliases | JSON list of text | other names that appear on documents |
| created_at | datetime | |

No lifecycle in this build.

### 3.6 Records that support the lifecycles
**`StateChange`**: an append-only history row for every transition.

| Field | Notes |
|---|---|
| object_kind, object_id | `box` / `page` / `document`, id |
| action, from_state, to_state | |
| at | datetime |
| note | optional plain-words note |

**`DisposalRecord`**: written when a document is destroyed. It is an immutable
snapshot, so later changes to clients don't alter it.

| Field | Notes |
|---|---|
| document_id | |
| filed_name | the filename it was filed under |
| doc_type_label, client_ref, client_name | snapshot |
| document_date, keep_until | snapshot |
| binned_at, destroyed_at | |
| page_count, page_hashes | the sha256 hashes of its photos |

### 3.7 How lifecycles are enforced in code
A small hand-written state machine in `lifecycle.py`, with no third-party library,
so that it is easy to explain:

```python
class InvalidTransition(Exception):
    """Carries a plain-words reason for the user."""

class Lifecycle:
    # (from_state, action) -> to_state
    transitions: dict[tuple[State, str], State]

class Stateful:                      # mixin for Box, Page, Document
    _state: Mapped[str]              # stored column
    @property
    def state(self): ...             # read-only
    def allowed_actions(self) -> list[str]: ...
    def apply(self, action: str, *, now: datetime, note: str | None = None) -> None:
        # 1. look up (state, action) in the table, or raise InvalidTransition
        # 2. call guard_<action>() if defined; if it returns a reason, raise InvalidTransition(reason)
        # 3. set _state, write a StateChange row
```

- Templates only show buttons for `allowed_actions()`, but the server still checks every POST. A forbidden POST is refused with a friendly message.
- Functions take `now` / `today` as arguments instead of reading the clock, so tests can fix the date.

---

## 4. Screens

All pages are rendered on the server with Jinja2 templates. There is one stylesheet
and no JavaScript. The design follows these rules:
- Base font 20px, buttons at least 48px tall, high contrast.
- One main action per screen, as the biggest button.
- Plain words throughout.
- Destructive actions always go through a separate confirmation page.
- Pages that are waiting for OCR refresh themselves every 5 seconds with `<meta http-equiv="refresh">`.

| # | Screen | Shows | Main actions |
|---|---|---|---|
| 1 | **Home** | Big tiles with counts: Photos to sort, Needs checking, Being read, Due for disposal, Bin | Upload photos; each tile links to its screen |
| 2 | **Upload** | Box picker: open boxes, or "New box" with a name field; file picker (`multiple`, `accept="image/jpeg,image/png"`) | Upload. Result: "38 photos added. 2 skipped – already uploaded. 1 refused – not a photo (notes.txt)." |
| 3 | **Boxes** | Each box with its state label and counts (to sort, being read, needs checking, filed) | Open a box |
| 4 | **Box detail** | State, counts, list of documents with markers, "Not a page" photos | Go to inbox; "I have destroyed the paper" (only when Complete) |
| 5 | **Inbox (per box)** | Large thumbnails in capture order, numbered, with time taken, "No time" label if needed, and **First** / **Last** radio buttons and a **Not a page** tick box on each. Banner: "2 documents need checking – Check now / Later" | Make document; Mark ticked as not a page. Should tier: a "Suggested documents" panel at the top |
| 6 | **Needs checking** | List of flagged documents, oldest first, with their reasons | Open a document to check |
| 7 | **Check document** | The PDF on the left (browser's built-in viewer in an `<iframe>`); on the right, the reasons in plain words, type dropdown, client dropdown + "Add new client", date, type fields; the filename that will be used | **File it**; Save for later; Ungroup (pages back to inbox) |
| 8 | **Document** | PDF, all fields, markers, state label, keep-until, history (StateChange rows) | Only the allowed actions: Correct details, Retry, Move to bin, Restore |
| 9 | **Filed documents** | Table: client, type, date, keep-until, markers; filter by client and type. Should tier: a text search box | Open |
| 10 | **Due for disposal** | Filed documents past keep-until, with tick boxes; the "illustrative rules, not legal advice" note | Move ticked to bin |
| 11 | **Bin** | Documents in the bin and "Not a page" photos | Restore (each); **Empty bin…** |
| 12 | **Empty bin – confirm** | The exact list that will be destroyed, the count, and the warning "This cannot be undone" | "Yes, destroy these N items permanently"; Cancel |
| 13 | **Paper destroyed – confirm** | Box summary; thumbnails of any "Not a page" photos for a last look | "Yes, I have destroyed the paper for this box"; Cancel |
| 14 | **Disposal log** | DisposalRecords, newest first | none (read-only) |
| 15 | **Clients** | Ref, name, aliases, document count | Add client |

Plain-word messages for errors and refusals appear in a banner at the top of
the next page (Flask `flash`).

---

## 5. Behaviours (given / when / then)

### 5.1 Boxes and upload
- **B1 New box:** **Given** no box named "Box 1", **when** the user uploads 40 photos choosing "New box: Box 1", **then** box "Box 1" is created as Open, one batch holds 40 Inbox pages, and the result says "40 photos added".
- **B2 Add to an existing box:** **Given** an Open box "Box 1" with 40 pages, **when** the user uploads 25 more photos into "Box 1", **then** a second batch is created and the inbox shows all 65 in capture order.
- **B3 Duplicate in a later upload:** **Given** photo P was uploaded before, **when** the same file is uploaded again into any box, **then** it is skipped and the result says "1 skipped – already uploaded".
- **B4 Duplicate in the same upload:** **Given** an upload containing the same file twice, **when** it is processed, **then** one page is created and one is reported as skipped.
- **B5 Photo of a destroyed record:** **Given** a photo whose document was destroyed, **when** it is uploaded again, **then** it is skipped with "This photo belonged to a record destroyed on 3 Feb 2026".
- **B6 Not a photo:** **Given** an upload containing `notes.txt` or a corrupt JPEG, **when** it is processed, **then** that file is refused by name, and the other photos are still added.
- **B7 HEIC (must tier):** **Given** an iPhone `.heic` photo, **when** it is uploaded, **then** it is refused with "iPhone HEIC photos aren't supported yet. On the iPhone: Settings → Camera → Formats → Most Compatible."
- **B8 Paper destroyed:** **Given** a PaperDestroyed box, **when** the user opens Upload, **then** that box is not offered, and a crafted POST to it is refused.
- **B9 Duplicate box name:** **Given** box "Box 1" exists, **when** the user creates a new box named "Box 1", **then** it is refused with "There is already a box called Box 1".

### 5.2 Capture order
- **O1 EXIF time:** **Given** photos with EXIF times 10:00:05, 10:00:01 and 10:00:03, **when** the inbox is shown, **then** they appear in the order 10:00:01, 10:00:03, 10:00:05 whatever their filenames or upload order.
- **O2 Same second:** **Given** two photos with the same `DateTimeOriginal` and fractions of a second .20 and .75, **then** .20 comes first. If the fractions are also missing or equal, filename order decides.
- **O3 No EXIF time:** **Given** a photo with no EXIF time, **then** it appears after all timed photos (sorted by filename) with a "No time" label.
- **O4 Rotated photo:** **Given** a photo whose EXIF orientation says it is rotated, **then** its thumbnail and PDF page are shown the right way up.

### 5.3 Grouping
- **G1 Make document:** **Given** Inbox pages 1–10 in a box, **when** the user picks First = 3 and Last = 6 and presses Make document, **then** a Document is created in Queued with pages 3, 4, 5, 6 as positions 1–4, those pages become Grouped and leave the inbox, and the inbox shows 1, 2, 7–10.
- **G2 One-page document:** **Given** First = Last = page 7, **then** a one-page document is created.
- **G3 First after Last:** **Given** First = 6 and Last = 3, **then** the app swaps them and groups pages 3–6.
- **G4 Discarded page inside a range:** **Given** page 4 is Discarded and the user groups 3–6, **then** the document contains pages 3, 5, 6, and page 4 stays Discarded.
- **G5 Range would swallow a grouped page:** **Given** page 5 is already Grouped (because the user grouped 5–5 earlier) and the user picks 3–7, **then** it is refused with "Photos 3 to 7 include a photo that is already in a document".
- **G6 Only one end picked:** **Given** First is picked but not Last, **then** it is refused with "Pick both the first and the last page".
- **G7 Not a page:** **Given** pages 2 and 9 are ticked, **when** the user presses Mark as not a page, **then** both become Discarded (reason `not_a_page`), leave the inbox and appear in the Bin.
- **G8 Restore:** **Given** a Discarded page in the Bin, **when** the user presses Restore, **then** it returns to the inbox in its original capture position, and an owning Complete box reopens.
- **G9 Ungroup:** **Given** a document in Needs checking, **when** the user presses Ungroup, **then** the document becomes Dissolved, its PDF work files are deleted, and its pages return to the inbox in capture order.
- **G10 No ungrouping after filing:** **Given** a Filed document, **then** Ungroup is not offered, and a crafted POST is refused with "Filed documents can't be ungrouped".

### 5.4 OCR worker
- **W1 Happy path:** **Given** a Queued document, **when** the worker picks it up, **then** it moves to Processing, a searchable PDF and a text file are written to `data/work/`, and classification runs (§5.5).
- **W2 Progress display:** **Given** a document is Waiting or Being read, **then** the inbox banner and the document page say so and refresh every 5 seconds.
- **W3 Failure:** **Given** OCRmyPDF exits with an error or exceeds the 5-minute timeout, **then** the document becomes Failed with "Couldn't read this document. Try again, or retake the photos.", and the technical detail is written to `data/logs/app.log`.
- **W4 Retry:** **Given** a Failed document, **when** the user presses Try again, **then** it goes back to Queued.
- **W5 Crash recovery:** **Given** the app was stopped while a document was Processing, **when** the app starts, **then** that document is requeued (Processing → Queued) and read again.
- **W6 Missing OCR tools:** **Given** Tesseract or Ghostscript is missing, **when** the app starts, **then** it prints which program is missing and how to install it, and exits.

### 5.5 Classification and review
Checks, in order. All reasons that fail are recorded.
1. **Type check:** each subclass scores the text by adding a keyword's weight once if it appears (case-insensitive, whole word or phrase). The type passes when the top score is at least `MIN_TYPE_SCORE` (default 6) and beats the runner-up by at least `MIN_TYPE_MARGIN` (default 3). Otherwise the type is Unclassified.
2. **Client check:** if exactly one `C-0000` reference is found and it exists in the register, it matches. If no reference is found, the client matches when exactly one client's name or alias appears (case-insensitive, whole phrase). Otherwise there is no match.
3. **Date** (does not block filing): the subclass extracts its date with UK day-first formats (`14/03/2021`, `14 March 2021`, `2021-03-14`). Dates after today are ignored as misreads.

Behaviours:
- **C1 Confident:** **Given** text containing "INVOICE", "Invoice number INV-1043", "Amount due", "C-0042" and "Invoice date 14/03/2021", **then** the type is Invoice, client is C-0042, document_date is 2021-03-14, and the document is Filed automatically with no marker.
- **C2 Unclear type:** **Given** text scoring Invoice 7 and Bank statement 5, **then** it is flagged with "Not sure what type this is (Invoice or Bank statement?)" and the type is shown as Unclassified.
- **C3 No keywords:** **Given** text matching no keywords, **then** it is flagged with "Couldn't tell what type this is".
- **C4 Two clients:** **Given** text naming "Smith" where two clients have that alias, **then** it is flagged with "More than one client matched: Smith Ltd, J Smith & Co".
- **C5 Unknown reference:** **Given** text containing "C-0099" and no such client, **then** it is flagged with "Client C-0099 isn't in your client list".
- **C6 No date:** **Given** a confident type and client but no date found, **then** it is Filed with the "No date" marker, keep_until is empty, and the filename uses "undated".
- **C7 Check now or later:** **Given** a flagged document, **when** the user groups more documents, **then** nothing blocks them, and the inbox banner, Home tile and Box detail all show "Needs checking" counts.
- **C8 Confirm in review:** **Given** a flagged document, **when** the user picks type Invoice and client C-0042 and presses File it, **then** `retype()` makes it an Invoice, its fields are re-extracted, and it is Filed with a calculated keep-until.
- **C9 Review guard:** **Given** the client is still empty, **when** File it is pressed, **then** it is refused with "Choose a client before filing", and the edits are kept.
- **C10 Add client in review:** **Given** the client isn't in the register, **when** the user presses Add new client and enters a name, **then** the client is created with the next free ref and selected in the form.
- **C11 Save for later:** **Given** the user has edited some fields, **when** they press Save for later, **then** the edits are stored, and the document stays Needs checking.

### 5.6 Naming and filing
Default template, a constant in `rules/naming.py`:
`{client_ref} {client_name}/{type_plural}/{date} {type_label} {key}.pdf`

- **N1 Invoice:** **Given** an Invoice for C-0042 Hollybrook Bakery Ltd, dated 2021-03-14, number INV-1043, **then** it is filed at `data/archive/C-0042 Hollybrook Bakery Ltd/Invoices/2021-03-14 Invoice INV-1043.pdf`.
- **N2 No date:** **Given** no date, **then** the date part is `undated`.
- **N3 Name clash:** **Given** a file already exists at the target path, **then** the new file gets ` (2)` (then ` (3)` …) before `.pdf`.
- **N4 Unsafe characters:** **Given** a client name containing `/ \ : * ? " < > |` or trailing dots or spaces, **then** those characters are replaced with `-` or trimmed, so the path works on Windows too.
- **N5 Correcting details:** **Given** a Filed document, **when** its type, client or date is corrected, **then** the file is moved to the newly calculated path, keep-until is recalculated, and empty old folders are removed.
- **N6 Database is the source of truth:** the database records `pdf_path`. If a file is missing from disk, the document page says "The PDF file is missing" instead of crashing.

### 5.7 Retention
- **R1 Invoice:** **Given** an Invoice dated 2021-03-14 and a financial year ending 31 March, **then** keep_until is 2027-03-31.
- **R2 Invoice after year end:** **Given** an Invoice dated 2021-04-02, **then** keep_until is 2028-03-31.
- **R3 Bank statement:** **Given** a Bank statement with period end 2018-06-30, **then** keep_until is 2024-06-30.
- **R4 Tax return:** **Given** a Tax return for tax year 2017-18, **then** document_date is 2018-04-05 and keep_until is 2024-04-05.
- **R5 Leap day:** **Given** a Bank statement with period end 2020-02-29, **then** keep_until is 2026-02-28.
- **R6 Due:** **Given** today is 2026-10-25 and keep_until is 2026-10-24, **then** the document is listed in Due for disposal. **Given** keep_until is 2026-10-25, **then** it is not listed (it is kept through that day).
- **R7 No date:** **Given** a Filed document with no date, **then** it never appears in Due for disposal, and its page says "Keep-until not set – add the document's date".

### 5.8 Disposal
- **D1 Move to bin:** **Given** two due documents ticked, **when** the user presses Move to bin, **then** both become InBin, their PDFs move to `data/bin/`, and binned_at is set.
- **D2 Not yet due:** **Given** a document that isn't due, **when** a crafted POST tries to move it to the bin, **then** it is refused with "This document must be kept until 31 Mar 2027".
- **D3 Restore:** **Given** a document in the bin, **when** the user presses Restore, **then** it becomes Filed again at its calculated path (clash rule N3 applies).
- **D4 Empty bin needs a second step:** **Given** a bin with 3 documents and 2 "Not a page" photos, **when** the user presses Empty bin…, **then** a confirmation page lists those 5 items, and nothing is deleted yet.
- **D5 Confirm:** **Given** the confirmation page, **when** the user presses "Yes, destroy these 5 items permanently", **then**:
  - the 3 PDFs and all their photos and thumbnails are deleted from disk;
  - the documents and their pages become Destroyed;
  - 3 DisposalRecords are written;
  - the 2 discarded photos are deleted and their pages become Destroyed;
  - the Disposal log shows the 3 records.
- **D6 Only what was confirmed:** **Given** a document was moved to the bin after the confirmation page was opened, **when** the user confirms, **then** only the items listed on that page are destroyed (the form carries their ids).
- **D7 Legal hold (should tier):** **Given** a due document on legal hold, **then** it is shown in Due for disposal with "On hold", and Move to bin refuses it.

### 5.9 Box completion
- **X1 Complete:** **Given** box "Box 1" has an empty inbox and all its documents are Filed, **when** the last document is filed, **then** the box becomes Complete, "All filed – paper can go".
- **X2 Not complete:** **Given** one document in the box is Needs checking, **then** the box stays Open, and Box detail says "1 document needs checking before this paper can go".
- **X3 Reopen:** **Given** a Complete box, **when** more photos are uploaded into it, **then** it becomes Open.
- **X4 Paper destroyed:** **Given** a Complete box, **when** the user confirms "Yes, I have destroyed the paper for this box", **then** it becomes PaperDestroyed with the date recorded, and the confirmation page showed any "Not a page" photos first.
- **X5 Not yet:** **Given** an Open box, **then** "I have destroyed the paper" is not offered, and a crafted POST is refused.

### 5.10 Should tier: dark-photo proposals
- **S1 Detection:** **Given** a photo whose downscaled greyscale mean is below 25/255 and whose standard deviation is below 12, **then** `is_dark` is true. Both values are config constants.
- **S2 Proposals:** **Given** inbox photos `D a b c D d e D` (D = dark), **then** two documents are proposed, a–c and d–e, each shown with First and Last pre-filled.
- **S3 Confirm:** **Given** a proposal, **when** the user confirms it, **then** the document is created as in G1, and the dark photos around it become Discarded with reason `separator`.
- **S4 Adjust:** **Given** a proposal that merges two documents (a forgotten lens cover), **then** the user can change First and Last before confirming, or ignore the proposal and group manually.
- **S5 Dark page:** **Given** a genuinely dark document page detected as dark, **then** the user can include it by grouping manually. Nothing is discarded without confirmation.

---

## 6. Acceptance tests

Automated tests use pytest in `tests/`. Tests marked `ocr` run real
Tesseract/OCRmyPDF on generated photos and are skipped with a clear message if
the tools are missing. All others use stored text fixtures and run in seconds.
Dates are passed in, not read from the clock.

| ID | Check | Type |
|---|---|---|
| AT-01 | Every row of every lifecycle table (§3) is allowed, and every other (state, action) pair raises `InvalidTransition` | unit, table-driven |
| AT-02 | Each guard refuses with the plain-words reason given in §5 | unit |
| AT-03 | Every transition writes exactly one StateChange row | unit |
| AT-04 | Setting `state` directly is impossible (no setter) | unit |
| AT-05 | Upload: B1–B9 (new box, add to box, duplicates incl. same upload and destroyed, refusals) | integration (Flask test client) |
| AT-06 | Capture order: O1–O3 using generated photos with set EXIF times | unit |
| AT-07 | Grouping: G1–G10 | integration |
| AT-08 | Classification: C1–C6 on text fixtures, including the reasons' exact wording | unit |
| AT-09 | Review: C8–C11, including `retype()` loading the right subclass | integration |
| AT-10 | Naming: N1–N5, including Windows-unsafe characters and clashes | unit |
| AT-11 | Retention: R1–R7, including the leap day and the "kept through that day" boundary | unit |
| AT-12 | Disposal: D1–D6; after D5, the files are gone from disk and the DisposalRecords match the snapshot | integration |
| AT-13 | Box completion: X1–X5 | integration |
| AT-14 | Worker: W3–W5 with OCR replaced by a fake that fails or hangs | integration |
| AT-15 | End to end: generate a box of photos → upload → group → OCR → Invoice filed at the expected path, with text searchable in the PDF | `ocr` |
| AT-16 | The app binds only to 127.0.0.1; a request with a foreign `Host` header is refused; a POST without the form token is refused | integration |
| AT-17 | No template or static file references an `http(s)://` URL | unit (scan files) |
| AT-18 | Seed: `docmanager seed --reset` on an empty data folder produces boxes, clients and documents in every main state (Filed, Needs checking, No date, Due, In bin, inbox photos) | `ocr` |
| AT-19 | Manual: the full demo script (§9) runs on a fresh clone following README steps only | manual |
| AT-20 | Manual: every screen is usable at 200% browser zoom, and every action button is at least 48px tall | manual |

`uv run pytest` must pass, and `uv run ruff check` and `uv run ruff format --check` must be clean, before each commit.

---

## 7. Technical decisions

| Area | Decision | Why (one line) |
|---|---|---|
| Language | Python 3.13, pinned in `.python-version` | Recent and widely supported by the libraries; uv installs it. |
| Web framework | Flask + Jinja2 templates | Smallest thing to learn: one function per URL returning HTML. |
| Database | SQLite file + SQLAlchemy 2.0 ORM | No server; single-table inheritance makes the Document class hierarchy the schema. |
| SQLite settings | WAL mode, one session per request/thread | The web pages and the OCR worker can read and write without locking each other out. |
| Lifecycles | Hand-written `Lifecycle` + `Stateful` mixin | Easy to read and explain; transition tables are plain data. |
| OCR | OCRmyPDF (pinned Python package) run as a subprocess (`python -m ocrmypdf`) with `-l eng --rotate-pages --deskew --sidecar`; photos combined first with `img2pdf` after EXIF rotation | Local only; a subprocess can't crash or block the web app and is easy to time out. |
| Background work | One worker thread started with the app; it claims Queued documents through the lifecycle | No extra programs to run; restart-safe because the queue is the database. |
| Images | Pillow: EXIF reading, orientation, thumbnails (400px), dark detection, demo page drawing | One library for all image work. |
| Dependencies | uv: `pyproject.toml` + committed `uv.lock` | Exact versions everywhere with one fast tool. |
| Formatting and linting | Ruff (format + check), default rules plus import sorting | One tool, fast, settings live in `pyproject.toml`. |
| Tests | pytest; `ocr` marker for slow tests | Standard and simple; slow tests can be skipped. |
| Error handling | Domain exceptions (`InvalidTransition`, `UploadRefused`, `GroupingError`) carry plain-words messages, shown with `flash`; custom 404/500 pages; OCR errors become the Failed state; technical detail goes to a rotating log at `data/logs/app.log` | The user never sees a stack trace; the developer can still find out what went wrong. |
| File storage | Everything in `data/` (gitignored), location overridable with `DOCMANAGER_DATA`. Uploaded files are named by sha256, never by their uploaded name | Code and data stay separate; no path tricks from filenames. |
| Run | `uv run docmanager` serves on `127.0.0.1:5000` (host fixed in code); `uv run docmanager seed [--reset]`; `uv run docmanager make-photos OUT_DIR` | One command each; nothing listens on the network. |
| Config | `config.py` constants: thresholds, financial year end, naming template, OCR timeout | Every tunable value lives in one place. |
| System programs | Tesseract (with `eng` and `osd` data), Ghostscript, from apt. Checked at start-up | OCRmyPDF needs them; a clear message beats a cryptic failure. |

### Project layout
```
doc-manager/
  pyproject.toml  uv.lock  .python-version  README.md  SPEC.md  CLAUDE.md
  src/docmanager/
    __init__.py          create_app()
    cli.py               run | seed | make-photos
    config.py
    db.py                engine, session, WAL
    lifecycle.py         Lifecycle, Stateful, InvalidTransition
    models/              box.py page.py document.py client.py records.py
    rules/               classify.py retention.py naming.py dates.py
    services/            upload.py grouping.py ocr_worker.py filing.py disposal.py darkness.py
    web/                 routes.py templates/ static/style.css
    demo/                pages.py (draws fake documents) photos.py (EXIF, noise, dark frames) seed.py
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

- **Localhost only:** the server binds `127.0.0.1` with a fixed host. Because there are no logins, POST forms carry a per-session token, and requests whose `Host` header isn't `127.0.0.1:5000` or `localhost:5000` are refused. This stops a malicious web page in the same browser from emptying the bin (CSRF and DNS rebinding).
- **No network:** no outbound requests at runtime; no CDN fonts, scripts or styles; Tesseract language data is local.
- **No real data:** all documents are generated by `demo/` code, using made-up names, fictional banks and offices, and `C-0000` refs. No real organisation's name or branding is imitated. The repo never contains a `data/` folder.
- **No AI at runtime:** classification is keyword weights and regexes only.
- **No JavaScript** in the must tier; only HTML forms and meta refresh.
- **Accessibility:** plain words, 20px base font, buttons at least 48px, high contrast, confirmations for anything destructive.
- **Legal note:** the retention rules are illustrative. The Due for disposal, Bin and Empty bin screens say "These keep-until dates come from example rules. Check the rules that apply to you."
- **Time:** about 3.5 hours of coding for the must tier, built in the order of §10. Should-tier work starts only after AT-01–AT-18 pass.
- **Upload size:** up to 500 MB per upload; above that, the user is told to upload in parts into the same box.

---

## 9. Demo script (about 5 minutes)
1. `uv run docmanager seed --reset`, then `uv run docmanager`, and open http://127.0.0.1:5000.
2. **Home:** point out the counts: some to sort, some needing checking, some due for disposal.
3. **Live upload:** `uv run docmanager make-photos ~/demo-box` beforehand; upload that folder into a new box "Interview box". Upload one photo twice to show the duplicate skip.
4. **Inbox:** group two documents with First and Last; mark the lens-cover photos as "Not a page". (If the should tier is built: confirm a suggested grouping.)
5. **While OCR runs:** show the code for `lifecycle.py` and one transition table; try a forbidden action and show the refusal.
6. **Needs checking:** open a flagged document, read out its reasons, pick the client and file it. Show the new filename on disk.
7. **Box detail:** the box turns "All filed – paper can go"; confirm paper destroyed.
8. **Disposal:** Due for disposal → Move to bin → Empty bin → confirm → Disposal log.
9. Close with the test run: `uv run pytest -m "not ocr"`.

## 10. Build order (must tier, about 3.5 hours over four sittings)
| Sitting | Work | Done when |
|---|---|---|
| 1 (~45 min) | uv project, ruff, pytest, `config`, `db`, `lifecycle.py`, all models and transition tables | AT-01–AT-04 pass |
| 2 (~50 min) | Demo page and photo generator, upload, capture order, inbox, grouping, Not a page, base template and style | AT-05–AT-07 pass; can upload and group generated photos |
| 3 (~60 min) | OCR worker, classification, review screens, naming and filing, clients screen | AT-08–AT-10, AT-14, AT-15 pass |
| 4 (~45 min) | Retention, due list, bin and empty-bin confirmation, disposal records, box completion, seed, localhost protections, README | AT-11–AT-13, AT-16–AT-19 pass |

Commit at the end of each sitting with the tests green.
