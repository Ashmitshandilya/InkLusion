@AGENTS.md

# InkLusion

Tattoo artist website. Workflow: `.claude/skills/build-website/SKILL.md` — follow it.
Start every session by reading `docs/status.md` (current phase, next step, what we wait on).

- Brief: `docs/brief.md` · Competitors: `docs/competitors.md`
- All copy/images/prices: `src/content/site.ts`. Artist photos → `public/artist/`, tattoos → `public/work/`.
- Theme tokens: `src/app/globals.css` (black base, neon magenta accent).
- Commands: `npm run dev`, `npm run build`, `npm run lint`.
- Branches: `main` = live, `dev` = work.
