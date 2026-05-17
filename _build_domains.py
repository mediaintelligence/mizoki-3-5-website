#!/usr/bin/env python3
"""Generate the 5 MIZOKI3 domain pages from a shared template."""
from pathlib import Path

OUT = Path(__file__).parent

DOMAINS = {
    "counsel": {
        "title": "Counsel",
        "subtitle": "Legal Intelligence",
        "accent_class": "accent-counsel",
        "accent_color": "var(--accent-blue)",
        "label_color": "var(--accent-blue)",
        "glow": "rgba(59, 130, 246, 0.15)",
        "mission": "Convert legal complexity into verified strategic position.",
        "intro": "Counsel turns the unstructured weight of contracts, correspondence, and litigation into a continuously updated map of obligation, leverage, and exposure — feeding every other layer of the system.",
        "consumes": [
            "Contracts", "Amendments", "Litigation filings", "Discovery",
            "Negotiation transcripts", "Regulatory communications",
            "Email correspondence", "Voice transcripts", "Fiduciary documentation",
        ],
        "produces": [
            "Legal exposure mapping", "Contradiction detection",
            "Litigation pathway analysis", "Fiduciary deviation alerts",
            "Negotiation leverage scoring", "Obligation propagation graphs",
            "Procedural risk forecasting",
        ],
        "reinforces": ["Risk", "Estate", "Capital", "Nexus"],
    },
    "estate": {
        "title": "Estate",
        "subtitle": "Wealth, Trust & Tax Intelligence",
        "accent_class": "accent-estate",
        "accent_color": "var(--accent-emerald)",
        "label_color": "var(--accent-emerald)",
        "glow": "rgba(16, 185, 129, 0.15)",
        "mission": "Make multi-generational wealth structures legible, simulatable, and defensible.",
        "intro": "Estate models the long-tail dynamics of trusts, ownership, and beneficiary intent — turning instruments designed to outlive their drafters into a living, queryable substrate.",
        "consumes": [
            "Trusts", "Amendments", "Tax positions", "Estate documents",
            "Ownership hierarchies", "Banking relationships",
            "Fiduciary communications", "Beneficiary records",
        ],
        "produces": [
            "Trust restructuring intelligence", "Tax exposure forecasting",
            "Succession pathway simulations", "Beneficiary conflict mapping",
            "Trustee behavior intelligence", "Liquidity forecasting",
            "Estate optimization scenarios",
        ],
        "reinforces": ["Counsel", "Capital", "Risk"],
    },
    "capital": {
        "title": "Capital",
        "subtitle": "Banking & Financial Intelligence",
        "accent_class": "accent-capital",
        "accent_color": "var(--accent-amber)",
        "label_color": "var(--accent-amber)",
        "glow": "rgba(245, 158, 11, 0.15)",
        "mission": "Give the enterprise causal foresight over capital.",
        "intro": "Capital reads the language of covenants, treasury, and counterparty behavior — converting financial position into forward-looking pathways the business can actually steer.",
        "consumes": [
            "Banking relationships", "Loan agreements", "Covenant structures",
            "Treasury telemetry", "Capital stack composition",
            "Cash flow intelligence", "Financing structures",
        ],
        "produces": [
            "Covenant breach forecasting", "Liquidity stress modeling",
            "Refinancing intelligence", "Capital allocation optimization",
            "Banking relationship scoring", "Restructuring pathways",
            "Negotiation leverage models",
        ],
        "reinforces": ["Estate", "Counsel", "Signal", "Risk"],
    },
    "signal": {
        "title": "Signal",
        "subtitle": "Autonomous Acquisition Intelligence",
        "accent_class": "accent-signal",
        "accent_color": "var(--accent-purple)",
        "label_color": "var(--accent-purple)",
        "glow": "rgba(168, 85, 247, 0.15)",
        "mission": "Replace correlation-based marketing with causal autonomous acquisition.",
        "intro": "Signal rebuilds growth on causal ground: it learns what actually moves customers, then steers spend, channel, and creative through the same governed reasoning loop the rest of the enterprise uses.",
        "consumes": [
            "Meta advertising data", "Google advertising data", "CRM systems",
            "Customer journey telemetry", "Web analytics", "Engagement signals",
            "Conversion events", "Retention data",
        ],
        "produces": [
            "Causal attribution modeling", "Churn forecasting",
            "Lifetime-value prediction", "Autonomous bid optimization",
            "Activation threshold analysis", "Budget reallocation intelligence",
            "Customer intent mapping",
        ],
        "reinforces": ["Capital", "Risk", "Counsel", "Nexus"],
    },
    "risk": {
        "title": "Risk",
        "subtitle": "Verification & Compliance Intelligence",
        "accent_class": "accent-risk",
        "accent_color": "var(--accent-rose)",
        "label_color": "var(--accent-rose)",
        "glow": "rgba(244, 63, 94, 0.15)",
        "mission": "Serve as the conscience, verifier, and governance layer of the entire system.",
        "intro": "Risk is not beside the system. Risk governs the system. Every consequential output produced anywhere in MIZOKI3 passes through Risk before it can be authorized to act.",
        "consumes": [
            "Cross-agent proposals", "Policy libraries", "Regulatory frameworks",
            "Operational telemetry", "Authorization histories",
            "Confidence distributions", "Simulation outputs", "Adversarial signals",
        ],
        "produces": [
            "Cross-agent verification", "Hallucination detection",
            "Contradiction arbitration", "Policy enforcement",
            "Regulatory compliance scoring", "Authorization scoring",
            "Tail-risk simulation", "Confidence arbitration",
            "Operational governance",
        ],
        "reinforces": ["Every layer. Authorizes every consequential action."],
    },
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MIZOKI3 — {title} · {subtitle}</title>
  <meta name="description" content="{mission}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="assets/css/styles.css" />
</head>
<body>

  <header class="site-header">
    <nav class="nav">
      <a href="index.html" class="brand">MIZOKI3</a>
      <ul class="nav-links">
        <li><a href="counsel.html"{ac_counsel}>Counsel</a></li>
        <li><a href="estate.html"{ac_estate}>Estate</a></li>
        <li><a href="capital.html"{ac_capital}>Capital</a></li>
        <li><a href="signal.html"{ac_signal}>Signal</a></li>
        <li><a href="risk.html"{ac_risk}>Risk</a></li>
      </ul>
    </nav>
  </header>

  <div class="domain-accent {accent_class}"></div>

  <section class="domain-hero" style="--domain-glow: {glow};">
    <div class="container">
      <div class="label" style="color: {label_color};">// MIZOKI3 {title_upper} · {subtitle}</div>
      <h1>{mission}</h1>
      <p class="mission">{intro}</p>
      <div class="hero-cta" style="margin-top: 36px;">
        <a href="index.html#layers" class="btn btn-ghost">← All domains</a>
        <a href="index.html#brain" class="btn btn-ghost">Inside the Brain</a>
      </div>
    </div>
  </section>

  <div class="container">
    <div class="domain-anatomy">
      <div class="anatomy-block">
        <div class="eyebrow" style="color: {label_color};">Consumes</div>
        <h3 style="margin-bottom: 24px;">The signals that enter {title}.</h3>
        <ul class="clean">
{consumes_html}
        </ul>
      </div>
      <div class="anatomy-block">
        <div class="eyebrow" style="color: {label_color};">Produces</div>
        <h3 style="margin-bottom: 24px;">The intelligence {title} contributes to the graph.</h3>
        <ul class="clean">
{produces_html}
        </ul>
      </div>
    </div>
  </div>

  <div class="reinforces-block">
    <div class="container">
      <div class="label">// Reinforces</div>
      <div class="layers">{reinforces_html}</div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <div class="footer-brand">MIZOKI3</div>
          <div class="footer-tag">// One intelligence. Many domains. Shared causal memory.</div>
        </div>
        <div class="footer-col">
          <h5>Domains</h5>
          <ul>
            <li><a href="counsel.html">Counsel</a></li>
            <li><a href="estate.html">Estate</a></li>
            <li><a href="capital.html">Capital</a></li>
            <li><a href="signal.html">Signal</a></li>
            <li><a href="risk.html">Risk</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h5>Architecture</h5>
          <ul>
            <li><a href="index.html#brain">Nexus</a></li>
            <li><a href="index.html#brain">SRPVDAL</a></li>
            <li><a href="index.html#brain">Decision Control Plane</a></li>
            <li><a href="index.html#flywheel">Flywheel</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© MIZOKI3 · MediaIntelligence.ai</span>
        <span>// Autonomous Decision Infrastructure</span>
      </div>
    </div>
  </footer>

</body>
</html>
"""

def render(slug, d):
    consumes_html = "\n".join(f"          <li>{x}</li>" for x in d["consumes"])
    produces_html = "\n".join(f"          <li>{x}</li>" for x in d["produces"])
    if len(d["reinforces"]) == 1:
        reinforces_html = d["reinforces"][0]
    else:
        reinforces_html = " · ".join(f"<span>{r}</span>" for r in d["reinforces"])
    active = {k: ' class="active"' if k == slug else '' for k in DOMAINS}
    return TEMPLATE.format(
        title=d["title"],
        title_upper=d["title"].upper(),
        subtitle=d["subtitle"],
        mission=d["mission"],
        intro=d["intro"],
        accent_class=d["accent_class"],
        accent_color=d["accent_color"],
        label_color=d["label_color"],
        glow=d["glow"],
        consumes_html=consumes_html,
        produces_html=produces_html,
        reinforces_html=reinforces_html,
        ac_counsel=active["counsel"],
        ac_estate=active["estate"],
        ac_capital=active["capital"],
        ac_signal=active["signal"],
        ac_risk=active["risk"],
    )

for slug, d in DOMAINS.items():
    path = OUT / f"{slug}.html"
    path.write_text(render(slug, d))
    print(f"wrote {path.name}")
