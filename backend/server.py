from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends, UploadFile, File, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import base64
import io
import uuid
import qrcode
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ---- Config ----
UPI_ID = os.environ.get("UPI_ID", "7483557316-3@ybl")
UPI_PAYEE_NAME = os.environ.get("UPI_PAYEE_NAME", "Stellar Entertainment")
ORGANIZER_PHONES = os.environ.get("ORGANIZER_PHONES", "+917483557316,+919844912006")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "stellar2026")
EARLY_BIRD_PRICE = 499
EARLY_BIRD_TOTAL_SLOTS = 45
HOLD_HOURS = 24  # full hold before auto-expiring a pending booking

# ---- Models ----
class BookingCreate(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    quantity: int = Field(ge=1, le=10)
    pass_type: str = "early_bird"


class BookingOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    full_name: str
    phone: str
    email: str
    quantity: int
    pass_type: str
    amount: int
    status: str
    created_at: datetime
    screenshot_uploaded: bool = False
    upi_id: Optional[str] = None
    upi_uri: Optional[str] = None
    qr_data_url: Optional[str] = None


class AdminLogin(BaseModel):
    password: str


# ---- Helpers ----
def now():
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def build_upi_uri(amount: int, booking_id: str) -> str:
    tn = f"Onam Party Booking {booking_id[:8]}"
    return (
        f"upi://pay?pa={UPI_ID}&pn={quote(UPI_PAYEE_NAME)}"
        f"&am={amount}&cu=INR&tn={quote(tn)}"
    )


def make_qr_data_url(data: str) -> str:
    qr = qrcode.QRCode(box_size=8, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B2046", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


async def count_confirmed_slots() -> int:
    """Count confirmed early_bird tickets (quantity aware)."""
    pipeline = [
        {"$match": {"pass_type": "early_bird", "status": "confirmed"}},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}},
    ]
    result = await db.bookings.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def count_held_slots() -> int:
    """Count pending bookings not yet expired (holds early_bird)."""
    expiry_cutoff = now() - timedelta(hours=HOLD_HOURS)
    pipeline = [
        {"$match": {
            "pass_type": "early_bird",
            "status": {"$in": ["pending", "awaiting_verification"]},
            "created_at_iso": {"$gte": iso(expiry_cutoff)},
        }},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}},
    ]
    result = await db.bookings.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


def require_admin(x_admin_password: Optional[str] = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(401, "Unauthorized")
    return True


def booking_doc_to_out(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "full_name": doc["full_name"],
        "phone": doc["phone"],
        "email": doc["email"],
        "quantity": doc["quantity"],
        "pass_type": doc["pass_type"],
        "amount": doc["amount"],
        "status": doc["status"],
        "created_at": datetime.fromisoformat(doc["created_at_iso"]),
        "screenshot_uploaded": bool(doc.get("screenshot")),
        "upi_id": UPI_ID,
        "upi_uri": doc.get("upi_uri"),
        "qr_data_url": doc.get("qr_data_url"),
    }


# ---- Endpoints ----
@api_router.get("/event/info")
async def event_info():
    confirmed = await count_confirmed_slots()
    held = await count_held_slots()
    remaining = max(0, EARLY_BIRD_TOTAL_SLOTS - confirmed - held)
    return {
        "event_name": "Onam Party",
        "tagline": "One Vibe. Our People. Endless Memories.",
        "organizer": "Stellar Entertainment",
        "city": "Namma Mysore",
        "venue": "Serenity Groove, Mysore, Karnataka",
        "date_iso": "2026-08-29T16:00:00+05:30",
        "time_display": "4:00 PM onwards",
        "upi_id": UPI_ID,
        "organizer_phones": ORGANIZER_PHONES.split(","),
        "early_bird_price": EARLY_BIRD_PRICE,
        "early_bird_total": EARLY_BIRD_TOTAL_SLOTS,
        "early_bird_confirmed": confirmed,
        "early_bird_held": held,
        "early_bird_remaining": remaining,
        "sold_out": remaining <= 0,
    }


@api_router.post("/bookings", response_model=BookingOut)
async def create_booking(payload: BookingCreate):
    if payload.pass_type != "early_bird":
        raise HTTPException(400, "Only Early Bird pass is available currently")

    confirmed = await count_confirmed_slots()
    held = await count_held_slots()
    remaining = EARLY_BIRD_TOTAL_SLOTS - confirmed - held
    if remaining < payload.quantity:
        raise HTTPException(409, f"Only {max(0, remaining)} Early Bird slots left")

    amount = EARLY_BIRD_PRICE * payload.quantity
    booking_id = str(uuid.uuid4())
    upi_uri = build_upi_uri(amount, booking_id)
    qr_data = make_qr_data_url(upi_uri)

    doc = {
        "id": booking_id,
        "full_name": payload.full_name.strip(),
        "phone": payload.phone.strip(),
        "email": payload.email.lower(),
        "quantity": payload.quantity,
        "pass_type": payload.pass_type,
        "amount": amount,
        "status": "pending",
        "screenshot": None,
        "screenshot_mime": None,
        "upi_uri": upi_uri,
        "qr_data_url": qr_data,
        "created_at_iso": iso(now()),
        "updated_at_iso": iso(now()),
    }
    await db.bookings.insert_one(doc)
    return booking_doc_to_out(doc)


@api_router.post("/bookings/{booking_id}/upload-screenshot")
async def upload_screenshot(booking_id: str, file: UploadFile = File(...)):
    doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Booking not found")
    if doc["status"] not in ("pending", "awaiting_verification"):
        raise HTTPException(400, "Cannot upload screenshot for this booking")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 5MB)")
    mime = file.content_type or "image/jpeg"
    if not mime.startswith("image/"):
        raise HTTPException(400, "Only image files allowed")
    b64 = base64.b64encode(content).decode()

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "screenshot": b64,
            "screenshot_mime": mime,
            "status": "awaiting_verification",
            "updated_at_iso": iso(now()),
        }},
    )
    return {"ok": True, "status": "awaiting_verification"}


@api_router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: str):
    doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Booking not found")
    return booking_doc_to_out(doc)


# ---- Admin ----
@api_router.post("/admin/login")
async def admin_login(payload: AdminLogin):
    if payload.password != ADMIN_PASSWORD:
        raise HTTPException(401, "Invalid password")
    return {"ok": True, "token": ADMIN_PASSWORD}


@api_router.get("/admin/bookings")
async def admin_list_bookings(_: bool = Depends(require_admin)):
    docs = await db.bookings.find(
        {},
        {"_id": 0, "screenshot": 0, "qr_data_url": 0},
    ).sort("created_at_iso", -1).to_list(500)
    confirmed = await count_confirmed_slots()
    held = await count_held_slots()
    return {
        "bookings": [
            {
                "id": d["id"],
                "full_name": d["full_name"],
                "phone": d["phone"],
                "email": d["email"],
                "quantity": d["quantity"],
                "pass_type": d["pass_type"],
                "amount": d["amount"],
                "status": d["status"],
                "created_at": d["created_at_iso"],
                "has_screenshot": bool(d.get("screenshot_mime")),
            }
            for d in docs
        ],
        "stats": {
            "confirmed_slots": confirmed,
            "held_slots": held,
            "remaining_slots": max(0, EARLY_BIRD_TOTAL_SLOTS - confirmed - held),
            "total_slots": EARLY_BIRD_TOTAL_SLOTS,
            "revenue": confirmed * EARLY_BIRD_PRICE,
        },
    }


@api_router.get("/admin/bookings/{booking_id}/screenshot")
async def admin_get_screenshot(booking_id: str, _: bool = Depends(require_admin)):
    doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not doc or not doc.get("screenshot"):
        raise HTTPException(404, "Screenshot not found")
    return {
        "data_url": f"data:{doc.get('screenshot_mime', 'image/jpeg')};base64,{doc['screenshot']}"
    }


@api_router.post("/admin/bookings/{booking_id}/confirm")
async def admin_confirm(booking_id: str, _: bool = Depends(require_admin)):
    doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Booking not found")
    if doc["status"] == "confirmed":
        return {"ok": True, "status": "confirmed"}
    # capacity check
    confirmed = await count_confirmed_slots()
    if confirmed + doc["quantity"] > EARLY_BIRD_TOTAL_SLOTS:
        raise HTTPException(409, "No more Early Bird slots available")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "confirmed", "updated_at_iso": iso(now())}},
    )
    return {"ok": True, "status": "confirmed"}


@api_router.post("/admin/bookings/{booking_id}/reject")
async def admin_reject(booking_id: str, _: bool = Depends(require_admin)):
    doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0, "id": 1})
    if not doc:
        raise HTTPException(404, "Booking not found")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "rejected", "updated_at_iso": iso(now())}},
    )
    return {"ok": True, "status": "rejected"}


@api_router.get("/")
async def root():
    return {"message": "Onam Party API", "status": "ok"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
