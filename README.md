# RegHunterZ Solver — CLI skeleton

This repository branch contains a minimal Python CLI skeleton for RegHunterZ Solver utilities.

Goals (MVP)
- Python CLI using Click.
- Basic `parse` command which reads an input file and writes a small summary (JSON/CSV/TXT).
- Project layout with src/, pyproject.toml, tests/ and .gitignore.
- Easy to extend with domain-specific parsing, OCR or AI integrations later.

Quick start (local)
1. Create virtual environment:
   python -m venv .venv
   source .venv/bin/activate   # (Linux/macOS)
   .venv\Scripts\activate.bat  # (Windows)

2. Install:
   pip install -r requirements.txt

3. Run CLI:
   regsolver parse path/to/handhistory.txt --show
   or
   python -m regsolver_cli.parse path/to/handhistory.txt

Tests
- Run pytest:
  pip install -r requirements.txt
  pytest -q

License
- MIT
