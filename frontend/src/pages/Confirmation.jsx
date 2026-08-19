import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Loader2, Upload, CheckCircle2, Copy, Flower2, Phone, Smartphone } from "lucide-react";

export default function Confirmation() {
  const { id } = useParams();
  const [b, setB] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const load = () => api.get(`/bookings/${id}`).then((r) => setB(r.data)).catch(() => {});
  useEffect(() => {
    load();
    const timer = setInterval(load, 15000);
    return () => clearInterval(timer);
    /* eslint-disable-next-line */
  }, [id]);

  const copyUpi = () => {
    navigator.clipboard.writeText(b.upi_id);
    toast.success("UPI ID copied");
  };

  const upload = async (file) => {
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      await api.post(`/bookings/${id}/upload-screenshot`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Screenshot uploaded! We're verifying now.");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (!b) {
    return (
      <div className="min-h-screen flex items-center justify-center pattern-bg">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
      </div>
    );
  }

  const confirmed = b.status === "confirmed";
  const awaiting = b.status === "awaiting_verification";

  return (
    <div className="min-h-screen pattern-bg py-10 px-5">
      <div className="max-w-2xl mx-auto">
        <Link to="/" className="inline-flex items-center gap-2 text-orange-600 hover:text-orange-700 mb-6 text-sm">
          <Flower2 className="w-4 h-4" /> Back to home
        </Link>

        <div className="card-warm p-8 sm:p-10">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-300 to-orange-500 flex items-center justify-center mx-auto mb-4">
              {confirmed ? <CheckCircle2 className="w-8 h-8 text-white" /> : <Flower2 className="w-8 h-8 text-white" />}
            </div>
            <h1 className="font-display text-3xl sm:text-4xl font-black text-slate-900 mb-2">
              {confirmed ? "Confirmed! You're In 🌺" : "Booking Received! 🌺"}
            </h1>
            <p className="text-slate-600">
              {confirmed
                ? "Show this screen at the venue entry."
                : awaiting
                ? "We're verifying your payment. You'll receive confirmation on WhatsApp/SMS shortly."
                : "Complete the UPI payment below to reserve your slot."}
            </p>
          </div>

          <div className="rounded-xl bg-amber-50 border border-amber-200 p-5 mb-6">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-slate-500">Name</span><div className="font-semibold text-slate-900" data-testid="conf-name">{b.full_name}</div></div>
              <div><span className="text-slate-500">Phone</span><div className="font-semibold text-slate-900">{b.phone}</div></div>
              <div><span className="text-slate-500">Tickets</span><div className="font-semibold text-slate-900">{b.quantity} × Early Bird</div></div>
              <div><span className="text-slate-500">Amount</span><div className="font-display font-black text-orange-600 text-xl" data-testid="conf-amount">₹{b.amount}</div></div>
              <div className="col-span-2"><span className="text-slate-500">Status</span><div className="font-semibold uppercase text-slate-900" data-testid="conf-status">{b.status.replace("_", " ")}</div></div>
            </div>
          </div>

          {!confirmed && (
            <>
              <div className="text-center mb-4">
                <p className="text-xs uppercase tracking-[0.25em] text-orange-600 font-semibold mb-2">Step 1 · Pay via UPI</p>
                <h3 className="font-display text-xl font-bold text-slate-900">Scan QR or use UPI ID</h3>
              </div>

              <div className="flex flex-col items-center gap-4 mb-6">
                <div className="p-4 bg-white rounded-2xl border-2 border-amber-300 shadow-lg">
                  <img src={b.qr_data_url} alt="UPI QR" className="w-56 h-56" data-testid="upi-qr" />
                </div>
                <p className="text-xs text-slate-500 -mt-1">Scan to auto-fill ₹{b.amount}</p>

                {/* One-tap UPI deep-link — auto-opens GPay/PhonePe/Paytm with amount prefilled */}
                <a
                  href={b.upi_uri}
                  className="pill-btn w-full sm:w-auto"
                  data-testid="pay-upi-app-btn"
                >
                  <Smartphone className="w-4 h-4 mr-2" /> Pay ₹{b.amount} via UPI App
                </a>

                <div className="flex items-center gap-2 rounded-full bg-slate-900 text-white px-4 py-2">
                  <span className="text-sm font-mono" data-testid="upi-id">{b.upi_id}</span>
                  <button onClick={copyUpi} className="text-amber-300 hover:text-amber-100" data-testid="copy-upi-btn">
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-slate-500">Any UPI app · GPay · PhonePe · Paytm · BHIM</p>
              </div>

              <div className="text-center mb-3">
                <p className="text-xs uppercase tracking-[0.25em] text-orange-600 font-semibold mb-1">Step 2 · Upload Payment Proof</p>
              </div>

              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                onChange={(e) => upload(e.target.files?.[0])}
                className="hidden"
                data-testid="screenshot-input"
              />
              <button
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
                className="pill-btn w-full mb-3"
                data-testid="upload-screenshot-btn"
              >
                {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Upload className="w-4 h-4 mr-2" /> {b.screenshot_uploaded ? "Re-upload Screenshot" : "Upload Payment Screenshot"}</>}
              </button>

              {b.screenshot_uploaded && (
                <div className="rounded-xl bg-green-50 border border-green-200 p-4 flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 shrink-0" />
                  <div className="text-sm text-green-900">
                    <b>Screenshot received.</b> Booking held for you. We'll confirm your e-pass on WhatsApp within a few hours.
                  </div>
                </div>
              )}
            </>
          )}

          <div className="mt-8 pt-6 border-t border-amber-200">
            <p className="text-xs text-slate-500 mb-3">Need help? Reach the organizers:</p>
            <div className="flex flex-wrap gap-3">
              <a href="tel:+917483557316" className="pill-btn-outline text-sm"><Phone className="w-4 h-4 mr-2" /> Kiran</a>
              <a href="tel:+919844912006" className="pill-btn-outline text-sm"><Phone className="w-4 h-4 mr-2" /> Rahul</a>
            </div>
            <p className="text-xs text-slate-500 mt-6 leading-relaxed">
              Alcoholic beverages available for purchase at the venue for guests aged 21+. Food & drinks not included.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
