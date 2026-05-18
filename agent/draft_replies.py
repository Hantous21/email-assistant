"""
Phase 3 — Draft replies (writes Gmail DRAFTS only — NEVER sends).

For triaged emails where needs_reply is true AND category is in
rules.json draft_replies.draft_for_categories, call Claude
(prompts/reply_v1.txt) and create a Gmail DRAFT in the original thread via
users.drafts.create. If the model returns NO_REPLY_NEEDED, skip.

HARD RULES:
  - Use users.drafts.create ONLY. messages.send must never appear in this file.
  - Skip if a draft already exists for the thread (idempotent).
  - Log every draft to output/drafts_log.csv (message_id, thread_id, ts, words).

CLI:
    python agent/draft_replies.py
    python agent/draft_replies.py 3   # smoke test: first 3 eligible
"""

# Contract:
#   def draft_one(email: dict, max_words: int) -> str | None   # None == NO_REPLY_NEEDED
#   def create_gmail_draft(thread_id: str, to: str, subject: str, body: str) -> str
#   def main(limit: int | None) -> None

if __name__ == "__main__":
    raise NotImplementedError("See ROADMAP Phase 3. Drafts only — no send.")
