import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Loader2, Ticket } from "lucide-react";

const PRICE = 499;

export default function BookingDialog({ open, onOpenChange, remaining }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", quantity: 1 });
  const navigate = useNavigate();

  const total = PRICE * (form.quantity || 1);
  const soldOut = remaining <= 0;

  const submit = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.phone || !form.email) {
      toast.error("Please fill all fields");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/bookings", { ...form, pass_type: "early_bird" });
      // Auto-open WhatsApp with booking details to first organizer, in the same
      // user-gesture click so browsers don't block the popup.
      const wa = data?.whatsapp_share_urls?.[0]?.url;
      if (wa) {
        window.open(wa, "_blank", "noopener,noreferrer");
      }
      toast.success("Booking created! Complete UPI payment.");
      onOpenChange(false);
      navigate(`/booking/${data.id}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Booking failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="booking-dialog" className="sm:max-w-lg bg-[#FFFBF0] border-amber-200">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1">
            <Ticket className="w-5 h-5 text-orange-600" />
            <DialogTitle className="font-display text-2xl text-slate-900">
              Early Bird Pass — ₹{PRICE}
            </DialogTitle>
          </div>
          <DialogDescription className="text-slate-600">
            {soldOut
              ? "Early Bird is sold out."
              : "Limited slots available. Fill details to reserve."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4 mt-2">
          <div>
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              data-testid="booking-name-input"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              disabled={soldOut}
              placeholder="Your name"
            />
          </div>
          <div>
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              data-testid="booking-phone-input"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              disabled={soldOut}
              placeholder="+91..."
            />
          </div>

          <div>
            <Label>Number of Tickets</Label>
            <div className="mt-1.5 flex items-center justify-between rounded-xl border-2 border-amber-300 bg-white p-2">
              <button
                type="button"
                data-testid="qty-minus-btn"
                onClick={() => setForm({ ...form, quantity: Math.max(1, form.quantity - 1) })}
                disabled={soldOut || form.quantity <= 1}
                className="w-11 h-11 rounded-lg bg-amber-100 hover:bg-amber-200 disabled:opacity-40 flex items-center justify-center text-2xl font-bold text-orange-700 transition-colors"
              >
                −
              </button>
              <div className="flex flex-col items-center">
                <span
                  data-testid="booking-quantity-input"
                  className="font-display text-4xl font-black text-slate-900 tabular-nums leading-none"
                >
                  {form.quantity}
                </span>
                <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">
                  {form.quantity === 1 ? "Ticket" : "Tickets"}
                </span>
              </div>
              <button
                type="button"
                data-testid="qty-plus-btn"
                onClick={() => setForm({ ...form, quantity: Math.min(20, form.quantity + 1) })}
                disabled={soldOut || form.quantity >= 20}
                className="w-11 h-11 rounded-lg bg-orange-500 hover:bg-orange-600 disabled:opacity-40 flex items-center justify-center text-2xl font-bold text-white transition-colors shadow-md"
              >
                +
              </button>
            </div>
            <div className="mt-2 flex gap-1.5 flex-wrap">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setForm({ ...form, quantity: n })}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                    form.quantity === n
                      ? "bg-orange-600 text-white"
                      : "bg-amber-50 text-slate-700 hover:bg-amber-100"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              data-testid="booking-email-input"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              disabled={soldOut}
              placeholder="you@email.com"
            />
          </div>

          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 flex items-center justify-between">
            <span className="text-slate-700 font-medium">Total</span>
            <span className="font-display text-2xl font-black text-orange-600" data-testid="booking-total">
              ₹{total}
            </span>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed">
            Alcoholic beverages are available for purchase at the venue for guests aged 21+. Food and drinks are <b>not</b> included in the ticket price.
          </p>

          <button
            type="submit"
            disabled={loading || soldOut}
            data-testid="booking-submit-btn"
            className="pill-btn w-full"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Continue to UPI Payment"}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
