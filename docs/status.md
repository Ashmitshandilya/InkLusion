# Status

**Phase:** 3 — landing page v2 (cosmic background, plain copy, real contact details). Waiting for feedback.

## Done
- Workflow skills, brief, competitor notes, artist questionnaire
- Landing v2: fixed nebula + stars + eclipse backdrop on the whole page, wordmark hero,
  story, process, work reel, idea finder, booking
- WhatsApp booking works now (pre-typed message); idea finder sends its result to WhatsApp
- Supabase URL + publishable key in `.env.example` (not used by code yet)

- Reel system `reels/` (`npm run reels`): drop media + songs, get every style x song; 6 styles; measured beat sync
  (beats <1 ms, cuts <=16.7 ms, audio <3 ms on test songs). Tested on stand-in clips only so far

## Next
- Apply feedback on v2
- Phase 4: /work gallery, /ideas full finder, /book slots, /admin, Supabase schema

## Waiting on user
- Reel footage + the song files (Farzi, Not Sure; artist for "Delicious Confusion") to run the first real batch
- Artist's answers + photos; his OK on the DRAFT story and process lines in `src/content/site.ts`
- Confirm: artist name "Shaurya", school name "Aliens Tattoo School, Mumbai"
- Prices, email, whether the personal Instagram should appear on the site (currently not shown)
- Vercel project linked to the repo (preview link for `dev`)
