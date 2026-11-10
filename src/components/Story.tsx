"use client";

import { useEffect, useRef } from "react";
import { gsap } from "@/lib/gsap";
import { story } from "@/content/site";
import Frame from "./Frame";

export default function Story() {
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const chapters = gsap.utils.toArray<HTMLElement>("[data-chapter]");
      const tl = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: { trigger: root.current, start: "top top", end: "bottom bottom", scrub: 0.6 },
      });
      tl.fromTo(
        "[data-portrait]",
        { clipPath: "inset(12% 12% 12% 12%)", scale: 1.15 },
        { clipPath: "inset(0% 0% 0% 0%)", scale: 1, duration: chapters.length * 2 },
        0,
      );
      chapters.forEach((ch, i) => {
        const at = i * 2;
        const words = ch.querySelectorAll("[data-word]");
        tl.fromTo(ch, { autoAlpha: 0, y: 40 }, { autoAlpha: 1, y: 0, duration: 0.4 }, at);
        tl.fromTo(words, { opacity: 0.14 }, { opacity: 1, duration: 0.2, stagger: 1 / words.length }, at + 0.2);
        if (i < chapters.length - 1) tl.to(ch, { autoAlpha: 0, y: -40, duration: 0.35 }, at + 1.65);
        tl.to("[data-bar]", { scaleX: (i + 1) / chapters.length, duration: 2 }, at);
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={root}
      id="story"
      className="relative"
      style={{ height: `${story.chapters.length * 110 + 60}vh` }}
    >
      <div className="sticky top-0 grid h-svh grid-rows-[38svh_1fr] gap-6 overflow-hidden px-5 pb-8 pt-24 md:grid-cols-12 md:grid-rows-1 md:gap-10 md:px-10 md:pb-12">
        <div className="md:col-span-5">
          <div data-portrait className="h-full">
            <Frame
              src={story.portrait}
              alt={`${story.artist} at work`}
              label="Artist portrait — arriving soon"
              className="h-full w-full"
              sizes="(min-width: 768px) 40vw, 100vw"
            />
          </div>
        </div>

        <div className="relative md:col-span-6 md:col-start-7">
          <p className="label">The story</p>
          {story.chapters.map((c) => (
            <article key={c.no} data-chapter className="absolute inset-x-0 top-10 md:top-1/2 md:-translate-y-1/2">
              <p className="mb-5 flex items-baseline gap-4">
                <span className="font-mono text-xs text-neon">{c.no}</span>
                <span className="label !text-ink/80">{c.title}</span>
              </p>
              <p className="font-display text-[8.2vw] leading-[1.08] tracking-[-0.01em] md:text-[3.4vw]">
                {c.text.split(" ").map((w, i) => (
                  <span key={i} data-word>
                    {w}{" "}
                  </span>
                ))}
              </p>
            </article>
          ))}
          <div className="absolute inset-x-0 bottom-0 h-px bg-line">
            <div data-bar className="h-full origin-left scale-x-0 bg-neon shadow-[0_0_12px_var(--neon)]" />
          </div>
        </div>
      </div>
    </section>
  );
}
