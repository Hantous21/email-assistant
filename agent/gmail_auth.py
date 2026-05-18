"""
Phase 0 — Gmail OAuth.

Ported from Rinata email_triage/gmail_auth.py. Scope is widened to gmail.modify
so the later phases (create drafts, apply labels) work WITHOUT a second consent
prompt. gmail.modify does NOT include send — we never request gmail.send.

FIRST-TIME SETUP (run once):
    1. console.cloud.google.com (sign in as hantous93@gmail.com) → new project
    2. APIs & Services → Library → enable "Gmail API"
    3. OAuth consent screen → External → add hantous93@gmail.com as a Test user
    4. Credentials → Create OAuth client ID → Desktop app → download JSON
    5. Save it as:  <project root>/credentials.json
    6. Run:  python agent/gmail_auth.py
    7. Browser opens → sign in as hantous93@gmail.com → Allow
    8. token.json is written. Other modules then call get_gmail_service() silently.

After setup, all other scripts call get_gmail_service() with no prompts.
"""

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# gmail.modify = read + create drafts + add/remove labels + archive.
# It does NOT permit sending. This is deliberate (draft-only design).
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

ROOT       = Path(__file__).parent.parent
CREDS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"


def get_gmail_service():
    """Return an authenticated Gmail API service object."""
    if not CREDS_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {CREDS_FILE}\n"
            "Download it from Google Cloud Console → APIs & Services → "
            "Credentials (Desktop app). See this file's docstring for steps."
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    print("Authenticating with Gmail...", flush=True)
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    print(f"\n✓ Authenticated as: {profile['emailAddress']}", flush=True)
    print(f"  Total messages: {profile.get('messagesTotal', 'unknown')}", flush=True)
    print(f"\ntoken.json saved to {TOKEN_FILE}", flush=True)
    print("Setup complete — you won't need to re-authenticate (until token expiry).",
          flush=True)
