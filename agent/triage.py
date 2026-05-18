"""
Phase 1 — Triage (READ-ONLY AI).

Reads output/raw_emails.json, runs each not-yet-triaged email through Claude
(prompts/triage_v1.txt) for category / priority / needs_reply / reason, applies
the VIP-sender override in Python (not the prompt), and appends to
output/triaged.json.

Ported from Rinata email_triage/categorize_emails.py: dotenv_values,
claude-haiku-4-5, batch+pause, checkpoint saves, markdown-fence-tolerant JSON
parse, FALLBACK on failure. Idempotent by message_id. Touches nothing in Gmail.

Usage:
    python agent/triage.py
    python agent/triage.py 5     # smoke test: first 5 only
"""

import sys
import json
import time
import re
import anthropic
from pathlib import Path
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).parent))
from _config import load_rules

ROOT        = Path(__file__).parent.parent
RAW_EMAILS  = ROOT / "output" / "raw_emails.json"
TRIAGED_OUT = ROOT / "output" / "triaged.json"
PROMPT_FILE = ROOT / "prompts" / "triage_v1.txt"

MODEL       = "claude-haiku-4-5-20251001"
MAX_TOKENS  = 250
BATCH_SIZE  = 10
BATCH_PAUSE = 2
SAVE_EVERY  = 25

env    = dotenv_values(ROOT / ".env")
client = anthropic.Anthropic(api_key=env["ANTHROPIC_API_KEY"])
SYSTEM_PROMPT = PROMPT_FILE.read_text(encoding="utf-8").strip()


def is_vip(sender: str, vip_list: list[str]) -> bool:
    s = (sender or "").lower()
    return any(v.strip().lower() in s for v in vip_list if v.strip())


def parse_response(raw: str, valid_categories: list[str], valid_priorities: list[str]) -> dict:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "category": "Other", "priority": "Today",
            "needs_reply": False,
            "reason": "[parse error — review manually]",
        }
    if data.get("category") not in valid_categories:
        data["category"] = "Other"
    if data.get("priority") not in valid_priorities:
        data["priority"] = "Today"
    data["needs_reply"] = bool(data.get("needs_reply", False))
    data["reason"] = str(data.get("reason", ""))[:200]
    return data


def triage_one(email: dict, categories: list[str], priorities: list[str]) -> dict:
    user_msg = (
        f"Allowed categories: {', '.join(categories)}\n"
        f"Priority levels: {', '.join(priorities)}\n\n"
        f"Sender: {email.get('sender','')}\n"
        f"Subject: {email.get('subject','')}\n"
        f"Date: {email.get('date','')}\n\n"
        f"{email.get('body', email.get('snippet',''))}"
    )
    for attempt in (1, 2):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": user_msg}],
            )
            return parse_response(resp.content[0].text, categories, priorities)
        except Exception as e:
            if attempt == 2:
                print(f"  ERROR: {e}", flush=True)
                return {
                    "category": "Other", "priority": "Today",
                    "needs_reply": False, "reason": "[generation failed]",
                }
            time.sleep(3)


def main():
    print("=== Email Assistant — Triage ===\n", flush=True)

    if not RAW_EMAILS.exists():
        print(f"ERROR: {RAW_EMAILS} not found. Run fetch_emails.py first.", flush=True)
        sys.exit(1)

    rules      = load_rules()
    categories = rules.get("categories", ["Other"])
    priorities = rules.get("priority_levels", ["Now", "Today", "Later", "Ignore"])
    vip_list   = rules.get("vip_senders", [])

    emails = json.loads(RAW_EMAILS.read_text(encoding="utf-8"))

    existing = []
    if TRIAGED_OUT.exists():
        try:
            existing = json.loads(TRIAGED_OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    done = {str(e["message_id"]) for e in existing}
    todo = [e for e in emails if str(e["message_id"]) not in done]

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        todo = todo[:int(sys.argv[1])]
        print(f"** SMOKE TEST: limited to {len(todo)} emails **\n", flush=True)

    print(f"Total raw:        {len(emails)}", flush=True)
    print(f"Already triaged:  {len(done)}", flush=True)
    print(f"To triage now:    {len(todo)}\n", flush=True)

    if not todo:
        print("Nothing to triage. output/triaged.json is up to date.", flush=True)
        return

    results = []
    for i, email in enumerate(todo, 1):
        t = triage_one(email, categories, priorities)

        vip = is_vip(email.get("sender", ""), vip_list)
        if vip:
            t["priority"] = "Now"
            t["reason"] = "VIP sender — " + t["reason"]

        results.append({
            "message_id":  email["message_id"],
            "thread_id":   email.get("thread_id", ""),
            "sender":      email.get("sender", ""),
            "subject":     email.get("subject", ""),
            "date":        email.get("date", ""),
            "snippet":     email.get("snippet", ""),
            "category":    t["category"],
            "priority":    t["priority"],
            "needs_reply": t["needs_reply"],
            "reason":      t["reason"],
            "vip":         vip,
        })

        flag = "VIP " if vip else "    "
        print(f"  [{i:>3}/{len(todo)}] {flag}{t['priority']:<6} "
              f"[{t['category']:<22}] {email.get('subject','')[:45]}", flush=True)

        if i % BATCH_SIZE == 0:
            time.sleep(BATCH_PAUSE)
        if i % SAVE_EVERY == 0:
            TRIAGED_OUT.write_text(
                json.dumps(existing + results, indent=2, ensure_ascii=False),
                encoding="utf-8")
            print(f"\n  -- Checkpoint ({i}/{len(todo)}) --\n", flush=True)

    TRIAGED_OUT.parent.mkdir(exist_ok=True)
    TRIAGED_OUT.write_text(
        json.dumps(existing + results, indent=2, ensure_ascii=False),
        encoding="utf-8")

    all_rows = existing + results
    print(f"\n{'='*55}", flush=True)
    print("TRIAGE SUMMARY", flush=True)
    print(f"{'='*55}", flush=True)
    print(f"  Newly triaged:  {len(results)}", flush=True)
    print(f"  Total:          {len(all_rows)}", flush=True)
    by_pri = {}
    for r in all_rows:
        by_pri[r["priority"]] = by_pri.get(r["priority"], 0) + 1
    for p in priorities:
        if p in by_pri:
            print(f"    {p:<8} {by_pri[p]}", flush=True)
    print(f"  Needs reply:    {sum(1 for r in all_rows if r['needs_reply'])}",
          flush=True)


if __name__ == "__main__":
    main()
