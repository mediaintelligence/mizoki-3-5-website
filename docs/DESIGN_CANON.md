# MIZOKI3 Design Canon — v1.5 "Night Dossier" (LOCKED)

**Status:** SOURCE OF TRUTH by owner directive (2026-07-30).
**Scope:** the complete public look and feel of mizoki3.com — homepage, demo
platform, Executive Briefing, and every connected surface.
**Governance:** changing ANY of this requires **specific human approval before
anything uploads to production**. No exceptions, no auto-deploys.

---

## 1. What is locked

The machine-readable manifest is [`canon.lock.json`](../canon.lock.json) at the
site root — sha256 pins for 19 core surfaces:

| Surface | Files |
|:--|:--|
| Canonical homepage | `index.html` (sha256 `35a7e5d3…66ac08ac`, 80,479 B) |
| Shared theme | `assets/css/styles.css`, `assets/css/demo-extras.css`, `assets/js/nav-mobile.js` |
| Demo platform (core of the operation) | `demo.html` + `demo-{signal,counsel,estate,capital,risk,nexus}.html` |
| Walkthrough | `walkthrough.html` |
| Executive Briefing (second track) | `executive-briefing/{index.html, css/briefing.css, js/app.js, js/data.js}` |
| Commercial + legal pages | `pricing.html`, `privacy.html`, `terms.html` |

Verify anytime:

```bash
python3 scripts/check_design_canon.py          # CANON OK / CANON DRIFT
python3 scripts/check_design_canon.py --update # re-pin — ONLY as part of an approved change
```

## 2. The look and feel (design vocabulary)

One continuous **dark dossier world** on every surface:

- **Plates:** page `#0A1418`, raised ink `#0B1E26`–`#0D2027`, hairlines `#1C2E36`/`#24404A` — no glows, 2px radii, flat editorial.
- **Text:** `#F4F6F7` display / `#DCE9ED` body / `#93A0A6` muted / `#5E7780` faint.
- **Accent:** cyan `#3FDCF2` primary (buttons carry ink `#06262C` text); status colors bright-for-dark — pass `#41D695`, warn `#E0A92E`/`#D9A83C`, veto `#FF6B7C`. Division wayfinding hues: counsel `#5FA0DC`, estate `#41D695`, capital `#D9A83C`, signal `#9D7BE8`, risk `#FF6B7C`; Nexus = cyan (flagship).
- **Type:** Instrument Serif (display, weight 400), DM Sans (body), JetBrains Mono (chrome/labels). No other font families.
- **Content canon (homepage):** the 16-item fingerprint suite — gauge **39** (`color:var(--veto)`), ILLUSTRATIVE FIGURES labeling, CanonicalEventEnvelope v1.0, Mixture-of-Legal-Experts, 12 connectors incl. The Trade Desk/Shopify/Meta Ads/Klaviyo, "Not a dashboard. Not an agent framework. Not a pipeline." — and the six banned drift markers (gauge-87, "customers we've onboarded", Live Nexus Snapshot, 18,742, Stripe, DV360) stay absent.

## 3. The operation's core

- `/` — canonical night dossier (content byte-frozen; only human-approved changes).
- `/demo` + six desks + `/demo/nexus` — the technical track; **the core of the operation**.
- `/executive-briefing/` — the executive track (~9 min), 8 domains, **Signal (default) and Legal listed first as the platform's most mature channels**.
- Two-track routing: §06 LIVE DEMO on the homepage, the demo-hub banner, and the closing plate all cross-link the tracks.

## 4. How a change ships now (human approval required)

1. Propose the change (branch/diff + rendered screenshots).
2. **A human explicitly approves it.**
3. Re-pin: `python3 scripts/check_design_canon.py --update`, commit lockfile with the change.
4. Merge to `main` — **nothing deploys automatically anymore.**
5. A human runs **Actions → "Deploy MIZ OKI 3.5 Homepage" → Run workflow** and types `APPROVED` in the `approve` input. The workflow refuses any other value and refuses trees that fail the canon check.
6. Verify live (fingerprints + canon hashes) after the run.

Agents/automation: do **not** dispatch the deploy workflow, edit canon files, or
re-pin the lockfile unless a human has explicitly instructed that exact change.
The old chain (push → auto-merge → Deploy Router → auto-deploy) is retired for
this site: the workflow no longer declares `push` paths, so the Router skips it.

## 5. Canon lineage

| Version | Homepage sha256 (first 8) | Shipped |
|:--|:--|:--|
| v1.0 dossier (paper) | `e9df2617` | rev 00126, 2026-07-28 |
| v1.1 + live-demo showcase | `7e3005ef` | rev 00127 |
| v1.2 + Executive Briefing two-track | `ed67bdb3` | rev 00128-gjn |
| v1.3 site-wide dossier unification | homepage unchanged | rev 00129-rvc |
| **v1.4/v1.5 night dossier + flagship briefing domains (LOCKED)** | **`35a7e5d3`** | rev 00132-z5s + v1.5 deploy, 2026-07-30 |

**Approved re-pins on v1.5** (canon version unchanged; homepage untouched):

- 2026-07-31 — **Boss voice docent** (explicit owner instruction): guided
  salesman tour on `/demo/signal` via new `assets/js/boss-docent.js`
  (output-only voice — no microphone ever; scripted claims-linted narration;
  one soft CTA; cooperative take-over). `demo-signal.html` gained the script
  wiring → re-pinned in the same commit. Awaiting a human `APPROVED` dispatch.

- 2026-07-30 — **ORACLE / Signal Intelligence incorporation** (explicit owner
  instruction): `signal.html` rewritten as the Signal Intelligence Division page
  (not canon-pinned) and `demo-signal.html` gained the static "5 · ORACLE —
  anticipatory intent" section (canon-pinned → re-pinned in the same commit).
  Source doc: `docs/SIGNAL_INTELLIGENCE_ORACLE_CAPABILITIES.md`. Awaiting a human
  `APPROVED` dispatch to ship.
