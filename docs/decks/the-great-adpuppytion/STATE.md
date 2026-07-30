# STATE — pick up here

**Last saved:** 2026-07-28 by code-puppy-b07cb8
**Status:** v1 complete, QA'd, live-previewable. Fine-tuning phase next.

## How to resume

```bash
cd /Users/tygranlund/code_puppy/docs/decks/the-great-adpuppytion
python3 -m http.server 8084   # then open http://localhost:8084/
```

Files: `index.html` (all 43 slides), `theme.css` (Code-Puppy brand tokens), `README.md` (structure + provenance).

## Hard requirements (do not break)

1. **Chaplin's Great Dictator speech = verbatim, one beat per slide, 8 slides** (sections numbered I–VIII in the eyebrow, slides 13–20). Text comes exactly from `docs/jack-conte-sxsw.md`. Bookended again on the closing slide.
2. Code-Puppy brand tokens (gold #f5b94d / sky #6cb6ff / mint #4cc46a / violet #b692f6 / coral #ff7b72 on ink #0b0f14). Modernized but on-brand; must cater to all generations.
3. Slide-puppy conventions: one idea per slide, 8% margins, dark mode luminous accents, auto-animate pairs.

## Narrative arc (locked)

Cold open → 1895 film (Méliès) → panic pattern timeline (Vitaphone/recording ban/Novachord) → Chaplin refusal + speech → sine wave (Pomplamoose) → 2026 dip (slop + consent) → why humans win (risk/scarcity/connection) → **CPU answer (Act VII)** → charter + ask.

## CPU framing (locked concept)

Two halves of one future: creative-non-technical + technical-non-creative.
Stack: **Puppy OS** (front door, desktop app, future) → **Code-Puppy** (engine, real, open-source, MIT) → **University** (bridge; this deck is its charter — NO prior CPU artifact ever existed on Tyler's machine).
5 schools: The New Medium / Agentic Craft for Creatives / Creative Direction for Engineers / The Rebuild Practice / Ethics, Consent & Credit.

## QA tooling that worked

Headless screenshots via playwright (installed at /tmp/pwqa — ephemeral, reinstall with `npm i playwright@1.62.0` if /tmp got wiped):

```js
// viewport 1440x810, goto http://localhost:8084/#/<slideNum>, wait 1100ms, screenshot
```

Known-fixed issue: `.vcenter` needed `.reveal .slides section.vcenter` specificity + min-height 92vh to beat Reveal's layout.

## Open fine-tuning ideas (not yet done)

- Optional images per slide (placehold.co/picsum FPO pattern from slide-puppy agent)
- PDF export (`?print-pdf` + decktape) if Tyler wants a shareable artifact
- Possibly a light-mode fork for projector-unfriendly rooms
- Speaker notes (`<aside class="notes">`) if this gets presented live
- Verify Conte's looser historical claims before any external audience (Petrillo timeline compression, "Kerrydax Chang" attribution)
