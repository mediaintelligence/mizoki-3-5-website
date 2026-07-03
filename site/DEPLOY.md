# MIZOKI3.com — Complete "Decision Ledger" Site (June 10, 2026)

Full static site, 16 pages, one design system. Commit to the
mizoki-3-5-website repo via GitHub (source of truth); Drive re-syncs.
Approve-before-edit: nothing has been deployed.

## Pages
/                    index.html        Homepage (ledger v3)
/counsel /estate     counsel.html ...  Five division dossiers — §04-A through
/capital /signal     estate.html       §04-E, each with FILE letter, Consumes/
/risk                ...               Produces ledger, live-metric exhibit
                                       plate, Reinforces cross-links, and the
                                       "example deployment, not a product
                                       ceiling" closer on every page.
/blog/               blog/index.html   "Notes from the nervous system" journal:
                                       featured Anatomy of a Veto with dark
                                       ACT-991 trace panel + post ledger.
/blog/<slug>/        4 full articles   Anatomy of a Veto · A Nervous System,
                                       Not a Brain · Why Agents Need a Decision
                                       Control Plane · How an Autonomous
                                       Decision Controller Thinks. Existing
                                       blog themes rewritten to current
                                       positioning; bylined Boris Mizhen.
/login               login.html        Ledger-styled sign-in shell. Form posts
                                       to /auth/login — WIRE TO EXISTING AUTH
                                       backend before deploy.
/privacy /terms      *.html            Real policy pages (counsel skim advised)
/404                 404.html          "This page was vetoed." with mini trace
robots.txt, sitemap.xml, og-image.png, favicon set

## Messaging corrections enforced site-wide
- "Inside the Brain" (live on all five current division pages) is now
  "Inside the Nervous System." Zero occurrences of "brain" as platform
  metaphor anywhere — the blog post addresses the distinction head-on.
- Divisions framed as example deployments on every dossier, not just home.
- Old "MIZ OKI 3.5 Journal / ROI Calculator / Campaign Intelligence" blog
  and login era fully retired.

## Interactive Control Plane Sandbox (homepage, §03)
Harvested from an external React prototype and rebuilt natively in the
ledger system: three threshold sliders + four scenario presets drive a live
DEL score against the autonomy gate at 80, with ELIGIBLE / OPERATOR GATE /
VETOED verdict stamps. Vanilla JS, zero dependencies, labeled ILLUSTRATIVE,
degrades to a sensible static state without JS. The prototype's React/
Tailwind/Babel stack, "One Brain" framing, invented Defense division, and
fabricated metrics were intentionally NOT adopted.

## Routing — zero config required
Every page is directory-style (counsel/index.html, blog/<slug>/index.html),
so clean URLs (/counsel/, /blog/anatomy-of-a-veto/) work on ANY static
server with no route mapping — verified by automated crawl: all 22 URLs
return 200 on a bare python http.server. On Cloud Run/Flask just serve the
directory statically. Wire 404.html as the error handler and /auth/login
as the login form target. RSS at /blog/feed.xml; sitemap.xml + robots.txt
included and cross-referenced.

## Engineering (all pages)
Progressive enhancement (full content with JS off / no IntersectionObserver),
legacy-safe JS (no NodeList.forEach, no strict-mode traps, rAF guard on the
homepage canvas with static SVG fallback), prefers-reduced-motion, flex-gap
fallback, keyboard-accessible interactive elements, per-page og/canonical
meta, JSON-LD on the homepage. Homepage, counsel, and blog index verified
end-to-end in a legacy pre-IO rendering engine.

## Pre-launch checklist
1. Wire /auth/login backend to login form.
2. Counsel skim: privacy.html, terms.html.
3. Map clean routes for the five divisions + /login + /privacy + /terms.
4. Validate share card at opengraph.xyz after deploy.
