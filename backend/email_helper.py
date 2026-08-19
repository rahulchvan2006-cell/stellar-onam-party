"""Emergent-managed Resend email helper with guardrails (see integration playbook)."""
import os
import re
import ipaddress
import logging
import httpx
from html.parser import HTMLParser
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()
logger = logging.getLogger(__name__)

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = (
    "reply with your password", "reply with the code", "send your password", "cvv",
    "send us your password", "enter your password below", "confirm your card number",
    "your full card number", "seed phrase", "recovery phrase", "verify your card",
    "social security number", "confirm your bank details",
)
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} ≠ real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str, reply_to: str | None = None) -> str | None:
    _assert_safe_email(subject, html)
    payload = {
        "to": [to],
        "subject": subject,
        "html": html,
        "from_name": EMAIL_FROM_NAME,
    }
    if reply_to or EMAIL_REPLY_TO:
        payload["contact_email"] = reply_to or EMAIL_REPLY_TO
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{EMAIL_BASE_URL}/api/v1/email/send",
                headers={"X-Email-Key": EMAIL_KEY},
                json=payload,
            )
        resp.raise_for_status()
        return resp.json().get("id")
    except httpx.HTTPStatusError as e:
        logger.error(f"Email send failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=502, detail="Failed to send email")
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")


def build_ticket_confirmed_html(*, guest_name: str, quantity: int, amount: int,
                                booking_short_id: str, ticket_pdf_url: str,
                                booking_page_url: str) -> str:
    """Server-side template only (G4). Caller passes IDs/URLs, never markup."""
    from html import escape as e
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#FDFBF7;padding:24px 0;font-family:Arial,Helvetica,sans-serif;color:#0B2046">
  <tr><td align="center">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFBF0;border:1px solid #F0D89B;border-radius:20px;overflow:hidden">
      <tr><td style="background:#0B2046;padding:22px;text-align:center;color:#F3D06F;font-size:14px;letter-spacing:6px;font-weight:700">STELLAR ENTERTAINMENTS</td></tr>
      <tr><td style="padding:32px 28px 8px 28px;text-align:center">
        <div style="font-size:12px;letter-spacing:3px;color:#F9530B;font-weight:700">YOU'RE IN 🌺</div>
        <h1 style="margin:8px 0 4px 0;font-size:28px;color:#0B2046">Onam Party Pass Confirmed</h1>
        <div style="font-size:14px;color:#475569">Hi {e(guest_name)}, your booking is confirmed. See you on 29th August, 4:00 PM at Serenity Groove, Mysore.</div>
      </td></tr>
      <tr><td style="padding:20px 28px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#FFF3D6;border-radius:14px">
          <tr><td style="padding:16px 20px">
            <div style="font-size:11px;letter-spacing:2px;color:#B8791C">BOOKING</div>
            <div style="font-size:18px;font-weight:700;color:#0B2046;margin-top:4px">#{e(booking_short_id)}</div>
            <div style="margin-top:10px;font-size:14px;color:#334155">
              {quantity} × Early Bird &nbsp;·&nbsp; ₹{amount}
            </div>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="padding:8px 28px 24px 28px;text-align:center">
        <a href="{e(ticket_pdf_url)}" style="display:inline-block;background:linear-gradient(135deg,#FF8008 0%,#F9530B 100%);color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:999px;font-weight:700;letter-spacing:.5px">Download Your E-Ticket (PDF)</a>
        <div style="margin-top:10px;font-size:12px;color:#64748B">Show this PDF (or its QR) at the entry gate.</div>
      </td></tr>
      <tr><td style="padding:0 28px 24px 28px;text-align:center">
        <a href="{e(booking_page_url)}" style="color:#F9530B;text-decoration:underline;font-size:13px">View booking online</a>
      </td></tr>
      <tr><td style="background:#0B2046;color:#94a3b8;padding:18px 28px;font-size:11px;line-height:1.6">
        Alcoholic beverages are available for purchase at the venue for guests aged 21+. Food and drinks are not included in the ticket price.<br/>
        Sent by Stellar Entertainments. We never ask for your password or card details by email.
      </td></tr>
    </table>
  </td></tr>
</table>
"""
