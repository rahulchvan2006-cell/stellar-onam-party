import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Marquee from "react-fast-marquee";
import {
  Music,
  Sparkles,
  Utensils,
  Users,
  Camera,
  Flower2,
  Flame,
  Sailboat,
  Leaf,
  MapPin,
  Calendar,
  Clock,
  Phone,
  Instagram,
  Facebook,
} from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import Countdown from "@/components/Countdown";
import BookingDialog from "@/components/BookingDialog";
import { api } from "@/lib/api";

const PALM = "https://images.pexels.com/photos/38601629/pexels-photo-38601629.jpeg";
const BAND = "https://images.pexels.com/photos/33284931/pexels-photo-33284931.jpeg";
const DJ = "https://images.pexels.com/photos/9534908/pexels-photo-9534908.jpeg";

export default function Landing() {
  const [info, setInfo] = useState(null);
  const [openBooking, setOpenBooking] = useState(false);

  useEffect(() => {
    api.get("/event/info").then((r) => setInfo(r.data)).catch(() => {});
    const id = setInterval(() => {
      api.get("/event/info").then((r) => setInfo(r.data)).catch(() => {});
    }, 15000);
    return () => clearInterval(id);
  }, []);

  const remaining = info?.early_bird_remaining ?? 45;
  const soldOut = info?.sold_out;

  return (
    <div className="min-h-screen cream-bg pb-24 md:pb-0">
      {/* NAV */}
      <nav className="absolute top-0 left-0 right-0 z-40 px-4 sm:px-10 py-4 sm:py-5 flex items-center justify-between">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/70 backdrop-blur-md border border-white/20">
          <Flower2 className="w-4 h-4 text-amber-300" />
          <span className="font-display text-[10px] sm:text-sm font-bold tracking-[0.2em] sm:tracking-[0.25em] gold-text uppercase">
            Stellar Entertainment
          </span>
        </div>
        <button
          data-testid="nav-book-btn"
          onClick={() => setOpenBooking(true)}
          className="hidden md:inline-flex pill-btn-outline"
        >
          Book Now
        </button>
      </nav>

      {/* HERO */}
      <section className="relative sky-bg overflow-hidden min-h-screen flex flex-col justify-center items-center text-center px-5 pt-20 pb-16 grain-overlay">
        {/* palm leaves */}
        <img
          src={PALM}
          alt=""
          className="absolute top-0 left-0 w-48 sm:w-72 md:w-96 h-full object-cover opacity-90 palm-left pointer-events-none"
          style={{ maskImage: "linear-gradient(to right, black 30%, transparent 100%)", WebkitMaskImage: "linear-gradient(to right, black 30%, transparent 100%)" }}
        />
        <img
          src={PALM}
          alt=""
          className="absolute top-0 right-0 w-48 sm:w-72 md:w-96 h-full object-cover opacity-90 pointer-events-none"
          style={{ maskImage: "linear-gradient(to left, black 30%, transparent 100%)", WebkitMaskImage: "linear-gradient(to left, black 30%, transparent 100%)" }}
        />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="relative z-10 max-w-4xl"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/70 backdrop-blur-md border border-amber-300 mb-6">
            <Sparkles className="w-3.5 h-3.5 text-orange-600" />
            <span className="text-[10px] sm:text-xs uppercase tracking-[0.3em] font-semibold text-slate-800">
              First Ever in Namma Mysore
            </span>
          </div>

          <h1 className="onam-3d font-display font-black text-7xl sm:text-8xl md:text-9xl leading-none">
            ONAM
          </h1>
          <div className="font-script gold-text text-5xl sm:text-6xl md:text-7xl -mt-4 sm:-mt-6 mb-4">
            Party
          </div>

          <p className="font-display italic text-lg sm:text-xl text-slate-900/90 mb-8 max-w-xl mx-auto">
            One Vibe. Our People. Endless Memories.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 mb-8 text-slate-900">
            <div className="flex items-center gap-2 text-sm sm:text-base">
              <Calendar className="w-4 h-4 text-orange-600" />
              <span className="font-semibold">29th August</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-slate-700 hidden sm:block" />
            <div className="flex items-center gap-2 text-sm sm:text-base">
              <Clock className="w-4 h-4 text-orange-600" />
              <span className="font-semibold">4:00 PM onwards</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-slate-700 hidden sm:block" />
            <div className="flex items-center gap-2 text-sm sm:text-base">
              <MapPin className="w-4 h-4 text-orange-600" />
              <span className="font-semibold">Serenity Groove, Mysore</span>
            </div>
          </div>

          {info?.date_iso && <Countdown targetIso={info.date_iso} />}

          <div className="mt-8 flex flex-col items-center gap-3">
            <div
              data-testid="slots-badge"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-orange-600 text-white text-xs sm:text-sm font-semibold shadow-lg"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {soldOut ? "SOLD OUT" : `Early Bird — Only ${remaining} of 45 slots left!`}
            </div>
            <button
              data-testid="hero-book-btn"
              onClick={() => setOpenBooking(true)}
              disabled={soldOut}
              className="pill-btn text-lg"
            >
              {soldOut ? "Sold Out" : "Book Now — ₹499"}
            </button>
          </div>
        </motion.div>
      </section>

      {/* MARQUEE */}
      <div className="bg-orange-600 py-3 border-y-4 border-amber-400">
        <Marquee gradient={false} speed={40}>
          {Array.from({ length: 8 }).map((_, i) => (
            <span key={i} className="mx-8 font-display italic text-white text-xl sm:text-2xl">
              One Vibe · Our People · Endless Memories · <Flower2 className="inline w-5 h-5 mb-1" /> ·
            </span>
          ))}
        </Marquee>
      </div>

      {/* ABOUT */}
      <section className="cream-bg py-20 px-5">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">About the Event</p>
          <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900 mb-6">
            A Kerala Celebration Like Never Before
          </h2>
          <div className="gold-divider w-32 mx-auto mb-6" />
          <p className="text-slate-700 leading-relaxed text-base sm:text-lg">
            Stellar Entertainment brings the spirit of God's Own Country to Mysore for one unforgettable evening.
            Expect pookalams, sadya vibes, traditional games, a live Kerala band, and a high-energy DJ night —
            all rolled into one grand Onam bash. Come home to your people.
          </p>
        </div>
      </section>

      {/* LINEUP */}
      <section className="py-20 px-5" style={{ background: "linear-gradient(180deg, #FDFBF7 0%, #FFF3D6 100%)" }}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">Featuring</p>
            <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900">Live Kerala Band + DJ Night</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              { img: BAND, title: "Live Kerala Band", sub: "Malayalam hits, folk beats & fusion sounds", icon: Music },
              { img: DJ, title: "DJ Night", sub: "Bollywood · Malayalam · House · Party bangers", icon: Sparkles },
            ].map((c) => (
              <motion.div
                key={c.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="card-warm overflow-hidden"
              >
                <img src={c.img} alt={c.title} className="w-full h-64 object-cover" />
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-amber-100 border border-amber-300 flex items-center justify-center">
                      <c.icon className="w-5 h-5 text-orange-600" />
                    </div>
                    <h3 className="font-display text-2xl font-bold text-slate-900">{c.title}</h3>
                  </div>
                  <p className="text-slate-600">{c.sub}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* HIGHLIGHTS */}
      <section className="cream-bg py-20 px-5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">The Vibe</p>
            <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900">What's Waiting for You</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { Icon: Music, t: "Live Music" },
              { Icon: Sparkles, t: "Traditional Fun" },
              { Icon: Utensils, t: "Onam Feast" },
              { Icon: Users, t: "Good People, Great Vibes" },
              { Icon: Camera, t: "Memories Worth Keeping" },
            ].map(({ Icon, t }) => (
              <motion.div
                key={t}
                whileHover={{ y: -4 }}
                className="card-warm p-6 text-center"
              >
                <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-gradient-to-br from-amber-300 to-orange-500 flex items-center justify-center shadow-md">
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <p className="font-semibold text-slate-900 text-sm sm:text-base">{t}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* TRADITIONS */}
      <section className="py-20 px-5" style={{ background: "linear-gradient(180deg, #FFF3D6 0%, #FDFBF7 100%)" }}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">Rooted in Tradition</p>
            <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900">Traditions & Games</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { Icon: Flower2, t: "Pookalam", d: "Floral rangoli welcomes King Mahabali" },
              { Icon: Flame, t: "Nilavilakku", d: "Brass lamp ceremony to bless the evening" },
              { Icon: Sailboat, t: "Vallam Kali Vibes", d: "Kerala's spirit on land" },
              { Icon: Leaf, t: "Sadya Feels", d: "Banana leaf feast experience" },
            ].map(({ Icon, t, d }) => (
              <div key={t} className="card-warm p-6 text-center float-slow">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white border-2 border-amber-400 flex items-center justify-center shadow-inner">
                  <Icon className="w-8 h-8 text-orange-600" />
                </div>
                <h4 className="font-display text-lg font-bold text-slate-900 mb-1">{t}</h4>
                <p className="text-xs text-slate-600">{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VENUE */}
      <section className="cream-bg py-20 px-5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">Venue & Location</p>
            <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900">Serenity Groove, Mysore</h2>
          </div>
          <div className="card-warm overflow-hidden">
            <iframe
              title="venue"
              width="100%"
              height="360"
              src="https://www.google.com/maps?q=Serenity+Groove+Mysore&output=embed"
              style={{ border: 0 }}
            />
            <div className="p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <MapPin className="w-5 h-5 text-orange-600" />
                <span className="text-slate-800">Serenity Groove, Mysore, Karnataka</span>
              </div>
              <a
                href="https://www.google.com/maps/search/?api=1&query=Serenity+Groove+Mysore"
                target="_blank"
                rel="noreferrer"
                className="pill-btn-outline"
                data-testid="get-directions-btn"
              >
                Get Directions
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* TICKETS */}
      <section id="tickets" className="py-20 px-5" style={{ background: "linear-gradient(180deg, #FFF3D6 0%, #FDFBF7 100%)" }}>
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">Book Your Pass</p>
            <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900">Early Bird Pass</h2>
          </div>
          <div className="card-warm p-8 sm:p-10 relative overflow-hidden">
            <div className="absolute -top-6 -right-6 w-32 h-32 rounded-full bg-gradient-to-br from-amber-300 to-orange-500 opacity-20" />
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-xs uppercase tracking-widest text-orange-600 font-semibold">Entry Only</p>
                  <h3 className="font-display text-3xl font-black text-slate-900">Early Bird Pass</h3>
                </div>
                <div className="text-right">
                  <div className="font-display text-5xl font-black gold-text">₹499</div>
                </div>
              </div>
              <ul className="space-y-2 text-slate-700 mb-6">
                <li>· Full entry to Onam Party</li>
                <li>· Live Kerala Band + DJ Night access</li>
                <li>· Traditional games & pookalam experience</li>
                <li>· Only 45 slots available</li>
              </ul>

              <div className="rounded-xl bg-orange-50 border border-orange-200 p-4 mb-6">
                <p className="text-sm text-slate-800">
                  <b>{soldOut ? "SOLD OUT" : `${remaining} of 45 slots left`}</b> — book fast before it's gone.
                </p>
              </div>

              <button
                onClick={() => setOpenBooking(true)}
                disabled={soldOut}
                data-testid="tickets-book-btn"
                className="pill-btn w-full text-lg"
              >
                {soldOut ? "Sold Out" : "Book Early Bird — ₹499"}
              </button>

              <p className="text-xs text-slate-500 mt-6 leading-relaxed">
                Alcoholic beverages are available for purchase at the venue for guests aged <b>21 years and above</b>.
                Food and drinks are <b>not</b> included in the ticket price.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="cream-bg py-20 px-5">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs uppercase tracking-[0.3em] text-orange-600 font-semibold mb-3">Good to Know</p>
            <h2 className="font-display text-4xl sm:text-5xl font-black text-slate-900">FAQs</h2>
          </div>
          <Accordion type="single" collapsible className="card-warm p-4 sm:p-6">
            <AccordionItem value="1">
              <AccordionTrigger data-testid="faq-1">What are the entry rules?</AccordionTrigger>
              <AccordionContent>
                Carry a valid photo ID. Entry is only with a confirmed e-pass sent via WhatsApp/SMS.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="2">
              <AccordionTrigger data-testid="faq-2">Is parking available?</AccordionTrigger>
              <AccordionContent>
                Yes, ample parking is available at Serenity Groove for both cars and two-wheelers.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="3">
              <AccordionTrigger data-testid="faq-3">Is food included in the ticket?</AccordionTrigger>
              <AccordionContent>
                No. Food and drinks are available for purchase at the venue and are not included in the ticket price.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="4">
              <AccordionTrigger data-testid="faq-4">What's the age policy?</AccordionTrigger>
              <AccordionContent>
                The event is open to all ages. Alcoholic beverages are strictly served only to guests aged 21+.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="5">
              <AccordionTrigger data-testid="faq-5">Refund policy?</AccordionTrigger>
              <AccordionContent>
                Tickets are non-refundable. In case of cancellation of the event by the organizer, full refunds
                will be initiated within 7 working days.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-slate-900 text-slate-200 py-14 px-5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-10">
          <div>
            <div className="font-display text-sm font-bold tracking-[0.25em] gold-text uppercase mb-3">
              Stellar Entertainment
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              Bringing the vibe of Kerala to Namma Mysore. Onam Party 2026 — one night, endless memories.
            </p>
          </div>
          <div>
            <h5 className="font-semibold mb-3 text-white">Contact</h5>
            <div className="space-y-2 text-sm">
              <a href="tel:+917483557316" className="flex items-center gap-2 hover:text-orange-400" data-testid="contact-kiran">
                <Phone className="w-4 h-4" /> Kiran — +91 7483 557 316
              </a>
              <a href="tel:+919844912006" className="flex items-center gap-2 hover:text-orange-400" data-testid="contact-rahul">
                <Phone className="w-4 h-4" /> Rahul — +91 98449 12006
              </a>
            </div>
          </div>
          <div>
            <h5 className="font-semibold mb-3 text-white">Follow</h5>
            <div className="flex gap-3">
              <a href="#" className="w-10 h-10 rounded-full bg-white/10 hover:bg-orange-500 flex items-center justify-center transition-colors" data-testid="social-instagram">
                <Instagram className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-white/10 hover:bg-orange-500 flex items-center justify-center transition-colors" data-testid="social-facebook">
                <Facebook className="w-5 h-5" />
              </a>
            </div>
            <p className="text-xs text-slate-500 mt-6 leading-relaxed">
              Alcoholic beverages available for purchase at venue for guests aged <b>21+</b>. Food & drinks not included.
            </p>
          </div>
        </div>
        <div className="max-w-5xl mx-auto mt-10 pt-6 border-t border-white/10 text-xs text-slate-500 flex flex-wrap items-center justify-between gap-3">
          <span>© 2026 Stellar Entertainment. All rights reserved.</span>
          <a href="/admin" className="hover:text-orange-400" data-testid="admin-link">Admin</a>
        </div>
      </footer>

      {/* Sticky Mobile CTA */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 p-3 bg-white/90 backdrop-blur-xl border-t border-amber-200">
        <button
          data-testid="sticky-book-btn"
          onClick={() => setOpenBooking(true)}
          disabled={soldOut}
          className="pill-btn w-full"
        >
          {soldOut ? "Sold Out" : `Book Now · ₹499 (${remaining} left)`}
        </button>
      </div>

      <BookingDialog open={openBooking} onOpenChange={setOpenBooking} remaining={remaining} />
    </div>
  );
}
