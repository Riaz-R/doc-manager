# Decisions log

One entry per decision in [SPEC.md](SPEC.md), grouped in the order of the spec.
Last updated 2026-10-27.

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
- **Alternatives considered:** Treating "paper destroyed" as the last step of a box lifecycle (now in the should tier, §11.2).
- **Who chose:** Me
- **Why I agreed:** The core of the product is to free up physical space by digitising the documents and so shredding the paper should never be gated behind the "keep-until" date unless the physical copy is explicitly required. The "paper destroyed" lifecycle state has been scoped out in the interest of time as it is non-critical.

### 2. Users
- **Decision:** The primary user is my dad, with boxes of client files. A similar user is a small local business owner. The demo audience is interviewers for roles that configure object models, lifecycles and workflows.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 3. Typical workflow, with the lens-cover tip
- **Decision:** Photograph each document's pages in order, covering the lens for one photo between documents. Mark those photos "Not a page", group the rest, shred the box's paper when Home shows "Paper can go", and destroy expired records later as a separate step.
- **Alternatives considered:** The interview draft's workflow, where shredding waited for the box lifecycle's confirmation step.
- **Who chose:** Me

### 4. Must tier cut to the core demo path
- **Decision:** The must tier covers only upload, inbox, grouping, Not a page, OCR, classification, review, naming and filing, Paper can go, retention, disposal of digital records, lifecycles, seed script, README and localhost binding. Everything else is in the should tier.
- **Alternatives considered:** The interview draft's must tier, estimated at 515 minutes. The second draft's must tier, estimated at 380 minutes.
- **Who chose:** Me

### 5. Known limitations are written down
- **Decision:** The spec lists what the must tier can't do yet: a client not in the register can't be filed, a phone counter rollover puts photos in the wrong order, and a long document holds the browser page until OCR finishes.
- **Alternatives considered:** Leaving the limitations unstated.
- **Who chose:** Proposed by Claude
- **Why I agreed:** The limitations would hinder use in practise; for the moment, the product is currently only a demo and so relevant example documents can be generated ahead of time and the program does not need to concern itself with edge cases

### 6. Stretch: QR separator sheets and a settings page for the naming template
- **Decision:** Both are stretch, not this build. The naming template is a constant in code until then.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 7. Stretch: importing clients from a CSV file
- **Decision:** Client import is stretch.
- **Alternatives considered:** "Register + CSV import" was offered in the interview; I chose the register without import.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 8. Stretch: event-based retention
- **Decision:** A "Client agreement" type, kept 6 years after the client leaves, is stretch. It needs a "left on" date on Client.
- **Alternatives considered:** "Client agreement" and "Date + event triggers" were offered in the interview; I didn't choose them.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 9. Roadmap: sorting loose pages
- **Decision:** Sorting pages that are neither grouped nor in order is roadmap only.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 10. Roadmap: Windows installer, backups and export, multiple users
- **Decision:** A Windows shortcut or installer, backups and export, and multiple users with logins and sign-off on disposal are roadmap only.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 11. Roadmap: checking each PDF before a box's paper can go
- **Decision:** Requiring the user to check each document's PDF before "Paper can go" is roadmap only.
- **Alternatives considered:** "Guard + page check" was offered in the interview (as a should); I chose the box guard without it.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 12. Out of scope from my brief
- **Decision:** No network access at runtime, no AI at runtime, no real client data, and no logins.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 13. Other things out of scope
- **Decision:** Editing PDF contents, annotations, versioning, and the legal accuracy of the retention rules are out of scope.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 14. All should-tier detail in one section
- **Decision:** Should-tier details live in §11, with a one-line pointer in each section.
- **Alternatives considered:** Should-tier details spread through each section (the earlier drafts).
- **Who chose:** Me

---

## Boxes, batches and photos (§3.1–§3.3, §5.1–§5.3)

### 15. A box holds many uploads
- **Decision:** A Box is the physical box. Each upload is a Batch into a new or existing box.
- **Alternatives considered:** One upload = one box (my original leaning); no boxes at all.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 16. Batches record their counts
- **Decision:** Each batch stores how many photos were added, skipped and refused, and shows them after upload.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 17. Box names are unique, 1–60 characters
- **Decision:** A second box with the same name is refused with "There is already a box called Box 1".
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 18. No box lifecycle in the must tier
- **Decision:** The box lifecycle (Open, Complete, PaperDestroyed), the "I have destroyed the paper" confirmation, the Boxes and Box detail screens, and automatic reopening are should tier.
- **Alternatives considered:** "Box lifecycle with guard" (accepted in the interview); "Just show counts".
- **Who chose:** Me

### 19. "Paper can go" marker on each box
- **Decision:** Worked out, not stored. Shown on Home when the box has at least one document, no photos in its inbox, and every document filed. When it isn't shown, Home says what is blocking it.
- **Alternatives considered:** The box lifecycle's Complete state; just showing counts.
- **Who chose:** Me

### 20. "Paper can go" details
- **Decision:** Documents later moved to the bin still count as filed. A document not read yet also blocks it. A box with nothing filed shows "Nothing filed from this box yet". The lines come from `box.paper_blockers()`.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 21. The same photo can't be uploaded twice
- **Decision:** A duplicate photo is skipped and reported.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 22. Duplicates are found by SHA-256 of the exact bytes
- **Decision:** The fingerprint is unique among pages currently in the app, including within a single upload.
- **Alternatives considered:** Not discussed. Other options would be matching by filename or by how similar the images look.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 23. A destroyed photo can be uploaded again
- **Decision:** Emptying the bin deletes the fingerprints, so the same photo can be added again later.
- **Alternatives considered:** Keeping fingerprints so destroyed photos stay blocked (the interview draft).
- **Who chose:** Me

### 24. JPEG and PNG only; HEIC refused with a hint
- **Decision:** iPhone HEIC photos are refused with the setting to change on the phone. HEIC support is should tier.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 25. Refused files are named; the rest still upload
- **Decision:** A non-photo or corrupt file is refused by name, and the other photos are still added.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 26. Uploads up to 500 MB
- **Decision:** Above 500 MB, the user is told to upload in parts into the same box.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 27. Uploaded files are named by their fingerprint
- **Decision:** Photos are stored under their sha256, never their uploaded name. The original filename is for display and ordering only.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 28. Inbox ordered by filename; EXIF order in the should tier
- **Decision:** A box's photos sort by filename. Ordering by the EXIF time taken is should tier.
- **Alternatives considered:** "EXIF time, then name" (recommended in the interview); upload order.
- **Who chose:** Me

### 29. Turning rotated photos the right way up is should tier
- **Decision:** Thumbnails and PDF pages follow the photo as stored. EXIF orientation handling is in §11.9.
- **Alternatives considered:** Correcting rotation in the must tier (the earlier drafts).
- **Who chose:** Me

### 30. "Not a page" in the must tier
- **Decision:** Marked photos leave the inbox and go to the bin. They can be restored, don't block "Paper can go", and are deleted when the bin is emptied, with no disposal record.
- **Alternatives considered:** In the interview I accepted the "Not a page" button, then moved it to should, then back. The other interview options were leaving the photos in the inbox or deleting them immediately.
- **Who chose:** Me

### 31. Page lifecycle states
- **Decision:** Inbox ("To sort"), Grouped ("In a document") and Discarded ("Not a page (in bin)"), with the transitions upload, group, discard, restore and destroy.
- **Alternatives considered:** Not discussed (my brief asked for enforced page lifecycles, not specific states).
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 32. Group by picking the first and last photo
- **Decision:** Consecutive photos become one document; grouped photos leave the inbox.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 33. Grouping rules
- **Decision:** First and Last are swapped if reversed; both must be picked; a range that includes a grouped photo is refused; "Not a page" photos inside a range are skipped; a one-page document is allowed.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 34. Ungroup is should tier
- **Decision:** Ungrouping a document is in §11.3.
- **Alternatives considered:** Ungrouping while a document is "Needs checking" or "Couldn't read" (the interview draft).
- **Who chose:** Me

### 35. Dark-photo proposals (should tier): propose, user confirms
- **Decision:** Runs of photos between dark lens-cover photos are proposed as documents. The user confirms, adjusts or ignores each one.
- **Alternatives considered:** Auto-group with no confirmation; two dark photos in a row mark a new box.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 36. Dark-photo thresholds
- **Decision:** A photo is dark when its greyscale mean is below 25/255 and its standard deviation below 12, both config constants.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Documents and document types (§3.4)

### 37. A Document holds a swappable DocumentType
- **Decision:** A `DocumentType` base class with one subclass per type; each overrides `score(text)` and `retention_years`. A Document stores its type's key, and `change_type()` swaps the type on the same document, re-extracting fields and recalculating keep-until.
- **Alternatives considered:** A Document base class with one subclass per type (my brief); single-table inheritance with a `retype()` function (the interview draft).
- **Who chose:** Me

### 38. Invoice and Letter in the must tier; Bank statement in the should tier
- **Decision:** `InvoiceType` and `LetterType` are built first; `BankStatementType` is in §11.9.
- **Alternatives considered:** Invoice, Bank statement and Tax return (accepted in the interview); Client agreement; Invoice, Letter and Bank statement (my first edit).
- **Who chose:** Me

### 39. Fields and filename keys for each type
- **Decision:** Invoice: invoice number and amount (stored in pence), keyed by invoice number. Letter: subject from a "Re:" line, keyed by its first 40 characters.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 40. A document with no type is "Unclassified" and can't be filed
- **Decision:** `doc_type` is null until a type is chosen.
- **Alternatives considered:** Stated in the interview's document-types question but not offered as a choice.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 41. Document lifecycle states
- **Decision:** Grouped ("Not read yet" / "Couldn't read"), NeedsReview ("Needs checking"), Filed and InBin, with the transitions group, file, flag, confirm, dispose, restore and destroy.
- **Alternatives considered:** Not discussed (my brief asked for enforced document lifecycles, not specific states).
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## OCR (§5.4, §7)

### 42. Local OCR with OCRmyPDF and Tesseract
- **Decision:** Each document becomes a searchable PDF, made entirely on this computer.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 43. OCR runs while the page waits; background worker is should tier
- **Decision:** OCR runs during the "Make document" request. The background worker, auto-refresh and SQLite WAL mode are in §11.1.
- **Alternatives considered:** "Background worker" (accepted in the interview); "Separate process command".
- **Who chose:** Me
- **Why I agreed:** Building a background worker would have inflated the development timeline by more than double its current length.

### 44. A failed OCR keeps the document Grouped, with an error and Retry
- **Decision:** No Failed state: the document stays Grouped with `ocr_error` and a Retry button.
- **Alternatives considered:** A Failed state in the document lifecycle (the interview draft).
- **Who chose:** Me

### 45. An interrupted read is shown with Retry
- **Decision:** A Grouped document with no text and no error (the app stopped mid-read) is listed with Retry.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 46. How OCR is run
- **Decision:** Photos are combined with `img2pdf`, then OCRmyPDF runs as a subprocess with `-l eng --rotate-pages --deskew --sidecar` and a 5-minute timeout. `--rotate-pages` stays, so sideways pages are still read correctly.
- **Alternatives considered:** Not discussed. Calling OCRmyPDF as a Python library would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 47. Missing OCR programs are checked at start-up
- **Decision:** Tesseract (with `eng` and `osd` data) and Ghostscript come from apt. If one is missing, the app says which and how to install it, and exits.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Clients (§3.5)

### 48. A client register with C-0000 refs
- **Decision:** Clients are matched against a register, not guessed from text.
- **Alternatives considered:** Free text from OCR; register with CSV import.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 49. Clients come only from the seed script in the must tier
- **Decision:** The clients screen and adding a client from review are should tier.
- **Alternatives considered:** A clients screen and inline "add client" in the must tier (the interview draft).
- **Who chose:** Me

### 50. Match by C-0000 reference or exact name only; aliases are should tier
- **Decision:** A ref is tried first, then the client's exact name.
- **Alternatives considered:** Matching names and aliases (part of the register accepted in the interview).
- **Who chose:** Me

### 51. Name matching ignores case and needs the whole phrase; names are unique
- **Decision:** "smith ltd" matches "Smith Ltd", but "Smith" alone doesn't. Two clients can't share a name.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Classification and review (§5.5)

### 52. Plain rules, no AI at runtime
- **Decision:** Each type's `score()` and regular expressions decide type, client and date.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 53. The type must clear a minimum score and beat the runner-up by a margin
- **Decision:** Each type scores the text; the top score must clear a threshold and beat the next type by a margin.
- **Alternatives considered:** Part of the "All three checks pass" option. The others were "Review everything" and "Type score only".
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 54. Scoring defaults and helper
- **Decision:** `MIN_TYPE_SCORE` 6 and `MIN_TYPE_MARGIN` 3; a `keyword_score(text, weights)` helper on the base class.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 55. Filing needs a clear type and a matched client; the date doesn't block
- **Decision:** A document is filed automatically when the type and client checks pass. A missing date gets the "No date" marker instead.
- **Alternatives considered:** All three checks, including the date (recommended in the interview); review everything; type score only.
- **Who chose:** Me

### 56. Review is a marker that never blocks
- **Decision:** Flagged documents get "Needs checking" and can be checked now or later. The inbox banner and Home tile show the count, so they aren't forgotten.
- **Alternatives considered:** Review as a step that must be done before carrying on.
- **Who chose:** Me

### 57. Reasons in plain words
- **Decision:** Every failed check is recorded with a plain-words reason, for example "More than one client matched: Smith Ltd, J Smith & Co".
- **Alternatives considered:** Part of the "All three checks pass" option.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 58. Dates are read in UK day-first formats; future dates are ignored
- **Decision:** `14/03/2021`, `14 March 2021` and `2021-03-14` are read. Dates after today are treated as misreads.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 59. Review extras are should tier
- **Decision:** "Save for later", adding a client from review, and correcting after filing are in §11.4.
- **Alternatives considered:** All three in the must tier (the interview draft).
- **Who chose:** Me

---

## Naming and filing (§5.6)

### 60. Client and type folders
- **Decision:** `{client_ref} {client_name}/{type_plural}/{date} {type_label} {key}.pdf`. A clash gets " (2)", and a missing date becomes "undated".
- **Alternatives considered:** One flat folder; folders by box.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 61. Safe filenames and the database as the source of truth
- **Decision:** Characters Windows can't use are replaced or trimmed. The database records each PDF's path, and a missing file shows "The PDF file is missing" instead of crashing.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Retention and disposal (§5.8–§5.9, §3.6)

### 62. Keep-until counts from the document's own date
- **Decision:** Each type says which date is its trigger date.
- **Alternatives considered:** Upload date; date plus event triggers.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 63. Keep-until is the date plus a number of years
- **Decision:** Invoice 6 years, Letter 3 years, stated as illustrative. No rounding to the end of a financial or tax year.
- **Alternatives considered:** The interview options described rules counted from the end of the financial or tax year.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 64. 29 February becomes 28 February
- **Decision:** A leap-day date plus whole years lands on 28 February.
- **Alternatives considered:** Not discussed. Rolling forward to 1 March would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 65. No date: keep-until "not set"
- **Decision:** Filed with a "No date" marker; never Due, so never destroyed early; the filename uses "undated".
- **Alternatives considered:** Fall back to the upload date; can't file without a date (my original leaning).
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 66. "Due" is worked out, not a state
- **Decision:** A record is Due when today is after its keep-until date; it is kept through that day.
- **Alternatives considered:** Not discussed. A Due state set by a scheduled job would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 67. Due list, bin, and a separate confirmation to empty it
- **Decision:** "Due for disposal" lists records; "Move to bin" moves them; the bin allows restore; "Empty bin" needs a separate confirmation page.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 68. Bin rules
- **Decision:** Only Due documents can be moved to the bin. Restoring puts a document back at its calculated path. The confirmation form carries the exact ids, so only the items listed are destroyed.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 69. Keep a disposal record
- **Decision:** Emptying the bin leaves proof of what was destroyed and when.
- **Alternatives considered:** Delete everything; soft-delete only.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 70. Destruction deletes everything except the disposal record
- **Decision:** The PDF, page photos and thumbnails, OCR text, fingerprints, and the Document, Page and StateChange rows are all deleted.
- **Alternatives considered:** Deleting the files but keeping the database rows and fingerprints (the interview draft).
- **Who chose:** Me

### 71. Disposal record fields
- **Decision:** Filed name, type label, client ref and name, document date, keep-until, page count, binned at and destroyed at.
- **Alternatives considered:** Not discussed (I asked Claude to choose the fields).
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 72. Legal note
- **Decision:** Due for disposal, Bin, Empty bin and the README say the keep-until dates come from example rules, and to check whether a digital copy may replace the paper.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 73. Legal hold and the disposal log screen are should tier
- **Decision:** Both are in §11.9.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Lifecycle code (§3.6–§3.7)

### 74. Lifecycles are enforced in code for pages and documents
- **Decision:** State is never set directly; every change goes through `apply(action)`.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 75. A hand-written state machine
- **Decision:** `Lifecycle` holds a transition table; a `Stateful` mixin gives a read-only `state`, `allowed_actions()` and `apply()`; guards are `guard_<action>()` methods that raise `InvalidTransition` with a plain-words reason.
- **Alternatives considered:** Not discussed. A state-machine library would be the other option.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 76. The server checks every action
- **Decision:** Pages only show buttons for allowed actions, but every form submission is checked again and refused with a friendly message if not allowed.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 77. Every transition writes a history row
- **Decision:** A StateChange row is written for each transition. Showing the history on a document's page is should tier.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 78. Dates are passed in, not read from the clock
- **Decision:** Functions take `now` / `today` as arguments, so tests can fix the date.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Screens (§4)

### 79. Simple server-rendered pages, plain words, large buttons
- **Decision:** Flask renders each page; wording is plain and buttons are large.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 80. No JavaScript at all
- **Decision:** Only HTML forms, not just no JavaScript framework.
- **Alternatives considered:** Not discussed. My brief ruled out a framework, not all JavaScript.
- **Who chose:** Proposed by Claude
- **Why I agreed:** Added complexity in coding set up and unfamiliar languages would be introduced in a limited-time bound project. The core of the product did not necessesitate the features that javascript would add (though a progress bar when pressing "make docuemtent" would probably be appreciated by the user if it takes long so that they know the system is working and not broken).

### 81. Design rules
- **Decision:** Base font 20px, buttons at least 48px tall, high contrast, one main action per screen, and every destructive action on its own confirmation page.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 82. The ten must-tier screens
- **Decision:** Home, Upload, Inbox, Needs checking, Check document, Document, Filed documents, Due for disposal, Bin and Empty bin – confirm. The PDF is shown in the browser's own viewer, and messages appear in a banner.
- **Alternatives considered:** The interview draft's 15 screens.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 83. Filed documents list in the must tier; filters and search in the should tier
- **Decision:** A plain table of filed documents is must; filters and text search are in §11.9.
- **Alternatives considered:** Filters in the must tier (the interview draft).
- **Who chose:** Me

---

## Technical decisions (§7)

### 84. Flask and Jinja2
- **Decision:** One function per URL returning an HTML template.
- **Alternatives considered:** FastAPI + Jinja2; Django.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** Flask was used as it works well with Jinja2 and SQLAlchemy and is well established with lots of documentation (so it will work well with AI coding tools) and it runs lean which makes developing an MVP a smoother/faster experience. It also has features built in that suited the project such as a test client for the acceptance test, simple form handling and flash for plain words messages. For small and old business owners, Flask does the job with no extra fuss.

### 85. SQLite and SQLAlchemy
- **Decision:** One database file; classes are saved and loaded by SQLAlchemy, with default settings and one session per request.
- **Alternatives considered:** SQLite with plain `sqlite3`; JSON files.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 86. uv, ruff and pytest, with the src layout and a data folder
- **Decision:** Python 3.13 pinned in `.python-version`; `pyproject.toml` and a committed `uv.lock`; every command runs with `uv run`. Code in `src/docmanager/`; files and the database in `data/`, kept out of git.
- **Alternatives considered:** pip with requirements.txt, black and flake8; Poetry.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** The project is pinned with the correct versions and dependencies without much set up faf like with venv and anyone who clones the repo for use/instals the program will have the correct version automatically. Ruff keeps the code clean and maintanable, pytest makes sure the code does what it intends to, and src layout ensures documents generated during testing don't accidentally make it to the final github repo as bloat or potential compromise of personal data.

### 87. Friendly messages for the user, details in a log
- **Decision:** The user never sees a crash; technical detail goes to a log file.
- **Alternatives considered:** Part of the "Background worker" option.
- **Who chose:** Claude's recommendation, which I accepted in the interview
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 88. How errors are handled in code
- **Decision:** Domain exceptions (`InvalidTransition`, `UploadRefused`, `GroupingError`) carry plain-words messages shown in a banner; custom 404 and 500 pages; a rotating log at `data/logs/app.log`.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 89. Pillow for images
- **Decision:** 400px thumbnails and drawing the demo photos.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 90. Settings in one place
- **Decision:** Thresholds, the naming template and the OCR timeout are constants in `config.py`. The data folder can be moved with `DOCMANAGER_DATA`.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 91. Ruff rules and commit checks
- **Decision:** Ruff's default rules plus import sorting. Tests and ruff must be clean before each commit; commit at the end of each sitting.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 92. Commands
- **Decision:** `uv run docmanager` serves the app and `uv run docmanager seed` fills the demo. Claude added `seed --reset` and `make-photos OUT_DIR`.
- **Alternatives considered:** Not discussed beyond the run and seed commands in the uv option.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 93. One demo photo generator
- **Decision:** It draws plain typed text on white images, with a plain black image for each lens cover. The seed script reuses it.
- **Alternatives considered:** Realistic page drawings with EXIF data, separate from the seed script (the earlier drafts).
- **Who chose:** Me

---

## Constraints (§8)

### 94. Localhost only
- **Decision:** The server binds `127.0.0.1:5000`, fixed in code, with no logins.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 95. Cross-site form protections are should tier
- **Decision:** The form token and Host-header check are in §11.8. The spec states the risk until then.
- **Alternatives considered:** Both in the must tier (the interview draft).
- **Who chose:** Me

### 96. Only made-up data
- **Decision:** All documents are generated by the code, with made-up names and `C-0000` refs. The repo never contains a `data/` folder.
- **Alternatives considered:** None discussed; set in my brief.
- **Who chose:** Me

### 97. No real organisation imitated
- **Decision:** Generated documents don't use any real organisation's name or branding.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Tests (§6)

### 98. Acceptance tests for "Paper can go" and "Not a page"
- **Decision:** Pass/fail tests for "Paper can go" shown and not shown (photo in the inbox, document needing checking, OCR error), and for "Not a page" and restore.
- **Alternatives considered:** None.
- **Who chose:** Me

### 99. How the tests are run
- **Decision:** pytest in `tests/`. Slow tests that run real OCR are marked `ocr` and skipped if the tools are missing; the rest use stored text and a fake OCR. Two manual checks: the demo script on a fresh clone, and 200% browser zoom.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 100. The localhost and no-network rules are tested
- **Decision:** One test checks the app binds only to 127.0.0.1; another scans templates and static files for `http(s)://` URLs.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Build order and demo (§9–§10)

### 101. Build in priority order, with a demo line after (d)
- **Decision:** (a) foundation; (b) upload, inbox, grouping and Not a page; (c) OCR, classification and filing; (d) review and Paper can go; then the demo line; (e) retention and destruction; (f) seed script and README.
- **Alternatives considered:** The earlier build orders, which followed the spec's sections.
- **Who chose:** Me

### 102. The seed script creates the demo clients in sitting (c)
- **Decision:** Without clients nothing can be filed at the demo line, so `seed` makes the clients in (c) and is extended in (f).
- **Alternatives considered:** Building the whole seed script in (f), which would leave nothing fileable at the demo line.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

### 103. Demo script works at the demo line
- **Decision:** Steps 1–7 (upload, Not a page, grouping, a refusal, filed documents, Needs checking, Paper can go) work after (d). Steps 8–9 are marked as needing (e) and (f).
- **Alternatives considered:** A demo script that needs the whole must tier (the earlier drafts).
- **Who chose:** Me

### 104. Should-tier work waits for the must tier
- **Decision:** Should-tier work starts only after AT-01 to AT-23 pass.
- **Alternatives considered:** Not discussed.
- **Who chose:** Proposed by Claude
- **Why I agreed:** <span style="color: #F5A623">Took the recommendation</span>

---

## Added with the build plan

### 105. Very little text read: flag the document for checking
- **Decision:** After OCR, a document with fewer than `MIN_OCR_WORDS` words (default 20, in `config.py`) is flagged Needs checking with the reason "Very little text was read. Check the photos are clear before shredding the paper." This is the first check in §5.5, and it adds a third condition to automatic filing (decision 55). Behaviour C11, tested in AT-11.
- **Alternatives considered:** Filing on the type and client checks alone, as in decision 55.
- **Who chose:** Me
- **Why I agreed:**

---

## How this project is built

### 106. Spec written by Opus at high effort after a multiple-choice interview
- **Decision:** SPEC.md was written by Claude Opus at high effort, after an interview in which Claude asked me multiple-choice questions.
- **Alternatives considered:** Writing the spec myself; an open-ended conversation instead of multiple-choice questions.
- **Who chose:** Me
- **Why I agreed:**

### 107. Plan written in plan mode with opusplan; building at medium effort
- **Decision:** PLAN.md was written in plan mode with the `opusplan` model setting: Opus plans, Sonnet builds. Building runs at medium effort.
- **Alternatives considered:** Opus for both planning and building; Sonnet for both; a higher effort for building.
- **Who chose:** Me
- **Why I agreed:**

### 108. Context cleared between phases
- **Decision:** The conversation is cleared between phases. The project files (SPEC.md, DECISIONS.md, PLAN.md, CLAUDE.md) carry everything across.
- **Alternatives considered:** One long conversation, relying on automatic compaction.
- **Who chose:** Me
- **Why I agreed:**

### 109. No MCP servers for this build
- **Decision:** The build uses no MCP servers. There is nothing external to connect, the `gh` command-line tool covers GitHub, and each server adds context overhead.
- **Alternatives considered:** Connecting MCP servers during the build, for example a GitHub server.
- **Who chose:** Me
- **Why I agreed:**

### 110. Pushes are blocked by an enforced rule, not an instruction
- **Decision:** `.claude/settings.json` denies `Bash(git push *)`, so Claude cannot push even if it tries. CLAUDE.md's "Never run `git push`" line stays as a reminder, but the rule is what enforces it.
- **Alternatives considered:** Relying on the CLAUDE.md instruction alone.
- **Who chose:** Me
- **Why I agreed:**

### 111. Task 1: no README until Task 25, so `readme` is left out of pyproject.toml
- **Decision:** `uv init` points `pyproject.toml` at a `README.md`, which doesn't exist until Task 25. I deleted the generated README and removed the `readme` line, because the build fails without the file.
- **Alternatives considered:** Keeping a placeholder README.md until Task 25.
- **Who chose:** Claude
- **Why I agreed:**

### 112. Task 1: `debug=False` is passed explicitly, and the ruff rule set is spelled `extend-select`
- **Decision:** The `docmanager` command calls `app.run(host="127.0.0.1", port=5000, debug=False)`, so the test checks debug is off too (plan decision 1 says debug stays off). Ruff uses `extend-select = ["I"]`, which keeps Ruff's default rules and adds import sorting.
- **Alternatives considered:** Leaving `debug` out, since Flask's default is already off; listing the default rules by hand in `select`.
- **Who chose:** Claude
- **Why I agreed:**

### 113. The /task skill was written from a prompt that already worked
- **Decision:** `.claude/skills/task/SKILL.md` (started with `/task <number>`) reuses, word for word, the prompt that built Task 1 successfully, with `$ARGUMENTS` for the task number. It has `disable-model-invocation: true`, so only I can start it, because it ends in a commit.
- **Alternatives considered:** Typing the prompt out each time; writing a new, longer skill before trying it on a second task.
- **Who chose:** Me
- **Why I agreed:**

### 114. Formatting is enforced by a hook, not an instruction
- **Decision:** A `PostToolUse` hook in `.claude/settings.json` runs `.claude/hooks/format-python.sh` after every Edit or Write. For a `.py` file it runs `uv run ruff format` and `uv run ruff check --fix` on it. I proved it by making a deliberate mistake (`PORT=5000` and an unused `import os`); the file came back fixed. The task loop's own ruff step stays as a final check.
- **Alternatives considered:** A line in CLAUDE.md asking Claude to format; relying on the task loop's ruff step alone.
- **Who chose:** Me
- **Why I agreed:**

### 115. Task 2: a `UserFacingError` base class for plain-words refusals
- **Decision:** `errors.py` holds `UserFacingError`. The one error handler flashes any `UserFacingError` and sends the user back to the page they came from. `InvalidTransition` (Task 3), `UploadRefused` (Task 5) and `GroupingError` (Task 7) will each be a kind of `UserFacingError`. The plan lists the three errors but not a shared parent.
- **Alternatives considered:** Registering the handler once per error class as each is written; catching plain `Exception` and showing its text.
- **Who chose:** Claude
- **Why I agreed:**

### 116. Task 2: "back to the page you came from" uses only the path of the Referer
- **Decision:** After a refusal, the app redirects to the path (and query) of the `Referer` header, or to Home if there is none. It never uses the full address.
- **Alternatives considered:** Redirecting to the full `Referer` address; each route naming its own return page.
- **Who chose:** Claude
- **Why I agreed:**

### 117. Task 2: secret key is random on each start; the app logger is shared
- **Decision:** Flask needs a secret key to carry flashed messages in a cookie. The app makes a new random one each start, so a banner still waiting when the app restarts is lost. The log file handler is swapped on each `create_app()` because Flask's logger is shared by every app made in one process (tests make many).
- **Alternatives considered:** A fixed key written in the code; a key saved in the data folder.
- **Who chose:** Claude
- **Why I agreed:**

### 118. Task 2: templates and styles live in `web/`, and an `autouse` test fixture isolates the data folder
- **Decision:** The Flask app is told to look for templates and the stylesheet in `web/templates` and `web/static`, matching the plan's file list. Every test automatically gets `DOCMANAGER_DATA` pointed at a private folder, so a test that calls `create_app()` with no overrides (like the Task 1 command test) can never write a `data/` folder into the project.
- **Alternatives considered:** Each test passing its own folder; relying on `.gitignore` to hide a stray `data/`.
- **Who chose:** Claude
- **Why I agreed:**

### 119. Task 3: how a refusal message is built, and what a "(new)" object is called
- **Decision:** `Lifecycle` is given a noun ("document") and, for each action, an optional phrase ("moved to the bin"), so a refusal reads `This document can't be moved to the bin while it is "Needs checking"`. An action with no phrase reads `can't have "action" applied`. A brand-new object (no state yet) is called "New" in these messages. The enum for each state has a `.label` property, as the plan describes.
- **Alternatives considered:** Building the message from the action name alone (awkward, for example "can't be dispose"); a separate message table kept outside the lifecycle.
- **Who chose:** Claude
- **Why I agreed:**

### 120. Task 3: a move to "(row deleted)" leaves the stored state alone
- **Decision:** When `apply()` makes a move whose target is "(row deleted)" (destroy), it records the StateChange with `to_state` empty but doesn't change the object's own state. A blank state would look like "(new)" and let the object be uploaded or grouped again; the disposal service deletes the row in the same transaction anyway.
- **Alternatives considered:** Setting the state to empty; adding a special "Destroyed" state.
- **Who chose:** Claude
- **Why I agreed:**

### 121. Task 3: `apply()` needs the object to be in a session already
- **Decision:** Calling `apply()` on an object that hasn't been added to a database session raises a plain `RuntimeError` ("Add this object to a session before applying an action"). This is a mistake in the code, not something a user can cause, so it is not a `UserFacingError`. A new object is added to the session first, and `apply()` then flushes it to get its id before writing the history row, as the plan says.
- **Alternatives considered:** Adding the object to a session inside `apply()`.
- **Who chose:** Claude
- **Why I agreed:**

### 122. Task 4: `is_due(today)` is built now, not in Task 21
- **Decision:** The dispose guard has to know whether a document is Due, so `Document.is_due(today)` (Filed, has a keep-until, and today is after it) is written in this task. Task 21 still adds `add_years()`, `keep_until()`, the Due marker on screens and the retention tests, and can reuse it. A document is kept through its keep-until day, as in R4.
- **Alternatives considered:** Writing the check inside the guard and moving it to `is_due` in Task 21.
- **Who chose:** Claude
- **Why I agreed:**

### 123. Task 4: "has been read" means the OCR text isn't empty-handed, and the filing guards check in a fixed order
- **Decision:** A document counts as read when `ocr_text` is set, even if the text is an empty string. Whether there is enough text is the separate low-text check in Task 11. The file and confirm guards report only the first problem, in this order: not read yet, no type, no client. The flag guard checks only that the document was read. Following the plan, the confirm guard also requires "read" (SPEC 3.4 only lists type and client), which is always true for a document that reached Needs checking.
- **Alternatives considered:** Treating empty text as unread; listing every problem at once; leaving "read" out of the confirm guard.
- **Who chose:** Claude
- **Why I agreed:**

### 124. Task 4: only the fields and tables are built now; markers, `type` and `Box` helpers wait for their tasks
- **Decision:** `Box`, `Batch`, `Client`, `Page` and `Document` have every field from SPEC 3, and linked objects can be reached from each other (a box's pages and documents, a document's pages in position order). The plan's other members wait for the tasks that use them: `Document.type` and `change_type()` (Tasks 10 and 14), the "No date" and "Needs checking" markers (Task 15), and `Box.ordered_pages()`, `inbox_pages()`, `paper_blockers()` and `paper_can_go()` (Tasks 6 and 19). `created_at`, `filed_at` and `binned_at` on a document can be empty, as the spec says. Box, Batch and Client `created_at` must be given, so the code passes `now` from the app's clock.
- **Alternatives considered:** Adding the empty markers and `type` now.
- **Who chose:** Claude
- **Why I agreed:**

### 125. Task 4: every (state, action) pair is a separate test, and the spec tables are written out a second time in the test
- **Decision:** AT-01 is a parametrised test: one test per (state, action) pair, including "(new)": 20 for Page (4 starting states × 5 actions) and 35 for Document (5 × 7). A separate test compares each lifecycle table to the spec's rows written out as plain text, so a wrong row in the code can't pass by being copied into the test. I checked the tests can fail by breaking a table row and a guard message on purpose: 5 tests failed, and I put the code back.
- **Alternatives considered:** One loop in a single test; checking the tables only through the pairs.
- **Who chose:** Claude
- **Why I agreed:**

### 126. Task 5: services never commit; `find_or_create_box` takes either a box id or a new name
- **Decision:** `find_or_create_box(session, box_id=..., new_name=..., now=...)` returns the existing box when it is given an id (refusing "That box doesn't exist" for an unknown one), and otherwise makes a new box from the name, trimmed of spaces. `upload_photos` is given the box and the files. Neither commits: the route commits once after both have worked, so a refusal leaves nothing behind. Files are passed as a generator of (filename, bytes), so only one photo's bytes are in memory at a time, which matters for a 500 MB upload.
- **Alternatives considered:** A single `upload_photos` that also finds the box; committing inside the service; reading every file into a list first.
- **Who chose:** Claude
- **Why I agreed:**

### 127. Task 5: wording the plan didn't give, and what counts as "not a photo"
- **Decision:** Choosing no files shows "Choose at least one photo", and no box is made. An unknown box id shows "That box doesn't exist". A corrupt or cut-off JPEG or PNG, and any other kind of file, are listed together as "not a photo", while HEIC files (by `.heic` or `.heif`, any capitalisation) use the HEIC wording from decision 12. A file that is decoded as a different kind of photo from its extension (a PNG named `scan.jpg`) is accepted and stored under its real extension.
- **Alternatives considered:** A separate "damaged photo" wording for corrupt files; trusting the filename's extension.
- **Who chose:** Claude
- **Why I agreed:**

### 128. Task 5: an upload always records a Batch, and the over-size page is a banner on the Upload screen
- **Decision:** Every upload that gets as far as a valid box writes a Batch with its counts, even when every file is skipped or refused (it is the record of what was tried). A too-large upload (HTTP 413) sends the user back to the Upload screen with the banner "That upload is too big for one go. Upload in parts: choose some of the photos, then the rest, into the same box." The limit is Flask's `MAX_CONTENT_LENGTH`, set from `config.MAX_UPLOAD_BYTES` and changeable in tests through the app overrides.
- **Alternatives considered:** Not recording a Batch when nothing was added; a separate error page for 413.
- **Who chose:** Claude
- **Why I agreed:**

### 129. Task 5: Home counts photos to sort with one database query
- **Decision:** Home gets each box's "N photos to sort" from a single grouped query (`boxes_with_inbox_counts`) instead of loading every Page of every box. It writes "1 photo" and "N photos", and "0 photos to sort" for an empty inbox. `Box.inbox_pages()` still waits for Task 6.
- **Alternatives considered:** Counting through `box.pages` in the template.
- **Who chose:** Claude
- **Why I agreed:**

### 130. Task 6: `ordered_pages()` returns (number, page) pairs, and `inbox_pages()` keeps the box-wide numbers
- **Decision:** `Box.ordered_pages()` returns a list of `(number, page)` pairs, numbered from 1 across every photo in the box, whatever its state. `Box.inbox_pages()` is the same list cut down to Inbox photos, so a photo keeps its number when others leave (decision 9). The sort key is a `Page.order_key` property, `(original_filename, id)`, compared as plain text, so `IMG_10` sorts before `IMG_9` and capital letters sort before small ones.
- **Alternatives considered:** Storing the number on the page; returning bare pages and numbering in the template (which would number the inbox 1, 2, 3 again after photos leave).
- **Who chose:** Claude
- **Why I agreed:**

### 131. Task 6: addresses, and the form has no buttons yet
- **Decision:** The Inbox is at `/boxes/<box id>/inbox` (a missing box shows the friendly 404), and thumbnails are at `/pages/<page id>/thumb`. The thumbnail is read from the stored relative path through Flask's `send_from_directory`, which refuses paths that leave the data folder and gives a 404 if the file is gone. Home turns each box name into a link to its inbox. The inbox form has the First, Last and Not a page controls but no submit buttons: Make document comes in Task 7 and Mark as not a page in Task 8. The thumbnails are shown at 400px wide (their real size) and shrink on narrow screens.
- **Alternatives considered:** Adding the buttons now, with routes that do nothing; sending the user to the inbox after an upload.
- **Who chose:** Claude
- **Why I agreed:**

### 132. Fix: the Upload screen's box choice is two radio buttons, and only the selected one is used
- **Decision:** Before, one dropdown held the existing boxes plus a "New box" entry, and the name field beside it was used only when "New box" was picked. So an existing box with a name typed added to the existing box and the typed name was silently ignored. Now the screen has two radio buttons, "Add to an existing box" (with the dropdown of boxes) and "New box" (with the name field). The form sends `choice` as `existing` or `new`, and only the selected option is used: the other field is ignored, even when filled in. "New box" with an empty name gives "Give the new box a name", and a duplicate name gives "There is already a box called …" (B8). With no boxes yet, "New box" is selected and "Add to an existing box" is greyed out; otherwise "Add to an existing box" is selected. Two refusals the rule needed, in new wording: "Choose a box to add the photos to" (existing chosen but no box selected) and "Choose whether to add to an existing box or make a new one" (a form with no valid choice, which only a crafted request can send).
- **Alternatives considered:** Keeping the single dropdown and refusing when both are filled in; using the typed name whenever it isn't empty.
- **Who chose:** Me
- **Why I agreed:**
