#!/usr/bin/env bash
# Runs after Claude edits a file: formats and lint-fixes it if it is a Python file.
file=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["tool_input"].get("file_path",""))')
case "$file" in
  *.py)
    uv run ruff format "$file" >/dev/null
    uv run ruff check --fix "$file" >/dev/null
    ;;
esac
exit 0
