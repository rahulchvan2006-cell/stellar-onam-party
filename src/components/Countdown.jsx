import { useEffect, useState } from "react";

function calc(target) {
  const diff = Math.max(0, target - Date.now());
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  const secs = Math.floor((diff % 60000) / 1000);
  return { days, hours, mins, secs };
}

export default function Countdown({ targetIso }) {
  const target = new Date(targetIso).getTime();
  const [t, setT] = useState(calc(target));
  useEffect(() => {
    const id = setInterval(() => setT(calc(target)), 1000);
    return () => clearInterval(id);
  }, [target]);

  const cell = (v, l) => (
    <div className="flex flex-col items-center min-w-[64px] sm:min-w-[80px] px-3 py-3 rounded-2xl bg-white/80 backdrop-blur-md border border-amber-200 shadow-lg">
      <span className="font-display text-3xl sm:text-4xl font-black text-slate-900 tabular-nums">
        {String(v).padStart(2, "0")}
      </span>
      <span className="text-[10px] sm:text-xs uppercase tracking-[0.2em] text-slate-600 mt-1">
        {l}
      </span>
    </div>
  );

  return (
    <div data-testid="countdown-timer" className="flex gap-2 sm:gap-3 justify-center">
      {cell(t.days, "Days")}
      {cell(t.hours, "Hrs")}
      {cell(t.mins, "Min")}
      {cell(t.secs, "Sec")}
    </div>
  );
}
