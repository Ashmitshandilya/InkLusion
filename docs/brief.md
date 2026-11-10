# InkLusion — brief

**What:** Website for a tattoo artist. Premium, minimal, black base with neon magenta accent.
**Goal:** Show the work at a very high level and turn visitors into booked slots.

## Pages
- **Landing:** scroll-animated story of the artist + the tattoo-making process, featured work, idea finder teaser, booking CTA.
- **Work:** interactive gallery. Admin can add / edit / remove pieces any time.
- **Ideas:** suggests a *direction*, not a design — based on interests, placement, skin tone, ink preference — and shows matching pieces from the artist's own work.
- **Book:** pick a slot, send the brief. Prices shown as starting points, clearly negotiable.
- **Admin:** manage work, slots, booking requests.

## Stack
Next.js on Vercel + Supabase (DB, auth, image storage). Render only if a worker is needed. Domain later.
Local version first, final check, then live.

## Waiting on
- Artist story (answers to `docs/artist-questionnaire.md`)
- Artist's tattoo photos (to be cleaned up: crop, light, background matched to the theme — no altering the tattoo itself)
- Studio name spelling, city, contact (WhatsApp / Instagram / email), price starting points
