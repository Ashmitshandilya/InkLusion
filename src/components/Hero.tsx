"use client";

import { useEffect, useRef } from "react";
import { gsap } from "@/lib/gsap";
import { booking, hero, styles, wa } from "@/content/site";

export default function Hero() {
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from("[data-rise]", { yPercent: 115, duration: 1.4, ease: "expo.out", stagger: 0.1, delay: 0.2 });
      gsap.from("[data-fade]", { opacity: 0, y: 16, duration: 1, delay: 1, stagger: 0.12 });
      gsap.to("[data-hero-copy]", {
        yPercent: -22,
        opacity: 0,
        ease: "none",
        scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="top" className="relative flex h-svh min-h-[600px] flex-col overflow-hidden">
      <div data-hero-copy className="flex flex-1 flex-col justify-end px-5 pb-10 md:px-10 md:pb-12">
        <p data-fade className="label mb-2 md:mb-0">
          <span className="mr-3 inline-block h-1.5 w-1.5 rounded-full bg-neon align-middle shadow-[0_0_12px_var(--neon)]" />
          {hero.eyebrow}
        </p>
        <h1 className="-ml-[0.04em] overflow-hidden pb-[0.06em] font-display text-[25.5vw] leading-[0.9] tracking-[-0.04em] md:text-[24.5vw]">
          <span data-rise className="inline-block">
            Ink
          </span>
          <span data-rise className="glow inline-block pr-[0.08em] italic text-neon">
            Lusion
          </span>
        </h1>
        <div className="mt-6 flex flex-col gap-6 border-t border-line pt-6 md:flex-row md:items-center md:justify-between">
          <p data-fade className="max-w-md text-base leading-relaxed text-ink/80">
            {hero.sub}
          </p>
          <div data-fade className="flex flex-wrap gap-3">
            <a href={wa(booking.message)} target="_blank" rel="noreferrer" className="btn">
              Book on WhatsApp
            </a>
            <a href="#work" className="btn btn-ghost">
              See the work
            </a>
          </div>
        </div>
      </div>

      <div className="overflow-hidden border-y border-line bg-bg/40 py-4 backdrop-blur-sm" aria-hidden>
        <div className="marquee flex w-max gap-10 whitespace-nowrap">
          {[...styles, ...styles, ...styles, ...styles].map((s, i) => (
            <span key={i} className="label flex items-center gap-10">
              {s}
              <span className="text-neon">✦</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
