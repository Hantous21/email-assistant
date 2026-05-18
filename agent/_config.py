"""Shared config loader. Prefers config/rules.json; falls back to the example
(with a printed warning) so the first run works before you customize."""

import json
import sys
from pathlib import Path

ROOT      = Path(__file__).parent.parent
RULES     = ROOT / "config" / "rules.json"
RULES_EX  = ROOT / "config" / "rules.example.json"


def load_rules() -> dict:
    if RULES.exists():
        return json.loads(RULES.read_text(encoding="utf-8"))
    if RULES_EX.exists():
        print("NOTE: config/rules.json not found — using rules.example.json. "
              "Copy it to rules.json and edit for your real inbox.",
              file=sys.stderr, flush=True)
        return json.loads(RULES_EX.read_text(encoding="utf-8"))
    raise FileNotFoundError("No config/rules.json or rules.example.json found.")
