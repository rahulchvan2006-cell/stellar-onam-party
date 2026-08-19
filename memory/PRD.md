# Onam Party — PRD & Progress

## Original Problem
Mobile-first Kerala Onam event site for **Stellar Entertainment** (Namma Mysore, 29 Aug, Serenity Groove). Poster-matched aesthetic: blue sky, palm leaves, gold/orange traditional typography. Manual UPI booking (no Stripe), Early Bird ₹499 × 45 slots. Admin panel to verify screenshots and confirm bookings.

## User Personas
- **Guest**: Books tickets via UPI, uploads payment screenshot, waits for WhatsApp confirmation.
- **Organizer (Kiran / Rahul)**: Uses admin panel at `/admin` to view screenshots and confirm bookings.

## Core Requirements (Static)
- Poster-style hero (blue sky, palm framing, ONAM 3D + Party script)
- Live countdown to 29 Aug 4:00 PM
- Sticky mobile "Book Now" bar
- Ticket booking with QR + UPI ID (`7483557316-3@ybl`), screenshot upload
- Admin (password `stellar2026`) to confirm/reject
- Slot counter: 45 total, decrements on admin confirm
- 21+ alcohol disclaimer repeated

## Implemented (Feb 2026)
- Landing page: hero, marquee, about, lineup (band+DJ), highlights, traditions, venue+map, tickets, FAQ, footer
- Backend: `/api/event/info`, `/api/bookings` (create + get), `/api/bookings/{id}/upload-screenshot`, `/api/admin/login`, `/api/admin/bookings` (with stats), `/api/admin/bookings/{id}/screenshot`, `/api/admin/bookings/{id}/confirm`, `/api/admin/bookings/{id}/reject`
- Confirmation page with auto-generated UPI QR (Python `qrcode`) + upload, auto-polls status
- Admin dashboard: stats cards + bookings table + screenshot preview modal
- Testing: 24/26 pytest passing + full Playwright E2E happy path passing

## Backlog (P1/P2)
- **P1**: WhatsApp/SMS notification to organizer on booking + guest on confirm (Twilio / MSG91)
- **P1**: E-ticket PDF with QR sent to guest on confirm
- **P2**: Signed JWT admin session instead of raw-password header
- **P2**: Cron sweep to expire pending bookings past 24h
- **P2**: Optimistic slot locking (unique index) to prevent oversell race
- **P2**: General pass tier (₹799) once Early Bird sells out

## Contacts
- UPI: 7483557316-3@ybl · Kiran +91 7483 557 316 · Rahul +91 98449 12006
