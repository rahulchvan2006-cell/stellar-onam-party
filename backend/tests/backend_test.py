"""Backend tests for Onam Party booking API (event info, bookings, upload, admin)."""
import base64
import io
import os
import re
from urllib.parse import unquote

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

ADMIN_PASSWORD = "stellar2026"

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    return s


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-Admin-Password": ADMIN_PASSWORD}


@pytest.fixture(scope="module")
def created_ids():
    return []


def make_booking(api, quantity=1, email="test_qa@example.com", phone="9999999999"):
    payload = {
        "full_name": "TEST_QA User",
        "phone": phone,
        "email": email,
        "quantity": quantity,
        "pass_type": "early_bird",
    }
    return api.post(f"{BASE_URL}/api/bookings", json=payload, timeout=30)


# ---- Module: event info ----
class TestEventInfo:
    def test_root(self, api):
        r = api.get(f"{BASE_URL}/api/", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_event_info(self, api):
        r = api.get(f"{BASE_URL}/api/event/info", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["upi_id"] == "7483557316-3@ybl"
        assert d["early_bird_price"] == 499
        assert d["early_bird_total"] == 45
        assert d["early_bird_remaining"] == max(
            0, 45 - d["early_bird_confirmed"] - d["early_bird_held"]
        )
        assert isinstance(d["organizer_phones"], list)
        assert d["sold_out"] == (d["early_bird_remaining"] <= 0)


# ---- Module: booking creation ----
class TestBookingCreate:
    def test_create_booking_and_persistence(self, api, created_ids):
        r = make_booking(api, 1)
        assert r.status_code == 200, r.text
        d = r.json()
        created_ids.append(d["id"])
        assert d["status"] == "pending"
        assert d["amount"] == 499
        assert d["quantity"] == 1
        assert d["email"] == "test_qa@example.com"
        assert d["upi_id"] == "7483557316-3@ybl"
        assert d["upi_uri"].startswith("upi://pay?pa=7483557316-3@ybl")
        assert "am=499" in d["upi_uri"]
        assert d["qr_data_url"].startswith("data:image/png;base64,")
        assert d["screenshot_uploaded"] is False
        assert "_id" not in d

        g = api.get(f"{BASE_URL}/api/bookings/{d['id']}", timeout=30)
        assert g.status_code == 200
        gd = g.json()
        assert gd["id"] == d["id"]
        assert gd["status"] == "pending"
        assert gd["amount"] == 499
        assert "_id" not in gd

    def test_amount_scales_with_quantity(self, api, created_ids):
        r = make_booking(api, 3)
        assert r.status_code == 200, r.text
        d = r.json()
        created_ids.append(d["id"])
        assert d["amount"] == 499 * 3
        assert "am=1497" in d["upi_uri"]

    def test_invalid_email_rejected(self, api):
        r = api.post(
            f"{BASE_URL}/api/bookings",
            json={"full_name": "X", "phone": "1", "email": "not-an-email", "quantity": 1},
            timeout=30,
        )
        assert r.status_code == 422

    def test_quantity_zero_rejected(self, api):
        r = make_booking(api, 0)
        assert r.status_code == 422

    def test_quantity_above_max_rejected(self, api):
        r = make_booking(api, 21)
        assert r.status_code == 422

    @pytest.mark.parametrize("phone", ["12345", "5123456789", "98449120061234", "abcdefghij"])
    def test_invalid_indian_mobile_rejected(self, api, phone):
        r = make_booking(api, 1, phone=phone)
        assert r.status_code == 422, f"{phone} accepted"

    @pytest.mark.parametrize("phone,expected", [("9844912099", "9844912099"), ("+919844912099", "9844912099"), ("91 98449 12099", "9844912099"), ("09844912099", "9844912099")])
    def test_indian_mobile_normalized(self, api, created_ids, phone, expected):
        r = make_booking(api, 1, phone=phone)
        assert r.status_code == 200, r.text
        d = r.json()
        created_ids.append(d["id"])
        assert d["phone"] == expected

    def test_wrong_pass_type_rejected(self, api):
        r = api.post(
            f"{BASE_URL}/api/bookings",
            json={
                "full_name": "TEST_QA User",
                "phone": "9844912006",
                "email": "test_qa2@example.com",
                "quantity": 1,
                "pass_type": "vip",
            },
            timeout=30,
        )
        assert r.status_code == 400

    def test_over_quantity_returns_409(self, api):
        info = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()
        remaining = info["early_bird_remaining"]
        # quantity max is 20; only testable when remaining < 20
        if remaining >= 20:
            pytest.skip(f"remaining={remaining} >= max quantity 20; cannot trigger 409 via API")
        r = make_booking(api, remaining + 1)
        assert r.status_code == 409
        assert "slots" in r.json()["detail"].lower()

    def test_get_unknown_booking_404(self, api):
        r = api.get(f"{BASE_URL}/api/bookings/does-not-exist", timeout=30)
        assert r.status_code == 404


# ---- Module: screenshot upload ----
class TestUploadScreenshot:
    def test_upload_and_status_change(self, api, created_ids):
        r = make_booking(api, 1)
        assert r.status_code == 200, r.text
        bid = r.json()["id"]
        created_ids.append(bid)

        up = api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("proof.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=60,
        )
        assert up.status_code == 200, up.text
        assert up.json() == {"ok": True, "status": "awaiting_verification"}

        g = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30).json()
        assert g["status"] == "awaiting_verification"
        assert g["screenshot_uploaded"] is True

    def test_upload_non_image_rejected(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        up = api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")},
            timeout=30,
        )
        assert up.status_code == 400

    def test_upload_unknown_booking_404(self, api):
        up = api.post(
            f"{BASE_URL}/api/bookings/nope/upload-screenshot",
            files={"file": ("p.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=30,
        )
        assert up.status_code == 404


# ---- Module: admin auth ----
class TestAdminAuth:
    def test_login_wrong_password(self, api):
        r = api.post(f"{BASE_URL}/api/admin/login", json={"password": "wrong"}, timeout=30)
        assert r.status_code == 401

    def test_login_success(self, api):
        r = api.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=30)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["token"] == ADMIN_PASSWORD

    def test_list_without_header_401(self, api):
        r = api.get(f"{BASE_URL}/api/admin/bookings", timeout=30)
        assert r.status_code == 401

    def test_list_with_header(self, api, admin_headers):
        r = api.get(f"{BASE_URL}/api/admin/bookings", headers=admin_headers, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["bookings"], list)
        stats = d["stats"]
        assert stats["total_slots"] == 45
        assert stats["revenue"] == stats["confirmed_slots"] * 499
        for b in d["bookings"][:5]:
            assert "_id" not in b
            assert "screenshot" not in b


# ---- Module: admin confirm / reject / screenshot ----
class TestAdminActions:
    def test_confirm_decrements_remaining(self, api, admin_headers, created_ids):
        # Uses confirmed/held deltas so the test is safe under parallel execution
        before = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()
        r = make_booking(api, 2)
        assert r.status_code == 200, r.text
        bid = r.json()["id"]
        created_ids.append(bid)
        # pending holds slots too
        held_info = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()
        assert held_info["early_bird_held"] >= before["early_bird_held"] + 2

        c = api.post(
            f"{BASE_URL}/api/admin/bookings/{bid}/confirm", headers=admin_headers, timeout=30
        )
        assert c.status_code == 200, c.text
        assert c.json()["status"] == "confirmed"

        g = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30).json()
        assert g["status"] == "confirmed"

        after = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()
        assert after["early_bird_confirmed"] >= before["early_bird_confirmed"] + 2
        assert after["early_bird_remaining"] == max(
            0,
            after["early_bird_total"]
            - after["early_bird_confirmed"]
            - after["early_bird_held"],
        )

    def test_confirm_idempotent(self, api, admin_headers, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        api.post(f"{BASE_URL}/api/admin/bookings/{bid}/confirm", headers=admin_headers, timeout=30)
        again = api.post(
            f"{BASE_URL}/api/admin/bookings/{bid}/confirm", headers=admin_headers, timeout=30
        )
        assert again.status_code == 200
        assert again.json()["status"] == "confirmed"

    def test_confirm_unknown_404(self, api, admin_headers):
        r = api.post(
            f"{BASE_URL}/api/admin/bookings/nope/confirm", headers=admin_headers, timeout=30
        )
        assert r.status_code == 404

    def test_confirm_without_auth_401(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        c = api.post(f"{BASE_URL}/api/admin/bookings/{bid}/confirm", timeout=30)
        assert c.status_code == 401

    def test_reject_flow_releases_hold(self, api, admin_headers, created_ids):
        before = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()["early_bird_held"]
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        rj = api.post(
            f"{BASE_URL}/api/admin/bookings/{bid}/reject", headers=admin_headers, timeout=30
        )
        assert rj.status_code == 200
        assert rj.json()["status"] == "rejected"
        g = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30).json()
        assert g["status"] == "rejected"
        # rejected booking must no longer be counted in held slots:
        # held count == sum of quantities of pending bookings in admin list
        info = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()
        listing = api.get(
            f"{BASE_URL}/api/admin/bookings", headers=admin_headers, timeout=60
        ).json()["bookings"]
        pending_qty = sum(b["quantity"] for b in listing if b["status"] == "pending")
        assert abs(info["early_bird_held"] - pending_qty) <= 2  # tolerance for parallel workers
        assert bid not in [b["id"] for b in listing if b["status"] == "pending"]
        assert before >= 0

    def test_reject_unknown_booking_behaviour(self, api, admin_headers):
        """Reject on a non-existent booking should 404, not silently succeed."""
        r = api.post(
            f"{BASE_URL}/api/admin/bookings/nonexistent-id-xyz/reject",
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 404, (
            f"reject returned {r.status_code} for unknown booking (no existence check)"
        )

    def test_admin_screenshot_data_url(self, api, admin_headers, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("proof.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=60,
        )
        s = api.get(
            f"{BASE_URL}/api/admin/bookings/{bid}/screenshot", headers=admin_headers, timeout=30
        )
        assert s.status_code == 200, s.text
        data_url = s.json()["data_url"]
        assert data_url.startswith("data:image/png;base64,")
        assert base64.b64decode(data_url.split(",", 1)[1]) == PNG_1PX

    def test_admin_list_has_screenshot_flag_after_upload(self, api, admin_headers, created_ids):
        """has_screenshot must be True in admin list once a proof is uploaded."""
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        up = api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("proof.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=60,
        )
        assert up.status_code == 200
        listing = api.get(
            f"{BASE_URL}/api/admin/bookings", headers=admin_headers, timeout=60
        ).json()["bookings"]
        row = next(b for b in listing if b["id"] == bid)
        assert row["has_screenshot"] is True, (
            "admin list reports has_screenshot=False even though screenshot exists "
            "(screenshot field is excluded by the Mongo projection before bool() check)"
        )

    def test_admin_screenshot_missing_404(self, api, admin_headers, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        s = api.get(
            f"{BASE_URL}/api/admin/bookings/{bid}/screenshot", headers=admin_headers, timeout=30
        )
        assert s.status_code == 404

    def test_upload_after_confirm_rejected(self, api, admin_headers, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        api.post(f"{BASE_URL}/api/admin/bookings/{bid}/confirm", headers=admin_headers, timeout=30)
        up = api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("p.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=30,
        )
        assert up.status_code == 400



# ---- Module: WhatsApp wa.me deep-link share URLs ----
class TestWhatsAppShareUrls:
    EXPECTED_PHONES = ["+917483557316", "+919844912006"]

    def _assert_shape(self, data):
        urls = data.get("whatsapp_share_urls")
        assert isinstance(urls, list), f"whatsapp_share_urls missing/not list: {urls!r}"
        assert len(urls) == len(self.EXPECTED_PHONES), f"expected {len(self.EXPECTED_PHONES)} entries, got {urls}"
        for i, item in enumerate(urls):
            assert item["phone"] == self.EXPECTED_PHONES[i]
            assert item["phone"].startswith("+91")
            assert item["url"].startswith("https://wa.me/91"), item["url"]
            assert item["label"] == f"Organizer {i+1}"
            decoded = unquote(item["url"].split("?text=", 1)[1])
            assert "TEST_QA User" in decoded
            assert f"Amount: ₹{data['amount']}" in decoded
            assert f"Tickets: {data['quantity']}" in decoded
            assert data["id"][:8] in decoded
        return urls

    def test_create_booking_returns_share_urls(self, api, created_ids):
        r = make_booking(api, 2)
        assert r.status_code == 200, r.text
        d = r.json()
        created_ids.append(d["id"])
        urls = self._assert_shape(d)
        assert urls[0]["url"].startswith("https://wa.me/917483557316?text=")
        assert urls[1]["url"].startswith("https://wa.me/919844912006?text=")

    def test_get_booking_returns_share_urls(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        g = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30)
        assert g.status_code == 200
        d = g.json()
        urls = self._assert_shape(d)
        assert "PENDING" in unquote(urls[0]["url"])

    def test_share_url_reflects_status_after_upload(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        up = api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("p.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=30,
        )
        assert up.status_code == 200, up.text
        # upload endpoint returns only {ok,status}; share urls come from GET
        d = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30).json()
        urls = self._assert_shape(d)
        assert "AWAITING VERIFICATION" in unquote(urls[0]["url"])


# ---- Module: public screenshot proof endpoint + wa.me links (iteration 6) ----
PUBLIC_BASE = "https://onam-memories-mysore.preview.emergentagent.com"


class TestPublicProofEndpoint:
    def test_proof_404_before_upload(self, api, created_ids):
        r = make_booking(api, 1)
        assert r.status_code == 200, r.text
        bid = r.json()["id"]
        created_ids.append(bid)
        p = api.get(f"{BASE_URL}/api/bookings/{bid}/proof", timeout=30)
        assert p.status_code == 404, p.status_code

    def test_proof_404_unknown_id(self, api):
        p = api.get(f"{BASE_URL}/api/bookings/no-such-booking-xyz/proof", timeout=30)
        assert p.status_code == 404

    def test_proof_returns_image_after_upload(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        up = api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("proof.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=60,
        )
        assert up.status_code == 200, up.text
        p = api.get(f"{BASE_URL}/api/bookings/{bid}/proof", timeout=30)
        assert p.status_code == 200, p.text[:300]
        assert p.headers["content-type"].startswith("image/"), p.headers["content-type"]
        assert p.headers["content-type"] == "image/png"
        assert p.content == PNG_1PX

    def test_proof_cache_control_private(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("proof.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=60,
        )
        p = api.get(f"{BASE_URL}/api/bookings/{bid}/proof", timeout=30)
        assert p.status_code == 200
        cc = p.headers.get("cache-control", "")
        # ingress may rewrite to "no-store, no-cache, must-revalidate"; no-store is the key part
        assert "no-store" in cc, cc

    def test_proof_jpeg_content_type_preserved(self, api, created_ids):
        r = make_booking(api, 1)
        bid = r.json()["id"]
        created_ids.append(bid)
        api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("proof.jpg", io.BytesIO(PNG_1PX), "image/jpeg")},
            timeout=60,
        )
        p = api.get(f"{BASE_URL}/api/bookings/{bid}/proof", timeout=30)
        assert p.status_code == 200
        assert p.headers["content-type"] == "image/jpeg"


class TestShareUrlContainsLinks:
    def test_links_before_and_after_upload(self, api, created_ids):
        r = make_booking(api, 2, phone="+919844912006")
        assert r.status_code == 200, r.text
        d = r.json()
        bid = d["id"]
        created_ids.append(bid)

        # Before upload: booking page link present, proof link absent
        pre = unquote(d["whatsapp_share_urls"][0]["url"].split("?text=", 1)[1])
        assert f"{PUBLIC_BASE}/booking/{bid}" in pre, pre
        assert f"/api/bookings/{bid}/proof" not in pre, pre

        api.post(
            f"{BASE_URL}/api/bookings/{bid}/upload-screenshot",
            files={"file": ("p.png", io.BytesIO(PNG_1PX), "image/png")},
            timeout=60,
        )
        g = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30).json()
        for item in g["whatsapp_share_urls"]:
            txt = unquote(item["url"].split("?text=", 1)[1])
            assert f"{PUBLIC_BASE}/booking/{bid}" in txt, txt
            assert f"{PUBLIC_BASE}/api/bookings/{bid}/proof" in txt, txt
            # full details
            assert "TEST_QA User" in txt
            assert "+91 9844912006" in txt
            assert "Tickets: 2 × Early Bird" in txt
            assert "Amount: ₹998" in txt
            assert bid[:8].upper() in txt
            assert "AWAITING VERIFICATION" in txt


class TestTicketPdfGating:
    def test_pdf_403_before_confirm_200_after(self, api, admin_headers, created_ids):
        r = make_booking(api, 1, email="delivered@resend.dev")
        bid = r.json()["id"]
        created_ids.append(bid)
        pre = api.get(f"{BASE_URL}/api/tickets/{bid}/pdf", timeout=30)
        assert pre.status_code == 403, pre.status_code

        c = api.post(
            f"{BASE_URL}/api/admin/bookings/{bid}/confirm", headers=admin_headers, timeout=60
        )
        assert c.status_code == 200, c.text
        assert c.json()["status"] == "confirmed"

        post = api.get(f"{BASE_URL}/api/tickets/{bid}/pdf", timeout=60)
        assert post.status_code == 200, post.text[:200]
        assert post.headers["content-type"] == "application/pdf"
        assert post.content[:4] == b"%PDF"

    def test_pdf_unknown_404(self, api):
        r = api.get(f"{BASE_URL}/api/tickets/unknown-xyz/pdf", timeout=30)
        assert r.status_code == 404
