# The Great Adpuppytion — Code-Puppy University deck

A Reveal.js presentation built on Jack Conte's SXSW 2026 talk ("a talk about change"),
extended into the founding charter for **Code-Puppy University**.

## Run it

```bash
cd docs/decks/the-great-adpuppytion
python3 -m http.server 8084
# open http://localhost:8084/
```

Or just open `index.html` directly — Reveal, fonts, and theme all load from CDN/local.

## Structure (43 slides, 8 acts)

| Act | Slides | What happens |
|-----|--------|--------------|
| 0 · Cold open | 1–2 | Title + "who here has felt it?" audience hook |
| I · 1895 | 3–6 | Lumière brothers, Gorky quote, Méliès' cut, "not a play" |
| II · The Panic Pattern | 7–9 | Timeline: film / Vitaphone / recording ban / Novachord ban; fear vs. art |
| III · Chaplin | 10–21 | 13 years of refusal → The Great Dictator speech, **verbatim, one beat per slide (I–VIII)** |
| IV · The Sine Wave | 22–25 | Pomplamoose rebuild cycles; SVG wave; "change is not death" |
| V · 2026 | 26–29 | The slop phase, consent/theft, mass disruption stats, permission to feel conflicted |
| VI · Why humans win | 30–32 | Risk / Scarcity / Connection; the 1959 thought experiment |
| VII · The Answer | 33–39 | **Code-Puppy University** — thesis, two personas, the stack (Puppy OS / Code-Puppy / University), founding curriculum (5 schools), terminal mock, who it's for |
| VIII · The Ask | 40–43 | Three charter commitments, Chaplin bookend, thank-you |

## The Chaplin requirement

The Great Dictator final speech appears **verbatim, one beat per slide**, slides 13–20
(numbered I of VIII → VIII of VIII in the eyebrow). Text is set in Source Serif 4 with
gold emphasis beats. Do not paraphrase, truncate, or split differently without sign-off —
this was an explicit, non-negotiable requirement.

## Design tokens (Code-Puppy brand)

Extracted from `docs/field-guide/index.html` CSS variables (the code_puppy field guide):

| Token | Hex | Used for |
|-------|-----|----------|
| `--bg` | `#0b0f14` | canvas |
| `--bg-card` | `#151e28` | cards |
| `--text` | `#e8eef4` | primary ink |
| `--text-soft` | `#9fb0c3` | body |
| `--accent` | `#f5b94d` | gold — creator / brand primary |
| `--accent-2` | `#6cb6ff` | sky — technical / builder |
| `--accent-3` | `#4cc46a` | mint — hope / recovery |
| `--accent-4` | `#b692f6` | violet — creative / weird |
| `--danger` | `#ff7b72` | coral — alarm / disruption |

Type: Space Grotesk (display), Inter (body), JetBrains Mono (eyebrows/labels/terminal),
Source Serif 4 (quotes + Chaplin). Dark mode with luminous accents, per slide-puppy
"Cornerstone" DS conventions (one idea per slide, 8% margins, auto-animate pairs).

## Provenance

- Source transcript: `docs/jack-conte-sxsw.md` (Jack Conte, SXSW 2026). All Conte
  pull-quotes are verbatim from the transcript.
- Chaplin speech text: as delivered in the transcript; trimmed only for stage delivery
  in the original film (this deck uses the transcript's wording exactly).
- Code-Puppy facts: the tool is real and open-source — github.com/mpfaffenberger/code_puppy (MIT).
- Code-Puppy University and Puppy OS are presented as founding concepts — this deck is
  intentionally their charter document. No prior CPU artifacts existed on disk as of
  2026-07-28 (full-machine search performed).
- Historical anchors (Lumière 1895, Gorky 1896, Méliès 1902, Jazz Singer 1927, Petrillo
  recording ban, Novachord 1939, 22K theater musicians, Baumol cost disease, 1991 ASOL
  crisis, 2008 Stanford GSB 46/63 deficits) are as cited in Conte's talk.

## Slide-puppy notes

Design system: slide-puppy DS v1 / Cornerstone conventions, Code-Puppy brand binding.
Reveal.js 5.1.0 via CDN. Auto-animate pairs on title/Chaplin/reveal sequences.
