# Code Puppy on Azure

Single home for everything related to hosting the open-source
[Code Puppy](https://github.com/mpfaffenberger/code_puppy) CLI as an
internal web app inside the HTT Azure tenant.

Both artifacts here are **fully static** — no backend, no runtime
calls. Open any `index.html` in a browser.

## Contents

```
docs/code-puppy-on-azure/
├── index.html          ← landing page, links to both artifacts
├── playbook/           ← four-section explainer for the rollout
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── mockup/             ← HTT-branded simulation of the actual app
    └── index.html
```

### `playbook/`

A dark-themed, multi-section SPA aimed at devs, DevOps and security.
Walks through:

1. **Architecture overview** — system diagram (browser → Entra ID →
   App Gateway → Code Puppy service → Key Vault → Azure OpenAI).
2. **Setup steps** — seven-step timeline from CLI prototype to
   internal Azure app, plus a delivery flow.
3. **Guardrails & limits** — dev-vs-prod capability matrix (shell,
   filesystem, network, tools, providers) and the policy
   middleware flow.
4. **CI/CD & tuning** — ten-stage pipeline and the two cards
   "what lives in git" and "how we tune safely".

### `mockup/`

A light, HTT-branded product mockup that shows what the actual app
will look and feel like. Uses the HTT parent palette (red, yellow,
maroon, pink on warm cream) and Montserrat. The mockup is
*interactive*: the env toggle changes the policy posture, the
shell-approval card's Allow / Block buttons both work, and the
composer simulates a token-streaming agent reply on send.

## How to view

- **Just open it** — double-click any `index.html`; everything is
  self-contained.
- **Serve the folder** — from this directory:
  `python3 -m http.server 8000`, then visit
  `http://localhost:8000/`.
- **GitHub Pages** — point Pages at the repo's `/docs` folder and
  this initiative lives at `/code-puppy-on-azure/`.

## Audience

| Reader                  | Start here                                      |
|-------------------------|-------------------------------------------------|
| Engineering / DevOps    | `playbook/` &rarr; Architecture & CI/CD         |
| Security                | `playbook/` &rarr; Guardrails & policy flow     |
| Brand / leadership      | `mockup/` &rarr; product look-and-feel          |
| Anyone new to the brief | `index.html` &rarr; pick from the two cards     |

## Brand reference

The mockup applies the **HTT parent** identity (§1 of the HTT Brands
Master Brand Book). The parent brand book defines colors by name
only — the hex values used here are a documented interpretation; swap
in canonical hexes once they're added to a formal HTT visual identity
guide (currently flagged as a gap in §7 of the brand book).

## Owner

HTT IT &middot; Tyler Granlund
