"use client";

import { useEffect, useRef } from "react";
import { gsap } from "@/lib/gsap";
import { work } from "@/content/site";
import Frame from "./Frame";

export default function Work() {
  const root = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.to(track.current, {
        x: () => -(track.current!.scrollWidth - window.innerWidth),
        ease: "none",
        scrollTrigger: {
          trigger: root.current,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.5,
          invalidateOnRefresh: true,
        },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="work" className="relative" style={{ height: `${work.length * 55}vh` }}>
      <div className="sticky top-0 flex h-svh flex-col justify-center overflow-hidden pt-16">
        <div className="mb-8 flex items-end justify-between px-5 md:px-10">
          <h2 className="font-display text-6xl leading-none md:text-8xl">
            Selected <span className="italic text-neon">work</span>
          </h2>
          <p className="label hidden md:block">Scroll →</p>
        </div>
        <div ref={track} className="flex w-max gap-5 px-5 will-change-transform md:gap-8 md:px-10">
          {work.map((w, i) => (
            <figure key={w.title} className={`group w-[72vw] shrink-0 md:w-[27vw] ${i % 2 ? "md:mt-14" : ""}`}>
              <Frame
                src={w.src}
                alt={`${w.style} tattoo on ${w.placement}`}
                label={`Tattoo photo ${String(i + 1).padStart(2, "0")}`}
                className="aspect-[4/5] w-full transition-[filter] duration-500 group-hover:brightness-125"
                sizes="(min-width: 768px) 27vw, 72vw"
              />
              <figcaption className="mt-4 flex items-baseline justify-between">
                <span className="font-display text-2xl">{w.style}</span>
                <span className="label">{w.placement}</span>
              </figcaption>
            </figure>
          ))}
          <div className="flex w-[60vw] shrink-0 flex-col justify-center md:w-[24vw]">
            <p className="font-display text-4xl leading-tight">The full gallery opens with the next build.</p>
            <p className="label mt-4">Filter by style and placement</p>
          </div>
        </div>
      </div>
    </section>
  );
}
