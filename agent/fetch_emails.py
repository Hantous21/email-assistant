"""
Phase 0 — Fetch recent inbox mail (READ-ONLY).

Ported from Rinata email_triage/fetch_emails.py, simplified for a personal
inbox: pulls recent INBOX messages (excluding SPAM/TRASH) within a date window,
up to fetch.max_emails, and writes output/raw_emails.json.

Idempotent: messages already in raw_emails.json (by message_id) are not
re-fetched. Safe to re-run and safe to schedule. Touches nothing in Gmail.

Usage:
    python agent/fetch_emails.py
    python agent/fetch_emails.py --since 7d     # overrides rules.json default
"""

import sys
import json
import base64
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gmail_auth import get_gmail_service
from _config import load_rules

ROOT    = Path(__file__).parent.parent
RAW_OUT = ROOT / "output" / "raw_emails.json"

MAX_BODY_CHARS = 3000


def parse_since(arg_default: str) -> str:
    """--since 7d  → '7d'. Falls back to rules.json fetch.default_since."""
    for i, a in enumerate(sys.argv):
        if a == "--since" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith("--since="):
            return a.split("=", 1)[1]
    return arg_default


def extract_body(payload: dict) -> str:
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime.startswith("multipart/"):
        for part in payload.get("parts", []):
            text = extract_body(part)
            if text:
                return text
    return ""


def clean_body(raw: str) -> str:
    cleaned = re.sub(r"\n{3,}", "\n\n", raw.strip())
    if len(cleaned) > MAX_BODY_CHARS:
        cleaned = cleaned[:MAX_BODY_CHARS] + "\n\n[... body truncated ...]"
    return cleaned


def get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def search_message_ids(service, query: str, cap: int) -> list[str]:
    ids, token = [], None
    while len(ids) < cap:
        kwargs = {"userId": "me", "q": query,
                  "maxResults": min(100, cap - len(ids))}
        if token:
            kwargs["pageToken"] = token
        resp = service.users().messages().list(**kwargs).execute()
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids[:cap]


def fetch_message(service, msg_id: str) -> dict | None:
    try:
        msg = service.users().messages().get(
            userId="me", id=msg_id, format="full").execute()
    except Exception as e:
        print(f"  Warning: could not fetch {msg_id}: {e}", flush=True)
        return None
    headers = msg.get("payload", {}).get("headers", [])
    return {
        "message_id": msg_id,
        "thread_id":  msg.get("threadId", ""),
        "sender":     get_header(headers, "From"),
        "subject":    get_header(headers, "Subject"),
        "date":       get_header(headers, "Date")[:31].strip(),
        "body":       clean_body(extract_body(msg.get("payload", {}))),
        "snippet":    msg.get("snippet", ""),
        "label_ids":  msg.get("labelIds", []),
    }


def main():
    rules = load_rules()
    fcfg  = rules.get("fetch", {})
    since = parse_since(fcfg.get("default_since", "1d"))
    cap   = int(fcfg.get("max_emails", 100))
    excl  = fcfg.get("exclude_labels", ["SPAM", "TRASH"])

    query = f"in:inbox newer_than:{since} " + " ".join(
        f"-in:{lbl.lower()}" for lbl in excl)

    print("=== Email Assistant — Fetch ===\n", flush=True)
    print(f"Query:        {query}", flush=True)
    print(f"Max emails:   {cap}", flush=True)

    existing = []
    if RAW_OUT.exists():
        try:
            existing = json.loads(RAW_OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    existing_ids = {e["message_id"] for e in existing}
    print(f"Already saved: {len(existing_ids)}\n", flush=True)

    service = get_gmail_service()
    found   = search_message_ids(service, query, cap)
    new_ids = [mid for mid in found if mid not in existing_ids]
    print(f"Matched: {len(found)}  |  New to fetch: {len(new_ids)}", flush=True)

    if not new_ids:
        print("Nothing new. output/raw_emails.json is up to date.", flush=True)
        return

    fetched = []
    for i, mid in enumerate(new_ids, 1):
        msg = fetch_message(service, mid)
        if msg:
            fetched.append(msg)
        if i % 20 == 0:
            print(f"  Fetched {i}/{len(new_ids)}...", flush=True)

    RAW_OUT.parent.mkdir(exist_ok=True)
    RAW_OUT.write_text(
        json.dumps(existing + fetched, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"\n✓ Saved {len(existing) + len(fetched)} total "
          f"({len(fetched)} new) → {RAW_OUT.name}", flush=True)


if __name__ == "__main__":
    main()
