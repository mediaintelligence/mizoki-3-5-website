# MIZ OKI Media — /media Standalone Product Site: Build & Launch Record

**Date:** 2026-08-04 · **Status:** LIVE in production (mizoki3.com/media)
**Deploy:** canonical `deploy-homepage.yml` run **#53** (`approve=APPROVED`, success in ~110s)
**Change chain:** mizoki-3-5-website PR `#28` (main `00cd7ea`) → MIZOKICloudRun parity PR `#591` (main `bc154c0`) → run #53 · docs records: PR `#29` / PR `#592`

This document is the complete record of the MIZ OKI Media build — the owner's
four-part deployment prompt executed end to end: mission and constraints,
integration strategy, everything built, every file touched, the truth-discipline
decisions, the verification evidence, the deployment chain, rollback, and what
was deliberately deferred. The compact operational summary lives in
`CLAUDE.md` ("Recent Work → MIZ OKI Media standalone site LAUNCHED"); this file
is the deep record.

---

## 1 · Mission and constraints

The owner supplied a four-part deployment prompt:

- **Part 1** — mission, constraints, repository inspection, architecture. Build
  a new standalone commercial product, **MIZ OKI Media** ("Causal Growth
  Control", "powered by the MIZ OKI Decision Graph"), at `mizoki3.com/media`.
  Strictly additive: the homepage, `/marketing`, `/signal`, demos, APIs,
  admin, deployment, and all shared assets stay untouched except the minimal
  route registration.
- **Part 2** — homepage structure: a required 12-section order, the customer
  problem wall, a 5×11 capability comparison, the interactive Decision Graph
  with four memory layers, the expandable SENSE→LEARN flow, a specified live
  decision scenario, film integration with transcript, and the executive
  value proposition.
- **Part 3** — eight supporting pages (platform, decision-graph, how-it-works,
  use-cases, pilot, trust, resources, contact), accessibility/performance/SEO
  requirements, the full testing protocol, deployment safety, and a mandated
  completion-report format.
- **Part 4** — the quality bar: category-defining enterprise product
  experience (executive copy, informational motion only, honest comparisons,
  interactive demonstrations, trust-before-AI, executive proof, evidence
  labels, conversion pathing, reusable design system), plus ten
  "beyond the website" recommendations recorded as roadmap.

House constraints that governed every decision: the v1.5 night-dossier canon
lock (20 surfaces, sha-pinned), human-approval-only deploys, the
`/marketing` drift guard, the truth-discipline content gate
(`scripts/content_qa.py`), and the story-bank claim rules (illustrative
labels, no guarantees, no compliance-cert claims).

## 2 · Integration strategy (why this shape)

**Chosen: isolated static directory + minimal Flask routes** — Part 1's
preferred option 1/2 hybrid, and the least invasive available:

- All pages are self-contained HTML files in `media/`; sub-pages share ONE
  route-local stylesheet (`media/assets/media.css`) that no classic-site page
  loads and that loads nothing from the classic site.
- `app.py` gained exactly one additive route block: an `any()`-converter
  route serving the eight clean sub-page URLs (`/media/<page>` →
  `media/<page>.html`), registered beside the pre-existing `/media` home and
  traversal-guarded asset routes, following the `/marketing` convention.
  Unknown paths still 404 through the asset route's allowlist.
- No shared template, stylesheet, nav, or sitemap entry was modified. The
  canon check (20/20) proves the classic site is byte-identical; a
  test-enforced isolation contract proves no classic surface links into
  `/media` and `/media` pulls no external origin.

## 3 · What was built

### 3.1 Homepage (`/media`) — the required 12-section order

1. **Hero** — mandated headline ("Know why performance moved. Put the next
   dollar where it creates profit."), category + platform labels, the
   mandated support paragraph, CTAs (Explore the 90-Day Pilot / Watch the
   Explainer), platform note, and the Decision Graph chain strip with a
   motion-guarded signal pulse (the Part 4 "hero movement").
2. **Customer problem** — "The Most Expensive Decisions Are Still Guesswork":
   the 11 executive questions as staggered chips converging into the answer
   band: *one governed decision pathway*.
3. **Why existing tools stop too early** — the specified 5-column × 11-row
   capability table (Dashboards / Attribution / CDPs / Bid Automation /
   MIZ OKI Media) with factual capability-boundary footnotes; accessible
   table semantics; horizontal scroll contained (see §7 bugfix).
4. **The Decision Graph** — Part 2 copy, connected-to chips, animated SVG
   pathway (dash-flow, motion-guarded), seven expandable nodes (native
   `<details>`; hover-opens on precise pointers; click pins), the pinned
   knowledge-graph distinction quote, and the four memory layers with their
   full stored-field lists.
5. **How MIZ OKI Media works** — the SENSE→LEARN strip plus seven expandable
   stages, each carrying Purpose / Inputs / Outputs / Example / Business
   value with the owner-specified example chip sets; LEARN closes with
   Predicted → Actual → Confidence adjustment → Future weighting.
6. **Live decision scenario** — the specified story: CPA +34% (labeled
   *Illustrative Example* in place), stable creative CTR, rising latency and
   checkout abandonment, constrained inventory; four hypotheses visibly
   ruled out (struck through), two confirmed; diagnosis = landing-page
   performance compounded by inventory constraints; action = repair /
   temporarily rebalance / protect margin; **approval routed to Operations**.
7. **Product explainer film** — native HTML5 video (controls, `playsinline`,
   `preload="metadata"`, poster, never autoplay), the mandated caption
   sentence, and a served verbatim transcript (see §6 truth note).
8. **Decision jobs** — eight labeled jobs (Pilot-ready / Roadmap).
9. **Platform architecture** — the reusable architecture SVG embedded +
   downloadable, linking to `/media/platform`.
10. **90-day pilot** — scope, three phases, earned-autonomy framing, linking
    to `/media/pilot`.
11. **Trust & governance** — four governance cards linking to `/media/trust`.
12. **Final CTA** — pilot mailto + contact-page link.

Interleaved non-required sections (order-safe, test-enforced): the film
storyboard, the executive value proposition (Marketing Leaders / Finance /
Operations → one governed recommendation), and the evidence-and-maturity
labels legend.

### 3.2 The eight sub-pages

| Route | Page |
|:------|:-----|
| `/media/platform` | **The Commercial Decision Operating System** — seven capabilities (Commercial Intelligence, Causal Reasoning, Counterfactual Planning, Policy Validation, Human Approval, Governed Execution, Outcome Learning) mapped to SRPVDAL, the architecture diagram, the continuous operating model, "what this is not". |
| `/media/decision-graph` | The definitive Decision Graph page — "**This remembers why.**"; operating-model-vs-storage positioning; honest does-well / where-it-stops comparison across data warehouse, semantic layer, knowledge graph, vector database, agent memory; Evidence→Context→Decision→Outcome diagram; six load-bearing properties (temporal memory, provenance, causal relationships, approval history, replay, continuous learning); a worked 7-layer decision-record explorer. |
| `/media/how-it-works` | The full lifecycle: all seven stages with Objective, Inputs, Outputs, AI responsibilities, Human responsibilities, Governance checkpoints, Example scenario, and Typical metrics (named, never valued) on a visual timeline — plus the **interactive walkthrough** (§3.4). |
| `/media/use-cases` | Fifteen use cases across Marketing (4), Commerce (4), Operations (3), Executive (4), each with Business problem / Current approach / MIZ OKI Media approach / Expected operational benefits / Required approvals. |
| `/media/pilot` | The structured 90-day plan: scope chips, three phases with per-phase governance checkpoints, named success metrics (targets set at scoping, not invented), and the three explicit exits: Expand / Extend / Stop. |
| `/media/trust` | The trust center: "Trust comes from governance, not automation." Ten commitments individually labeled Live / Pilot-ready / Roadmap; six executive-evaluator cards (CFO, Legal, Security, Marketing, Operations, Procurement); bright lines (no certification theater, no outcome promises, no quiet autonomy). |
| `/media/resources` | Downloads hub (six materials) + a nine-entry FAQ; whitepapers honestly listed as "publish here as released". |
| `/media/contact` | Executive contact experience on the approved mailto (`contact@mizoki3.com`, subject "MIZ OKI Media Pilot") — what to include, what happens next, no-pressure framing. **No new backend, no form.** |

Every page: unique title, meta description, canonical, OG + Twitter card,
exactly one `h1`, skip link, consistent site nav with `aria-current`, footer,
and a next-step conversion band (platform → decision-graph → how-it-works →
use-cases → pilot → contact; trust → pilot; resources → contact).

### 3.3 Route-local design system (`media/assets/media.css`)

The Part 4 "reusable component library": tokens (night-dossier palette,
system font stacks only), nav, sub-page hero, cards (capability / decision /
evidence / value), labels (Live / Pilot-ready / Illustrative / Roadmap),
chips, buttons + CTA/answer bands, definition-row grids, comparison tables,
vertical timeline blocks, flow strips, the interactive-demo components,
verdict rows, resource cards, FAQ accordions, footer, and responsive rules.
Sub-pages only — the homepage deliberately keeps its inline CSS
(zero-dependency landing, test-pinned as self-contained).

### 3.4 Interactive demonstrations

- **Decision Graph nodes** (`/media`): native `<details>` — click/keyboard
  everywhere; on `(hover:hover) and (pointer:fine)` devices hover opens a
  node and clicking a hover-opened node **pins** it (the naive implementation
  closed under the cursor; caught in browser verification and fixed —
  hover→open, click→pin, second click→close, hover-away closes unpinned).
- **"Move the signal. Watch the system answer."** (`/media/how-it-works`):
  a CPA-movement slider drives four hypothesis weight bars, policy-check
  results, the recommendation, and the required authority through three
  deterministic states — noise envelope (no action; restraint recorded),
  diagnosed rebalance (routed to the media lead), escalation (larger actions
  vetoed; Operations + Finance authorize jointly). **Strictly deterministic**:
  no randomness, no clock reads (test-enforced across every /media page);
  `aria-valuetext` on the slider, `aria-live` verdicts, `noscript` fallback
  describing all three states; every number labeled illustrative.

### 3.5 Downloadable resources (sales enablement)

Single-file, print-friendly (`@media print` light theme), `noindex`:

- `mizoki-media-product-overview.html` — the one-page product argument
- `mizoki-media-decision-graph-overview.html` — the operating-model argument
- `mizoki-media-pilot-guide.html` — the 90-day structure
- `mizoki-media-executive-summary.html` — "The sixty-second version"
- `mizoki-media-architecture.svg` — the four-layer platform diagram
  (sources → Decision Graph → authority → execution, with the learning
  return arc); embedded on `/media/platform` and the homepage
- `mizoki-media-transcript.html` — the film transcript (§3.6)

### 3.6 Film integration

The explainer film (`media/video/mizoki-signal-explainer.mp4`) streams
through the traversal-guarded asset route as seekable `video/mp4` (Range →
206). During the build the actual asset was verified by **extracting and
reading its frames** (Playwright's Chromium lacks H.264 decode; the
`imageio-ffmpeg` static binary was used): it is a **32-second silent
seven-scene preview render** whose own persistent footer reads "PLACEHOLDER
RENDER — FINAL NARRATED FILM PENDING". The transcript quotes all seven
scenes' on-screen text verbatim and states the silent-preview status.

## 4 · Backend changes (`app.py`)

One additive block (12 lines): the sub-page route.

```python
@app.route(
    "/media/<any('platform', 'decision-graph', 'how-it-works',"
    " 'use-cases', 'pilot', 'trust', 'resources', 'contact'):page>",
    strict_slashes=False)
def media_subpage(page: str):
    return send_from_directory(BASE_DIR / "media", f"{page}.html")
```

The pre-existing `/media` home route and extension-allowlisted,
resolved-path-checked asset route are untouched; `.css` and `.svg` were
already on the allowlist. `/media-buying` remains an unrelated 301 to
`/marketing`. The sitemap route was deliberately NOT modified (§9).

## 5 · Truth discipline (decisions of record)

- **"Two-minute film" NOT adopted.** Part 2 mandated a caption calling it a
  two-minute film; the measured asset is 32 seconds and silent. The page
  keeps the mandated sentence's substance ("This film demonstrates how
  MIZ OKI Media transforms fragmented commercial signals into governed
  business decisions.") and frames the cut honestly as a "silent preview
  render" with a Preview-render label. Restore the exact wording only when
  the real narrated film ships.
- **Every visible number labeled** (the scenario's +34% carries
  *Illustrative Example* inline and in the footnote; the walkthrough carries
  section-level Illustrative labels and a determinism footnote). The house
  gate (`content_qa.check_file`) passes on every /media page, in-suite.
- **Zero buzzwords** — swept for leverage / revolutionary / next-generation /
  best-in-class / AI-powered / cutting-edge / seamless / game-changing:
  clean across all pages and downloadables.
- **No compliance-cert claims** anywhere (also test-banned: "SOC 2
  certified", "HIPAA certified", "guaranteed ROI", "patented", …); the trust
  page names principles and offers scoping review instead.
- **Capability labels never blurred**: Live / Pilot-ready / Illustrative /
  Roadmap applied per capability, with the platform loop labeled Live and
  media-application delivery labeled Pilot-ready.
- **Comparisons stay complementary** — every category (and every storage
  structure) gets a genuine "does well" before "where it stops"; footnotes
  credit bid automation's in-platform competence and position the Decision
  Graph as complementing warehouses/CDPs, not replacing them.
- **Signal is never a public product name** on this surface (internal file
  names like `mizoki-signal-explainer.mp4` are paths, not copy).

## 6 · Accessibility & performance

- One `h1` per page; ordered headings; skip links; keyboard-native
  `<details>` interactions; visible focus rings; native video controls; alt
  text + explicit width/height on all imagery; `aria-live` demo verdicts;
  screen-reader yes/no cells in the comparison table; reduced-motion guards
  on every animation; no essential information behind hover or motion.
- No external fonts, no CDNs, no frameworks, no third-party requests of any
  kind; sub-pages share one cached stylesheet; below-the-fold images lazy-load;
  video preloads metadata only; JS exists on exactly two pages (homepage
  reveal/nodes; how-it-works walkthrough), each a few KB, dependency-free.

## 7 · Verification evidence

- **Test suite**: 415 tests, only the 2 documented pre-existing homepage
  failures (they predate this work and test `/`, untouched). The `/media`
  contract is 49 tests: routes (incl. 404s and trailing slashes), verbatim
  positioning, required section order, question wall, comparison grid
  (11 rows × 5 columns, full MIZ column), interactive node chain, memory
  layer fields, flow contract (5 required rows × 7 stages), scenario story,
  film caption + transcript verbatim lines, executive value prop, per-page
  SEO/a11y/isolation, internal-link crawl (zero broken links), the
  deterministic-JS guard, per-page truth-discipline checks, downloadables
  on disk + served with correct mimetypes, contact backend-free, and
  classic-site-untouched.
- **Gates**: canon check 20/20 · `content_qa` self-test + scan clean ·
  marketing drift guard OK — run in this repo AND re-run inside the
  MIZOKICloudRun tree before the parity merge.
- **Browser verification** (headless Chromium, desktop 1280px + mobile
  390px, reduced-motion honored): all nine pages, zero page errors, zero
  console errors, zero horizontal overflow; the walkthrough's three states
  exercised; hover/pin/close node sequence exercised.
- **Bugs caught by verification, fixed pre-launch**: (1) the comparison
  table's absolutely-positioned visually-hidden cells escaped the scroll
  container's clipping and widened the page on mobile — fixed with
  `position: relative` on the wrapper; (2) clicking a hover-opened graph
  node snapped it shut — fixed with the pin behavior.

## 8 · Deployment chain & production verification

Owner approval in-session ("Approved deployment"); dispatch performed under
the canonical workflow's own governance clause (explicit human instruction),
matching the recorded precedent of runs #47–#49 and #52.

1. **PR #28** (this repo) → `main` @ `00cd7ea` — the full /media site.
2. **Parity sync** → MIZOKICloudRun: the three modified shared surfaces and
   the film verified **byte-identical to the last parity point before
   copying** (the binding lesson from the 2026-08-04 route-loss incident:
   parity is a union merge, never a blind byte-copy); 18-file delta landed
   as **PR #591** → their `main` @ `bc154c0`; all four gates + the 49 tests
   re-verified inside their tree first.
3. **Canonical deploy**: `deploy-homepage.yml` run **#53**,
   `approve=APPROVED`, success (15:34–15:35 UTC).
4. **Production verified from the live domain**: all nine pages 200; film
   `video/mp4` with Range 206; poster/storyboard `image/png`; architecture
   `image/svg+xml`; transcript/downloadables `text/html`; stylesheet
   `text/css`; content markers live on decision-graph, how-it-works, and
   trust; classic root 200 with ZERO `/media` references; `/marketing` and
   `/signal` 200; `/media-buying` 301 → `/marketing` intact.
5. **Records**: CLAUDE.md launch entries merged in both repos (PR #29 /
   PR #592) + this document.

**Rollback:** re-dispatch `deploy-homepage.yml` (typed `APPROVED`) from the
prior known-good sha `c3e0537` (their main before PR #591). The classic site
never needs rolling back — it was not modified.

## 9 · Deliberately deferred (roadmap, not oversights)

- **Sitemap**: /media pages carry canonicals but are not yet listed in the
  dynamic sitemap — one line in `app.py`'s `sitemap_xml()` when the owner
  wants them indexed.
- **Drift guard**: `check_marketing_surfaces.py` asserts the /media homepage
  marker, film, and route — not yet the eight sub-pages. Extend it in BOTH
  repos in the same change (it gates both pipelines).
- **Final narrated film** + `.vtt` captions + regenerated transcript +
  restored "two-minute" caption, when the asset exists.
- **Part 4 "beyond the website" items** (interactive product tour, ROI
  calculator, industry selector, synthetic-data sandbox, briefing generator,
  technical docs portal, benchmark methodology page, customer evidence
  center, "Why MIZ OKI" comparison hub, cross-product design system):
  recorded as roadmap. `media/assets/media.css` is the seed of the shared
  design system.

## 10 · File manifest

**Added (16):** `media/{platform,decision-graph,how-it-works,use-cases,pilot,trust,resources,contact}.html` ·
`media/assets/media.css` · `media/assets/mizoki-media-architecture.svg` ·
`media/assets/mizoki-media-{product-overview,decision-graph-overview,pilot-guide,executive-summary,transcript}.html` ·
`docs/MEDIA_SITE_LAUNCH_2026-08-04.md` (this file)

**Modified (4):** `media/index.html` (Part 2 rebuild + site nav + architecture/governance sections) ·
`app.py` (the 12-line sub-page route) · `tests/test_media_page.py` (20 → 49 tests) ·
`CLAUDE.md` + `README.md` (records)

All mirrored byte-identically into MIZOKICloudRun's `# MIZ OKI 3.5/`
(README/CLAUDE.md with repo-relative wording only).
