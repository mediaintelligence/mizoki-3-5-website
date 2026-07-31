# Homepage Merge Plan — Grok Redesign → mizoki3.com

**Date:** July 27, 2026
**Target:** `# MIZ OKI 3.5/index.html` (Cloud Run service `mizoki-website`)
**Source of proposals:** Grok shared conversation `MIZ OKI 3.5 Modern Website Redesign`
(`grok.com/share/bGVnYWN5_dcd9c3b9-f0ad-44b4-b9c7-47b0aaa93943`, 32 messages, 11 HTML iterations)
**Branch:** `claude/mizoki3-homepage-redesign-53mcth`

---

## Prior art — read this first

**A large part of this exact Grok output was already dispositioned on 2026-07-23.**
See `docs/LANDING_REMIX_ADOPTION_NOTES.md`: the "externally drafted single-file
MIZOKI3 landing page" reviewed in that session is an artifact from this same
conversation. Already **adopted**: the homepage live teaser, the Capital covenant-veto
scenario, the VETOED outcome state, Causal Truth, the teaser progress line + ✓ marks,
the millisecond log, the pricing tier naming (on `/pricing`), and the hero ghost CTA.
Already **rejected**: Tailwind/Font Awesome CDN, `Math.random` confidence, fabricated
impact metrics, the Inventory Exception scenario, `boris@mizoki3.com`, and wholesale
replacement of `index.html`.

**Do not re-litigate any of that.** This plan covers only what that ledger left open —
the *presentation-layer* critique from the conversation's final two messages (#29, #31),
which the prior session did not address.

| Grok item | Status after 2026-07-23 | This plan |
|:---|:---|:---|
| Live teaser exists on homepage | ✅ Adopted | — |
| Live teaser is *positioned as the centerpiece* | ❌ Still buried at section 12/14 | **§1** |
| Animated stage rail | ✅ On the teaser (`.lt-*`) | ❌ Not on the static `#orchestration` loop → **§2** |
| Pricing tiers | ✅ On `/pricing` | ❌ No homepage signal → **§4** |
| Omnichannel / media acquisition (msg 11) | Not in the ledger | **§3 — genuinely new** |
| Density, hierarchy, flow, nav, mobile | Not addressed at all | **§5** |

---

## Context

The Grok conversation produced a series of full-page rewrites of mizoki3.com. Its
**diagnosis is accurate** and matches what the live page actually does:

| Grok's finding | Verified against `index.html` |
|:---|:---|
| Extremely text-dense | 1,720 lines, 15 sections, multi-sentence `.sub` blocks on nearly every section |
| Weak visual hierarchy / no breathing room | `section{padding:120px 0}` but dense internal copy; 11-item nav |
| Interactive elements feel secondary | The real live teaser sits at **line 1543 — section 12 of 14**, below the fold by a wide margin |
| Disjointed flow | evidence → orchestration → architecture → capabilities → divisions → enterprise → nexus → governance → usecases: nine consecutive "explainer" sections before any interaction |
| Repetition of metrics and division lists | Division list appears in hero grid, `#divisions`, and `#enterprise`; metrics repeat in `#flywheel` and `#nexus` |
| No pricing signal | Homepage has zero pricing content; `/pricing` exists but is only reachable from nav |

**However, the Grok artifacts themselves are not directly usable.** They are
Tailwind-CDN single-file demos that would regress the production site. The correct
move is to **port the ideas into the existing hand-built design system**, not to
replace the page.

### What we already have that is better than the proposal

The homepage already ships a **real** live demo teaser (`assets/js/home-demo.js`,
309 lines) that calls `/api/demo/<division>/run` and replays the actual SRPVDAL
trace returned by the seeded engines — real stage summaries, real confidence, real
trace IDs, seed 42. Grok's demo is a `setTimeout` animation over hardcoded strings.
**We keep ours and simply move it up.**

---

## Decisions: what to take, what to reject

### ✅ MERGE IN

| # | Item | Rationale |
|:--|:-----|:----------|
| **1** | **Elevate the live teaser** — move from section 12 to immediately after the hero, as `#live` | Grok's single strongest point. Ours is real, so promoting it is a straight win. |
| **2** | **Animated SRPVDAL pipeline rail** — progress line + `active`/`completed` stage dots in `#orchestration` | Currently 7 static cards. Port the interaction pattern (not the CSS) onto our tokens; drive it from `IntersectionObserver`. |
| **3** | **Omnichannel Acquisition block** — Meta / Google / Email / Programmatic under SIGNAL | Genuinely net-new. The platform has these connectors (Connector Gateway, 9 native connectors) but the homepage never shows them. |
| **4** | **Pricing preview** — 3 tiers (Starter / Scale / Enterprise) linking to `/pricing` | Homepage currently gives buyers no commercial signal at all. |
| **5** | **Density + flow pass** — trim `.sub` copy, collapse repeated division/metric lists, nav 11 → 6 | Directly addresses the density and repetition findings. |

### ❌ REJECT

| Item | Why |
|:-----|:----|
| `cdn.tailwindcss.com` | Not production-safe (Tailwind says so itself; the conversation hit this warning twice). We have a complete design system in the inline `<style>` block. |
| Font Awesome CDN + emoji icons (`⚖️ 🏛️ 🏦 📡 🛡️`) | The site uses inline SVG throughout. Emoji render inconsistently and break the enterprise tone. |
| Palette swap to zinc-950 + cyan/violet | Our five-division palette (`--counsel #a855f7`, `--estate #21d07a`, `--capital #34a6ff`, `--signal #f5a623`, `--risk #f4495f`) is brand-load-bearing and used across **27 HTML pages**. Swapping the homepage alone would desynchronize the site. |
| Grok's hardcoded performance metrics — *"31% CPA drop in 11 minutes"*, *"$42k shifted"* | **These are fabricated.** The platform is under a documented `built, pre-benchmark` claims discipline (`tools/claims_lint.py`, `miz_oki_source_of_truth`). Publishing invented performance numbers as marketing claims is exactly what that discipline exists to prevent. The Omnichannel block ships as **capability description**, not measured results. |
| Deleting `#evidence`, `#governance`, `#nexus`, `#usecases` | Grok's version is a 5-section landing page. These sections carry the enterprise/SEO substance that differentiates the site. We compress them, not remove them. |
| `boris@mizoki3.com` contact | Site uses `hello@mizoki3.com`. |

---

## Implementation

All changes are confined to **`# MIZ OKI 3.5/index.html`** (inline `<style>`, markup,
inline `<script>`) plus a small extension to **`assets/js/home-demo.js`** only if the
teaser move requires it (it should not — the script binds by ID).

### Target section order

```
NAV (6 items)
HERO                     #platform      ← trimmed sub-copy
LIVE DECISION            #live          ← MOVED UP (was #action-flow, line 1543)
7-STAGE LOOP             #orchestration ← + animated rail
DIVISIONS                #divisions     ← absorbs #enterprise autonomy strip
OMNICHANNEL              #omnichannel   ← NEW
DECISION CONTROL PLANE   #architecture
EVIDENCE                 #evidence      ← compressed
3.5 RELEASE              #capabilities
GOVERNANCE (CSE + DEL)   #governance
LIVE NEXUS SNAPSHOT      #nexus
USE CASES                #usecases      ← compressed
PRICING                  #pricing       ← NEW
POSITIONING              #positioning
CTA + FOOTER             #contact
```

### Step detail

1. **Nav** — reduce to `Platform · Divisions · Live Demo · Governance · Pricing · About`,
   keeping `Sign In` (`/admin/login`) and `Request Enterprise Pilot`. Update
   `assets/js/nav-mobile.js` consumers implicitly (it clones `.nav-links`, so no JS change).

2. **Move the teaser** — relocate the `.lt-wrap` block (index.html:1553–1581) and its
   section header into a new `<section id="live">` placed directly after the hero.
   Leave the 6-step static walkthrough in place further down as `#action-flow`.
   **Do not touch the element IDs** (`ltScenarios`, `ltStages`, `ltProgress`, `ltLog`,
   `ltTimer`, `ltPlaceholder`, `ltResult`, `ltStatus`, `ltConf`, `ltAction`, `ltTruth`,
   `ltTrace`, `ltOpen`) — `home-demo.js` binds to all of them by ID.

3. **Animated rail** — add `.srp-rail` / `.srp-rail-fill` to `.srp-loop`, plus
   `.srp-stage.lit` / `.srp-stage.done` states reusing the existing `--nexus` / `--estate`
   tokens (same visual language as `.lt-stage.lit` / `.lt-stage.done`, lines 534–537).
   Drive with a small `IntersectionObserver` in the existing inline `<script>` (index.html:1695)
   alongside the current `.reveal` observer. Honor `prefers-reduced-motion` — snap to
   complete instead of animating, matching `home-demo.js`.

4. **Omnichannel** — 4 cards in the existing `.card` idiom, accented `var(--signal)`,
   inline SVG icons. Copy describes what the system *does* (sense → simulate → govern →
   act across Meta / Google Ads / lifecycle email / programmatic), with no invented metrics.
   CTA → `/demo/signal`.

5. **Pricing preview** — 3 cards, middle one flagged, all CTAs → `/pricing` (Starter
   and Scale) and `#contact` (Enterprise). No dollar figures — "Contact for pilot" /
   "Custom quote", consistent with the existing enterprise-pilot motion.

6. **Density pass** — shorten the `.sub` line on `#evidence`, `#capabilities`,
   `#governance`, `#usecases`; drop the duplicated division roll-call in `#enterprise`
   (fold its autonomy ladder into `#divisions`); remove the repeated metric strip that
   appears in both `#flywheel` and `#nexus`.

---

## Verification

```bash
cd "# MIZ OKI 3.5"

# 1. Unit tests (Flask API + runtime + demo platform)
python -m unittest discover tests

# 2. Serve locally
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8080 --timeout 120 app:app
```

Then check, at 1440px / 768px / 390px widths:

- [ ] Live teaser renders directly below the hero and **runs** — pick a scenario,
      click run, confirm stages light, log streams, outcome + trace id appear
      (this proves `home-demo.js` still binds after the move)
- [ ] Covenant-veto scenario returns a VETO status, not a success
- [ ] SRPVDAL rail animates once on scroll into view; with
      `prefers-reduced-motion: reduce` it appears complete without animating
- [ ] Omnichannel + Pricing sections render with correct division accent colors
- [ ] Nav (desktop) shows 6 items; hamburger sheet on mobile still opens/closes
      and every anchor resolves to a real section id
- [ ] No horizontal scroll at 390px; tap targets ≥ 44px
- [ ] Zero console errors

Deploy is automatic on merge to `main` via `.github/workflows/deploy-homepage.yml`
(path-filtered to `# MIZ OKI 3.5/**`), then routed by `deploy-router.yml` for bot merges.

---

## The prompt (for re-running or handing off this work)

> Merge the best parts of the Grok redesign into the **existing** mizoki3.com
> homepage at `# MIZ OKI 3.5/index.html`. Treat the Grok output as a **design
> critique with reference patterns**, not as code to paste.
>
> **Keep** the existing inline design system: Sora/Inter/JetBrains Mono, the
> `--bg-0 #04060f` base, and the five-division palette. No Tailwind CDN, no Font
> Awesome, no emoji icons — inline SVG only, matching the existing `.srp-ico` idiom.
>
> **Apply these five changes:**
> 1. Move the existing live demo teaser (`.lt-wrap`, currently section 12) to a new
>    `#live` section directly after the hero. Preserve every `lt*` element ID —
>    `assets/js/home-demo.js` binds to them and drives the real `/api/demo/*` runtime.
> 2. Add an animated progress rail + lit/done stage states to the `#orchestration`
>    7-stage loop, reusing the `.lt-stage.lit` / `.lt-stage.done` visual language and
>    the `--nexus` / `--estate` tokens. Trigger on scroll via `IntersectionObserver`;
>    honor `prefers-reduced-motion`.
> 3. Add an `#omnichannel` section (4 cards: Meta, Google Ads, lifecycle email,
>    programmatic) accented `var(--signal)`, CTA → `/demo/signal`.
> 4. Add a `#pricing` preview (Starter / Scale / Enterprise, middle flagged) → `/pricing`.
> 5. Cut density: nav 11 → 6 items, trim over-long section sub-copy, remove the
>    duplicated division roll-call and repeated metric strips.
>
> **Hard constraint on claims:** do not copy Grok's performance numbers
> ("31% CPA drop in 11 minutes", "$42k shifted", etc.). They are invented. This
> platform operates under a `built, pre-benchmark` claims discipline — describe
> capability, never fabricate measured results.
>
> Verify with `python -m unittest discover tests`, then serve locally and confirm
> the teaser still runs end-to-end at 1440/768/390px with no console errors.
