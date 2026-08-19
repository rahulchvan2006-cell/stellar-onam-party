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
          <div className="grid grid-cols-2 gap-3">
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
              <Label htmlFor="qty">Tickets</Label>
              <Input
                id="qty"
                data-testid="booking-quantity-input"
                type="number"
                min={1}
                max={Math.min(10, remaining || 1)}
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: Math.max(1, Number(e.target.value)) })}
                disabled={soldOut}
              />
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
