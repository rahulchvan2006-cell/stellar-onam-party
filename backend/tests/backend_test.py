"""Backend tests for Onam Party booking API (event info, bookings, upload, admin)."""
import base64
import io
import os
import re

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


def make_booking(api, quantity=1, email="test_qa@example.com"):
    payload = {
        "full_name": "TEST_QA User",
        "phone": "9999999999",
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
        r = make_booking(api, 11)
        assert r.status_code == 422

    def test_wrong_pass_type_rejected(self, api):
        r = api.post(
            f"{BASE_URL}/api/bookings",
            json={
                "full_name": "X",
                "phone": "1",
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
        # quantity max is 10; only testable when remaining < 10
        if remaining >= 10:
            pytest.skip(f"remaining={remaining} >= max quantity 10; cannot trigger 409 via API")
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
        before = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()["early_bird_remaining"]
        r = make_booking(api, 2)
        assert r.status_code == 200, r.text
        bid = r.json()["id"]
        created_ids.append(bid)
        # pending holds slots too
        held = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()["early_bird_remaining"]
        assert held == before - 2

        c = api.post(
            f"{BASE_URL}/api/admin/bookings/{bid}/confirm", headers=admin_headers, timeout=30
        )
        assert c.status_code == 200, c.text
        assert c.json()["status"] == "confirmed"

        g = api.get(f"{BASE_URL}/api/bookings/{bid}", timeout=30).json()
        assert g["status"] == "confirmed"

        after = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()
        assert after["early_bird_remaining"] == before - 2
        assert after["early_bird_confirmed"] >= 2

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
        before = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()["early_bird_remaining"]
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
        after = api.get(f"{BASE_URL}/api/event/info", timeout=30).json()["early_bird_remaining"]
        assert after == before

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
