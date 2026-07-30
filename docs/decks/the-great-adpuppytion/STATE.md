# STATE — pick up here

**Last saved:** 2026-07-30 by code-puppy-8aaf0e
**Status:** v2 — DS "Cornerstone+" overhaul complete, QA'd headless (45 slides @1440×810).
Fireship beat integrated. Fact-check pass done + staged in FACTCHECK.md (applied).

## How to resume

```bash
cd /Users/tygranlund/code_puppy/docs/decks/the-great-adpuppytion
python3 -m http.server 8084   # then open http://localhost:8084/
```

## Docs map

- `DESIGN.md` — DS v2 spec: four archetypes (STATEMENT/SPLIT/STAGE/LEDGER),
  act→color discipline, type scale, motion budget, asset pipeline. **Read first
  before editing slides.**
- `FACTCHECK.md` — web-puppy verified claims table. v2 slide text already
  reflects the corrections (Petrillo 1942, Moog 1969, ~20K musicians,
  Karen X. Cheng, Flanagan 2012). Keep it as the audit trail.
- `README.md` — structure + provenance.
- `index.html` — all 45 slides, 8 acts.
- `theme.css` — DS v2 "Cornerstone+".

## Hard requirements (do not break)

1. **Chaplin's Great Dictator speech = verbatim, one beat per slide, 8 slides**
   (eyebrow I–VIII, slides 13–20). Text exactly from `docs/jack-conte-sxsw.md`.
   Bookended on slide 44.
2. Code-Puppy brand tokens (gold #f5b94d / sky #6cb6ff / mint #4cc46a /
   violet #b692f6 / coral #ff7b72 on ink #0b0f14). One accent hue per act/slide
   (`.act-*` scoping) — the v1 five-hues-per-slide sin is banned.
3. Archetype discipline: every slide is STATEMENT, SPLIT, STAGE, or LEDGER.
   Cards/tables ONLY in LEDGER. Images ONLY in SPLIT/STAGE (`.duo` duotone).
4. Motion budget: exactly two animated moments — sine stroke-draw (slide 23)
   and terminal type-in (slide 40). Wow is scarcity.

## Narrative arc (locked, v2)

Cold open → 1895 film (Méliès) → panic rail (1896/1927/1942/1969) → Chaplin
refusal + speech → sine wave (Pomplamoose) → 2026 dip (slop + consent +
**Fireship: the moat is gone / asteroid→soil, slides 29–30**) → why humans win
(risk/scarcity/connection) → **CPU answer (Act VII)** → charter + ask.

## CPU framing (locked concept)

Two halves of one future: creative-non-technical + technical-non-creative.
Stack: **Puppy OS** (front door) → **Code-Puppy** (engine, real, MIT) →
**University** (bridge; this deck is its charter).
5 schools: New Medium / Agentic Craft for Creatives / Creative Direction for
Engineers / The Rebuild Practice / Ethics, Consent & Credit.

## QA tooling

Playwright at /tmp/pwqa (ephemeral — `npm i playwright@1.62.0` to reinstall):

```js
// shoot.js — all 45 slides @1440×810, 1100ms settle
// reshoot.js — slides 23 & 40 (animations need 3.2s / 6s settle)
// audit.js — overflow sweep (note: full-width block elements are false
//            positives; only text ending past x≈1415 is a real clip)
```

v2 QA findings fixed: sine SVG label overlap (labels repositioned to top/bottom
rows), terminal animation fill-mode (`both`), 2020+ label clip (x=960).

## Open ideas (not yet done)

- Real licensed stills to replace placehold.co FPOs (Méliès moon is the only
  FPO placed so far — slide 5)
- PDF export (`?print-pdf` + decktape) for a shareable artifact
- Light-mode fork for projector-hostile rooms
- Speaker notes (`<aside class="notes">`) for live delivery
- The Karen X. Cheng quote is only sourced via Conte's talk — fine as
  attributed, but a primary link would be better
