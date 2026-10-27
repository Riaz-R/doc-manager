# Doc Manager

Local document manager. SPEC.md is the spec, PLAN.md the build plan and progress checklist, DECISIONS.md the decisions log. Work through PLAN.md one task at a time.

## Commands
- Install: `uv sync`
- Tests: `uv run pytest` (skip the slow OCR tests with `uv run pytest -m "not ocr"`)
- Ruff: `uv run ruff format`, then `uv run ruff check`
- App: `uv run docmanager`, then open http://127.0.0.1:5000

## Rules
- Localhost only: the app binds to 127.0.0.1, never any other address.
- No real data and no network calls: tests and demos use made-up documents drawn with Pillow, and nothing is fetched at runtime or in tests (only `uv sync` and `uv add` download).
- Never run `git push`.
- I'm new to programming: explain each new concept in one plain sentence when you introduce it.
- When compacting, keep the progress checklist and the test command.

## Loop for every task
1. Write the tests first, then the code.
2. Run all the tests (`uv run pytest`) until they pass, then `uv run ruff format` and `uv run ruff check`.
3. Tick the task in PLAN.md.
4. Append a numbered entry to DECISIONS.md for any decision the plan didn't specify: decision, alternatives, who chose, and a blank "Why I agreed:" line.
5. Commit with a message naming the task, for example "Task 7: Make document".
6. Stop and give me three lines: what you built, which classes are involved, and any decision you made.
