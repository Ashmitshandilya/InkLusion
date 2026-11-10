import { booking, site } from "@/content/site";

export default function Booking() {
  return (
    <section id="book" className="relative overflow-hidden border-t border-line px-5 py-28 md:px-10 md:py-44">
      <div
        className="pointer-events-none absolute -bottom-1/2 left-1/2 h-[90vh] w-[120vw] -translate-x-1/2 rounded-full blur-3xl"
        style={{ background: "radial-gradient(closest-side, rgba(255,43,214,.22), transparent)" }}
        aria-hidden
      />
      <div className="relative grid gap-14 md:grid-cols-12">
        <div className="md:col-span-7">
          <p className="label mb-6">Booking</p>
          <h2 className="font-display text-[17vw] leading-[0.88] tracking-[-0.02em] md:text-[9.5vw]">
            {booking.heading[0]}
            <br />
            <span className="glow italic text-neon">{booking.heading[1]}</span>
          </h2>
          <p className="mt-8 max-w-md text-base leading-relaxed text-ink/70">{booking.text}</p>
          <div className="mt-10 flex flex-wrap items-center gap-5">
            <span className="btn" aria-disabled>
              Request a slot
            </span>
            <span className="label">Slot picker arrives with the next build</span>
          </div>
        </div>

        <div className="md:col-span-4 md:col-start-9 md:self-end">
          <p className="label mb-4">Starting from</p>
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

      <footer className="relative mt-32 flex flex-col gap-3 border-t border-line pt-8 md:flex-row md:justify-between">
        <p className="font-display text-2xl">
          Ink<span className="italic text-neon">Lusion</span>
        </p>
        <p className="label">
          © {site.name} {site.city && `· ${site.city}`}
        </p>
      </footer>
    </section>
  );
}
