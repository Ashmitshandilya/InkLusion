import { booking, site, wa } from "@/content/site";

export default function Booking() {
  const { contact } = site;
  return (
    <section id="book" className="relative overflow-hidden border-t border-line px-5 pt-28 md:px-10 md:pt-44">
      <div
        className="pointer-events-none absolute -bottom-1/2 left-1/2 h-[90vh] w-[120vw] -translate-x-1/2 rounded-full blur-3xl"
        style={{ background: "radial-gradient(closest-side, rgba(255,43,214,.2), transparent)" }}
        aria-hidden
      />
      <div className="relative grid gap-14 md:grid-cols-12">
        <div className="md:col-span-7">
          <p className="label mb-6">Booking</p>
          <h2 className="font-display text-[19vw] leading-[0.88] tracking-[-0.02em] md:text-[10vw]">
            Book a <span className="glow italic text-neon">slot</span>
          </h2>
          <p className="mt-8 max-w-md text-base leading-relaxed text-ink/80">{booking.text}</p>
          <div className="mt-10 flex flex-wrap items-center gap-5">
            <a href={wa(booking.message)} target="_blank" rel="noreferrer" className="btn">
              WhatsApp {contact.whatsappDisplay}
            </a>
            <a href={contact.instagram} target="_blank" rel="noreferrer" className="btn btn-ghost">
              Instagram
            </a>
          </div>
        </div>

        <div className="md:col-span-4 md:col-start-9 md:self-end">
          <p className="label mb-4">Starting prices</p>
          <dl>
            {booking.prices.map((p) => (
              <div key={p.label} className="flex items-baseline justify-between border-t border-line py-5">
                <dt>
                  <span className="font-display text-3xl">{p.label}</span>
                  <span className="ml-3 text-sm text-muted">{p.note}</span>
                </dt>
                <dd className="font-mono text-sm text-ink/80">{p.from}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-5 border-l border-neon pl-4 text-sm leading-relaxed text-ink/80">{booking.negotiable}</p>
        </div>
      </div>

      <footer className="relative mt-28 border-t border-line py-8 md:mt-36">
        <div className="flex flex-col gap-3 md:flex-row md:items-baseline md:justify-between">
          <p className="label !text-ink">
            {site.name} <span className="text-neon">✦</span> {site.city}
          </p>
          <p className="label">
            <a href={contact.instagram} target="_blank" rel="noreferrer" className="hover:text-ink">
              {contact.instagramHandle}
            </a>
          </p>
        </div>
      </footer>
    </section>
  );
}
