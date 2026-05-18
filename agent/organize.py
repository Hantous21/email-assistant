"""
Phase 4 — Organize (reversible; DRY-RUN by default).

From output/triaged.json + rules.json auto_organize.label_map: apply a Gmail
label (create it if missing) and optionally archive (remove the INBOX label).

SAFETY:
  - DRY-RUN by default: write intended actions to output/organize_plan.csv,
    change nothing. --live actually applies them.
  - NEVER delete. NEVER touch TRASH/SPAM. NEVER archive a category listed in
    rules.json auto_organize.never_archive_categories.
  - Idempotent by message_id (skip already-organized).

CLI:
    python agent/organize.py            # dry-run -> output/organize_plan.csv
    python agent/organize.py --live     # apply labels/archive for trusted rules
"""

# Contract:
#   def plan(triaged: list[dict], rules: dict) -> list[dict]   # intended actions
#   def apply(actions: list[dict]) -> None                      # only when --live
#   def main(live: bool) -> None

if __name__ == "__main__":
    raise NotImplementedError("See ROADMAP Phase 4. Dry-run default; reversible only.")
