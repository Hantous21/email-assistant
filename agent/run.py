"""
Phase 5 — Orchestrator (single entrypoint for scheduling).

Order:  fetch_emails -> triage -> digest -> draft_replies
        organize stays DRY-RUN unless --organize-live is passed.

Sanity checks between steps (mirror Rinata run_all.py):
  - abort with nonzero exit if fetch produced 0 emails
  - abort with nonzero exit if any step errors
  -> a scheduler (Task Scheduler / n8n) can alert on the failure.

CLI:
    python agent/run.py                  # daily pass; organize = dry-run
    python agent/run.py --since 1d
    python agent/run.py --organize-live  # also apply trusted organize rules

Exit codes: 0 = success, 1 = a step failed / sanity check failed.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PY   = sys.executable

STEPS = [
    ("Fetch emails",   "agent/fetch_emails.py"),
    ("Triage",         "agent/triage.py"),
    ("Daily digest",   "agent/digest.py"),
    ("Draft replies",  "agent/draft_replies.py"),
    # organize handled separately (dry-run vs --organize-live)
]

# TODO (Phase 5): implement run_step()/sanity() like Rinata run_all.py:
#   - subprocess.run([PY, script], cwd=ROOT); nonzero -> fail()
#   - after fetch: assert output/raw_emails.json non-empty else fail()
#   - run organize.py with or without --live based on --organize-live

if __name__ == "__main__":
    raise NotImplementedError("See ROADMAP Phase 5 — mirror Rinata run_all.py.")
