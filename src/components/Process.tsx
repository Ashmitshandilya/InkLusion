"use client";

import { useEffect, useRef, useState } from "react";
import { gsap } from "@/lib/gsap";
import { process } from "@/content/site";

const P = { pathLength: 1, className: "draw" } as const;

/** Right half of the moth; mirrored for the left. */
function Wing() {
  return (
    <>
      <path {...P} d="M205 175 C216 150 236 136 258 134" />
      <path {...P} d="M212 200 C250 150 320 120 368 132 C376 180 350 232 300 250 C266 260 232 244 213 226" />
      <path {...P} d="M222 208 C258 172 310 150 348 152 C350 186 330 218 294 232 C268 238 240 230 224 220" />
      <path {...P} d="M214 212 C250 196 290 176 340 150" />
      <path {...P} d="M214 218 C256 214 300 214 344 196" />
      <circle {...P} cx="300" cy="190" r="16" />
      <circle className="fill" cx="300" cy="190" r="6" />
      <path {...P} d="M212 232 C246 252 296 262 312 300 C318 336 290 366 258 356 C232 346 214 300 209 250" />
      <path {...P} d="M220 250 C246 264 282 276 292 304 C296 328 278 344 260 338" />
      <circle {...P} cx="268" cy="306" r="9" />
      <circle className="fill" cx="268" cy="306" r="3" />
      <path {...P} d="M200 392 C218 382 232 388 236 402 C220 406 208 402 200 392" />
      <path {...P} d="M200 416 C216 408 228 413 231 425 C217 428 207 425 200 416" />
      <path {...P} d="M200 438 C212 432 221 436 223 445 C213 447 205 445 200 438" />
    </>
  );
}

export default function Process() {
  const root = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const draw = gsap.utils.toArray<SVGElement>(".draw");
      gsap.set(draw, { strokeDasharray: 1, strokeDashoffset: 1, stroke: "#6f6873", strokeWidth: 1 });
      gsap.set(".fill", { opacity: 0, fill: "#f4eef2" });
      gsap.set(".guide", { opacity: 0 });

      const tl = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: {
          trigger: root.current,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.5,
          onUpdate: (st) => setActive(Math.min(process.length - 1, Math.floor(st.progress * process.length))),
        },
      });
      // 01 talk: construction lines
      tl.to(".guide", { opacity: 1, duration: 0.8 }, 0.1)
        // 02 sketch: pencil lines draw in
        .to(draw, { strokeDashoffset: 0, duration: 0.7, stagger: 0.3 / draw.length }, 1)
        // 03 stencil: violet transfer
        .to(draw, { stroke: "#8b5cf6", duration: 0.5 }, 2.1)
        .to(".guide", { opacity: 0, duration: 0.5 }, 2.1)
        // 04 ink
        .to(draw, { stroke: "#f4eef2", strokeWidth: 1.9, duration: 0.6, stagger: 0.3 / draw.length }, 3.05)
        .to(".fill", { opacity: 1, duration: 0.4 }, 3.5)
        // 05 heal: settles, glows
        .to("[data-art]", { scale: 1.05, duration: 0.9 }, 4.05)
        .to("[data-halo]", { opacity: 1, duration: 0.9 }, 4.05)
        .to({}, { duration: 0.05 }, 4.95);
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} id="process" className="relative" style={{ height: `${process.length * 100}vh` }}>
      <div className="sticky top-0 grid h-svh grid-rows-[46svh_1fr] overflow-hidden px-5 pt-20 md:grid-cols-12 md:grid-rows-1 md:px-10">
        <div className="relative flex items-center justify-center md:col-span-6">
          <div
            data-halo
            className="absolute h-[70%] w-[70%] rounded-full opacity-0 blur-3xl"
            style={{ background: "radial-gradient(circle, rgba(255,43,214,.32), transparent 65%)" }}
          />
          <svg
            data-art
            viewBox="0 0 400 480"
            className="relative h-full max-h-[78svh] w-auto"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            role="img"
            aria-label="A moth tattoo being drawn step by step"
          >
            <g className="guide" stroke="#4a444d" strokeWidth="0.75" strokeDasharray="3 6">
              <circle cx="200" cy="232" r="172" />
              <path d="M200 20 V460 M20 232 H380 M78 110 L322 354 M322 110 L78 354" />
            </g>
            <path {...P} d="M216 54 A34 34 0 1 0 216 116 A26 26 0 1 1 216 54 Z" />
            <circle {...P} cx="200" cy="182" r="9" />
            <ellipse {...P} cx="200" cy="212" rx="13" ry="23" />
            <path {...P} d="M190 232 C186 270 194 318 200 334 C206 318 214 270 210 232" />
            <path {...P} d="M189 256 H211 M190 276 H210 M193 296 H207" />
            <path {...P} d="M200 350 V452" />
            <Wing />
            <g transform="translate(400 0) scale(-1 1)">
              <Wing />
            </g>
            <circle className="fill" cx="150" cy="70" r="1.6" />
            <circle className="fill" cx="262" cy="88" r="1.6" />
            <circle className="fill" cx="128" cy="100" r="1.1" />
            <circle className="fill" cx="282" cy="58" r="1.1" />
          </svg>
        </div>

        <div className="flex flex-col justify-start pb-8 md:col-span-5 md:col-start-8 md:justify-center">
          <p className="label mb-6 md:mb-10">The process</p>
          <ol>
            {process.map((s, i) => {
              const on = i === active;
              return (
                <li
                  key={s.no}
                  className={`border-t border-line py-4 transition-opacity duration-500 md:py-5 ${
                    on ? "opacity-100" : "hidden opacity-30 md:block"
                  }`}
                >
                  <div className="flex items-baseline gap-5">
                    <span className={`font-mono text-xs ${on ? "text-neon" : "text-muted"}`}>{s.no}</span>
                    <h3 className={`font-display text-5xl md:text-4xl ${on ? "glow italic text-neon" : ""}`}>
                      {s.title}
                    </h3>
                  </div>
                  <div
                    className={`grid transition-[grid-template-rows] duration-500 ${
                      on ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                    }`}
                  >
                    <p className="max-w-md overflow-hidden pl-9 text-base leading-relaxed text-ink/70">
                      <span className="block pt-3">{s.text}</span>
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
          <p className="label mt-6 md:hidden">
            {String(active + 1).padStart(2, "0")} / {String(process.length).padStart(2, "0")}
          </p>
        </div>
      </div>
    </section>
  );
}
