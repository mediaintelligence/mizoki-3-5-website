# MIZ OKI 3.5 — Executive Briefing integration

Deployable module for **mizoki3.com**. Implements the approved skills:

- `miz-oki-platform`
- `executive-briefing-process`
- `domain-scenario-packs`

## What ships

```
mizoki3-executive-briefing/
├── index.html          # Standalone page + embed shell
├── css/briefing.css    # Premium dark design system (no Tailwind CDN)
├── js/data.js          # Domain packs + economics
├── js/app.js           # Stages, critical-path gate, decision capture
└── INTEGRATION.md
```

## Process (fixed)

1. Context → role, scale, domain  
2. Exposure → status-quo cost  
3. Live scenario → resolve signals (**critical gate before case**)  
4. Business case → ROI / payback / board points  
5. Decision path → pilot | board packet | deep-dive (**intent required**)

Domains: Logistics, HR, Finance, Ops, CX, Supply.

## Integrate with mizoki3.com

### A. Full route (recommended)

Copy the folder to the site static root as `/executive-briefing/` and link CTAs:

```html
<a href="/executive-briefing/">Start executive briefing</a>
```

### B. Homepage modal / iframe

```html
<iframe
  id="mizoki-briefing-frame"
  src="/executive-briefing/"
  title="MIZ OKI executive briefing"
  style="width:100%;min-height:90vh;border:0;border-radius:16px;background:#0a0a0b"
></iframe>

<script>
  window.addEventListener("message", (e) => {
    if (!e.data || e.data.source !== "mizoki-executive-briefing") return;
    // e.data.event: briefing_started | stage_changed | signal_resolved |
    //               decision_intent | decision_confirmed | briefing_restarted
    if (e.data.event === "decision_confirmed") {
      // e.data.detail → { intent, domain, role, companyName, companySize }
      // Route to CRM, calendar, or contact form
    }
  });
</script>
```

### C. Config hooks

Set before `app.js`:

```js
window.MIZOKI_CONFIG = {
  contactUrl: "/contact",
  onDecisionConfirmed: function (payload) {
    // payload: { intent: pilot|board|deep-dive, domain, role, companyName, companySize }
    // Send to analytics / form endpoint
  },
};
```

This page's own `index.html` ships a default `MIZOKI_CONFIG` (guarded by
`window.MIZOKI_CONFIG || {…}`, so an embedding page set before these scripts
still wins) that implements the deployed handoff:

1. validates `intent` against `pilot | board | deep-dive` and `domain` against
   the packs in `js/data.js`;
2. stores `{ intent, domain, role, companyName, companySize, source,
   confirmedAt }` in `sessionStorage` under `mizoki.executiveBriefing.decision`;
3. navigates to `/contact?source=executive-briefing&intent=…&domain=…` —
   company/role deliberately stay out of the URL; the contact page prefills
   them from the sessionStorage payload.

Public API:

```js
MIZOKI_Briefing.start();
MIZOKI_Briefing.reset();
MIZOKI_Briefing.getState();
```

## Production notes

- CSS is self-contained (no CDN framework). Fonts load from Google Fonts; self-host if preferred.
- `css/briefing.css` styles the page shell (`html`, `body`, `*`, `button`
  globals). That is safe for the full route and for iframe embeds (separate
  document); the inline "`#mizoki-briefing` on any page" option would leak
  those globals — scope them first if you ever embed inline.
- Progress persists in `localStorage` key `mizoki-exec-briefing-v1`; saved
  state is re-validated on load, so a stale or hand-edited value can never
  brick the page. Confirmed decisions persist in `sessionStorage` key
  `mizoki.executiveBriefing.decision`.
- Metrics in domain packs are **illustrative** until replaced with customer data in `js/data.js`.
- Mobile-first; primary targets ≥ 44px.

## Deployed on mizoki3.com (this repository)

| Concern | Implementation |
|---------|----------------|
| Canonical path | `/executive-briefing/` (trailing slash — asset links are relative). Flask serves it in `app.py`; the bare path 308-redirects to the canonical form. |
| Assets | `/executive-briefing/<path>` route with extension allowlist + traversal check; css/js verified to serve `text/css` / `text/javascript`. |
| Decision handoff | Default `MIZOKI_CONFIG` above → `/contact` (the site's real lead path), which prefills company/interest/message from the sessionStorage payload — never raw JSON. |
| CTAs | Homepage (§06 card, §07 plate, footer), `/pricing` enterprise tier, `/demo` hub banner, `/walkthrough` hero cross-link, `demo-opener.html` audience note — all linking `/executive-briefing/`. |
| Two-track positioning | Executive Briefing = executive decision track (~9 min); Technical Walkthrough + live demos = evaluator track. |
| Sitemap | `/executive-briefing/` listed in the generated `/sitemap.xml`. |
| Tests | `python -m unittest tests.test_executive_briefing` (routes, redirect, MIME, traversal, handoff wiring, CTAs, sitemap) — part of `python -m unittest discover tests`. |
