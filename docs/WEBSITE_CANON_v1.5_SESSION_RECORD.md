# MIZOKI3 Website — Canon v1.5 Session Record (July 28–30, 2026)

**Status:** ✅ LOCKED, LIVE-VERIFIED, GOVERNED
**Owner directive:** the v1.5 "night dossier" look and feel is the source of
truth; `/demo` + `/executive-briefing/` are the core of the operation; nothing
uploads to production without specific human approval.
**Authoritative docs:** `README.md` + `CLAUDE.md` (monorepo root and
`# MIZ OKI 3.5/`). This record is the durable session archive behind them.

---

## 1. What is live (production, mizoki3.com)

| Property | Value |
|:--|:--|
| Cloud Run service | `mizoki-website` · project `spry-bus-425315-p6` · us-central1 |
| Homepage | Canonical **night dossier**, sha256 `35a7e5d33a486725b7f997263885d287340c944d980f6f7b1121185e66ac08ac` (80,479 B), **16/16 fingerprint suite passing** |
| Demo platform (core) | `/demo` hub + six desks (`signal, counsel, estate, capital, risk`) + `/demo/nexus` flagship — unified dossier dark-plate design |
| Executive Briefing (2nd track) | `/executive-briefing/` — 8 domains, **Signal (default) + Legal listed first** as the platform's most mature channels; lead-path handoff via `/contact` |
| Design system | Ink plates `#0A1418`/`#0B1E26`, hairlines `#1C2E36`, cyan `#3FDCF2` primary (ink `#06262C` text), pass `#41D695` / warn `#E0A92E` / veto `#FF6B7C`; Instrument Serif · DM Sans · JetBrains Mono; 2px flat, no glows |
| Final audit | All 19 canon files downloaded from production — **LIVE == CANON byte-for-byte** |

## 2. Canonical lineage (this session)

| Version | Change | Deploy proof |
|:--|:--|:--|
| v1.0 | Fingerprint-gated canonical dossier homepage reconstructed (gauge-39, 12 connectors incl. The Trade Desk; DV360/Stripe/Nexus-snapshot drift markers banned) | rev `00126-c4l` |
| v1.1 | Live-demo showcase (§06) + privacy/terms + favicon set | rev `00127-jr5` |
| v1.2 | Executive Briefing module + Flask routes (traversal-guarded) + two-track CTAs (3 links) + demo-hub banner | rev `00128-gjn`, run 30484256691 |
| v1.3 | Site-wide dossier unification — 45-file retoken (demo hub/desks/Nexus/walkthrough/briefing/marketing/blog), serif display, flat radii, glow removal, SRDPV-DAL→SRPVDAL sweep | rev `00129-rvc`, run 30552930242 |
| v1.4 | **Night dossier homepage** — style-block-only inversion; content byte-identical; fingerprints intact | rev `00132-z5s`, run 30554839657 |
| v1.5 | Briefing gains **Signal + Legal flagship domain packs** (ReLU-gated reallocation w/ rollback token; MoLE conflict catch, privilege gate, **advisory-only by design** — zero autonomous legal conclusions) | run 30555860065, live-verified 15:18Z |

Parallel integration reconciled: `feature/executive-briefing` (`16b324f`,
theirs-synced `42b7a63`, terminology repaired `d8d9160`) shipped the briefing
lead-path handoff + walkthrough two-track banner + pricing CTA; merged cleanly
with v1.5; canon re-pinned to the union (`baa848d`).

## 3. The lock (governance in force)

| Layer | Mechanism | Proof |
|:--|:--|:--|
| Canon manifest | `# MIZ OKI 3.5/canon.lock.json` — 19 surfaces sha256-pinned; checker `scripts/check_design_canon.py` (verify / `--update` re-pin) | tamper-tested; live audit 19/19 |
| CI deploy | `deploy-homepage.yml` **dispatch-ONLY** (push trigger removed) + required typed `APPROVED` input + pre-build canon gate | wrong-token dispatch **failed in 13s** (run #40); governance merges fired **zero** deploys |
| Deploy Router | No `push.paths` → router structurally cannot match the workflow — push→auto-merge→router→auto-deploy chain retired for the site | empirical: merges 6cf7716/baa848d/56e9570 → no runs |
| Mirror repo | `mizoki-3-5-website/deploy-cloudrun.yml` dispatch-only (`ef600ec`); parity commits `[skip ci]` | latest pipeline run remains #56 (July 6) |
| Legacy scripts | `deploy.sh`/`master-deploy.sh` (both repos) demand typed `APPROVED` or `MIZOKI_DEPLOY_APPROVED=APPROVED` + canon check | refusal path tested |
| Documentation | Governance blocks in root+site `README.md`/`CLAUDE.md`/`AGENTS.md`; `docs/DESIGN_CANON.md`; root docs at v6.45.37 | this record |

**Human deploy procedure:** approve the specific change → re-pin lockfile in the
same commit → merge → Actions → "Deploy MIZ OKI 3.5 Homepage" → type `APPROVED`.

## 4. Repository state

| Repo | Role | Key commits (this session) |
|:--|:--|:--|
| `mediaintelligence/MIZOKICloudRun` (SOURCE OF TRUTH) | `# MIZ OKI 3.5/` → Cloud Build → `mizoki-website` | v1.2 `6cc9a35` · v1.3 `aed5a98` · v1.4 `313292b` · v1.5 `0d9dd2c` · canon+gates `d308263` · re-pin `baa848d` · docs lock `56e9570` |
| `mediaintelligence/mizoki-3-5-website` (MIRROR) | Parity mirror; pipeline dispatch-only | dispatch-lock `ef600ec` · parity `ae21de7`/`2180a41`/`8f71520`/`16b06d9` · governance `b51be2a` |

## 5. Verification methodology (repeatable)

- **Fingerprint suite (16 items)** on every homepage change: 10 must-be-present
  (incl. `id="gscore" style="color:var(--veto)">39`, ILLUSTRATIVE FIGURES label,
  CanonicalEventEnvelope v1.0, MoLE, The Trade Desk, 12-connector count) and 6
  must-be-absent drift markers (gauge-87, "customers we've onboarded", Live
  Nexus Snapshot, 18,742, Stripe, DV360).
- **Canon audit**: download all 19 pinned files from production, run
  `check_design_canon.py --root <downloads>` → must print `CANON OK`.
- **Deploy causality**: revision line from the workflow job log
  ("Service [mizoki-website] revision [...] serving 100 percent of traffic").
- **Rendering**: Playwright (bundled Chromium) full-page screenshots + interactive
  walks (briefing stage machine, domain switching) before every ship.
- **Tests**: site suite 251 tests — the only 2 failures are pre-existing
  dossier-swap artifacts (old-homepage assertions); any NEW failure blocks.

## 6. Rules for future agents (binding)

1. `README.md` + `CLAUDE.md` are the only sources of truth; read the site
   folder's governance block first.
2. Never edit canon-pinned files, dispatch the deploy workflow, run deploy
   scripts, or re-pin the lockfile without an explicit, specific human
   instruction.
3. Approved changes re-pin `canon.lock.json` in the same commit.
4. Parity pushes to the mirror always use `[skip ci]`.
5. Homepage edits must keep the 16-item fingerprint suite passing — run
   the checker before and after.

---

## 7. Post-lock approved change — ORACLE / Signal Intelligence (2026-07-30)

Owner instruction: *"incorporate this into the single intelligence marketing
page and demo"* (the Signal Intelligence Division / ORACLE capabilities doc).
That instruction is the specific human approval required by §3.

| Item | What shipped to `main` (NOT deployed — awaits `APPROVED` dispatch) |
|:--|:--|
| `signal.html` | Rewritten as the Signal Intelligence Division page (ORACLE / Latent Intent Inference): claim-strip hero ("What we say / What we never say"), crystal-ball-plus-proof plates, 4 intent stages, 6 capability cards (Cells 33/28/34), proof section (X-Learner/DR-Learner + DoWhy + holdout/ghost-bid/geo + caused-vs-anticipated ledger), claim-labeled targets (−40% CAC / +35% ROAS / +67% ROI as design targets), 5 playbooks, governance plate, cell map. Night-dossier vocabulary throughout; not canon-pinned; `/signal` test contract intact. |
| `demo-signal.html` | New static section "5 · ORACLE — anticipatory intent" (stage strip + SERVE/PROVE/GOVERN + promotion gates + `/signal` link). Canon-pinned → `canon.lock.json` re-pinned in the same commit (new sha for `demo-signal.html`; lock `locked` note records the approval). Demo runtime untouched — interactive run re-verified. |
| Doc archive | `docs/SIGNAL_INTELLIGENCE_ORACLE_CAPABILITIES.md` (owner-supplied source, verbatim, with incorporation header). |
| Verification | Canon `CANON OK 19/19` after re-pin; suite 260 tests with only the 2 pre-existing dossier-swap homepage failures; Playwright renders of both pages; live demo run smoke (decision card produced). |

Claim discipline embedded in the copy: "anticipatory intent with proof of
causal lift", never "mind-reading"; calibrated probabilities, never "will buy";
"proven-incremental" only after refutation; targets labeled, never guaranteed;
no audio ever; consent-first; observe-only default (Brier ≤ 0.20 · AUC ≥ 0.72 ·
stable lift ≥ 2 purchase cycles to promote).

---

## 9. Post-lock approved change — Decision Concierge (2026-07-31)

Owner spec: guided-by-default Guide Agent for the executive track — narrator +
option framer riding the fixed 5 stages, sales-trained, never bypassing the
critical gate, always ending in pilot / board / deep-dive capture, with every
interaction remembered for improvement.

Shipped as Executive Briefing v1.1 (details: `docs/GUIDE_AGENT_SPEC.md`):
`guide.js` docked rail (canon-pinned; manifest now **20 surfaces**;
`index.html`/`app.js` re-pinned), allowlist-retrieval Q&A + 6-objection bank in
`mizoki_runtime/briefing_guide.py` (no generative path), interaction memory
ledger + `/api/briefing/guide/{event,ask,summary}`, and `guide.answer` /
`guide.memory_summary` MCP tools under the Boss runtime. Verified: Playwright
E2E (guided default, stage sync, BI-objection Q&A round-trip, highlight w/ zero
auto-resolves, self-drive persistence) — one real overlap bug caught and fixed
by docking; suite **279** w/ only the 2 pre-existing homepage failures;
`CANON OK 20/20`. Ships via human `APPROVED` dispatch.

## 8. Post-lock approved change — Boss voice docent (2026-07-31)

Owner instruction: give the Boss a voice on the demo — walk viewers through
every action and why, cooperatively, as a salesman who never pushes.

| Item | What shipped to `main` (ships via human `APPROVED` dispatch) |
|:--|:--|
| `assets/js/boss-docent.js` | Self-injecting guided-tour engine: Web Speech **synthesis only** (no mic / SpeechRecognition / getUserMedia — test-enforced), captions always on, dossier-styled launch button + bottom docent bar. Narration = pre-vetted copy + dynamic slots read from the run's own DOM (gate rows, verbatim guardrail veto, causal truth, decision title) — the Boss never invents a number. Presses Start itself; yields on any visitor control touch; closing chips: replay-remixed / executive briefing / one pilot CTA. Tour epochs kill stopped-tour leakage; minimum caption reading time survives voiceless-speechSynthesis browsers. |
| `demo-signal.html` | Script wiring + `MizokiBossDocent.init()` — canon re-pinned in the same commit. Player (`demo-signal.js`) untouched. |
| `tests/test_boss_docent.py` | 6 tests: wiring + claims-lint of every speakable string (banned sales/claims vocabulary absent; disclosures present; exactly one pilot CTA; no audio-capture APIs). |
| Verification | 3 Playwright end-to-end runs (full tour in captions mode, take-over courtesy, restart-from-fresh); suite 266 with only the 2 pre-existing homepage failures; `CANON OK 19/19` after re-pin. |
