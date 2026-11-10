---
name: build-software
description: Ashmit's standard workflow for building software with a website (web app / SaaS / tool with accounts, data and a marketing landing page). Use when the user says they are building software, an app, a tool or a platform rather than a showcase website.
---

# Software + website workflow

Same rules of conduct as `build-website` (short chat, no repeated questions, `docs/status.md` as memory,
`main` = live / `dev` = work, local first, go live only after approval). Differences below.

## Phase 0 — Intake (one message, only what is missing)
1. Who uses it and the one job it does for them
2. The 3–5 core actions a user takes (these become the MVP)
3. Roles (user / admin / others) and what each can see
4. Money: free, subscription, one-time? (payments need a provider — ask before adding)
5. Data that must be stored, and anything sensitive
Save to `docs/brief.md`.

## Phase 1 — Competitors (always)
Max 3 searches: closest products, their pricing/onboarding, the most common user complaints about them.
Write `docs/competitors.md`: table of product / strength / weakness, then "our wedge" in 2 lines.

## Phase 2 — Spec before code
Write `docs/spec.md` (max 1 page): MVP scope, out-of-scope, data model (tables + relations),
screens list, auth rules. Reply with **Your to-dos**, **Major problems**, **Plan**. Wait for a yes.

## Phase 3 — Build order
1. Data model: `supabase/schema.sql` with RLS on every table
2. Auth + roles
3. Core actions end to end, one at a time, each verified in the browser before the next
4. Landing page (reuse `build-website` Phase 3 rules)
5. Admin, settings, emails, polish

Default stack: Next.js + Supabase on Vercel. Render for workers, cron, websockets or heavy jobs.

## Phase 4 — Final check
Everything in `build-website` Phase 5, plus: tests for the core actions, RLS checked with a second
account, rate limits on public endpoints, error logging, backups noted, seed script for a demo account.

## Phase 5 — Go live
Supabase → Render (if used) → Vercel, then smoke test the core actions on the live URL with a fresh account.
