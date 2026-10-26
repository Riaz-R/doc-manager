# Decisions log

One entry per decision in [SPEC.md](SPEC.md), grouped in the order of the spec.
Last updated 2026-10-26.

"Who chose" is one of:
- **Me**: from my original brief, or an edit I asked for after the interview.
- **Claude's recommendation, which I accepted in the interview**.
- **Proposed by Claude**: decisions I wasn't asked about.

Where something was chosen in the interview and later changed by my edits, the
entry describes the current decision and lists the interview choice under
alternatives.

---

## Purpose and scope (§1–§2)

### 1. Shredding the paper and destroying the digital record are separate events
- **Decision:** A box's paper can be shredded as soon as everything in it is filed. Each digital record is destroyed separately, after its keep-until date. The paper never waits for keep-until.
- **Alternatives considered:** Treating "paper destroyed" as the last step of a box lifecycle (the interview choice, now in the should tier, §11.2).
- **Who chose:** Me
- **Why I agreed:**

### 2. Users
- **Decision:** The primary user is my dad, with boxes of client files. A similar user is a small local business owner. The demo audience is interviewers for roles that configure object models, lifecycles and workflows.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 3. Typical workflow, with the lens-cover tip
- **Decision:** Photograph each document's pages in order, covering the lens for one photo between documents. Mark those photos "Not a page", group the rest, shred the box's paper when Home shows "Paper can go", and destroy expired records later as a separate step.
- **Alternatives considered:** The interview draft's workflow, where shredding waited for the box lifecycle's confirmation step.
- **Who chose:** Me
- **Why I agreed:**

### 4. Must tier cut to the core demo path
- **Decision:** The must tier covers only upload, inbox, grouping, Not a page, OCR, classification, review, naming and filing, Paper can go, retention, disposal of digital records, lifecycles, seed script, README and localhost binding. Everything else is in the should tier.
- **Alternatives considered:** The interview draft's must tier, estimated at 515 minutes. The second draft's must tier, estimated at 380 minutes.
- **Who chose:** Me
- **Why I agreed:**

### 5. Known limitations are written down
- **Decision:** The spec lists what the must tier can't do yet: a client not in the register can't be filed, a phone counter rollover puts photos in the wrong order, and a long document holds the browser page until OCR finishes.
- **Alternatives considered:** Leaving the limitations unstated.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 6. Stretch: QR separator sheets and a settings page for the naming template
- **Decision:** Both are stretch, not this build. The naming template is a constant in code until then.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 7. Stretch: importing clients from a CSV file
- **Decision:** Client import is stretch.
- **Alternatives considered:** "Register + CSV import" was offered in the interview; I chose the register without import.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 8. Stretch: event-based retention
- **Decision:** A "Client agreement" type, kept 6 years after the client leaves, is stretch. It needs a "left on" date on Client.
- **Alternatives considered:** "Client agreement" and "Date + event triggers" were offered in the interview; I didn't choose them.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 9. Roadmap: sorting loose pages
- **Decision:** Sorting pages that are neither grouped nor in order is roadmap only.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 10. Roadmap: Windows installer, backups and export, multiple users
- **Decision:** A Windows shortcut or installer, backups and export, and multiple users with logins and sign-off on disposal are roadmap only.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 11. Roadmap: checking each PDF before a box's paper can go
- **Decision:** Requiring the user to check each document's PDF before "Paper can go" is roadmap only.
- **Alternatives considered:** "Guard + page check" was offered in the interview (as a should); I chose the box guard without it.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 12. Out of scope from my brief
- **Decision:** No network access at runtime, no AI at runtime, no real client data, and no logins.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 13. Other things out of scope
- **Decision:** Editing PDF contents, annotations, versioning, and the legal accuracy of the retention rules are out of scope.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 14. All should-tier detail in one section
- **Decision:** Should-tier details live in §11, with a one-line pointer in each section.
- **Alternatives considered:** Should-tier details spread through each section (the earlier drafts).
- **Who chose:** Me
- **Why I agreed:**

---

## Boxes, batches and photos (§3.1–§3.3, §5.1–§5.3)

### 15. A box holds many uploads
- **Decision:** A Box is the physical box. Each upload is a Batch into a new or existing box.
- **Alternatives considered:** One upload = one box (my original leaning); no boxes at all.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 16. Batches record their counts
- **Decision:** Each batch stores how many photos were added, skipped and refused, and shows them after upload.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 17. Box names are unique, 1–60 characters
- **Decision:** A second box with the same name is refused with "There is already a box called Box 1".
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 18. No box lifecycle in the must tier
- **Decision:** The box lifecycle (Open, Complete, PaperDestroyed), the "I have destroyed the paper" confirmation, the Boxes and Box detail screens, and automatic reopening are should tier.
- **Alternatives considered:** "Box lifecycle with guard" (accepted in the interview); "Just show counts".
- **Who chose:** Me
- **Why I agreed:**

### 19. "Paper can go" marker on each box
- **Decision:** Worked out, not stored. Shown on Home when the box has at least one document, no photos in its inbox, and every document filed. When it isn't shown, Home says what is blocking it.
- **Alternatives considered:** The box lifecycle's Complete state; just showing counts.
- **Who chose:** Me
- **Why I agreed:**

### 20. "Paper can go" details
- **Decision:** Documents later moved to the bin still count as filed. A document not read yet also blocks it. A box with nothing filed shows "Nothing filed from this box yet". The lines come from `box.paper_blockers()`.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 21. The same photo can't be uploaded twice
- **Decision:** A duplicate photo is skipped and reported.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 22. Duplicates are found by SHA-256 of the exact bytes
- **Decision:** The fingerprint is unique among pages currently in the app, including within a single upload.
- **Alternatives considered:** Not discussed. Other options would be matching by filename or by how similar the images look.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 23. A destroyed photo can be uploaded again
- **Decision:** Emptying the bin deletes the fingerprints, so the same photo can be added again later.
- **Alternatives considered:** Keeping fingerprints so destroyed photos stay blocked (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 24. JPEG and PNG only; HEIC refused with a hint
- **Decision:** iPhone HEIC photos are refused with the setting to change on the phone. HEIC support is should tier.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 25. Refused files are named; the rest still upload
- **Decision:** A non-photo or corrupt file is refused by name, and the other photos are still added.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 26. Uploads up to 500 MB
- **Decision:** Above 500 MB, the user is told to upload in parts into the same box.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 27. Uploaded files are named by their fingerprint
- **Decision:** Photos are stored under their sha256, never their uploaded name. The original filename is for display and ordering only.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 28. Inbox ordered by filename; EXIF order in the should tier
- **Decision:** A box's photos sort by filename. Ordering by the EXIF time taken is should tier.
- **Alternatives considered:** "EXIF time, then name" (recommended in the interview); upload order.
- **Who chose:** Me
- **Why I agreed:**

### 29. Turning rotated photos the right way up is should tier
- **Decision:** Thumbnails and PDF pages follow the photo as stored. EXIF orientation handling is in §11.9.
- **Alternatives considered:** Correcting rotation in the must tier (the earlier drafts).
- **Who chose:** Me
- **Why I agreed:**

### 30. "Not a page" in the must tier
- **Decision:** Marked photos leave the inbox and go to the bin. They can be restored, don't block "Paper can go", and are deleted when the bin is emptied, with no disposal record.
- **Alternatives considered:** In the interview I accepted the "Not a page" button, then moved it to should, then back. The other interview options were leaving the photos in the inbox or deleting them immediately.
- **Who chose:** Me
- **Why I agreed:**

### 31. Page lifecycle states
- **Decision:** Inbox ("To sort"), Grouped ("In a document") and Discarded ("Not a page (in bin)"), with the transitions upload, group, discard, restore and destroy.
- **Alternatives considered:** Not discussed (my brief asked for enforced page lifecycles, not specific states).
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 32. Group by picking the first and last photo
- **Decision:** Consecutive photos become one document; grouped photos leave the inbox.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 33. Grouping rules
- **Decision:** First and Last are swapped if reversed; both must be picked; a range that includes a grouped photo is refused; "Not a page" photos inside a range are skipped; a one-page document is allowed.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 34. Ungroup is should tier
- **Decision:** Ungrouping a document is in §11.3.
- **Alternatives considered:** Ungrouping while a document is "Needs checking" or "Couldn't read" (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 35. Dark-photo proposals (should tier): propose, user confirms
- **Decision:** Runs of photos between dark lens-cover photos are proposed as documents. The user confirms, adjusts or ignores each one.
- **Alternatives considered:** Auto-group with no confirmation; two dark photos in a row mark a new box.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 36. Dark-photo thresholds
- **Decision:** A photo is dark when its greyscale mean is below 25/255 and its standard deviation below 12, both config constants.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Documents and document types (§3.4)

### 37. A Document holds a swappable DocumentType
- **Decision:** A `DocumentType` base class with one subclass per type; each overrides `score(text)` and `retention_years`. A Document stores its type's key, and `change_type()` swaps the type on the same document, re-extracting fields and recalculating keep-until.
- **Alternatives considered:** A Document base class with one subclass per type (my brief); single-table inheritance with a `retype()` function (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 38. Invoice and Letter in the must tier; Bank statement in the should tier
- **Decision:** `InvoiceType` and `LetterType` are built first; `BankStatementType` is in §11.9.
- **Alternatives considered:** Invoice, Bank statement and Tax return (accepted in the interview); Client agreement; Invoice, Letter and Bank statement (my first edit).
- **Who chose:** Me
- **Why I agreed:**

### 39. Fields and filename keys for each type
- **Decision:** Invoice: invoice number and amount (stored in pence), keyed by invoice number. Letter: subject from a "Re:" line, keyed by its first 40 characters.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 40. A document with no type is "Unclassified" and can't be filed
- **Decision:** `doc_type` is null until a type is chosen.
- **Alternatives considered:** Stated in the interview's document-types question but not offered as a choice.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 41. Document lifecycle states
- **Decision:** Grouped ("Not read yet" / "Couldn't read"), NeedsReview ("Needs checking"), Filed and InBin, with the transitions group, file, flag, confirm, dispose, restore and destroy.
- **Alternatives considered:** Not discussed (my brief asked for enforced document lifecycles, not specific states).
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## OCR (§5.4, §7)

### 42. Local OCR with OCRmyPDF and Tesseract
- **Decision:** Each document becomes a searchable PDF, made entirely on this computer.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 43. OCR runs while the page waits; background worker is should tier
- **Decision:** OCR runs during the "Make document" request. The background worker, auto-refresh and SQLite WAL mode are in §11.1.
- **Alternatives considered:** "Background worker" (accepted in the interview); "Separate process command".
- **Who chose:** Me
- **Why I agreed:**

### 44. A failed OCR keeps the document Grouped, with an error and Retry
- **Decision:** No Failed state: the document stays Grouped with `ocr_error` and a Retry button.
- **Alternatives considered:** A Failed state in the document lifecycle (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 45. An interrupted read is shown with Retry
- **Decision:** A Grouped document with no text and no error (the app stopped mid-read) is listed with Retry.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 46. How OCR is run
- **Decision:** Photos are combined with `img2pdf`, then OCRmyPDF runs as a subprocess with `-l eng --rotate-pages --deskew --sidecar` and a 5-minute timeout. `--rotate-pages` stays, so sideways pages are still read correctly.
- **Alternatives considered:** Not discussed. Calling OCRmyPDF as a Python library would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 47. Missing OCR programs are checked at start-up
- **Decision:** Tesseract (with `eng` and `osd` data) and Ghostscript come from apt. If one is missing, the app says which and how to install it, and exits.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Clients (§3.5)

### 48. A client register with C-0000 refs
- **Decision:** Clients are matched against a register, not guessed from text.
- **Alternatives considered:** Free text from OCR; register with CSV import.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 49. Clients come only from the seed script in the must tier
- **Decision:** The clients screen and adding a client from review are should tier.
- **Alternatives considered:** A clients screen and inline "add client" in the must tier (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 50. Match by C-0000 reference or exact name only; aliases are should tier
- **Decision:** A ref is tried first, then the client's exact name.
- **Alternatives considered:** Matching names and aliases (part of the register accepted in the interview).
- **Who chose:** Me
- **Why I agreed:**

### 51. Name matching ignores case and needs the whole phrase; names are unique
- **Decision:** "smith ltd" matches "Smith Ltd", but "Smith" alone doesn't. Two clients can't share a name.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Classification and review (§5.5)

### 52. Plain rules, no AI at runtime
- **Decision:** Each type's `score()` and regular expressions decide type, client and date.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 53. The type must clear a minimum score and beat the runner-up by a margin
- **Decision:** Each type scores the text; the top score must clear a threshold and beat the next type by a margin.
- **Alternatives considered:** Part of the "All three checks pass" option. The others were "Review everything" and "Type score only".
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 54. Scoring defaults and helper
- **Decision:** `MIN_TYPE_SCORE` 6 and `MIN_TYPE_MARGIN` 3; a `keyword_score(text, weights)` helper on the base class.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 55. Filing needs a clear type and a matched client; the date doesn't block
- **Decision:** A document is filed automatically when the type and client checks pass. A missing date gets the "No date" marker instead.
- **Alternatives considered:** All three checks, including the date (recommended in the interview); review everything; type score only.
- **Who chose:** Me
- **Why I agreed:**

### 56. Review is a marker that never blocks
- **Decision:** Flagged documents get "Needs checking" and can be checked now or later. The inbox banner and Home tile show the count, so they aren't forgotten.
- **Alternatives considered:** Review as a step that must be done before carrying on.
- **Who chose:** Me
- **Why I agreed:**

### 57. Reasons in plain words
- **Decision:** Every failed check is recorded with a plain-words reason, for example "More than one client matched: Smith Ltd, J Smith & Co".
- **Alternatives considered:** Part of the "All three checks pass" option.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 58. Dates are read in UK day-first formats; future dates are ignored
- **Decision:** `14/03/2021`, `14 March 2021` and `2021-03-14` are read. Dates after today are treated as misreads.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 59. Review extras are should tier
- **Decision:** "Save for later", adding a client from review, and correcting after filing are in §11.4.
- **Alternatives considered:** All three in the must tier (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

---

## Naming and filing (§5.6)

### 60. Client and type folders
- **Decision:** `{client_ref} {client_name}/{type_plural}/{date} {type_label} {key}.pdf`. A clash gets " (2)", and a missing date becomes "undated".
- **Alternatives considered:** One flat folder; folders by box.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 61. Safe filenames and the database as the source of truth
- **Decision:** Characters Windows can't use are replaced or trimmed. The database records each PDF's path, and a missing file shows "The PDF file is missing" instead of crashing.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Retention and disposal (§5.8–§5.9, §3.6)

### 62. Keep-until counts from the document's own date
- **Decision:** Each type says which date is its trigger date.
- **Alternatives considered:** Upload date; date plus event triggers.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 63. Keep-until is the date plus a number of years
- **Decision:** Invoice 6 years, Letter 3 years, stated as illustrative. No rounding to the end of a financial or tax year.
- **Alternatives considered:** The interview options described rules counted from the end of the financial or tax year.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 64. 29 February becomes 28 February
- **Decision:** A leap-day date plus whole years lands on 28 February.
- **Alternatives considered:** Not discussed. Rolling forward to 1 March would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 65. No date: keep-until "not set"
- **Decision:** Filed with a "No date" marker; never Due, so never destroyed early; the filename uses "undated".
- **Alternatives considered:** Fall back to the upload date; can't file without a date (my original leaning).
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 66. "Due" is worked out, not a state
- **Decision:** A record is Due when today is after its keep-until date; it is kept through that day.
- **Alternatives considered:** Not discussed. A Due state set by a scheduled job would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 67. Due list, bin, and a separate confirmation to empty it
- **Decision:** "Due for disposal" lists records; "Move to bin" moves them; the bin allows restore; "Empty bin" needs a separate confirmation page.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 68. Bin rules
- **Decision:** Only Due documents can be moved to the bin. Restoring puts a document back at its calculated path. The confirmation form carries the exact ids, so only the items listed are destroyed.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 69. Keep a disposal record
- **Decision:** Emptying the bin leaves proof of what was destroyed and when.
- **Alternatives considered:** Delete everything; soft-delete only.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 70. Destruction deletes everything except the disposal record
- **Decision:** The PDF, page photos and thumbnails, OCR text, fingerprints, and the Document, Page and StateChange rows are all deleted.
- **Alternatives considered:** Deleting the files but keeping the database rows and fingerprints (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 71. Disposal record fields
- **Decision:** Filed name, type label, client ref and name, document date, keep-until, page count, binned at and destroyed at.
- **Alternatives considered:** Not discussed (I asked Claude to choose the fields).
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 72. Legal note
- **Decision:** Due for disposal, Bin, Empty bin and the README say the keep-until dates come from example rules, and to check whether a digital copy may replace the paper.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 73. Legal hold and the disposal log screen are should tier
- **Decision:** Both are in §11.9.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Lifecycle code (§3.6–§3.7)

### 74. Lifecycles are enforced in code for pages and documents
- **Decision:** State is never set directly; every change goes through `apply(action)`.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 75. A hand-written state machine
- **Decision:** `Lifecycle` holds a transition table; a `Stateful` mixin gives a read-only `state`, `allowed_actions()` and `apply()`; guards are `guard_<action>()` methods that raise `InvalidTransition` with a plain-words reason.
- **Alternatives considered:** Not discussed. A state-machine library would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 76. The server checks every action
- **Decision:** Pages only show buttons for allowed actions, but every form submission is checked again and refused with a friendly message if not allowed.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 77. Every transition writes a history row
- **Decision:** A StateChange row is written for each transition. Showing the history on a document's page is should tier.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 78. Dates are passed in, not read from the clock
- **Decision:** Functions take `now` / `today` as arguments, so tests can fix the date.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Screens (§4)

### 79. Simple server-rendered pages, plain words, large buttons
- **Decision:** Flask renders each page; wording is plain and buttons are large.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 80. No JavaScript at all
- **Decision:** Only HTML forms, not just no JavaScript framework.
- **Alternatives considered:** Not discussed. My brief ruled out a framework, not all JavaScript.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 81. Design rules
- **Decision:** Base font 20px, buttons at least 48px tall, high contrast, one main action per screen, and every destructive action on its own confirmation page.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 82. The ten must-tier screens
- **Decision:** Home, Upload, Inbox, Needs checking, Check document, Document, Filed documents, Due for disposal, Bin and Empty bin – confirm. The PDF is shown in the browser's own viewer, and messages appear in a banner.
- **Alternatives considered:** The interview draft's 15 screens.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 83. Filed documents list in the must tier; filters and search in the should tier
- **Decision:** A plain table of filed documents is must; filters and text search are in §11.9.
- **Alternatives considered:** Filters in the must tier (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

---

## Technical decisions (§7)

### 84. Flask and Jinja2
- **Decision:** One function per URL returning an HTML template.
- **Alternatives considered:** FastAPI + Jinja2; Django.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 85. SQLite and SQLAlchemy
- **Decision:** One database file; classes are saved and loaded by SQLAlchemy, with default settings and one session per request.
- **Alternatives considered:** SQLite with plain `sqlite3`; JSON files.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 86. uv, ruff and pytest, with the src layout and a data folder
- **Decision:** Python 3.13 pinned in `.python-version`; `pyproject.toml` and a committed `uv.lock`; every command runs with `uv run`. Code in `src/docmanager/`; files and the database in `data/`, kept out of git.
- **Alternatives considered:** pip with requirements.txt, black and flake8; Poetry.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 87. Friendly messages for the user, details in a log
- **Decision:** The user never sees a crash; technical detail goes to a log file.
- **Alternatives considered:** Part of the "Background worker" option.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:**

### 88. How errors are handled in code
- **Decision:** Domain exceptions (`InvalidTransition`, `UploadRefused`, `GroupingError`) carry plain-words messages shown in a banner; custom 404 and 500 pages; a rotating log at `data/logs/app.log`.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 89. Pillow for images
- **Decision:** 400px thumbnails and drawing the demo photos.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 90. Settings in one place
- **Decision:** Thresholds, the naming template and the OCR timeout are constants in `config.py`. The data folder can be moved with `DOCMANAGER_DATA`.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 91. Ruff rules and commit checks
- **Decision:** Ruff's default rules plus import sorting. Tests and ruff must be clean before each commit; commit at the end of each sitting.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 92. Commands
- **Decision:** `uv run docmanager` serves the app and `uv run docmanager seed` fills the demo. Claude added `seed --reset` and `make-photos OUT_DIR`.
- **Alternatives considered:** Not discussed beyond the run and seed commands in the uv option.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 93. One demo photo generator
- **Decision:** It draws plain typed text on white images, with a plain black image for each lens cover. The seed script reuses it.
- **Alternatives considered:** Realistic page drawings with EXIF data, separate from the seed script (the earlier drafts).
- **Who chose:** Me
- **Why I agreed:**

---

## Constraints (§8)

### 94. Localhost only
- **Decision:** The server binds `127.0.0.1:5000`, fixed in code, with no logins.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 95. Cross-site form protections are should tier
- **Decision:** The form token and Host-header check are in §11.8. The spec states the risk until then.
- **Alternatives considered:** Both in the must tier (the interview draft).
- **Who chose:** Me
- **Why I agreed:**

### 96. Only made-up data
- **Decision:** All documents are generated by the code, with made-up names and `C-0000` refs. The repo never contains a `data/` folder.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me
- **Why I agreed:**

### 97. No real organisation imitated
- **Decision:** Generated documents don't use any real organisation's name or branding.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Tests (§6)

### 98. Acceptance tests for "Paper can go" and "Not a page"
- **Decision:** Pass/fail tests for "Paper can go" shown and not shown (photo in the inbox, document needing checking, OCR error), and for "Not a page" and restore.
- **Alternatives considered:** None.
- **Who chose:** Me
- **Why I agreed:**

### 99. How the tests are run
- **Decision:** pytest in `tests/`. Slow tests that run real OCR are marked `ocr` and skipped if the tools are missing; the rest use stored text and a fake OCR. Two manual checks: the demo script on a fresh clone, and 200% browser zoom.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 100. The localhost and no-network rules are tested
- **Decision:** One test checks the app binds only to 127.0.0.1; another scans templates and static files for `http(s)://` URLs.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

---

## Build order and demo (§9–§10)

### 101. Build in priority order, with a demo line after (d)
- **Decision:** (a) foundation; (b) upload, inbox, grouping and Not a page; (c) OCR, classification and filing; (d) review and Paper can go; then the demo line; (e) retention and destruction; (f) seed script and README.
- **Alternatives considered:** The earlier build orders, which followed the spec's sections.
- **Who chose:** Me
- **Why I agreed:**

### 102. The seed script creates the demo clients in sitting (c)
- **Decision:** Without clients nothing can be filed at the demo line, so `seed` makes the clients in (c) and is extended in (f).
- **Alternatives considered:** Building the whole seed script in (f), which would leave nothing fileable at the demo line.
- **Who chose:** Proposed by Claude
- **Why I agreed:**

### 103. Demo script works at the demo line
- **Decision:** Steps 1–7 (upload, Not a page, grouping, a refusal, filed documents, Needs checking, Paper can go) work after (d). Steps 8–9 are marked as needing (e) and (f).
- **Alternatives considered:** A demo script that needs the whole must tier (the earlier drafts).
- **Who chose:** Me
- **Why I agreed:**

### 104. Should-tier work waits for the must tier
- **Decision:** Should-tier work starts only after AT-01 to AT-23 pass.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:**
