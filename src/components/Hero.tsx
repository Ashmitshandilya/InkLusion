"use client";

import { useEffect, useRef } from "react";
import { gsap } from "@/lib/gsap";
import { hero, styles } from "@/content/site";
import InkCanvas from "./InkCanvas";

export default function Hero() {
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from("[data-rise]", {
        yPercent: 115,
        duration: 1.3,
        ease: "expo.out",
        stagger: 0.12,
        delay: 0.15,
      });
      gsap.from("[data-fade]", { opacity: 0, y: 16, duration: 1, delay: 0.9, stagger: 0.12 });
      gsap.to("[data-hero-copy]", {
        yPercent: -28,
        opacity: 0,
        ease: "none",
        scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="top" className="relative flex h-svh min-h-[600px] flex-col overflow-hidden">
      <InkCanvas />
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-bg" />

      <div data-hero-copy className="relative z-10 flex flex-1 flex-col justify-end px-5 pb-24 md:px-10 md:pb-28">
        <p data-fade className="label mb-6">
          <span className="mr-3 inline-block h-1.5 w-1.5 rounded-full bg-neon align-middle shadow-[0_0_12px_var(--neon)]" />
          {hero.eyebrow}
        </p>
        <h1 className="font-display text-[19vw] leading-[0.86] tracking-[-0.03em] md:text-[12.5vw]">
          <span className="block overflow-hidden pb-[0.08em]">
            <span data-rise className="block">
              {hero.lines[0]}
            </span>
          </span>
          <span className="block overflow-hidden pb-[0.12em]">
            <span data-rise className="glow block italic text-neon">
              {hero.lines[1]}
            </span>
          </span>
        </h1>
        <div className="mt-8 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <p data-fade className="max-w-sm text-base leading-relaxed text-ink/70">
            {hero.sub}
          </p>
          <div data-fade className="flex flex-wrap gap-3">
            <a href="#book" className="btn">
              Book a slot
            </a>
            <a href="#ideas" className="btn btn-ghost">
              Find your idea
            </a>
          </div>
        </div>
      </div>

      <div className="relative z-10 overflow-hidden border-y border-line py-4" aria-hidden>
        <div className="marquee flex w-max gap-10 whitespace-nowrap">
          {[...styles, ...styles, ...styles, ...styles].map((s, i) => (
            <span key={i} className="label flex items-center gap-10">
              {s}
              <span className="h-1 w-1 rounded-full bg-neon" />
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
