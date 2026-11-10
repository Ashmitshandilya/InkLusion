---
name: build-website
description: Ashmit's standard workflow for building a client website (landing page + inner site + light backend). Use as soon as the user says they are building a website, e.g. "we're building a website for a salon". Covers intake, competitor research, plan, landing page, inner site, final check, go-live.
---

# Website workflow

Run the phases in order. Never make the user repeat anything this file already covers.
Be short in chat: results, decisions, what you need from the user. No long explanations.

## Phase 0 — Intake
If `docs/brief.md` exists, read it and skip to the first unfinished phase in `docs/status.md`.
Otherwise ask for the task description. Ask only for what is missing, in ONE message:
1. Business + who the customers are
2. Main goal of the site (bookings, leads, sales, showcase)
3. Theme / vibe / reference sites
4. Features wanted inside the site and what the admin must be able to change
5. Assets available now (logo, photos, text) and what comes later
Save answers to `docs/brief.md`.

## Phase 1 — Competitors (always, without being asked)
Max 3 web searches: best sites in the niche, what converts (booking/lead flow), one differentiator.
Write `docs/competitors.md` (max 40 lines): patterns to copy, gaps to beat, features worth adding.

## Phase 2 — Plan reply (short)
Reply with exactly these blocks:
- **Your to-dos** — the few things only the user can do (accounts, assets, client answers)
- **Major problems** — real risks only; skip the block if none
- **Plan** — stack + pages, 5 lines max
If client content is needed, write a questionnaire the user can forward (`docs/<client>-questionnaire.md`).
Do not wait for assets: build with labelled placeholders.

## Phase 3 — Landing page first
- Default stack: Next.js (App Router, TS, Tailwind) on Vercel + Supabase (DB, auth, storage).
  Render only when a long-running server/worker is truly needed. No other paid services without asking.
- All copy, images and prices live in `src/content/site.ts`. Missing assets render as labelled placeholders,
  so real content is a one-file swap.
- Premium + minimal: one accent colour, strong type, scroll animation with purpose, fast on mobile.
- Verify before showing: `npm run build`, `npm run lint`, screenshots at 1440px and 390px. Look at them.
- Checkpoint: show screenshots, ask for feedback. Stop here until the user answers.

## Phase 4 — Inner site + backend
Confirm the feature list in one message (propose defaults from the brief, user just says yes / edits).
Build with Supabase: schema in `supabase/schema.sql`, RLS on every table, admin behind Supabase auth.
The site must run locally without keys (seed data fallback) so the user can always preview.

## Phase 5 — Final check (local)
Build + lint clean, every page at desktop and mobile, forms submit, empty/error states, SEO meta +
OG image, favicon, 404 page, image sizes, no secrets in the repo, `.env.example` up to date.
Report the result as a short pass/fail list.

## Phase 6 — Go live (only after the user approves the local version)
Supabase project → run schema → Vercel import with env vars → smoke test the live URL.
Domain is bought later; note where to connect it.

## Always
- Branches: `main` = live, `dev` = work in progress. Commit small, push at the end of every session.
- End every session by updating `docs/status.md`: done, next, waiting-on-user. Start every session by reading it.
- Never edit or "improve" a client's real work photos beyond crop, light and background — no generated detail.
- If the user gives a new standing preference, add it to this file.
