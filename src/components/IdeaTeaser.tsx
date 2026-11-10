"use client";

import { useState } from "react";
import { wa } from "@/content/site";
import { interests, placements, tones, suggest, type Interest, type Placement, type Tone } from "@/lib/ideas";

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm transition-colors ${
        on
          ? "border-neon bg-neon text-black shadow-[0_0_24px_rgba(255,43,214,.4)]"
          : "border-line text-ink/75 hover:border-neon/60 hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

export default function IdeaTeaser() {
  const [interest, setInterest] = useState<Interest>("Nature");
  const [placement, setPlacement] = useState<Placement>("Calf");
  const [tone, setTone] = useState<Tone>("medium");
  const results = suggest(interest, placement, tone);

  return (
    <section id="ideas" className="relative border-t border-line px-5 py-28 md:px-10 md:py-40">
      <div className="grid gap-14 md:grid-cols-12 md:gap-10">
        <div className="md:col-span-6">
          <p className="label mb-6">Idea finder</p>
          <h2 className="font-display text-6xl leading-[0.95] md:text-8xl">
            Stuck on
            <br />
            what to <span className="glow italic text-neon">get?</span>
          </h2>
          <p className="mt-6 max-w-md text-base leading-relaxed text-ink/70">
            Pick three things. You get a style to look into and why it fits that spot. Shaurya draws the
            actual design.
          </p>

          <div className="mt-12 space-y-8">
            <fieldset>
              <legend className="label mb-3">I like</legend>
              <div className="flex flex-wrap gap-2">
                {interests.map((v) => (
                  <Chip key={v} on={v === interest} onClick={() => setInterest(v)}>
                    {v}
                  </Chip>
                ))}
              </div>
            </fieldset>
            <fieldset>
              <legend className="label mb-3">Placement</legend>
              <div className="flex flex-wrap gap-2">
                {placements.map((v) => (
                  <Chip key={v} on={v === placement} onClick={() => setPlacement(v)}>
                    {v}
                  </Chip>
                ))}
              </div>
            </fieldset>
            <fieldset>
              <legend className="label mb-3">Skin tone</legend>
              <div className="flex gap-3">
                {tones.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    aria-label={t.label}
                    aria-pressed={t.id === tone}
                    onClick={() => setTone(t.id)}
                    className={`h-10 w-10 rounded-full transition-shadow ${
                      t.id === tone ? "shadow-[0_0_0_2px_var(--bg),0_0_0_4px_var(--neon)]" : ""
                    }`}
                    style={{ background: t.hex }}
                  />
                ))}
              </div>
            </fieldset>
          </div>
        </div>

        <div className="md:col-span-5 md:col-start-8 md:pt-16" aria-live="polite">
          <p className="label mb-6">Look into</p>
          <div className="space-y-4">
            {results.map((r, i) => (
              <article key={r.style} className="border border-line bg-panel p-6 md:p-8">
                <p className="font-mono text-xs text-neon">0{i + 1}</p>
                <h3 className="mt-3 font-display text-4xl leading-none">{r.style}</h3>
                <p className="mt-4 text-base leading-relaxed text-ink/85">Think {r.idea}.</p>
                <p className="mt-3 text-sm leading-relaxed text-muted">{r.why}</p>
              </article>
            ))}
          </div>
          <a
            href={wa(
              `Hi Shaurya, I used the idea finder on your site.\nI like: ${interest}\nPlacement: ${placement}\nSuggested: ${results.map((r) => r.style).join(" / ")}\nCan we talk about a design?`,
            )}
            target="_blank"
            rel="noreferrer"
            className="btn mt-8"
          >
            Send this to Shaurya
          </a>
        </div>
      </div>
    </section>
  );
}
