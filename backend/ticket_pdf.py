"""Generate a branded Onam Party e-ticket PDF with an embedded QR code."""
import io
import qrcode
from reportlab.lib.pagesizes import A5
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def _draw_qr(c: canvas.Canvas, data: str, x: float, y: float, size: float):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B2046", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), x, y, width=size, height=size, mask="auto")


def build_ticket_pdf(booking: dict) -> bytes:
    """Return a PDF (bytes) with booking info + QR code (contains booking id)."""
    buf = io.BytesIO()
    page_w, page_h = A5
    c = canvas.Canvas(buf, pagesize=A5)

    # Cream background
    c.setFillColor(HexColor("#FDFBF7"))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Top navy bar
    c.setFillColor(HexColor("#0B2046"))
    c.rect(0, page_h - 60, page_w, 60, fill=1, stroke=0)
    c.setFillColor(HexColor("#F3D06F"))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(page_w / 2, page_h - 32, "STELLAR ENTERTAINMENTS")
    c.setFont("Helvetica", 8)
    c.drawCentredString(page_w / 2, page_h - 48, "PRESENTS  •  ONAM PARTY  •  29 AUG")

    # Headline
    c.setFillColor(HexColor("#0B2046"))
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(page_w / 2, page_h - 110, "ONAM PARTY")
    c.setFillColor(HexColor("#F9530B"))
    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(page_w / 2, page_h - 132, "One Vibe. Our People. Endless Memories.")

    # Details card
    card_x, card_y, card_w, card_h = 30, page_h - 320, page_w - 60, 170
    c.setFillColor(HexColor("#FFFBF0"))
    c.setStrokeColor(HexColor("#F0D89B"))
    c.roundRect(card_x, card_y, card_w, card_h, 12, fill=1, stroke=1)

    c.setFillColor(HexColor("#B8791C"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(card_x + 16, card_y + card_h - 22, "GUEST")
    c.setFillColor(HexColor("#0B2046"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(card_x + 16, card_y + card_h - 40, booking["full_name"][:40])

    def label_val(label: str, val: str, off_x: float, off_y: float, val_size=12):
        c.setFillColor(HexColor("#B8791C"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(card_x + off_x, card_y + card_h - off_y, label)
        c.setFillColor(HexColor("#0B2046"))
        c.setFont("Helvetica-Bold", val_size)
        c.drawString(card_x + off_x, card_y + card_h - off_y - 14, val)

    label_val("TICKETS", f"{booking['quantity']} × Early Bird", 16, 68)
    label_val("AMOUNT PAID", f"Rs. {booking['amount']}", 180, 68)
    label_val("BOOKING ID", "#" + booking["id"][:8].upper(), 16, 108)
    label_val("STATUS", booking["status"].replace("_", " ").upper(), 180, 108)

    # QR (contains booking id — gate staff scan to verify)
    qr_size = 130
    qr_x = (page_w - qr_size) / 2
    qr_y = 60
    _draw_qr(c, f"ONAMPARTY:{booking['id']}", qr_x, qr_y, qr_size)

    c.setFillColor(HexColor("#0B2046"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(page_w / 2, qr_y + qr_size + 8, "Show this QR at the gate")

    # Footer
    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica", 7)
    c.drawCentredString(page_w / 2, 40, "Venue: Serenity Groove, Mysore, Karnataka  •  Doors: 4:00 PM onwards")
    c.drawCentredString(page_w / 2, 28, "Alcoholic beverages available at venue for guests aged 21+.")
    c.drawCentredString(page_w / 2, 16, "Food & drinks not included in ticket price.")

    c.showPage()
    c.save()
    return buf.getvalue()
