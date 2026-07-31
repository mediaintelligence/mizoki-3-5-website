# Landing-Remix Adoption Notes — July 23, 2026

**Source:** an externally drafted single-file "MIZOKI3" landing page (Tailwind CDN +
Font Awesome + Space Grotesk, scripted in-page demo) supplied for review on
2026-07-23. **Verdict:** the page was largely a condensed remix of the live
`index.html` (same hero copy, divisions, and 7-stage loop), plus a handful of
genuinely good UX ideas wrapped in an implementation that would have violated the
site's engineering and claims-governance rules. This document is the complete
disposition ledger — what was adopted, how it was re-implemented, and what was
rejected and why — so future sessions do not re-litigate it.

## Governing rule for everything adopted

> **Keep the UX idea; reject the mocked implementation.** Every number shown to a
> visitor must come from the real demo runtime (`/api/demo/*`, deterministic with
> seed 42) or not be shown at all. No CDN frameworks, no third font system, no
> `Math.random`, no fabricated performance metrics.

## Disposition ledger

| # | Element in the remix page | Disposition | Where it landed |
|:--|:--------------------------|:------------|:----------------|
| 1 | Interactive demo ON the homepage (scenario cards, stage strip, timer, log, outcome panel) | **Adopted — rebuilt on the real runtime** | `index.html` `#liveTeaser` (originally inside `#action-flow`; **moved to `#live` right after the hero in Round 3**) + `assets/js/home-demo.js`. POSTs to `/api/demo/{capital,signal}/run` with seed 42 and replays the returned trace. Log lines are the engines' stage summaries; confidence is the executed action's real confidence. A test forbids `Math.random` in the driver. |
| 2 | "Capital Covenant Veto" scenario ending **VETOED — nothing executes, human override required** | **Adopted — as a real engine scenario** | `mizoki_runtime/demo_capital.py` `dividend_covenant_veto`: the one planned move (`special_distribution +16% → holdco_dividend`) models covenant headroom 7% vs the 15% floor and is blocked; `funnel.executed == 0`, `executed_action is None`. Echoes the platform's ACT-991 governance story. Default teaser card; also selectable on `/demo/capital`. |
| 3 | VETOED/EXECUTED as the colored hero status of the outcome panel | **Adopted** | `home-demo.js` `showOutcome()`: pure-veto runs show a red "VETOED — nothing executed · blocked by covenant_headroom · human override required" hero status and hide the confidence block; executed runs show green "EXECUTED n of m candidates" with any veto as a secondary note. `demo-pipeline.js`/`demo-signal.js` title a null action "No action executed — the veto held". |
| 4 | "Causal Truth" one-paragraph explainer on the outcome | **Adopted — derived, not authored** | `demo_signal.build_causal_truth()` (shared; capital passes `constraint_noun="the covenant"`). Composed **only** from run data: winner's gate numbers + ranking arithmetic, then the vetoed move quoting the failing guardrail check's own detail, ending "The veto is not an opinion — it is arithmetic against …". Rendered on `/demo/capital`, `/demo/signal` (`#dcTruthWrap`), and the homepage teaser. |
| 5 | Animated gradient pipeline progress line + ✓ completed stage dots | **Adopted** | `.lt-progress` gradient fill (nexus→accent) + `markDone()` ✓ prefixes in `home-demo.js`. |
| 6 | Millisecond-stamped log + elapsed timer | **Adopted** | Teaser log rows carry the live elapsed clock; the timestamps are real wall-clock, not scripted. |
| 7 | Pricing tiers Starter/Scale/Enterprise named Core Intelligence / Operational Autonomy / Full Governance Suite | **Adopted — extended with the autonomy ladder** | `pricing.html` rebuilt in the MIZOKI3 design system; tiers map to autonomy levels (L0–L1 approval-first / L2–L3 bounded thresholds / L0–L5 per-scope grants). Served at `/pricing` + `/pricing.html` (the legacy page had been 301-redirected to `/` — it was unreachable), sitemap + homepage nav wired. |
| 8 | Hero CTAs that both funnel to the demo | **Adopted (one)** | Hero ghost button now reads "Run a Live Decision" → `#action-flow`. Primary stays "Explore the Platform". |
| 9 | Hero copy, five divisions, 7-stage loop, NEXUS constellation | **Already live** — the remix lifted them from `index.html`; no action. |
| 10 | Tailwind CDN, Font Awesome CDN, Space Grotesk font | **Rejected.** Site is deliberately framework-free and self-hosted (Google Fonts only); the remix even suppressed Tailwind's own "not for production" console warning. Would add a third font system to a site already split across two. |
| 11 | `Math.random()` confidence (94–97) | **Rejected.** Contradicts the demo platform's signature guarantee: "every number above is reproducible with seed N". Real confidence comes from the executed action. |
| 12 | Fabricated impact metrics ("CAC ↓27% • +2,340 customers", "Prevented $1.8M exposure", "Avoided $124k lost sales") | **Rejected.** Platform-wide claims governance: everything is *built, pre-benchmark*; `tools/claims_lint.py` polices vocabulary; Stage 2 benchmarks gate performance claims. Real funnel counts are shown instead. |
| 13 | "Inventory Exception" scenario | **Rejected.** Fulfillment is an "extensible architecture" chip, not one of the five production divisions — a demo for it would over-claim. |
| 14 | `boris@mizoki3.com` founder CTA | **Rejected pending a verified address.** No such address exists anywhere in the repo; canonical contact is `hello@mizoki3.com` + `/contact?source=…` telemetry links. A founder-direct CTA is fine *if* a real owned address is supplied. |
| 15 | Replacing `index.html` wholesale with the 6-section remix | **Rejected.** It drops the Flywheel, Evidence/envelope, DCP, Engine Room, autonomy ladder, Nexus snapshot, governance charts, use cases, and positioning — the differentiating substance. |

## What shipped (files)

| File | Change |
|:-----|:-------|
| `index.html` | `#liveTeaser` widget + CSS (design-token based), progress line, hero CTA → `#action-flow`, Pricing nav link |
| `assets/js/home-demo.js` | NEW — teaser driver: 4 scenario cards (covenant veto default), real `/run` fetch + trace replay, VETOED/EXECUTED outcome states, reduced-motion + backend-unreachable fallbacks |
| `mizoki_runtime/demo_capital.py` | `dividend_covenant_veto` scenario (pure veto); `causal_truth` on decision cards |
| `mizoki_runtime/demo_signal.py` | `build_causal_truth()` helper (+ holding sentence for pure vetoes); `causal_truth` on decision cards |
| `assets/js/demo-pipeline.js`, `assets/js/demo-signal.js` | Render `causal_truth` into `#dcTruthWrap`; null-action title |
| `demo-capital.html`, `demo-signal.html` | Causal Truth slot + CSS |
| `pricing.html` | Full rebuild (modern design system, autonomy-ladder tiers, live CTAs) |
| `app.py` | `/pricing` + `/pricing.html` served (removed from legacy 301 group); sitemap entry |
| `tests/…` | `HomepageLiveTeaserTestCase`, `CausalTruthMarkupTestCase`, `PricingPageTestCase`, engine `causal_truth` + pure-veto tests — suite at 248 passing |

## Invariants to preserve

1. The homepage teaser must keep calling the **real** demo endpoints — never inline
   scripted outcomes. The `Math.random` ban is test-enforced; keep it that way.
2. `dividend_covenant_veto` must stay a **pure veto** (one planned action, blocked by
   `covenant_headroom` only, `executed == 0`) — it is the flagship governance moment.
3. `causal_truth` may only ever be composed from figures already present in the
   trace. If a scenario changes, the truth changes with it automatically — do not
   hand-write truth copy.
4. Pricing stays free of performance claims and dead `href="#"` CTAs (test-enforced).

## Deployment note

Homepage changes ship via `.github/workflows/deploy-homepage.yml` on pushes to
`main` touching `# MIZ OKI 3.5/**`. The auto-merge bot's `GITHUB_TOKEN` merges still
do not fire push-triggered workflows — but **this is now handled automatically** by
the Deploy Router (`.github/workflows/deploy-router.yml`, shipped 2026-07-23 as the
CI-001 fix). The bot dispatches the router on merge; the router diffs the merge range
against each `deploy-*.yml`'s own `on.push.paths` and dispatches what a human push
would have fired.

**Proven on this page's 2026-07-27 deploy:** bot merged `48cc683` → router ran
`14:42:24Z` → `deploy-homepage` ran `14:42:49Z` with `event=workflow_dispatch` →
live. No manual intervention.

Do **not** run manual deploy sweeps after a bot merge any more. Instead check the
router run for that merge — its summary states exactly which deploy workflows matched.
Only dispatch by hand if the router shows no match and you believe it should have.

---

## Round 3 — 2026-07-27 (presentation layer)

**Source:** the same Grok conversation, re-supplied via its share link
(`grok.com/share/bGVnYWN5_dcd9c3b9-f0ad-44b4-b9c7-47b0aaa93943`, 32 messages).
Its final two messages (#29, #31) are a *presentation* critique that Rounds 1–2 never
addressed — density, hierarchy, flow, and the demo's position on the page.

| # | Item | Disposition | Where it landed |
|:--|:-----|:------------|:----------------|
| 16 | Interactive demo as the **centerpiece**, not a mid-page feature | **Adopted** | The `#liveTeaser` block moved out of `#action-flow` into a new `#live` section directly after the hero — section 2 of 15. All `lt*` IDs preserved so `home-demo.js` binds unchanged. |
| 17 | Animated pipeline rail with lit/completed stage dots on the **static** 7-stage loop | **Adopted** | `.srp-rail` / `.srp-rail-fill` + `.srp-stage.lit/.done` in `#orchestration`, reusing the `.lt-stage` visual language and `--nexus`/`--estate` tokens. `IntersectionObserver`, fires once, snaps complete under `prefers-reduced-motion`. Round 1 had added this to the *teaser* only. |
| 18 | Omnichannel acquisition surface (Meta / Google / email / programmatic) — from msg 11 | **Adopted — as capability description** | New `#omnichannel` section accented `var(--signal)`. See rejection 21 for what was stripped out of it. |
| 19 | Pricing tiers visible on the **homepage** | **Adopted** | New `#pricing` preview mapped to the autonomy ladder, consistent with `pricing.html`. No dollar figures; CTAs → `/pricing` + `hello@mizoki3.com`. |
| 20 | "Reduce text density / strengthen hierarchy / simplify nav" | **Adopted** | Nav 11 → 6 items; hero lede 6 lines → 4; hero CTA order flipped so "Run a Live Decision" leads; over-long section sub-copy trimmed; redundant `→` separators dropped from `#orchestration` now that the rail carries flow. |
| 21 | Omnichannel impact metrics — *"31% CPA drop in 11 minutes"*, *"shifts $42k to high-ROAS lookalikes"* | **Rejected** | Same rule as ledger item 12. Fabricated; no source anywhere in the conversation. The `#omnichannel` cards describe mechanism only and were audited to contain zero numeric performance claims. |
| 22 | Palette swap to zinc-950 + cyan/violet, Tailwind CDN, Font Awesome, emoji division icons | **Rejected** | Re-confirms ledger item 10. The five-division palette is load-bearing across 27 pages; swapping the homepage alone desynchronizes the site. |
| 23 | Grok's 5-section page shape (drops Evidence, Governance, Nexus, Use Cases) | **Rejected** | Re-confirms ledger item 15. |

**Verification:** 248/248 tests; HTML tag-balanced; no broken anchors; zero console
errors; no horizontal scroll at 1440/768/390px; mobile sheet resolves all six nav
anchors; live demo driven headlessly end-to-end (covenant veto → `VETOED`, 7/7 stages,
real trace id). Production re-verified after deploy: same trace id as local
(`cap-cbd156c16c74`) — seed-42 determinism holds end-to-end.

**Added invariant (5):** the live teaser stays **above the fold region** — it is the
page's primary proof, not a mid-page feature. If sections are reordered, `#live` stays
immediately after the hero.

Plan + reusable prompt: `docs/HOMEPAGE_MERGE_PLAN_2026-07.md`.
