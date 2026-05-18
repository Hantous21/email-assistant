"""
Phase 2 — Daily digest (read-only).

Render output/triaged.json into one readable digest:
  - "Now" items first (with reason), then Today, then Later
  - counts per priority and per category
  - an explicit "Needs your reply" list (and whether a draft was created,
    cross-referenced from output/drafts_log.csv if present)

Writes output/digest_YYYY-MM-DD.md and prints a short summary to console.
Useful on its own before drafts/organize exist.

CLI:
    python agent/digest.py
"""

# Contract:
#   def build_digest(triaged: list[dict], drafts_log: list[dict] | None) -> str
#   def main() -> None

if __name__ == "__main__":
    raise NotImplementedError("See ROADMAP Phase 2.")
