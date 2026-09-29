import os
import sys
import argparse
import imaplib
import email
from email.header import decode_header
import datetime
from pathlib import Path

# Load .env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

def dec(val):
    if not val: return ""
    try:
        parts = decode_header(val)
        res = []
        for p, enc in parts:
            if isinstance(p, bytes):
                res.append(p.decode(enc or "utf-8", errors="replace"))
            else:
                res.append(str(p))
        return " ".join(res)
    except:
        return str(val)

def scan_inbox(days=2):
    if not GMAIL_USER or not GMAIL_PASS:
        print("[!] GMAIL_USER or GMAIL_APP_PASSWORD not set in _system/.env")
        return []
    
    print(f"Connecting to Gmail ({GMAIL_USER})...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("INBOX")
        
        since_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%d-%b-%Y")
        status, data = mail.search(None, f'(SINCE "{since_date}")')
        
        msg_ids = data[0].split()
        print(f"Found {len(msg_ids)} emails in the last {days} days.")
        
        results = []
        for mid in reversed(msg_ids[-15:]):  # last 15 emails
            _, mdata = mail.fetch(mid, "(RFC822.HEADER)")
            raw_email = mdata[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = dec(msg["Subject"])
            sender = dec(msg["From"])
            date = msg["Date"]
            results.append({"from": sender, "subject": subject, "date": date})
            print(f"• [{date}] From: {sender} | Subject: {subject}")
            
        mail.logout()
        return results
    except Exception as e:
        print(f"[✗] Error scanning emails: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=2)
    args = parser.parse_args()
    scan_inbox(days=args.days)
