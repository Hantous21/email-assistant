# Build Roadmap — Personal Email Assistant

Build in this order. Each phase is independently useful and testable, so you get
value early and de-risk the Gmail-write steps until last.

## Phase 0 — Foundations (no AI yet)
- [ ] `pip install` deps; `.env` from `.env.example`.
- [ ] `agent/gmail_auth.py` — OAuth flow, creates `token.json`. Copy this almost
      verbatim from Rinata `email_triage/gmail_auth.py` (proven, same scopes plus
      `gmail.modify` for labels/drafts).
- [ ] `agent/fetch_emails.py` — pull recent mail per `rules.json` (`fetch.since`,
      `max_emails`, exclude SPAM/TRASH) → `output/raw_emails.json`. Store
      `message_id`, `thread_id`, sender, subject, date, snippet, body.
- [ ] Verify: run it, eyeball the JSON. **Read-only — zero risk.**

## Phase 1 — Triage (read-only AI)
- [ ] `agent/triage.py` — for each email not already triaged, call Claude with
      `prompts/triage_v1.txt` + `rules.json` categories. Apply VIP override
      (vip_senders → priority "Now") in Python, not the prompt.
- [ ] Output `output/triaged.json` (append-only; idempotent by `message_id`).
- [ ] Smoke test: `python agent/triage.py 5`.
- [ ] Still read-only — nothing touches the inbox.

## Phase 2 — Daily digest (read-only)
- [ ] `agent/digest.py` — render `triaged.json` into a single readable digest:
      "Now" first, then Today/Later, counts, and a needs-reply list. Write
      `output/digest_YYYY-MM-DD.md` (and/or print to console).
- [ ] This alone is already useful every morning.

## Phase 3 — Draft replies (writes Gmail DRAFTS only)
- [ ] `agent/draft_replies.py` — for emails where `needs_reply` and category in
      `draft_replies.draft_for_categories`, call Claude with `prompts/reply_v1.txt`.
- [ ] Create the draft via Gmail API `users.drafts.create` **in the right thread**.
      Never `messages.send`. Skip if a draft already exists for that thread
      (idempotent). Log to `output/drafts_log.csv`.
- [ ] Verify drafts appear in Gmail, in-thread, unsent.

## Phase 4 — Organize (reversible, dry-run first)
- [ ] `agent/organize.py` — from `triaged.json` + `rules.json` `label_map`.
      Default **dry-run**: write the intended actions to
      `output/organize_plan.csv`, change nothing.
- [ ] `--live` flag actually applies labels (create label if missing) and
      archives (remove INBOX label) per the map. **Never delete; never touch
      `never_archive_categories`.** Idempotent by `message_id`.
- [ ] Promote rules one category at a time as you trust them.

## Phase 5 — Orchestrate & schedule
- [ ] `agent/run.py` — fetch → triage → digest → draft (organize stays dry-run
      unless `--organize-live`). Sanity checks: abort if fetch returned 0, or if
      a step errors, with a clear nonzero exit so a scheduler can alert.
- [ ] Schedule daily: Windows Task Scheduler calling `python agent/run.py`, or
      n8n (Docker) using the same file-handoff pattern designed for Rinata
      (n8n triggers/notifies; Python does the work on the host).

## Guardrails to keep (every phase)
- Drafts only — no `messages.send`, ever.
- No deletes — labels and archive are the only mutations, and only in Phase 4 `--live`.
- Idempotent — key everything by Gmail `message_id` / `thread_id`.
- Auditable — every AI decision and inbox action logged to `output/` with a reason.
- Reuse Rinata patterns — `dotenv_values`, `claude-haiku-4-5-20251001`, batch +
  checkpoint loop, markdown-fence-tolerant JSON parsing, FALLBACK on parse fail.
