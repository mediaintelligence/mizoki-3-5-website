// Centralized content. All five flagship divisions + eight extended divisions, etc.

export const FLYWHEEL_STEPS = [
  { n: 1, name: 'Signal Enters',       desc: 'New data or event is captured across any domain.',          color: 'counsel' },
  { n: 2, name: 'Graph Updates',       desc: 'Knowledge Graph and relationships update in real time.',     color: 'estate' },
  { n: 3, name: 'Cross-Domain Impact', desc: 'Insights propagate across all divisions.',                   color: 'signal' },
  { n: 4, name: 'Better Decisions',    desc: 'Smarter simulations, proposals, and strategies.',            color: 'capital' },
  { n: 5, name: 'Lasting Memory',      desc: 'Outcomes are learned and strengthen the whole system.',      color: 'risk' },
];

export const FLYWHEEL_RESULTS = [
  'Deeper context', 'Lower risk', 'Stronger strategies', 'Faster execution', 'Continuous improvement',
];

export const FLYWHEEL_STATS = [
  { lbl: 'Active Signals',    val: '18,742', delta: '↑ 24% vs yesterday', tone: 'up' },
  { lbl: 'Simulations Run',   val: '3,982',  delta: '↑ 31% vs yesterday', tone: 'up' },
  { lbl: 'Actions Executed',  val: '642',    delta: '↑ 18% vs yesterday', tone: 'up' },
  { lbl: 'Risk Alerts',       val: '27',     delta: '↓ 12% vs yesterday', tone: 'down' },
  { lbl: 'System Confidence', val: '94.7%',  delta: 'Enterprise Grade',   tone: 'flat' },
];

export const SRPVDAL = [
  { id: 'S', n: '01', name: 'Sense',    desc: 'Capture signals from all sources across all domains.' },
  { id: 'R', n: '02', name: 'Reason',   desc: 'Interpret signals through temporal-causal models.' },
  { id: 'P', n: '03', name: 'Plan',     desc: 'Generate strategies, options, and action plans.' },
  { id: 'V', n: '04', name: 'Validate', desc: 'Verify facts, test assumptions, and run simulations.' },
  { id: 'D', n: '05', name: 'Decide',   desc: 'Select the best course of action with confidence.' },
  { id: 'A', n: '06', name: 'Act',      desc: 'Execute with precision through the Decision Control Plane.' },
  { id: 'L', n: '07', name: 'Learn',    desc: 'Record outcomes and continuously improve.' },
];

export const DCP_LAYERS = [
  { key: 'propose',   color: 'counsel', title: 'Propose',   desc: 'Agents generate options and recommendations.' },
  { key: 'verify',    color: 'nexus',   title: 'Verify',    desc: 'Independent verification by Risk, Policy, and Compliance agents.' },
  { key: 'authorize', color: 'signal',  title: 'Authorize', desc: 'Human or policy-based authorization at the right threshold.' },
  { key: 'execute',   color: 'estate',  title: 'Execute',   desc: 'Action is executed, monitored, and logged.' },
];

export const DIVISIONS = [
  {
    key: 'counsel', color: 'counsel', img: '/assets/07-legal-cell.png',
    name: 'MIZOKI3 COUNSEL', title: 'Legal Intelligence',
    feats: [
      'Contract & agreement analysis',
      'Litigation intelligence & strategy',
      'Negotiation leverage modeling',
      'Regulatory & compliance mapping',
      'Fiduciary duty monitoring',
    ],
    deepHeading: 'Contracts, obligations, evidence — reasoned and governed.',
    deepBody: 'Unifies legal knowledge, contracts, obligations, rules, and evidence relationships into a governed intelligence layer that reasons, validates, and supports better decisions — autonomously.',
  },
  {
    key: 'estate', color: 'estate', img: '/assets/08-estate-cell.png',
    name: 'MIZOKI3 ESTATE', title: 'Wealth, Trust & Tax Intelligence',
    feats: [
      'Trust & estate structure mapping',
      'Tax exposure & scenario modeling',
      'Beneficiary & succession planning',
      'Fiduciary behavior intelligence',
      'Multi-generational simulations',
    ],
    deepHeading: 'Intelligence for what matters most.',
    deepBody: 'Unifies family, stakeholders, trusts, entities, holdings, and ownership lines into one model of trust, governance, and succession — surfacing concentration risk and control gaps in real time.',
  },
  {
    key: 'capital', color: 'capital', img: null,
    name: 'MIZOKI3 CAPITAL', title: 'Financial & Banking Intelligence',
    feats: [
      'Banking & lending relationship maps',
      'Covenant & obligation monitoring',
      'Liquidity & cash flow forecasting',
      'Capital allocation optimization',
      'Refinancing & restructuring intel',
    ],
    deepHeading: 'Causal foresight over capital structures.',
    deepBody: 'Maps treasury telemetry directly against the covenants Counsel ingests — forecasting liquidity stress before a mathematical breach occurs. Capital proposes; it never authorizes alone.',
  },
  {
    key: 'signal', color: 'signal', img: '/assets/10-media-cell.png',
    name: 'MIZOKI3 SIGNAL', title: 'Acquisition & Customer Intelligence',
    feats: [
      'Causal attribution (not correlation)',
      'Customer intent & journey mapping',
      'Churn & LTV forecasting',
      'ROAS optimization with simulation',
      'Autonomous budget reallocation',
    ],
    deepHeading: 'Autonomous omni-source customer acquisition.',
    deepBody: 'Acquisition decisions powered by unified signals, causal reasoning, and real-time intent. Search, social, video, display, email — fused into one decision surface that learns and compounds.',
  },
  {
    key: 'risk', color: 'risk', img: '/assets/09-risk-cell.png',
    name: 'MIZOKI3 RISK', title: 'Verification & Compliance Intelligence',
    feats: [
      'Cross-agent verification & arbitration',
      'Policy & regulatory compliance',
      'Risk scoring & early warnings',
      'Counterfactual & stress testing',
      'Audit functions & audit trails',
    ],
    deepHeading: 'Risk is not beside the system. Risk governs it.',
    deepBody: 'Every consequential output passes through cross-agent verification, hallucination arbitration, and policy gating before authorization. Risk holds the veto over every other division.',
  },
];

export const EXTENDED_DIVISIONS = [
  { name: 'People & HR',          blurb: 'Talent, retention & org-design intelligence.' },
  { name: 'Procurement',          blurb: 'Vendor, sourcing & spend intelligence.' },
  { name: 'Supply Chain',         blurb: 'Logistics, inventory & disruption intelligence.' },
  { name: 'IT & Security',        blurb: 'Infrastructure, threat & access intelligence.' },
  { name: 'Operations',           blurb: 'Process, throughput & efficiency intelligence.' },
  { name: 'R&D & Product',        blurb: 'Innovation pipeline & roadmap intelligence.' },
  { name: 'ESG & Sustainability', blurb: 'Impact, reporting & compliance intelligence.' },
  { name: 'Investor Relations',   blurb: 'Capital-markets & stakeholder intelligence.' },
];

export const USE_CASES = [
  { name: 'Law Firms & Legal Departments',          desc: 'Litigation strategy, contracts, compliance, and risk.' },
  { name: 'Family Offices & Wealth Managers',       desc: 'Estate, tax, trust, and multi-generational planning.' },
  { name: 'Banks & Financial Institutions',         desc: 'Risk, lending, compliance, and capital optimization.' },
  { name: 'Private Equity & Portfolio Companies',   desc: 'Operational intelligence and value creation.' },
  { name: 'Enterprises & Operating Companies',      desc: 'Strategy, operations, risk, and growth.' },
  { name: 'Government & Regulated Industries',      desc: 'Compliance, audit, and mission assurance.' },
];

export const DEMO_STEPS = [
  { n: '01', name: 'Upload',             desc: 'Connect documents, CRM, emails, and more.' },
  { n: '02', name: 'Nexus Ingests',      desc: 'Signals are mapped to the Knowledge Graph.' },
  { n: '03', name: 'Analyze & Simulate', desc: 'Agents run causal models and counterfactuals.' },
  { n: '04', name: 'Review & Authorize', desc: 'Proposals verified and ready for approval.' },
  { n: '05', name: 'Execute',            desc: 'Actions taken with DCP authorization and monitoring.' },
  { n: '06', name: 'Learn',              desc: 'Outcomes recorded. The system improves continuously.' },
];

export const REPLAY_TIMELINE = [
  { t: 'T-05s', event: 'Signal Ingested',        detail: 'Capital cell proposes ACT-991: distribute $5.0M to equity.',                  tone: 'neutral' },
  { t: 'T-04s', event: 'Paths Simulated',        detail: 'CSE runs 4 counterfactuals; cross-domain check engages Counsel + Estate.',     tone: 'plan'    },
  { t: 'T-03s', event: 'V&A — Conflict',         detail: 'Reserves $12.0M − $5.0M = $7.0M  ·  COV-01 minimum liquidity = $10.0M.',       tone: 'warn'    },
  { t: 'T-02s', event: 'Eligibility Failed',     detail: 'DEL score 0.31 — below 0.80 threshold. Projected breach −$3.0M at p=0.97.',   tone: 'bad'     },
  { t: 'T-01s', event: 'DCP — Vetoed',           detail: 'Option A blocked before execution. Authorization withheld.',                   tone: 'bad'     },
  { t: 'T-00s', event: 'Autonomous Execution',   detail: 'Re-routed to Option B (defer). Liquidity held at $12.0M. Covenant preserved.', tone: 'good'    },
];

export const VETO_TRACE = [
  { stg: '$',        body: 'srpvdal.trace --decision ACT-991', cls: 'dim' },
  { stg: 'SENSE',    body: '▸ ingest: treasury telemetry · COV-01 covenant terms' },
  { stg: 'REASON',   body: '▸ Capital cell proposes ACT-991: distribute $5.0M to equity' },
  { stg: 'PLAN',     body: '▸ option A — distribute now  ·  option B — defer one quarter' },
  { stg: 'VALIDATE', body: '▸ Counterfactual Simulation Engine: 4 scenarios modeled' },
  { stg: '',         body: '▸ cross-domain check — Counsel + Estate cells engaged', cls: 'dim' },
  { stg: '',         body: '──────────────────────────────────────────────', cls: 'rule' },
  { stg: 'V&A',      body: '⚠  Verification & Arbitration — CONFLICT DETECTED', cls: 'warn', layer: { va: 'flag' } },
  { stg: '',         body: '▸ reserves $12.0M − distribution $5.0M = $7.0M', cls: 'warn' },
  { stg: '',         body: '▸ COV-01 minimum liquidity = $10.0M' },
  { stg: '',         body: '▸ projected breach −$3.0M · probability 0.97', cls: 'bad', layer: { va: 'veto' } },
  { stg: 'DEL',      body: '✕  Decision Eligibility — score 0.31 · BELOW THRESHOLD (0.80)', cls: 'bad', layer: { del: 'veto' } },
  { stg: '',         body: '──────────────────────────────────────────────', cls: 'rule' },
  { stg: 'DCP',      body: '✕  ACTION VETOED — authorization withheld', cls: 'bad', layer: { dcp: 'veto' }, stamp: true },
  { stg: '',         body: '▸ option A blocked before execution', cls: 'dim' },
  { stg: 'DECIDE',   body: '▸ re-route → option B (defer) · covenant preserved' },
  { stg: 'ACT',      body: '✓  executed: defer distribution · liquidity held at $12.0M', cls: 'good' },
  { stg: 'LEARN',    body: '▸ outcome recorded — covenant-breach pattern reinforced', cls: 'dim' },
  { stg: '$',        body: '', cls: 'cursor' },
];
