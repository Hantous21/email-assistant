# Personal Email Intelligence System

An AI agent for the Gmail inbox: triages incoming email by priority, drafts replies in your voice (saved as Gmail drafts — never auto-sent), applies reversible labels to organize noise, and produces a daily digest.

Built on the same architecture as the [Rinata AI Agent Suite](../Rinata/README.md): deterministic Python orchestrates, Claude handles only the judgment calls.

---

## What It Does

| Capability | Output | Autonomy |
|---|---|---|
| **Triage & prioritize** | Every new email scored: Now / Today / Later / Ignore, with a one-line reason | Read-only |
| **Draft replies** | Ready-to-edit Gmail draft in your voice for every email that needs a response | Draft-only — never sends |
| **Daily digest** | One summary: what came in, what's waiting on you, what to act on first | Read-only |
| **Auto-organize** | Applies reversible Gmail labels (and optional archive) to group newsletters / receipts / noise | Dry-run first, then opt-in |

---

## Core Design Principles

1. **Human-in-the-loop** — replies are Gmail *drafts* only. The agent never sends email. You review and click Send.
2. **Reversible-only actions** — organizing uses Gmail labels (fully reversible). It never deletes mail.
3. **Dry-run by default** — `organize` logs what it *would* do until you promote a rule to live. You build trust before it touches the inbox.
4. **Idempotent** — re-running never re-processes or re-drafts an email already handled. Safe to schedule.
5. **Auditable** — every classification, draft, and label action is written to `output/` with a timestamp and reason.
6. **Your data stays on the Claude API path only** — Gmail API + Anthropic API, nothing else.

---

## Architecture

```
Gmail API          Claude (Haiku)        Deterministic Python        You
─────────          ──────────────        ────────────────────        ───
fetch_emails.py  → triage.py          →  priority scoring        →  digest.py  →  daily digest
                 → draft_replies.py   →  Gmail draft (not sent)  →  review & send
                 → organize.py        →  label map (dry-run)     →  promote rules when trusted
```

`run.py` is the single entrypoint — orchestrates the above in order, with sanity checks.

---

## Project Structure

```
email-assistant/
├── README.md
├── .env.example               ← copy to .env, add ANTHROPIC_API_KEY
├── config/
│   └── rules.example.json     ← copy to rules.json: VIP senders, categories, label map
├── agent/
│   ├── gmail_auth.py          ← one-time Gmail OAuth
│   ├── fetch_emails.py        ← pull recent mail → output/raw_emails.json
│   ├── triage.py              ← Claude categorize + priority score
│   ├── draft_replies.py       ← Claude draft replies → saved as Gmail drafts
│   ├── organize.py            ← reversible label/archive (dry-run default)
│   ├── digest.py              ← build the daily digest
│   └── run.py                 ← orchestrator (single entrypoint)
├── prompts/
│   ├── triage_v1.txt          ← triage system prompt
│   └── reply_v1.txt           ← reply-drafting system prompt (your voice)
├── output/                    ← all generated artifacts (git-ignored)
└── docs/
    └── ROADMAP.md             ← phased build plan
```

---

## Setup

1. **Python deps:**
   ```
   pip install anthropic google-api-python-client google-auth-oauthlib pandas
   ```

2. **Anthropic key:** copy `.env.example` → `.env`, set `ANTHROPIC_API_KEY`

3. **Gmail OAuth:** create a Google Cloud project, enable the Gmail API, make a Desktop OAuth client, download `credentials.json` into the project root, then run:
   ```
   python agent/gmail_auth.py
   ```
   Browser opens once, creates `token.json`. Same OAuth flow as the Rinata suite.

4. **Tune your rules:** copy `config/rules.example.json` → `rules.json` and configure VIP senders, categories, and the label map for your inbox.

---

## Running

```bash
python agent/run.py                  # full pass: fetch → triage → draft → digest
python agent/run.py --since 1d       # only mail from the last 24 hours
python agent/triage.py 5             # smoke test: triage 5 emails, no drafts
python agent/organize.py --live      # apply labels (after you trust the dry-run)
```

**Recommended cadence:** once each morning. Open the digest, skim drafts in Gmail, send the good ones. Promote organize rules to `--live` one at a time.

---

## Tech Stack

- **Python** — orchestration and pipeline logic
- **Claude API** (`claude-haiku-4-5`) — triage classification, reply drafting
- **Gmail API** — email fetch, draft creation, label management
- **OAuth 2.0** — Google authentication

---

## Status

Architecture, module contracts, and prompts are fully defined. Build proceeds phase by phase from `docs/ROADMAP.md`.

---

## Contact

**Sammi Hantous** — AI Automation Consultant  
[hantous93@gmail.com](mailto:hantous93@gmail.com) · [calendly.com/hantous93](https://calendly.com/hantous93)
