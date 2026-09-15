# The Leather Apron Club — Bentonville 2026

The founding presentation for the first meeting of the Leather Apron Club:
**Friday, September 18, 2026 · Bentonville Barber Company.**

A full visual reimagining of `the-great-adpuppytion` ("Cornerstone+") deck,
re-skinned onto the **Spruce Grove design system** (granlund-grove Nordic
forest dark tokens, Fraunces / Inter / JetBrains Mono) and re-anchored on
Benjamin Franklin's Junto (1727), documented in
`dev/1.MASTER-ORCHESTRATION/Junto-Leather Apron Club.md` and `ETHOS.md`.

## Run it

```bash
cd docs/decks/the-great-adpuppytion/leather-apron-club
python3 -m http.server 8085
# open http://localhost:8085/
```

Reveal.js + fonts load from CDN (same as the parent deck). Presenting offline?
Open with the machine's browser after a warm-up load (fonts cache).

## Structure (44 slides, Act 0 + 8 acts, ~30–35 min with the Chaplin read)

| Act | Slides | What happens |
|-----|--------|--------------|
| 0 · Cold open | 1–7   | The real spruce-trio mark, the name (Granlund = spruce grove), the path strata, the why, the language, the pantheon, "What did you build this week?" |
| 0.5 · The lineage | 8–10 | Code Puppy → Spruce Grove (both real logos), the 300-year timeline (dates verified against `FACTCHECK.md`), the grove shipping — terminal + mark |
| I · 1727 | 11–16 | The Junto: 4 admission inquiries (verbatim), what 12 tradesmen compounded into, the pipeline, the operating code |
| II · Machines | 17–20 | The panic rail (1896/1927/1942/1969), the 2026 moat-is-gone beat, the bridge to 1940 |
| III · 1940 | 21–22 | Chaplin's Great Dictator — **verbatim, 8 beats** live-transcribed and ignited on ONE stage section; "why we read all of it" |
| IV · Proof | 23–30 | Bentonville: what survives, the Sept 3 receipts, the Sept 4–13 build log, the voice loop, the understone, the desktop app |
| V · The club | 31–36 | The rules, the harness in four layers, Franklin's pipeline, the charter as a running process, first 30–90 day experiments |
| VI · The ask | 37–40 | Three commitments, the creed, the crazy ones, TOGETHER WE ARE BETTER. ALWAYS. |

## Design discipline (inherited, non-negotiable)

1. **Four archetypes only** — STATEMENT / SPLIT / STAGE / LEDGER. Cards and
   tables live in LEDGER. Typography-first; images appear only where the image
   IS the artifact: the grove mark (`assets/spruce_grove_official.svg`,
   the real logo, 4 display spots), the pantheon portraits (17, Wikimedia),
   and the Chaplin film frame.
2. **One accent hue per slide** via `.act-*` scoping; act map in `tokens.css` §4.
3. **Motion budget = 2, total**: terminal self-type in Act V; Chaplin
   live-transcription key-statement ignition (emperor / humanity / you are men /
   unite burn ember). The title mark is a static image — wow is scarcity.
4. **Chaplin is verbatim** (beat section I–VIII inside the stage slide),
   sourced from `docs/jack-conte-sxsw.md` exactly as the parent deck's test
   suite locks it. His words, not ours.
5. **Every fact has a file** — Junto mechanics
   (`dev/1.MASTER-ORCHESTRATION/Junto-Leather Apron Club.md`), panic-rail
   verdicts (`FACTCHECK.md`, inherited from the parent deck), receipts
   (`tylergranlund.com/progress`, `sprucegrove.io`), creed (`ETHOS.md`, Ozark
   Bagels transcript), Fireship beat (Code Report, Jul 29 2026).

## Tokens

Spruce grove oklch palette in `tokens.css`: night canvas 0.18·150,
cedar (founder gold) 0.78·55, grove 0.72·155, frost 0.80·210, ember 0.72·40.
Matches `granlund-grove/src/styles.css` and the OPERATION GRANLUND dashboard —
one design system across site, dashboard, and deck.

## Open to-dos before Friday

- Confirm venue specifics, timing, and invite list with **Victor & Drew** (this week).
- Printable one-pager: the four admission inquiries (hand everyone standing).
- Speaker notes pass (`<aside class="notes">`), 1 rehearsal at full pace.
