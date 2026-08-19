import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Loader2, LogOut, Ticket, IndianRupee, Users, Eye, Check, X } from "lucide-react";

export default function Admin() {
  const [token, setToken] = useState(localStorage.getItem("admin_token") || "");
  const [pw, setPw] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const load = async (t = token) => {
    if (!t) return;
    setLoading(true);
    try {
      const { data } = await api.get("/admin/bookings", { headers: { "X-Admin-Password": t } });
      setData(data);
    } catch (e) {
      if (e?.response?.status === 401) {
        localStorage.removeItem("admin_token");
        setToken("");
        toast.error("Session expired");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (token) load(token); /* eslint-disable-next-line */ }, []);

  const login = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post("/admin/login", { password: pw });
      localStorage.setItem("admin_token", data.token);
      setToken(data.token);
      load(data.token);
    } catch {
      toast.error("Invalid password");
    }
  };

  const confirm = async (id) => {
    try {
      await api.post(`/admin/bookings/${id}/confirm`, {}, { headers: { "X-Admin-Password": token } });
      toast.success("Confirmed");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    }
  };

  const reject = async (id) => {
    if (!window.confirm("Reject this booking?")) return;
    try {
      await api.post(`/admin/bookings/${id}/reject`, {}, { headers: { "X-Admin-Password": token } });
      toast.success("Rejected");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to reject");
    }
  };

  const viewScreenshot = async (id) => {
    try {
      const { data } = await api.get(`/admin/bookings/${id}/screenshot`, { headers: { "X-Admin-Password": token } });
      setPreview(data.data_url);
    } catch {
      toast.error("No screenshot found");
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen pattern-bg flex items-center justify-center px-5">
        <form onSubmit={login} className="card-warm p-8 w-full max-w-sm">
          <h1 className="font-display text-3xl font-black text-slate-900 mb-6 text-center">Admin Login</h1>
          <Label htmlFor="pw">Password</Label>
          <Input
            id="pw"
            type="password"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            data-testid="admin-password-input"
            className="mb-4"
          />
          <button type="submit" className="pill-btn w-full" data-testid="admin-login-btn">Sign In</button>
        </form>
      </div>
    );
  }

  const stats = data?.stats;

  return (
    <div className="min-h-screen pattern-bg py-8 px-5">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-black text-slate-900">Admin — Bookings</h1>
            <p className="text-sm text-slate-500">Onam Party · Stellar Entertainment</p>
          </div>
          <button
            onClick={() => { localStorage.removeItem("admin_token"); setToken(""); }}
            className="pill-btn-outline text-sm"
            data-testid="admin-logout-btn"
          >
            <LogOut className="w-4 h-4 mr-2" /> Logout
          </button>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard icon={Ticket} label="Confirmed" value={`${stats.confirmed_slots}/${stats.total_slots}`} />
            <StatCard icon={Users} label="Held (Pending)" value={stats.held_slots} />
            <StatCard icon={Ticket} label="Remaining" value={stats.remaining_slots} />
            <StatCard icon={IndianRupee} label="Revenue" value={`₹${stats.revenue}`} />
          </div>
        )}

        <div className="card-warm overflow-hidden">
          {loading ? (
            <div className="p-10 text-center"><Loader2 className="w-6 h-6 animate-spin mx-auto text-orange-600" /></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="bookings-table">
                <thead className="bg-amber-100 text-slate-800 uppercase text-xs">
                  <tr>
                    <th className="text-left px-4 py-3">Name</th>
                    <th className="text-left px-4 py-3">Contact</th>
                    <th className="text-left px-4 py-3">Qty</th>
                    <th className="text-left px-4 py-3">Amount</th>
                    <th className="text-left px-4 py-3">Status</th>
                    <th className="text-left px-4 py-3">Screenshot</th>
                    <th className="text-right px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.bookings?.length ? data.bookings.map((b) => (
                    <tr key={b.id} className="border-t border-amber-200" data-testid={`booking-row-${b.id}`}>
                      <td className="px-4 py-3 font-medium text-slate-900">{b.full_name}</td>
                      <td className="px-4 py-3 text-slate-600">
                        <div>{b.phone}</div>
                        <div className="text-xs text-slate-400">{b.email}</div>
                      </td>
                      <td className="px-4 py-3">{b.quantity}</td>
                      <td className="px-4 py-3 font-semibold">₹{b.amount}</td>
                      <td className="px-4 py-3">
                        <StatusPill status={b.status} />
                      </td>
                      <td className="px-4 py-3">
                        {b.has_screenshot ? (
                          <button onClick={() => viewScreenshot(b.id)} className="text-orange-600 hover:underline flex items-center gap-1" data-testid={`view-screenshot-${b.id}`}>
                            <Eye className="w-4 h-4" /> View
                          </button>
                        ) : <span className="text-slate-400 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="inline-flex gap-2">
                          {b.status !== "confirmed" && (
                            <button
                              onClick={() => confirm(b.id)}
                              className="px-3 py-1.5 rounded-full bg-green-600 text-white text-xs font-semibold hover:bg-green-700"
                              data-testid={`confirm-${b.id}`}
                            >
                              <Check className="w-3.5 h-3.5 inline mr-1" /> Confirm
                            </button>
                          )}
                          {b.status !== "rejected" && b.status !== "confirmed" && (
                            <button
                              onClick={() => reject(b.id)}
                              className="px-3 py-1.5 rounded-full bg-red-100 text-red-700 text-xs font-semibold hover:bg-red-200"
                              data-testid={`reject-${b.id}`}
                            >
                              <X className="w-3.5 h-3.5 inline" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan={7} className="text-center py-10 text-slate-500">No bookings yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <Dialog open={!!preview} onOpenChange={() => setPreview(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Payment Screenshot</DialogTitle>
            <DialogDescription>UPI payment proof uploaded by the guest.</DialogDescription>
          </DialogHeader>
          {preview && <img src={preview} alt="screenshot" className="w-full rounded-lg" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="card-warm p-5">
      <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-slate-500 mb-2">
        <Icon className="w-4 h-4 text-orange-600" /> {label}
      </div>
      <div className="font-display text-3xl font-black text-slate-900">{value}</div>
    </div>
  );
}

function StatusPill({ status }) {
  const map = {
    pending: "bg-amber-100 text-amber-800",
    awaiting_verification: "bg-blue-100 text-blue-800",
    confirmed: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
    expired: "bg-slate-200 text-slate-700",
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${map[status] || "bg-slate-100"}`}>
      {status.replace("_", " ")}
    </span>
  );
}
