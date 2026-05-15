# MIZOKI3 — Site

Marketing site for **MIZOKI3 — Autonomous Strategic Intelligence Infrastructure**.

## Stack

Pure static HTML / CSS / JS. No build step required for browsing — the site runs as-is.

```
.
├── index.html           # Hero, animated Nexus, brain, 5 domains, flywheel, category, positioning
├── counsel.html         # Legal Intelligence
├── estate.html          # Wealth, Trust & Tax Intelligence
├── capital.html         # Banking & Financial Intelligence
├── signal.html          # Autonomous Acquisition Intelligence
├── risk.html            # Verification & Compliance Intelligence
├── assets/
│   ├── css/styles.css   # Shared dark cinematic theme
│   └── js/nexus.js      # Animated SVG hero (vanilla JS, no deps)
└── _build_domains.py    # Regenerates the 5 domain pages from a single template
```

## Local preview

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Editing domain pages

The five domain pages share a template. Edit copy / lists in `_build_domains.py` and regenerate:

```bash
python3 _build_domains.py
```

## Deployment

The site is fully static, so any of the following work:

- **GitHub Pages** — enable Pages on `main`, set folder to root.
- **Vercel / Netlify** — drag-and-drop or connect the repo, no build command.
- **Cloudflare Pages** — same.

## Design language

- Dark, cinematic, technical
- Inter (body) + JetBrains Mono (eyebrows / labels / code)
- Cyan / violet gradient accent on the Nexus brand line
- Per-domain accent colors:
  - Counsel — cyan
  - Estate — violet
  - Capital — emerald
  - Signal — amber
  - Risk — rose
