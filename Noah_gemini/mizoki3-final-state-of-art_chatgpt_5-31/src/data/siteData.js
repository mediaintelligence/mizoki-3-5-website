import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  Building2,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Eye,
  FileCheck,
  GitBranch,
  GitMerge,
  Gauge,
  History,
  Layers,
  Network,
  RotateCw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Workflow,
  Zap,
} from "lucide-react";

export const srpvdalNodes = [
  {
    id: "S",
    key: "sense",
    name: "Sense",
    phase: "OBSERVE",
    icon: Eye,
    desc: "Ingests live event streams, telemetry, logs, market feeds, documents, asset states, and enterprise system changes without rip-and-replace.",
    short: "Signals stream from CRM, finance, market, legal, media, documents, and operations.",
  },
  {
    id: "R",
    key: "reason",
    name: "Reason",
    phase: "INFER",
    icon: BrainCircuit,
    desc: "Models relationships, dependencies, and causal pathways through the Temporal-Causal Knowledge Graph rather than relying on shallow correlation.",
    short: "Specialized agents analyze context, causality, risk, timing, and intent.",
  },
  {
    id: "P",
    key: "plan",
    name: "Plan",
    phase: "PROPOSE",
    icon: GitMerge,
    desc: "Generates constraint-aware action blueprints, fallback paths, task dependencies, resource needs, and asset-owner routing using REWOO planning logic.",
    short: "The platform generates executable options, alternatives, and projected outcomes.",
  },
  {
    id: "V",
    key: "validate",
    name: "Validate / Verify",
    phase: "STRESS-TEST",
    icon: ShieldCheck,
    desc: "Acts as the Devil’s Advocate: validating plans against compliance boundaries, regulatory guardrails, corporate policy, feasibility, identity, and context sufficiency.",
    short: "Verification, policy, compliance, and evidence checks pressure-test every path.",
  },
  {
    id: "D",
    key: "decide",
    name: "Decide",
    phase: "CHOOSE",
    icon: Layers,
    desc: "Scores risk, ROI, confidence, authority, context sufficiency, and historical performance before authorizing execution or escalating to a human stakeholder.",
    short: "A governed authorization score determines what can move forward.",
  },
  {
    id: "A",
    key: "act",
    name: "Act",
    phase: "EXECUTE",
    icon: Zap,
    desc: "Executes secure, governed runtime protocols across external APIs, workflows, cloud services, and enterprise infrastructure layers.",
    short: "Approved actions execute through connected systems with guardrails.",
  },
  {
    id: "L",
    key: "learn",
    name: "Learn",
    phase: "COMPOUND",
    icon: Activity,
    desc: "Compares outcomes against the original hypothesis, then updates graph memory, causal weights, confidence thresholds, and operating policies.",
    short: "Outcomes feed back into the temporal-causal knowledge graph.",
  },
];

export const divisions = [
  { id: "core", title: "MIZOKI3 Core", body: "Autonomous decision intelligence infrastructure." },
  { id: "media", title: "MIZOKI3 Media", body: "Causal acquisition, attribution, and omnichannel growth." },
  { id: "counsel", title: "MIZOKI3 Counsel", body: "Legal reasoning, evidence memory, and litigation intelligence." },
  { id: "estate", title: "MIZOKI3 Estate", body: "Trust, tax, estate, and asset intelligence." },
  { id: "capital", title: "MIZOKI3 Capital", body: "Risk, lending, markets, and financial decision systems." },
  { id: "nexus", title: "MIZOKI3 Nexus", body: "Cross-agent orchestration and enterprise nervous system." },
];

export const lenses = {
  legal: {
    label: "Legal",
    title: "Legal Intelligence Cell",
    tagline: "Contract, compliance, obligation, and evidence-chain governance.",
    desc: "Unifies contracts, policies, regulatory context, entity relationships, and evidence chains into one governed reasoning surface.",
    features: ["Obligation mapping", "Compliance matching", "Evidence validation", "Active legal risk routing"],
    icon: Scale,
  },
  estate: {
    label: "Estate",
    title: "Estate & Governance Cell",
    tagline: "Entity architecture, control mapping, liquidity exposure, and fiduciary guardrails.",
    desc: "Models trusts, holdings, corporate entities, stakeholders, asset lines, and control paths to uncover structural gaps and governance risk.",
    features: ["Control-gap detection", "Trust/entity mapping", "Liquidity liability monitoring", "Stakeholder-line analysis"],
    icon: Building2,
  },
  risk: {
    label: "Risk",
    title: "Risk & Resilience Cell",
    tagline: "Continuous threat modeling and operational resilience simulation.",
    desc: "Turns risk from a retrospective audit into a live operational state by simulating supply-chain exposure, infrastructure dependencies, and threat scenarios.",
    features: ["Scenario simulation", "Dependency stress tests", "Threat path modeling", "Fallback activation"],
    icon: ShieldAlert,
  },
  media: {
    label: "Media",
    title: "Media Acquisition Cell",
    tagline: "Audience telemetry, ad-spend arbitrage, and asset alignment.",
    desc: "Converts high-velocity audience signals, creative telemetry, margin constraints, and spend patterns into governed acquisition actions.",
    features: ["Causal attribution", "Pre-bid intelligence", "Budget threshold routing", "Real-time ROAS protection"],
    icon: BarChart3,
  },
};

export const simulationScenarios = {
  capital: {
    title: "Capital Arbitrage Routing",
    subtitle: "MIZOKI3 Capital Decision Loop",
    signals: ["Order flow imbalance detected", "Fed liquidity shift detected", "Yield curve variance across 3 pools"],
    agents: ["Liquidity Agent", "Yield Arb Optimizer", "Risk Bound Sentry", "Compliance Validator"],
    paths: [
      { id: "A", desc: "Route 65% liquidity through Pool Alpha. Arb margin: +0.42%.", risk: "Low", confidence: 97 },
      { id: "B", desc: "Route 100% liquidity through Pool Gamma. Arb margin: +0.68%.", risk: "High", confidence: 71 },
      { id: "C", desc: "De-escalate positions to USD cash reserve.", risk: "Minimal", confidence: 99 },
    ],
    logs: [
      "Sensing: CRM orders, exchange APIs, and treasury thresholds unified.",
      "Reasoning: Structural arbitrage window mapped to pool exhaustion conditions.",
      "Planning: Three routing configurations prepared with counterfactual yield results.",
      "Validating: Asset compliance and policy 4B maximum exposure constraints verified.",
      "Deciding: Strategy A cleared with 97% confidence scoring.",
      "Acting: Orders staged to API gateways. Circuit breakers active.",
      "Learning: Slippage of -0.01% recorded. Future routing matrices updated.",
    ],
  },
  media: {
    title: "Dynamic Omnichannel Media Spend Redirection",
    subtitle: "MIZOKI3 Media Decision Loop",
    signals: ["Sports event viral spike", "Competitor ad inventory exhaustion", "Cost-per-mille fluctuation"],
    agents: ["Attribution Agent", "Bid Optimizer", "Brand Safety Guard", "Trend Correlator"],
    paths: [
      { id: "A", desc: "Pivot 40% budget to real-time CTV inventory.", risk: "Medium", confidence: 89 },
      { id: "B", desc: "Maintain programmatic standard baseline.", risk: "Low", confidence: 94 },
      { id: "C", desc: "Hyper-scale social channels instantly.", risk: "High", confidence: 64 },
    ],
    logs: [
      "Sensing: Real-time ad telemetry, traffic signals, and media APIs ingested.",
      "Reasoning: Viral inflection vector mapped to competitor dropout.",
      "Planning: Dynamic bid structures built for CTV and social inventory.",
      "Validating: Brand safety and budget safety protocols checked.",
      "Deciding: Strategy A authorized with bid modifiers set to 1.4x.",
      "Acting: API push to programmatic DSP executed.",
      "Learning: Conversion lift of +18.4% logged. Attribution weightings adjusted.",
    ],
  },
  counsel: {
    title: "Contract Liability Exposure Defense",
    subtitle: "MIZOKI3 Counsel Decision Loop",
    signals: ["Supplier force majeure notification", "Precedent litigation records", "SLA violation matrix"],
    agents: ["Contract Parser", "Jurisdictional Expert", "Exposure Predictor", "Precedent Analyst"],
    paths: [
      { id: "A", desc: "Execute safe-harbor clause 9.2. Mitigates 80% damages.", risk: "Minimal", confidence: 98 },
      { id: "B", desc: "Initiate renegotiation timeline option.", risk: "Low", confidence: 85 },
      { id: "C", desc: "Proceed directly to arbitration.", risk: "High", confidence: 52 },
    ],
    logs: [
      "Sensing: Contracts, compliance guidelines, and jurisdictional filings indexed.",
      "Reasoning: Liability curves mapped to force majeure trigger causality.",
      "Planning: Legal response options modeled against historic precedent clusters.",
      "Validating: Regulatory reporting dates and notice period limits checked.",
      "Deciding: Strategy A authorized for corporate counsel sign-off.",
      "Acting: Formal legal notice drafted and staged for secure delivery.",
      "Learning: Supplier response logged. Causal memory updated for similar clauses.",
    ],
  },
};

export const kpis = [
  [Clock, "Decision Latency", "Time from signal detection to authorized action."],
  [Gauge, "Decision Confidence", "Mathematical confidence relative to active thresholds."],
  [ShieldAlert, "Override Frequency", "How often human review is triggered and why."],
  [BarChart3, "Outcome Delta", "Performance variance against manual or legacy baselines."],
  [RotateCw, "Learning Velocity", "How quickly outcome feedback improves confidence calibration."],
  [FileCheck, "Audit Completeness", "Percent of actions with complete reasoning trace and attribution."],
];

export const replaySteps = [
  ["T-04s", "Signal Ingested", "Contract obligation, CRM activity, media telemetry, and financial variance detected across connected systems."],
  ["T-03s", "Causal Paths Simulated", "Three alternatives evaluated against the Temporal-Causal Knowledge Graph and historical outcome patterns."],
  ["T-02s", "Validation Challenge", "One path rejected after policy, feasibility, and context sufficiency checks failed."],
  ["T-01s", "Authorization Scored", "Decision Control Plane calculates confidence, risk, ROI, authority, and audit completeness."],
  ["T-00s", "Action Executed", "Approved pathway executes with immutable trace, stakeholder notice, and learning feedback loop."],
];

export const capabilityCards = [
  { icon: Activity, title: "From signals to strategy", body: "Unifies live transactional pipelines, documentation structures, risk registers, and active workflows in one memory canvas." },
  { icon: Network, title: "Causality over correlation", body: "Computes systemic dependencies to prove why an outcome occurs, ensuring decisions hold logical merit." },
  { icon: ShieldCheck, title: "Governed execution", body: "Separates strategic option planning from actual corporate execution through customized, audit-proof parameters." },
  { icon: GitBranch, title: "Self-learning memory", body: "Every execution path outcome loops recursively to reinforce rules and metrics in the corporate knowledge graph." },
];

export const agents = [
  "Reasoning Agents",
  "Forecasting Agents",
  "Verification Agents",
  "Execution Agents",
  "Policy Agents",
  "Arbitration Agents",
];

export const governanceCards = [
  [Scale, "Context Sufficiency & Attestation", "Validates data lineage, user permissions, role boundaries, identity, and required context before an execution payload is eligible."],
  [FileCheck, "Explainable Reasoning Paths", "Records why a path was chosen, which alternatives were rejected, and how confidence, risk, ROI, and policy variables were weighted."],
  [History, "Immutable Audit Trail", "Commits states, reasoning logs, validations, overrides, confidence metrics, and final actions to tamper-resistant review records."],
];

export const antiDashboardCards = [
  ["Plug-In Architecture", "Hooks into ERP, CRM, SIEM, data lakes, legal systems, media platforms, and cloud workflows."],
  ["Signal-To-Action Conversion", "Turns events, obligations, alerts, telemetry, and market changes into controlled execution pathways."],
  ["Threshold-Aware Autonomy", "Routes actions through context, identity, policy, risk, confidence, authority, and audit gates before execution."],
];

export const authorityBands = [
  ["Autonomous", "Green Zone", "Routine actions execute automatically when context, policy, confidence, identity, and audit gates pass.", "bg-emerald-400"],
  ["Human Review", "Yellow Zone", "Stakeholder review is triggered when ambiguity, risk, or authority boundary pressure rises.", "bg-amber-300"],
  ["Executive Escalation", "Red Zone", "Board, CISO, counsel, fiduciary, or executive approval is required before action.", "bg-red-400"],
];

export const blogArticle = {
  title: "Beyond Probabilities: Why High-Stakes Operations Require Causal, Threshold-Aware Autonomy",
  author: "MIZOKI3 Systems Engineering Group",
  sections: [
    {
      heading: "The Illusions of Generative Enterprise",
      body: "For the past several years, the corporate world has treated generative, probabilistic systems as decision-making tools. That is structurally dangerous when the environment involves compliance, financial exposure, legal obligations, operational risk, or fiduciary responsibility."
    },
    {
      heading: "The Decisive Question",
      body: "The question is not whether artificial intelligence can execute actions. The question is what conditions must be true before it is allowed to execute. MIZOKI3 turns that question into architecture through the Decision Control Plane and the SRPVDAL cognitive loop."
    },
    {
      heading: "From Chatbots to Deterministic Control",
      body: "Prompt-to-action systems collapse reasoning, validation, authorization, and execution into one fragile motion. MIZOKI3 separates those stages into Sense, Reason, Plan, Validate / Verify, Decide, Act, and Learn."
    },
    {
      heading: "One Brain, Distributed Lenses",
      body: "Legal, estate, risk, media, and capital operations are not separate intelligence problems. They are different lenses over shared system memory. MIZOKI3 uses Domain Cells to specialize behavior while preserving one core knowledge graph."
    },
    {
      heading: "Measured Autonomy",
      body: "Governed autonomy must be visible. Decision latency, decision confidence, override frequency, outcome delta, learning velocity, and audit completeness become the operating metrics for enterprise cognition."
    }
  ]
};
