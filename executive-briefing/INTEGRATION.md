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
  contactUrl: "https://mizoki3.com/#contact",
  onDecisionConfirmed: function (payload) {
    // payload.intent: pilot | board | deep-dive
    // Send to analytics / form endpoint
  },
};
```

Public API:

```js
MIZOKI_Briefing.start();
MIZOKI_Briefing.reset();
MIZOKI_Briefing.getState();
```

## Production notes

- CSS is self-contained (no CDN framework). Fonts load from Google Fonts; self-host if preferred.
- State persists in `localStorage` key `mizoki-exec-briefing-v1`.
- Metrics in domain packs are **illustrative** until replaced with customer data in `js/data.js`.
- Mobile-first; primary targets ≥ 44px.

## CTA mapping suggestions for mizoki3.com

| Site CTA | Action |
|----------|--------|
| Hero “See it for your domain” | `/executive-briefing/` |
| Demo modal | iframe embed |
| Pricing “Talk to us” | after `decision_confirmed` → contact / Calendly |
