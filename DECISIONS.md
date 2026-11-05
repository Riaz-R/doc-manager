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

### 133. Task 7: `make_document` takes the two photos' ids, and the form values are turned into ids in the route
- **Decision:** The Inbox radio buttons carry page ids, so `make_document(session, box, first_page_id, last_page_id, *, now)` takes ids and finds their inbox numbers itself. It returns a `MadeDocument` (the document and its first and last numbers), whose `.message()` gives "Document made from photos 3 to 6", or "Document made from photo 7" for a one-photo document (the plan only gave the plural wording). A form value that isn't a number counts as "not picked", so it gets the G5 refusal. As in Task 5, the service doesn't commit; the route does.
- **Alternatives considered:** Taking inbox numbers from the form instead of ids (a number can point at a different photo if the inbox changed since the page was shown).
- **Who chose:** Claude
- **Why I agreed:**

### 134. Task 7: refusals the plan didn't word, and a refused grouping changes nothing
- **Decision:** Two crafted-request refusals get new wording: "That photo isn't in this box" (an id that doesn't exist or belongs to another box) and "Photo 4 is marked as not a page" (the first or last photo is a Not a page photo; only photos in the middle of a range are skipped, G7). A photo that is already Grouped at either end gets the G4 sentence. G4 names the range after any swap, so picking 7 then 3 says "Photos 3 to 7". Every check runs before anything is changed, so a refusal leaves no half-made document.
- **Alternatives considered:** Quietly moving an end that is Not a page to the nearest photo that is still in the inbox.
- **Who chose:** Claude
- **Why I agreed:**

### 135. Task 7: the inbox lists unread documents in their own section, and has the button above and below the photos
- **Decision:** A "Documents not read yet" section at the top of the Inbox lists the box's Grouped documents ("Document 3: 4 pages – Not read yet"), using `Document.state_label`, so it will say "Couldn't read" once Task 14 stores errors. It shows even when no photos are left to sort. `Box.unread_documents()` supplies the list, oldest first. The **Make document** button, labelled "(takes up to a minute)", appears both above and below the photos, because a box can have hundreds of photos and the list is long.
- **Alternatives considered:** One button at the bottom only; a single combined list of photos and documents.
- **Who chose:** Claude
- **Why I agreed:**

### 136. Task 8: discarding is all-or-nothing, and what counts as a refusal
- **Decision:** `discard_pages(session, box, page_ids, *, now)` marks every ticked photo through `apply("discard")` and returns how many it marked. Nothing ticked is refused with "Tick the photos that are not pages" (new wording). A ticked id that isn't in this box gets "That photo isn't in this box" (same wording as Make document). A photo that isn't in the inbox (for example, already in a document) is refused by the lifecycle itself, with its usual sentence ("This photo can't be marked as not a page while it is "In a document""). If any tick is refused, none are applied, because nothing is committed. The same photo ticked twice counts once, and a ticked value that isn't a number counts as not ticked. The success message is "2 photos marked as not a page" ("1 photo" for one).
- **Alternatives considered:** Quietly skipping the photos that can't be marked and discarding the rest.
- **Who chose:** Claude
- **Why I agreed:**

### 137. Task 8: restoring, the Bin screen and the tile
- **Decision:** `restore_page()` uses `apply("restore")`; a photo that isn't in the Bin is refused by the lifecycle's own sentence, and an id that doesn't exist gets "That photo isn't in the Bin". After a restore the user stays on the Bin, with the message "Restored IMG_0002.jpg to the inbox of Box 1". The photo is back in its filename position because the order is worked out each time (decision 130). The Bin lists the photos from every box, grouped by box and in filename order, each with a 200px thumbnail, its box name and a **Restore** button. Documents, **Empty bin…** and the legal note wait for Tasks 22 and 23. Home gets a tile "Bin: 2 items" (the count is photos only for now), and the navigation bar gets a Bin link.
- **Alternatives considered:** Sending the user to the box's inbox after a restore; one Bin per box.
- **Who chose:** Claude
- **Why I agreed:**

### 138. Task 8: one inbox form, two buttons
- **Decision:** Make document and **Mark ticked as not a page** are two submit buttons in the same form: the second one carries its own address (`formaction`), so no JavaScript is needed. Both buttons are shown above and below the photo list, from one template macro. Mark ticked as not a page has the plain (white, outlined) button style so that Make document stays the main action (SPEC section 4).
- **Alternatives considered:** Two separate forms (a tick box would then belong to only one of them); the "Not a page" button at the bottom only.
- **Who chose:** Claude
- **Why I agreed:**

### 139. Task 9: no pound sign in the demo invoice, because the built-in font can't draw it
- **Decision:** Pillow's built-in font draws `£` (and `€`) as the same blank "missing character" box, so the OCR would never see it. The demo invoice therefore has no currency symbol: "All prices in pounds" above the lines, and "Amount due 120.00". A test draws every character used in the demo text and fails if any of them comes out as that blank box, so this can't creep back in. **For Task 10:** the amount rule should treat the `£` as optional ("Amount due 120.00" as well as "Amount due £120.00"), which is sensible anyway because OCR often misreads that symbol.
- **Alternatives considered:** Writing "GBP"; drawing a `£` by hand; using a font file from the computer (not the same on every machine, and the plan says to use Pillow's built-in font).
- **Who chose:** Claude
- **Why I agreed:**

### 140. Task 9: the two lens covers are pure black but not byte-for-byte identical
- **Decision:** The upload skips a photo whose bytes match one it already has (B3/B4), so two identical black JPEGs would make the second lens cover "skipped – already uploaded". Each demo JPEG carries its own short comment (for example "lens cover 1"), which changes the file's bytes but not a single pixel: the covers still decode to exactly black. Tests check that the covers are pure black, that every file's bytes differ, that every page image differs, and that the whole folder uploads with all 7 photos added and none skipped.
- **Alternatives considered:** Making the second cover one pixel taller or a very slightly different black (not "pure black"); a different quality setting.
- **Who chose:** Claude
- **Why I agreed:**

### 141. Task 9: the demo box layout, its made-up content, and what `make-photos` does
- **Decision:** `write_demo_box(out_dir)` writes 7 files: the invoice on `IMG_0001` and `IMG_0002`, a lens cover on `IMG_0003`, the letter on `IMG_0004`, a lens cover on `IMG_0005`, and the unclear document on `IMG_0006` and `IMG_0007` (covers between documents only, none at the end). It makes the folder if needed, overwrites files of the same names, and returns the paths. Content, all invented: the invoice is from "Brightwell Flour Mills" to C-0042 Hollybrook Bakery Ltd (INV-1043, 14/03/2026, amount due 120.00, a second page of payment terms); the letter is from "Fernwood Accountancy Services" to the same client C-0042 (5 May 2026, "Re: Year end accounts reminder"), so Task 16's seed only has to include the one client the plan names; the unclear document is some notes with no client and none of the words either type looks for ("invoice", "amount", "due", "dear", "please" and so on; a test lists them, so Task 10's keywords must stay away from those words in this document). Every page has at least 20 words. Text is 40px, wrapped inside 100px margins, and an overlong page raises "Too much text for one page" rather than running off the bottom.
- **Alternatives considered:** A different client for the letter (needs the seed to know it); a trailing lens cover after the last document.
- **Who chose:** Claude
- **Why I agreed:**

### 142. Task 9: `docmanager` now reads its command line
- **Decision:** `cli.main(argv=None)` uses `argparse`. With no arguments it serves the app on 127.0.0.1 exactly as before (still no option for the host), and `docmanager make-photos OUT_DIR` writes the demo box, prints "Wrote 7 photos to OUT_DIR" and does not start the server. A missing OUT_DIR is refused by argparse (exit code 2, "OUT_DIR" in the message). The older AT-21 test now calls `cli.main([])`, because with no list it would read pytest's own command line. `seed` joins in Task 16.
- **Alternatives considered:** A separate script for the demo photos; leaving `main()` unchanged and adding a second entry point in `pyproject.toml`.
- **Who chose:** Claude
- **Why I agreed:**

### 143. Task 10: the keyword weights
- **Decision:** Invoice: "invoice" 4, "invoice number" 3, "invoice date" 2, "amount due" 3, "balance due" 2, "vat" 1, "total" 1. Letter: "dear" 3, "yours sincerely" 3, "yours faithfully" 3, "kind regards" 2, "best regards" 2, "re:" 2, "enclosed" 1. A keyword counts once, whatever its case, as a whole word or phrase (decision 10), and a phrase may be split by spaces or line breaks. A keyword that ends in a colon ("re:") has no word edge after it, so "Re:Subject" still counts. With the thresholds of 6 and 3 this gives: the SPEC C1 text Invoice 12 / Letter 0; the demo invoice 12 / 0; the demo letter 0 / 9; the demo notes 0 / 0; and a made-up mixed text of exactly Invoice 7 / Letter 5 for C2. A test scores the demo documents so a later change to the weights can't quietly break the demo.
- **Alternatives considered:** Higher weights for "invoice" alone (a letter that merely mentions an invoice would then pass as one); counting every occurrence.
- **Who chose:** Claude
- **Why I agreed:**

### 144. Task 10: what `extract()` returns, and when a field is empty
- **Decision:** `extract(text, today)` returns a dict that holds the type's fields **and** a `"document_date"` key (a `date` or `None`), as SPEC 3.4 describes. Every key is always there, with `None` when it wasn't found, so the review screen can show an empty box for each field. The caller will move `document_date` into its own column, because a `date` can't be stored in the JSON `fields` column. Invoice number: the token after "Invoice number / no. / #" that contains a digit (so "Invoice number is shown below" gives none). Amount: the number after "Amount due", in pence, worked out exactly with `Decimal` (not floating point); the `£` is optional and thousands commas are fine, which settles the question decision 139 raised. Letter subject: the text of the first line that starts "Re:". `filename_key` for a letter is the first 40 characters of the subject with the end trimmed, or "letter"; for an invoice it is the number or "no number". Cleaning unsafe characters out of a key is Task 12's job.
- **Alternatives considered:** Returning a small object with two parts; leaving missing keys out.
- **Who chose:** Claude
- **Why I agreed:**

### 145. Task 10: how dates are read, and which date an invoice gets
- **Decision:** `find_dates(text, today)` reads `14/03/2021` (day first), `14 March 2021` (full or short month names in any case, `Sept` too, and 1st/2nd/3rd/4th) and `2021-03-14`, and gives the dates in the order they appear. Two-digit years aren't read. A date that doesn't exist (31/02/2021) is skipped, and a date after `today` is ignored as a misread; today itself is allowed. A date glued to digits or slashes ("114/03/2021") is not taken. `find_dated_spans` also gives each date's position, which is how an invoice finds its labelled date: the date must come straight after "Invoice date" or "Date of invoice" (only spaces, a colon, a dash or a line break between). If that date is missing or is in the future, the invoice uses the first date in the text. A letter uses the first date. `keep_until()` waits for Task 21, as the plan says.
- **Alternatives considered:** Taking any date near the label; reading two-digit years.
- **Who chose:** Claude
- **Why I agreed:**

### 146. Task 11: what `classify()` returns, and how the reasons are worded and ordered
- **Decision:** `classify(text, clients, today)` returns a `Classification`: `reasons` (empty when the document can be filed automatically, with a `passed` property), `doc_type` (a key or `None`), `type_score` and `runner_up_score` (kept even when no type is chosen, to explain the decision, as SPEC 3.4 says), `client` (the matching client object or `None`), `fields` (the type's fields **without** the date) and `document_date`. All failing checks add a reason, always in the order text, type, client. When the type check fails, no fields or date are read (review re-reads them through `change_type`). `clients` only needs a `ref` and a `name` from each client, so the rules stay free of the database. Reason wording: low text, C2 and C3 are the SPEC's; where only one type scored above 0 the candidates list has one name ("Not sure what type this is (Invoice?)"); and a score above 0 but under the minimum also gets the "Not sure" wording, not "Couldn't tell". A tie between types keeps the registry's order (Invoice before Letter).
- **Alternatives considered:** Returning the date inside `fields`; stopping at the first failed check.
- **Who chose:** Claude
- **Why I agreed:**

### 147. Task 11: how the client is found
- **Decision:** A client reference is `C-` and four digits, in any case ("c-0042" counts), and not part of a longer word or number. Exactly one distinct reference: that client, or "Client C-0099 isn't in your client list" if the register doesn't have it. The same reference written twice is one reference. Two or more different references: "More than one client reference found: C-0043, C-0042" (decision 11's wording, with the references in the order they appear), even if all are known. **A reference settles it:** if any reference is in the text, names are not looked at, so an unknown reference is not rescued by a name. With no reference, a client's exact name is searched as a whole phrase, ignoring case, with any run of spaces or line breaks allowed inside it; exactly one match gives that client, none gives "Couldn't tell which client this is for", and two or more give "More than one client matched: Smith Ltd, J Smith & Co" with the names in the order they appear in the text. A known limit: a client named "Smith" and another named "Smith Ltd" would both match the text "Smith Ltd" and be reported as two.
- **Alternatives considered:** Listing names in register order; letting a unique name win over an unknown reference.
- **Who chose:** Claude
- **Why I agreed:**

### 148. Task 11: the file guard checks the text, the confirm guard doesn't, and `count_words` lives in `rules/classify.py`
- **Decision:** `Document.guard_file` now refuses with the low-text reason when `ocr_text` has fewer than `MIN_OCR_WORDS` words, so the lifecycle itself enforces what Check 1 reports. The guards still report only the first problem; the order for filing is now: not read yet, too little text, no type, no client (this adds one step to decision 123). `guard_confirm` does not check the text, because a person has looked at the document in review (decision 18), and `guard_flag` still only asks whether the document was read. The empty string still counts as read, so it gets the low-text reason, not "hasn't been read yet". `rules/classify.py` imports the document types only inside `classify()`, because the model package imports this module for the guards and a top-level import would go round in a circle. The shared reason text is `LOW_TEXT_REASON`. In `test_lifecycles.py`, the default made-up document text is now 20 words, and the old "empty text counts as read" test became a group of low-text tests.
- **Alternatives considered:** Putting `count_words` in a separate small module; putting the text check before the "not read yet" check.
- **Who chose:** Claude
- **Why I agreed:**

### 149. Task 12: the shape of `rules/naming.py`, and the template stays in `config.py`
- **Decision:** Three pure functions. `relative_path(client_ref=, client_name=, doc_type=, fields=, document_date=, template=None)` builds the path **under** the archive folder (as a `PurePosixPath`, so it is the same on every machine) from a `DocumentType` and its fields. `free_path(path, is_taken)` returns the path or the first free "name (2).pdf", "name (3).pdf" ..., where `is_taken` is a function the caller supplies (a test passes a set, filing will pass a check on the disk), so the clash rule needs no files to test. `clean_part(text)` makes one value safe. The template is read from `config.NAMING_TEMPLATE` each time it's needed (plan decision 2), so a test can change it. The caller will keep the chosen path in `pdf_path` and its last part (`path.name`, suffix included) in `filed_name`. Whether Windows treats "A.pdf" and "a.pdf" as the same file is not handled.
- **Alternatives considered:** Putting the template constant in `rules/naming.py`, as SPEC 5.6 says; one function that also looks at the disk.
- **Who chose:** Claude
- **Why I agreed:**

### 150. Task 12: how unsafe characters, spaces and dots are cleaned
- **Decision:** Each value (client reference, client name, type names, date, key) is cleaned **before** it goes into the template, so a "/" inside a client's name can never create a folder. Cleaning: runs of spaces, tabs and line breaks become one space (so a subject that wraps over two lines still makes a tidy name; this goes a little beyond N4); each of `/ \ : * ? " < > |` and control characters becomes "-"; dots and spaces are trimmed from **both** ends (trailing ones are refused by Windows, and a leading dot would hide the file or, as "..", climb a folder); if nothing is left, the value is "-". After the template is filled in, each folder name is trimmed of dots and spaces again, in case the template itself leaves one. Ordinary non-English letters are kept. A few control characters (like `\x1f`) count as spaces in Python, so they become a space, not a dash. Very long names and Windows' reserved names (CON, NUL ...) are not handled: the folder and file names always have other text around them.
- **Alternatives considered:** Only trimming the end of a name, as N4 literally says; dropping unsafe characters instead of turning them into dashes.
- **Who chose:** Claude
- **Why I agreed:**

### 151. Task 13: how `run_ocrmypdf` runs the program and what counts as a failure
- **Decision:** `run_ocrmypdf(pdf_in, pdf_out, sidecar, *, timeout=None, command=None)` runs `python -m ocrmypdf -l eng --rotate-pages --deskew --sidecar <sidecar> <in> <out>` with the same Python that runs the app. It raises `OcrFailed` (whose `.detail` is the technical text for the log) when the program exits with anything but 0 (the detail holds the exit code and the **last** 2000 characters of its error output), when it takes longer than the timeout (default `config.OCR_TIMEOUT_SECONDS`, 300), or when it exits 0 but didn't write both the PDF and the text file. The program is started in its own process group, and on a timeout the **whole group** is killed, because OCRmyPDF starts Tesseract and Ghostscript, and killing only the parent would leave them running (and would make the web request wait for them). This needs Linux or macOS (it uses `start_new_session` and `killpg`), which is fine for the apt-based setup; a Windows version would need changing. `command` replaces the program, only so tests can use a stand-in script. `OcrFailed` is a plain exception, not a `UserFacingError`: the user sees the fixed sentence `OCR_ERROR_MESSAGE` ("Couldn't read this document. Try again, or retake the photos.") on the document instead.
- **Alternatives considered:** `subprocess.run(timeout=...)`, which kills only the parent; calling OCRmyPDF's Python API in the web process (a crash or hang would take the app with it).
- **Who chose:** Claude
- **Why I agreed:**

### 152. Task 13: combining photos, and the `OCR_RUNNER` setting
- **Decision:** `combine_photos(photo_paths, pdf_path)` uses img2pdf with its defaults: one page per photo, in the order given, each page the size of its photo (JPEGs are embedded untouched, not re-compressed). img2pdf refuses a PNG with transparency or an unusual colour mode, so such a PNG is first flattened onto white (a test covers RGBA, LA, palette and 16-bit PNGs). Any failure while combining (a damaged file, no photos) is raised as `OcrFailed`, so the reading code has one kind of failure to deal with. `create_app` sets `OCR_RUNNER` to `run_ocrmypdf` by default, and a test can replace it with a function taking `(pdf_in, pdf_out, sidecar)`. EXIF rotation isn't applied (that is the should-tier item B9).
- **Alternatives considered:** Fitting every page to A4; refusing PNGs with transparency at upload.
- **Who chose:** Claude
- **Why I agreed:**

### 153. Task 13: the start-up check, and the fake OCR in the tests
- **Decision:** `check_ocr_tools()` returns a list of plain-words problems (empty means fine): Tesseract not installed; Tesseract installed but won't start; Tesseract missing the English (`eng`) or page-direction (`osd`) data (found with `tesseract --list-langs`, and only asked when Tesseract exists); Ghostscript (`gs`) not installed. Every problem is listed together. `docmanager` with no arguments runs the check first; if anything is wrong it prints "Doc Manager can't start yet:", the problems, and `sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd ghostscript`, to the error stream and exits with code 1 without starting the server. `make-photos` doesn't need the tools, so it doesn't check. In the tests, `FakeOcr(text, fail=None)` copies the PDF, writes the text as the sidecar, or raises `OcrFailed`; the shared `app` fixture now uses a fake that **fails** until a test gives it text, so no ordinary test can run the real OCR by accident. Tests marked `ocr` are skipped, with the missing tools and the install command in the reason, when the check finds a problem. The two older AT-21 tests now set the check to "no problems", so they don't depend on this machine.
- **Alternatives considered:** Checking only when the first document is read; a fake that succeeds by default.
- **Who chose:** Claude
- **Why I agreed:**

### 154. Task 14: how `read_document` works, step by step
- **Decision:** `filing.read_document(session, document, *, paths, ocr_runner, now)` (1) refuses a document that isn't Grouped or already has text, with "This document has already been read"; (2) commits, so the Grouped document is safely stored before the long OCR step (plan decision 5; this is the one service that commits itself, and the route commits the outcome afterwards); (3) clears any old `work/<id>.pdf` and `work/<id>.txt`, combines the photos into `work/<id>-images.pdf`, runs the OCR program, and reads the text file as UTF-8 (a bad byte is replaced, not a crash); (4) always deletes the images PDF afterwards, while the text file stays in `work/`; (5) on `OcrFailed` writes "Reading document 3 failed: <detail>" to the log, removes partial output, sets `ocr_error` to the fixed sentence and leaves the document Grouped; (6) on success stores the text, clears `ocr_error`, runs `classify`, and stores the type, fields, date, client, both scores and the reasons **even when the document is then flagged** (so review starts from what was found); (7) files it or flags it. Filing works out the archive path and the clash suffix first, then applies `file` (so the guards have the last word), then moves the PDF from `work/` into the archive, and records `pdf_path` ("archive/…", relative to the data folder), `filed_name` and `filed_at`. A flagged document keeps its PDF at `work/<id>.pdf`. Any other error (the power going out, a bug) is not caught: the 500 page is shown and the committed document is left Grouped with no text and no error, which is exactly the W4 case, listed with Retry.
- **Alternatives considered:** Making the route commit before calling the service; deleting the work PDF of a flagged document.
- **Who chose:** Claude
- **Why I agreed:**

### 155: Task 14: the message after Make document, and what happened to "Document made from photos 3 to 6"
- **Decision:** The banner is now exactly one of the three the plan lists: "Filed as 2021-03-14 Invoice INV-1043" (the archive filename without ".pdf", including any " (2)"), "Needs checking: <reasons joined with "; ">" (decision 11), or the W2 sentence "Couldn't read this document. Try again, or retake the photos." The Task 7 wording "Document made from photos 3 to 6" was only meant to last until this task, so `MadeDocument.message()` is gone (the first and last numbers stay on `MadeDocument`). Seven earlier tests (in `test_grouping.py` and `test_not_a_page.py`) asserted that wording or the "Not read yet" label; they now check what they were really about (the pages grouped, their positions, the inbox listing) and leave the OCR outcomes to `test_reading.py`.
- **Alternatives considered:** Keeping the photo range as a prefix ("Document made from photos 3 to 6. Filed as …").
- **Who chose:** Claude
- **Why I agreed:**

### 156: Task 14: Retry, and the inbox list of documents waiting to be read
- **Decision:** `POST /documents/<id>/retry` runs the same reading steps and returns to the inbox of the document's box. It is refused with "This document has already been read" for a document that is Filed, Needs checking or already has text (so a crafted POST can't read a document twice), and an unknown id is a 404. The inbox section "Documents not read yet" lists every Grouped document with its label ("Couldn't read" when `ocr_error` is set, "Not read yet" otherwise), the error sentence when there is one, and a **Retry** button. SPEC section 4 calls this section "Couldn't read" and says it lists Grouped documents with their error; I kept the Task 7 heading because it also holds W4 documents that have no error (stopped mid-read), and both kinds get the same button.
- **Alternatives considered:** Two separate sections ("Couldn't read" and "Not read yet"); letting Retry re-read a document that has text.
- **Who chose:** Claude
- **Why I agreed:**

### 157: Task 14: `Document.change_type()`
- **Decision:** `change_type(new_type, *, today)` sets `doc_type` to the new type's key, then reads the fields and the date again from `ocr_text` with the new type (a document with no text is read as empty text, so every field comes out `None`). The date goes into `document_date` and the fields into a **new** dict, as the plan's JSON rule says. The id, state and pages are untouched. It does not calculate `keep_until` yet: that is Task 21, which the plan says will make `change_type()` set it. `read_document` doesn't call it, because `classify` has already read the fields for the chosen type; Task 17 (confirming in review) will.
- **Alternatives considered:** Taking the type's key instead of the object; having `read_document` call `change_type`.
- **Who chose:** Claude
- **Why I agreed:**

### 158. Task 15: the Filed documents list
- **Decision:** The list is at `/documents` and shows only documents in the Filed state (documents in the bin, needing checking or still being read are not listed), newest filed first. The columns are Client ("C-0042 Hollybrook Bakery Ltd", or "No client"), Type ("Unclassified" when there is none), Date, Keep until ("–" when empty) and Markers, plus an **Open** link to the Document page. The empty list says "No documents have been filed yet". Home gets a **Filed documents** button and the navigation bar a **Filed documents** link. Dates are shown in the "14 Mar 2021" form (`format_date`, now also a template filter).
- **Alternatives considered:** Sorting by client or by document date; listing documents in the bin too.
- **Who chose:** Claude
- **Why I agreed:**

### 159. Task 15: the markers, and the field names on screen
- **Decision:** `Document` gets `needs_checking` and `has_no_date` (the plan's markers) and `markers(today)`, which lists the badges to show in a fixed order: "Needs checking", "No date" (only for a Filed document with no date), "Due" (`is_due`). Each document type now says how its fields are named and shown (`field_labels` and `describe_fields()`): Invoice shows "Invoice number" and "Amount due", Letter shows "Subject". An amount in pence is shown as pounds ("£120.00"), which is fine in an HTML page even though the demo photos can't draw the symbol. A field that wasn't found shows "Not found". The Document page shows a "Keep until" line only when keep-until is set; the "Keep-until not set – add the document's date" sentence is task 21's.
- **Alternatives considered:** Hard-coding the field names in the template; formatting the amount in the template.
- **Who chose:** Claude
- **Why I agreed:**

### 160. Task 15: the Document page, the PDF route and N5
- **Decision:** The page at `/documents/<id>` works for a document in any state (it shows the state label, markers, type, client, date and fields). The PDF is served at `/documents/<id>/pdf` (shown in the page's `<iframe>`, inline, as `application/pdf`). The database's `pdf_path` is the source of truth, but a file is only served if it is **inside the data folder** once the path is resolved, so a bad or hostile path can never read another file. If the path is set but the file isn't there (or is outside the folder), the page says "The PDF file is missing" and the PDF route answers 404, and the rest of the page still works (N5). A document that has no PDF yet (for example one that hasn't been read) says "There is no PDF for this document yet", which N5 doesn't cover.
- **Alternatives considered:** One wording for both cases; letting the browser download the PDF.
- **Who chose:** Claude
- **Why I agreed:**

### 161. Task 15: "only the allowed buttons" has no buttons yet
- **Decision:** The page shows a button for each of the document's `allowed_actions()` that has an entry in `routes.ACTION_BUTTONS` (action → label and screen). **That table is empty for now**, because the screens the buttons would lead to arrive later (File it in tasks 17–18, Move to bin and Restore in task 22), and a button that leads nowhere would be worse than none. Tests cover the rule with entries added on the fly: a Filed document offers only its own action, a document in the bin only its own, an unread document none, and with the table empty no button is shown at all. Task 22 fills the table in.
- **Alternatives considered:** Showing Move to bin and Restore now, pointing at pages that don't exist yet.
- **Who chose:** Claude
- **Why I agreed:**

### 162. Task 16: the demo clients, and how seeding adds them
- **Decision:** Eight invented clients, C-0042 Hollybrook Bakery Ltd first (the one the demo photos belong to), then C-0007 Ashgrove Dental Practice, C-0013 Birchfield Garden Centre, C-0021 Kestrel Print & Design, C-0034 Larkspur Tea Rooms, C-0051 Marlowe Joinery Ltd, C-0066 Quayside Bike Repairs and C-0078 Thornbury Plumbing Services. They are in `demo.seed.DEMO_CLIENTS`, where task 24 can draw documents for them. Seeding uses the normal app start-up on the data folder, so it also makes the usual folders and the empty database tables, then adds each client that isn't there yet. A client counts as "already there" if its **reference or its name** (ignoring case) exists, so a different spelling under the same reference, or the same name under another reference, is left alone and never causes a database error. An existing client is never changed. Each new client gets the current time as its `created_at`.
- **Alternatives considered:** Matching on the reference only (a clash on the name would crash the seed); updating existing clients to the demo spelling.
- **Who chose:** Claude
- **Why I agreed:**

### 163: Task 16: the `.demo-data` marker, and what "empty" means for `--reset`
- **Decision:** Plan decision 16 says `--reset` only empties a folder the seed script made (it carries a `.demo-data` marker) or one that is empty. The marker is written **only when the folder had nothing in it** when seeding began (or had just been emptied by `--reset`). A plain `seed` into a folder that already has other things in it adds the clients but does **not** mark it, because marking it would let a later `--reset` delete someone's real work. "Empty" is strict: a missing folder, or one with no entries at all. That includes the folders the app makes when it starts (`photos`, `archive`, `app.db` ...), so a data folder created by running `docmanager` once is **not** empty and has no marker, and `seed --reset` will refuse it. The refusal says so and what to do: "The data folder (…) already has things in it that the seed script didn't make, so --reset won't empty it. To start the demo from scratch, move or delete that folder yourself, or set DOCMANAGER_DATA to a new folder." **For task 25:** the README should tell the demo user to run `seed --reset` before first starting the app, or to use a fresh `DOCMANAGER_DATA`.
- **Alternatives considered:** Treating an app-made folder with an empty database as empty (it would need a guess about what counts as "nothing"); marking every folder that is seeded.
- **Who chose:** Claude
- **Why I agreed:**

### 164: Task 16: how `--reset` empties, and what it refuses
- **Decision:** With the marker present, **everything** inside the folder is deleted (the folder itself stays), including any file that isn't the app's: the marker is the seed script's promise that the folder is demo data. A link inside the folder is removed but never followed, so what it points at is untouched (a test proves it). A path that is a file is refused with "… is a file, not a folder." A refusal changes nothing at all: no files deleted, no database made, no marker written. `SeedResult` says how many clients were added and skipped, whether the folder was emptied and whether it is now marked.
- **Alternatives considered:** Deleting only the folders the app makes; asking "are you sure?" first (a refusal when it isn't ours is the safety, and the demo needs it to run without prompts).
- **Who chose:** Claude
- **Why I agreed:**

### 165: Task 16: the `seed` command
- **Decision:** `docmanager seed [--reset]` seeds the data folder named by `DOCMANAGER_DATA` (default `./data`), with no other options. It prints one line ("Added 8 clients.", "Added 0 clients. 8 already there.", "Emptied the data folder first. Added 8 clients."). A refusal goes to the error stream and exits with code 1. It doesn't start the server, and it doesn't check for the OCR programs, because adding clients needs no OCR (task 24 will make the seeding of documents need them).
- **Alternatives considered:** Letting `seed` take a folder as an option (the environment setting is how every other part finds the data folder).
- **Who chose:** Claude
- **Why I agreed:**

### 166. Task 17: the review test fixture needed a Batch
- **Decision:** `tests/test_review.py` built its Pages with `batch=None`, but `pages.batch_id` is required (SPEC §3.3, set by every upload), so every test failed with a database error before reaching the new code. I fixed the **test**, by giving the fixture's pages a real `Batch`, and left the model alone. No test's expectations changed.
- **Alternatives considered:** Making `Page.batch_id` optional, which would loosen the model for the sake of one fixture.
- **Who chose:** Claude
- **Why I agreed:**

### 167. Task 17: what "not chosen" means when confirming
- **Decision:** `confirm_document()` treats a type or client of `None` as "keep what the document already has" (a document flagged only for too little text already has both). A type key that isn't in `DOCUMENT_TYPES` counts as no type and is refused with "Choose a type before filing", rather than falling back to the stored type. A client id that matches no client is refused with "That client isn't in your client list". The route (task 18) turns a blank dropdown into `None`.
- **Alternatives considered:** Always requiring both to be posted; letting an unknown type key fall back to the stored one.
- **Who chose:** Claude
- **Why I agreed:**

### 168. Task 17: how typed values are read, and the wording of the refusals
- **Decision:** Typed values are read before anything is saved: the date by the new `rules.dates.parse_date()` (the same three layouts as `find_dates`, but it must be exactly one date, with no extra words, and a date after today is allowed through so the caller can say something specific); the amount as pounds with an optional "£" and commas, no minus sign. A blank date or field means "clear it" (None). New wordings: `Couldn't read the date "banana". Write it like 14/03/2021`, "The date can't be after today", "Amount due must be a number like 120.00", "The PDF file is missing, so this document can't be filed". Values shown on the screen use the same shapes you type: the date as `14/03/2021` and the amount as `45.50` with no "£" sign.
- **Alternatives considered:** Reusing `find_dates` on the typed text (it would accept "14/03/2021 and more" and silently ignore words); showing the amount as "£45.50".
- **Who chose:** Claude
- **Why I agreed:**

### 169. Task 17: a refused confirmation changes nothing
- **Decision:** `confirm_document()` works out the final values first, then sets them on the document, then runs the guard, checks the work PDF exists and files it. If any step refuses, the type, fields, date and client are put back as they were, and no StateChange is written. The caller commits only on success. Keep-until is not set here yet: task 21 adds it for confirming and for `change_type()` together.
- **Alternatives considered:** Rolling the whole session back (the refused screen shows the person's choices from the form, and the route can't tell what else is in the session).
- **Who chose:** Claude
- **Why I agreed:**

### 170. Task 18: the inbox banner and the Home tile count every box
- **Decision:** "N documents need checking" on the inbox, and the "Needs checking: N documents" tile on Home, both count all documents in Needs checking, in every box, the same as the Needs checking list they link to. **Later** is a link back to the same inbox with `?later=1` added, which hides the banner for that one visit (plan decision 13); the next ordinary visit shows it again. The banner is not shown when the count is 0.
- **Alternatives considered:** Counting only this box's documents (then "Check now" would open a list with a different number in it).
- **Who chose:** Claude
- **Why I agreed:**

### 171. Task 18: a link to the Check screen, not an `ACTION_BUTTONS` entry
- **Decision:** Decision 161 expected the File it button to be added to `routes.ACTION_BUTTONS`. Those entries are drawn as buttons that **post** straight away, and a post to the Check screen files the document with whatever it already holds, without a person looking. So the Document page instead shows a plain link, "Check this document", while the document is in Needs checking. `ACTION_BUTTONS` stays empty until task 22.
- **Alternatives considered:** An `ACTION_BUTTONS` entry pointing at the Check screen (it would be a button that does the wrong thing).
- **Who chose:** Claude
- **Why I agreed:**

### 172. Task 18: what the Check screen does after each outcome
- **Decision:** The screen is at `/documents/<id>/check` (GET shows it, POST is **File it**). A blank type or client dropdown means "keep what the document already has". After filing, the person goes to the Needs checking list with the "Filed as …" message, so they can carry straight on to the next one. A refusal shows the same form again (status 200) with the message in the banner, the person's type, client and typed values kept, and the hidden "shown" values left as they were first drawn, so the next press of File it still knows what was changed. A document that is no longer in Needs checking (already filed in another tab, or a crafted post) sends the person to its Document page with the refusal, and its Check screen does the same.
- **Alternatives considered:** Redirecting back to the form after a refusal (the typed values would be lost); going to the document's page after filing.
- **Who chose:** Claude
- **Why I agreed:**

### 173. Task 18: the filename shown on the Check screen
- **Decision:** The screen shows the filename the document would get from what it holds **now** (its stored type, client, fields and date, with a " (2)" suffix if the name is taken), or "Choose a type and a client to see the filename" if it has no type or no client yet. It does not change as you pick things in the dropdowns, because that would need JavaScript (SPEC §8). The real name is shown in the "Filed as …" message afterwards.
- **Alternatives considered:** Working out a preview from the posted form on every refusal.
- **Who chose:** Claude
- **Why I agreed:**

### 174. Task 19: the order of the blocking lines, and the lines that go together
- **Decision:** `Box.paper_blockers()` lists lines in this fixed order: photos to sort, documents that need checking, documents that couldn't be read, documents that haven't been read yet, then "Nothing filed from this box yet". Each count line is plural when the count isn't 1 ("2 documents need checking", "2 documents haven't been read yet", "3 photos to sort"). "Nothing filed…" appears whenever the box has no documents, so a box with only unsorted photos shows both its photo line and that one (P7). A Grouped document with no error counts as "hasn't been read yet", even if it somehow has text, so no document can block the paper without a line saying why.
- **Alternatives considered:** Showing only "Nothing filed…" when there are no documents; leaving a Grouped document that has text out of the lines.
- **Who chose:** Claude
- **Why I agreed:**

### 175. Task 19: how Home shows the answer
- **Decision:** Each box on Home keeps its "N photos to sort" line. Under it, a box that can go shows a **Paper can go** badge; any other box shows its blocking lines as a list. `Box.paper_can_go()` is simply "no blockers", so the badge and the lines can never disagree. Both are worked out when Home is drawn, one box at a time, which is fine for a handful of boxes.
- **Alternatives considered:** A single query counting everything for all boxes (faster, but harder to read and only worth it with hundreds of boxes).
- **Who chose:** Claude
- **Why I agreed:**

### 176. Task 20: the end-to-end test uses the real OCR program and needed no font change
- **Decision:** `tests/test_end_to_end.py` builds the app without an `OCR_RUNNER` override, so the real OCRmyPDF and Tesseract read the demo photos. Tesseract read all three demo documents correctly with the existing font, so `demo/photos.py` is unchanged. The unclear document is reviewed as a **Letter** for Hollybrook Bakery (any type would do; it has no real type). The test checks the invoice's text layer with `pdfminer.six` (added as a dev dependency, plan decision 17). Steps 2's duplicate-photo skip and 4's refusal are not repeated here: they are covered by `test_upload.py` and `test_grouping.py`.
- **Alternatives considered:** Reviewing it as an Invoice; repeating the duplicate and refusal steps in the end-to-end test.
- **Who chose:** Claude
- **Why I agreed:**

### 177. Task 20: "run the demo by hand" was done through the test client
- **Decision:** The plan says to run demo steps 1–7 by hand after the `ocr` test. I can't drive a browser from this session, so the end-to-end test (which goes through Flask's test client, the same routes and templates a browser uses) stands in for it. A real click-through in a browser is still worth doing once, at the demo line.
- **Alternatives considered:** Starting the server and fetching pages with curl (it would only repeat what the test client already does).
- **Who chose:** Claude
- **Why I agreed:**

### 178. Fix: Inbox thumbnails showed only their alt text
- **Decision:** The thumbnail route gave Flask's `send_from_directory` the data folder as it is configured. The real app's folder is the relative `data`, and Flask reads a relative folder as relative to the app's own code folder, so every thumbnail request was a 404 even though the files were in `data/thumbs`. The route now passes the folder's absolute path (`.resolve()`). The task 6 tests passed because they use absolute temporary folders; a new test in `tests/test_inbox.py` uses the relative `data` folder, fetches every `<img>` address on the inbox page and checks each is a 200 JPEG. Nothing else was changed.
- **Alternatives considered:** Making `Paths` always absolute for the whole app (a wider change than the bug needs); serving the file with `send_file` (the same path logic would need repeating).
- **Who chose:** Me
- **Why I agreed:**

### 179. Task 21: where keep-until is worked out
- **Decision:** `Document.recalculate_keep_until()` sets keep-until from the document's type and date (None if either is missing). It is called from `change_type()`, after `read_document` classifies, and in `confirm_document` (which also restores the old keep-until if the confirm is refused). So a document flagged with a type already has its keep-until before anyone confirms it. The Document page always shows a "Keep until" line, with "Keep-until not set – add the document's date" when it is empty, whatever the document's state.
- **Alternatives considered:** Setting it only when the document is filed; showing the "not set" line only for Filed documents.
- **Who chose:** Claude
- **Why I agreed:**

### 180. Task 22: how moving to the bin and restoring behave
- **Decision:** `move_to_bin()` checks every ticked document's guard before changing any, so one that must still be kept stops the whole move (nothing changes). A document whose PDF has gone from disk is still binned (so it can eventually be destroyed), but `restore_document()` refuses it, saying the PDF file is missing, and it stays in the bin. Nothing ticked gives "Tick the documents to move to the bin"; an unknown id gives "That document can't be found". The legal note is `config.LEGAL_NOTE`, available to every template as `LEGAL_NOTE`. The Home Bin tile now counts documents as well as photos, and a new Due for disposal tile shows the due count. Restoring sends you to the document's page. `test_no_buttons_are_offered_until_their_actions_exist` was a placeholder for this task, so it became `test_only_move_to_bin_and_restore_have_buttons`.
- **Alternatives considered:** Moving the documents that pass and refusing the rest; refusing to bin a document with a missing PDF.
- **Who chose:** Claude
- **Why I agreed:**
