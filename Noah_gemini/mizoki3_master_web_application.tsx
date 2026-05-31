import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowRight, BrainCircuit, ShieldCheck, Network, Activity, 
  GitBranch, Cpu, Eye, Lock, Play, Zap, Layers, Orbit, 
  CheckCircle2, Terminal, ShieldAlert, Scale, Building2, 
  Landmark, Target, AlertTriangle, BarChart3, Clock, 
  Gauge, RotateCw, FileCheck, GlobeLock, Workflow, 
  Sparkles, Database, ChevronRight, GitMerge
} from "lucide-react";

// --- Custom Mock UI Components for Flawless Single-File Compilation ---
const Button = ({ className = "", variant = "default", size = "default", children, ...props }) => {
  const base = "inline-flex items-center justify-center rounded-sm font-mono tracking-widest uppercase text-xs font-bold transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white disabled:pointer-events-none disabled:opacity-50";
  const variants = {
    default: "bg-white text-black hover:bg-zinc-200 shadow-[0_0_20px_rgba(255,255,255,0.1)]",
    outline: "border border-zinc-700 bg-transparent text-white hover:bg-zinc-800 hover:border-zinc-500",
    ghost: "hover:bg-white/10 hover:text-white text-zinc-400",
  };
  const sizes = {
    default: "h-11 px-6 py-2.5",
    sm: "h-8 px-4 text-[10px]",
    lg: "h-14 px-8 text-sm",
    icon: "h-10 w-10",
  };
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
};

const Card = ({ className = "", children }) => (
  <div className={`rounded-xl border border-zinc-800 bg-gradient-to-b from-[#0a0a0c] to-[#030305] text-white shadow-2xl transition-all duration-300 hover:border-zinc-700 ${className}`}>
    {children}
  </div>
);

const CardContent = ({ className = "", children }) => (
  <div className={`p-8 ${className}`}>
    {children}
  </div>
);

// --- Deep-Dive Dataset Setup ---
const srpvdalNodes = [
  {
    id: "S",
    name: "Sense",
    phase: "OBSERVE",
    icon: Eye,
    metrics: { confidence: "98.9%", latency: "14ms", alignment: "100%", wConf: "99%", wLat: "25%", wAl: "100%" },
    desc: "Ingests live event streams, telemetry, logs, market feeds, documents, asset states, and enterprise system changes without requiring rip-and-replace of your core infrastructure.",
  },
  {
    id: "R",
    name: "Reason",
    phase: "INFER",
    icon: BrainCircuit,
    metrics: { confidence: "95.4%", latency: "42ms", alignment: "100%", wConf: "95%", wLat: "45%", wAl: "100%" },
    desc: "Models relationships, dependencies, and causal pathways through the Temporal-Causal Knowledge Graph (TCKG) rather than relying on shallow vector or semantic correlation.",
  },
  {
    id: "P",
    name: "Plan",
    phase: "PROPOSE",
    icon: GitMerge,
    metrics: { confidence: "92.1%", latency: "115ms", alignment: "98%", wConf: "92%", wLat: "75%", wAl: "98%" },
    desc: "Generates constraint-aware action blueprints, dynamic fallback paths, task dependencies, resource needs, and asset-owner routing templates based on strict REWOO orchestration.",
  },
  {
    id: "V",
    name: "Validate",
    phase: "STRESS-TEST",
    icon: ShieldCheck,
    metrics: { confidence: "99.8%", latency: "84ms", alignment: "100%", wConf: "100%", wLat: "60%", wAl: "100%" },
    desc: "Acts as the physical governor: validation of proposed plans against active compliance boundaries, regulatory guardrails, corporate policies, feasibility, and identity bounds.",
  },
  {
    id: "D",
    name: "Decide",
    phase: "CHOOSE",
    icon: Layers,
    metrics: { confidence: "94.2%", latency: "220ms", alignment: "100%", wConf: "94%", wLat: "90%", wAl: "100%" },
    desc: "Scores risk, ROI, confidence, authorization limits, context sufficiency, and historical performance metrics before deciding to execute autonomously or route to humans.",
  },
  {
    id: "A",
    name: "Act",
    phase: "EXECUTE",
    icon: Zap,
    metrics: { confidence: "100%", latency: "38ms", alignment: "100%", wConf: "100%", wLat: "30%", wAl: "100%" },
    desc: "Executes secure, encrypted runtime protocols across external APIs, distributed ledger systems, cloud services, and custom enterprise system integration adapters.",
  },
  {
    id: "L",
    name: "Learn",
    phase: "COMPOUND",
    icon: Activity,
    metrics: { confidence: "97.5%", latency: "310ms", alignment: "100%", wConf: "97%", wLat: "95%", wAl: "100%" },
    desc: "Compares realized real-world outcomes against the original system hypothesis, updating graph edge weights, causal thresholds, confidence indices, and future prior probabilities.",
  },
];

const lenses = {
  legal: {
    label: "Counsel",
    title: "Counsel Intelligence",
    tagline: "Legal reasoning, contract risk, and liability mapping.",
    desc: "Unifies contracts, regulatory filings, corporate policies, and compliance documentation into an executable causal memory graph that flags multi-domain legal liabilities.",
    features: ["Obligation propagation maps", "Causal compliance parsing", "Active risk threshold routing", "Evidence-chain validation"],
    icon: Scale,
    color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20"
  },
  estate: {
    label: "Estate",
    title: "Estate & Trust Intelligence",
    tagline: "Generational asset governance, trust compliance, and tax exposure.",
    desc: "Models highly complex trust structures, asset holding arrangements, family office hierarchies, and active taxation baselines to uncover control gaps and preserve wealth.",
    features: ["Control-gap auto-detection", "Trust structure visualization", "Dynamic tax exposure logs", "Succession boundary analysis"],
    icon: Building2,
    color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/20"
  },
  capital: {
    label: "Capital",
    title: "Capital & Treasury Intelligence",
    tagline: "Debt covenant stress-tests, capital structure metrics, and risk.",
    desc: "Bridges legal agreements and active cash/treasury telemetry. Projects covenant performance against market volatility curves and legal contracts continuously.",
    features: ["Breach predictive simulation", "Treasury covenant alignment", "Stress curve cash modeling", "Allocation opportunity index"],
    icon: Landmark,
    color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20"
  },
  signal: {
    label: "Signal",
    title: "Signal Media Intelligence",
    tagline: "Causal media attribution, customer acquisition, and budget gating.",
    desc: "Replaces correlation marketing algorithms with threshold-governed customer growth. Tracks exact conversion flows directly against capital liquidity bounds.",
    features: ["Causal marketing attribution", "Real-time pre-bid filters", "Budget reallocation limits", "Omnichannel growth stress tests"],
    icon: Target,
    color: "text-purple-500", bg: "bg-purple-500/10", border: "border-purple-500/20"
  },
  risk: {
    label: "Risk",
    title: "Risk & Governance",
    tagline: "The ultimate cross-agent arbiter, policy engine, and verifier.",
    desc: "Governs the entire cognitive loop. Operates as an independent challenge layer, vetting actions, preventing hallucinations, and ensuring complete audit traceability.",
    features: ["Cross-agent arbitration", "Hallucination override gates", "Tail-risk stress simulations", "Immutable transaction logging"],
    icon: ShieldAlert,
    color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/20"
  },
};

const kpis = [
  [Clock, "Decision Latency", "Time from raw signal ingestion to authorized autonomous action.", "text-blue-400"],
  [Gauge, "Causal Calibration", "Mathematical certainty indexed relative to enterprise risk appetite.", "text-emerald-400"],
  [ShieldAlert, "Escalation Velocity", "How efficiently ambiguous edge cases are routed to human stakeholders.", "text-amber-400"],
  [BarChart3, "Outcome Variance", "Execution accuracy compared against historical manual decision baselines.", "text-purple-400"],
  [RotateCw, "Memory Compounding", "How rapidly post-execution learning logs updates future graph priors.", "text-rose-400"],
  [FileCheck, "Audit Completeness", "Absolute traceability of every autonomous state transition and veto.", "text-cyan-400"],
];

const replaySteps = [
  ["T-04s", "Multi-System Signal Ingest", "Contract updates, real-time treasury telemetry, and conversion signals processed across 42 endpoints."],
  ["T-03s", "Causal Path Simulation", "Three competitive action pathways generated and simulated against the live Temporal-Causal Knowledge Graph."],
  ["T-02s", "V&A Challenge Veto", "One pathway flagged and vetoed by Risk Cell due to newly updated legal covenant thresholds."],
  ["T-01s", "Authorization Evaluation", "Decision Control Plane assesses context sufficiency, policy alignment, and calculates authority scores."],
  ["T-00s", "Autonomous Execution", "System triggers API action. Immutable trace records generated for CISO audit ledger. Learning feedback loop engaged."],
];

const terminalLog = [
  { text: "[COUNSEL] [SENSE    ] Ingesting Legal Amendment AMEND-842...", delay: 800 },
  { text: "[COUNSEL] [REASON   ] Extracting Causal Constraints from text...", delay: 600 },
  { text: "[NEXUS  ] [MEMORY   ] TCKG Updated with executable Liquidity Covenant.", delay: 900 },
  { text: "", delay: 200 },
  { text: "[CAPITAL] [PLAN     ] Proposing $5M Q3 Dividend Distribution.", delay: 1100 },
  { text: "[NEXUS  ] [SIMULATE ] Initializing Counterfactual Engine...", delay: 600 },
  { text: "[RISK   ] [VERIFY   ] Cross-referencing simulated state against TCKG.", delay: 1200 },
  { text: "", delay: 200 },
  { text: "[RISK   ] [ARBITRATE] VETO. Causal Inconsistency Detected.", color: "text-rose-500 font-bold", delay: 800 },
  { text: "                      -> Simulated Liquidity violates AMEND-842 threshold.", color: "text-rose-500", delay: 400 },
  { text: "", delay: 200 },
  { text: "[DCP    ] [DECIDE   ] Decision Control Plane: AUTONOMOUS ACTION REJECTED.", color: "text-white font-bold", delay: 800 },
  { text: "[NEXUS  ] [LEARN    ] Arbitration logic recorded. Flywheel updated.", delay: 1000 },
];

// --- Sub-components ---
function KnowledgeGraphBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-25">
      <div className="absolute left-1/4 top-1/4 h-[32rem] w-[32rem] rounded-full bg-cyan-900/10 blur-[140px]" />
      <div className="absolute right-1/4 top-1/2 h-[36rem] w-[36rem] rounded-full bg-indigo-950/10 blur-[160px]" />
      <div className="absolute bottom-1/4 left-1/3 h-[28rem] w-[28rem] rounded-full bg-amber-950/10 blur-[130px]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,.01)_1px,transparent_1px)] bg-[size:4rem_4rem]" />
    </div>
  );
}

function GlowNode({ className = "", delay = 0, colorClass = "bg-cyan-300 shadow-[0_0_24px_rgba(34,211,238,.95)]" }) {
  return (
    <motion.div
      className={`absolute h-2 w-2 rounded-full ${colorClass} ${className}`}
      animate={{ scale: [1, 1.8, 1], opacity: [0.35, 1, 0.35] }}
      transition={{ duration: 2.8, repeat: Infinity, delay }}
    />
  );
}

function LivingEnterpriseVisual() {
  const systems = [
    ["ERP Feed", "left-[8%] top-[25%]", "bg-cyan-300"],
    ["CRM Sync", "left-[14%] top-[70%]", "bg-amber-300"],
    ["SIEM Logs", "right-[10%] top-[22%]", "bg-cyan-300"],
    ["Legal Doc", "right-[16%] top-[72%]", "bg-amber-300"],
    ["Data Lake", "left-[43%] bottom-[5%]", "bg-cyan-300"],
    ["Media Hub", "left-[45%] top-[5%]", "bg-amber-300"],
  ];

  return (
    <div className="relative min-h-[560px] w-full overflow-hidden rounded-[2rem] border border-zinc-800 bg-[#020205] shadow-2xl">
      <KnowledgeGraphBackground />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_48%,rgba(34,211,238,.12),transparent_35%),linear-gradient(135deg,#020204_0%,#050b15_55%,#000_100%)]" />
      
      {/* Dynamic Animated Paths */}
      <svg className="absolute inset-0 h-full w-full opacity-60" viewBox="0 0 1000 560" preserveAspectRatio="none">
        {[
          "M100 145 C260 205, 370 250, 500 280",
          "M200 420 C340 360, 405 310, 500 280",
          "M880 125 C690 180, 610 235, 500 280",
          "M805 430 C690 365, 610 315, 500 280",
          "M500 520 C500 410, 500 350, 500 280",
          "M500 55 C500 140, 500 215, 500 280",
        ].map((d, i) => (
          <motion.path
            key={d}
            d={d}
            fill="none"
            stroke={i % 2 ? "rgba(245,158,11,.6)" : "rgba(34,211,238,.7)"}
            strokeWidth="1.5"
            strokeDasharray="6 10"
            animate={{ strokeDashoffset: [0, -100] }}
            transition={{ duration: 4 + i, repeat: Infinity, ease: "linear" }}
          />
        ))}
      </svg>

      {/* Orbit Rings */}
      <motion.div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-500/10" animate={{ rotate: 360 }} transition={{ duration: 32, repeat: Infinity, ease: "linear" }} />
      <motion.div className="absolute left-1/2 top-1/2 h-[26rem] w-[26rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-amber-500/5" animate={{ rotate: -360 }} transition={{ duration: 48, repeat: Infinity, ease: "linear" }} />

      {/* Center Brain */}
      <div className="absolute left-1/2 top-1/2 grid h-40 w-40 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-cyan-500/40 bg-black/80 text-center shadow-[0_0_80px_rgba(34,211,238,0.2)] backdrop-blur-md z-10">
        <div>
          <BrainCircuit className="mx-auto mb-1.5 h-9 w-9 text-cyan-200" />
          <div className="text-[9px] font-bold uppercase tracking-[0.25em] text-zinc-500">Shared brain</div>
          <div className="text-xs font-bold uppercase tracking-[0.15em] text-white">TCKG Core</div>
        </div>
      </div>

      {/* Edge Glow Nodes */}
      <GlowNode className="left-[12%] top-[25%]" delay={0} />
      <GlowNode className="left-[19%] top-[69%]" delay={0.4} />
      <GlowNode className="right-[13%] top-[21%]" delay={0.8} />
      <GlowNode className="right-[19%] top-[71%]" delay={1.2} />

      {/* Render Node Anchors */}
      {systems.map(([label, pos, color]) => (
        <div key={label} className={`absolute ${pos} rounded-lg border border-zinc-800 bg-zinc-950/80 px-4 py-2.5 backdrop-blur-md`}>
          <div className="text-[9px] font-mono tracking-wider text-zinc-600">STATE :: CONNECTED</div>
          <div className="text-[11px] font-bold text-zinc-100">{label}</div>
          <div className={`mt-1.5 h-1 rounded-full ${color}`} />
        </div>
      ))}

      {/* Bottom Labels */}
      <div className="absolute bottom-4 left-4 right-4 grid gap-2 grid-cols-2 md:grid-cols-4">
        {["Causally Grounded", "Zero Agent Drift", "Continuous Learning", "Sovereign Audit Log"].map((label) => (
          <div key={label} className="rounded-md border border-zinc-900 bg-black/60 px-3 py-2 text-center text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-400 backdrop-blur-sm">
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

function DcpAuthorizationPanel() {
  const rows = [
    ["Context Sufficiency Check", "PASS", "text-emerald-400"],
    ["Policy Vector Alignment", "PASSED", "text-emerald-400"],
    ["Financial Threshold Check", "VERIFIED", "text-cyan-400"],
    ["Arbitration Conflict State", "CLEAR", "text-cyan-400"],
    ["Identity Entitlement Key", "ACTIVE", "text-emerald-400"],
    ["Authorization Status", "EXECUTE_AUTONOMOUS", "text-white font-mono font-bold bg-white/5 px-2 rounded-sm"],
  ];

  return (
    <div className="rounded-xl border border-zinc-800 bg-[#050508] p-6 shadow-[0_0_60px_rgba(6,182,212,.03)] backdrop-blur-md">
      <div className="mb-6 flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <div className="text-[9px] font-mono tracking-[0.25em] text-cyan-400 uppercase">Layer 01 :: DECISION CONTROL PLANE</div>
          <h3 className="mt-1 text-lg font-bold text-white tracking-tight">Eligibility Verification</h3>
        </div>
        <Lock className="h-5 w-5 text-amber-400 animate-pulse" />
      </div>
      <div className="space-y-2 font-mono text-xs">
        {rows.map(([label, value, color]) => (
          <div key={label} className="flex items-center justify-between rounded border border-white/5 bg-white/[0.01] px-4 py-2.5">
            <span className="text-zinc-500 text-[10px] uppercase tracking-wider">{label}</span>
            <span className={`${color} text-[11px]`}>{value}</span>
          </div>
        ))}
      </div>
      <div className="mt-5 rounded-lg border border-amber-500/10 bg-amber-500/5 p-4">
        <div className="mb-2 flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-widest text-amber-400">
          <span>Required Confidence Floor</span>
          <span>94.2%</span>
        </div>
        <div className="h-1 overflow-hidden rounded-full bg-zinc-900">
          <motion.div className="h-full rounded-full bg-amber-400" initial={{ width: "0%" }} animate={{ width: "94.2%" }} transition={{ duration: 1.5 }} />
        </div>
      </div>
    </div>
  );
}

function TerminalSimulator() {
  const [lines, setLines] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < terminalLog.length) {
      const timer = setTimeout(() => {
        setLines(prev => [...prev, terminalLog[currentIndex]]);
        setCurrentIndex(prev => prev + 1);
      }, terminalLog[currentIndex].delay);
      return () => clearTimeout(timer);
    } else {
      const resetTimer = setTimeout(() => {
        setLines([]);
        setCurrentIndex(0);
      }, 6000);
      return () => clearTimeout(resetTimer);
    }
  }, [currentIndex]);

  const getTimeStr = () => {
    const now = new Date();
    return `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}.${now.getMilliseconds().toString().padStart(3,'0').substring(0,3)}`;
  };

  return (
    <div className="flex h-[400px] w-full flex-col overflow-hidden rounded-xl border border-zinc-800 bg-[#030305] font-mono text-[11px] shadow-2xl">
      <div className="flex items-center justify-between border-b border-zinc-800 bg-[#0a0a0d] px-4 py-3">
        <div className="flex items-center gap-3 text-zinc-500">
          <Terminal className="h-4 w-4" />
          <span className="uppercase tracking-[0.15em] text-[10px] font-bold">System_Trace :: SRPVDAL_Execution</span>
        </div>
        <div className="flex items-center gap-2 text-emerald-500 text-[10px] font-bold">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" /> System Active
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6 text-zinc-400 scrollbar-hide">
        <AnimatePresence>
          {lines.map((line, idx) => (
            <motion.div 
              key={idx} 
              initial={{ opacity: 0, y: 5 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="mb-1.5"
            >
              {line.text === "" ? <br /> : (
                <div className="flex items-start">
                  <span className="mr-3 text-zinc-600 shrink-0 select-none">[{getTimeStr()}]</span>
                  <span className={line.color || "text-zinc-300"}>{line.text}</span>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        <motion.div animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.8 }} className="inline-block h-3 w-1.5 bg-zinc-600 ml-1 mt-1" />
      </div>
    </div>
  );
}

// --- Main Presentation Platform ---
export default function App() {
  const [activeNode, setActiveNode] = useState(0);
  const [activeLens, setActiveLens] = useState("legal");

  const active = srpvdalNodes[activeNode];
  const ActiveIcon = active.icon;
  const lens = lenses[activeLens];
  const LensIcon = lens.icon;

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveNode((prev) => (prev + 1) % srpvdalNodes.length);
    }, 3500);
    return () => clearInterval(timer);
  }, []);

  const authorityBands = useMemo(() => [
    ["Autonomous Execution", "0–72 Threshold Score", "System acts autonomously within strict delegated limits when all verification parameters are met.", "bg-emerald-400"],
    ["Stakeholder Review", "73–88 Threshold Score", "Actions are paused and queued for human verification when ambiguity triggers policy boundaries.", "bg-amber-400"],
    ["Fiduciary Veto / Escalation", "89+ Threshold Score", "Full executive, general counsel, or regulatory override requested immediately when high-stakes parameters are crossed.", "bg-rose-500"],
  ], []);

  return (
    <div className="min-h-screen bg-[#020204] text-zinc-100 antialiased selection:bg-white selection:text-black">
      {/* Structural Overlays */}
      <div className="fixed inset-0 -z-10 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:40px_40px]" />
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_center,rgba(255,255,255,0.02),transparent_70%)]" />

      {/* Navigation Layer */}
      <header className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#020204]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="h-2 w-2 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,1)] animate-pulse" />
            <span className="font-mono text-xs font-black tracking-[0.25em] text-white">MIZOKI3</span>
          </div>
          <nav className="hidden gap-8 text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-500 md:flex">
            <a href="#control" className="hover:text-white transition-colors">Control Planes</a>
            <a href="#engine" className="hover:text-white transition-colors">Cognitive Loop</a>
            <a href="#lenses" className="hover:text-white transition-colors">Domain Cells</a>
            <a href="#replay" className="hover:text-white transition-colors">Decision Flight Record</a>
            <a href="#kpis" className="hover:text-white transition-colors">Resilience KPIs</a>
          </nav>
          <Button variant="outline" size="sm" className="font-mono text-[9px] border-zinc-800">Request Audit Briefing</Button>
        </div>
      </header>

      <main className="pt-16">
        {/* Immersive Hero Section */}
        <section className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 py-20 lg:grid-cols-[1fr_1.1fr] lg:py-28">
          <div className="relative z-10">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 font-mono text-[9px] font-bold uppercase tracking-[0.22em] text-zinc-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" /> Governed Autonomy Protocol Active
            </div>
            <h1 className="mb-6 text-5xl font-semibold leading-[1.05] tracking-tight text-white md:text-7xl">
              Enterprise action<br />
              <span className="text-zinc-500">governed by causation.</span>
            </h1>
            <p className="mb-10 max-w-xl text-lg font-light leading-relaxed text-zinc-400">
              MIZOKI3 is the autonomous decision layer for high-stakes enterprise transactions. We don't ask if AI can write text. We establish the mathematical conditions under which AI is permitted to act.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="w-full sm:w-auto">Request System Access <ArrowRight className="ml-2 h-4 w-4" /></Button>
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-zinc-300 border-zinc-800">
                <Play className="mr-2 h-3.5 w-3.5 text-zinc-500" /> Watch Operations Loop
              </Button>
            </div>
          </div>
          <div className="relative">
            <LivingEnterpriseVisual />
          </div>
        </section>

        {/* Status Quo Paradigm Clash */}
        <section className="border-y border-white/5 bg-[#030306] py-24">
          <div className="mx-auto max-w-7xl px-6 grid gap-8 lg:grid-cols-2">
            <Card className="border-rose-500/10 bg-rose-950/5">
              <CardContent className="p-8">
                <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/5">
                  <AlertTriangle className="h-5 w-5 text-rose-400" />
                </div>
                <div className="font-mono text-[9px] text-rose-400 tracking-[0.2em] uppercase mb-1">Traditional LLM Execution</div>
                <h3 className="text-2xl font-bold text-white mb-6">The Hallucination Trap</h3>
                <ul className="space-y-4 text-sm font-light text-zinc-400">
                  <li className="flex gap-3"><AlertTriangle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" /> Predicts next-token strings without causal mathematical model structures.</li>
                  <li className="flex gap-3"><AlertTriangle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" /> Floods management with disconnected chat streams instead of governed actions.</li>
                  <li className="flex gap-3"><AlertTriangle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" /> Fails to preserve explanation state, leaving actions un-auditable for regulators.</li>
                </ul>
              </CardContent>
            </Card>

            <Card className="border-cyan-500/10 bg-cyan-950/5">
              <CardContent className="p-8">
                <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-lg border border-cyan-500/20 bg-cyan-500/5">
                  <ShieldCheck className="h-5 w-5 text-cyan-400" />
                </div>
                <div className="font-mono text-[9px] text-cyan-400 tracking-[0.2em] uppercase mb-1">MIZOKI3 System Blueprint</div>
                <h3 className="text-2xl font-bold text-white mb-6">Autonomous Causal Substrate</h3>
                <ul className="space-y-4 text-sm font-light text-zinc-400">
                  <li className="flex gap-3"><ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" /> Anchors all actions in a live, bi-temporal enterprise knowledge graph (TCKG).</li>
                  <li className="flex gap-3"><ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" /> Executes deep counterfactual simulations before any API payload release.</li>
                  <li className="flex gap-3"><ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" /> Separates proposal pathways from final execution via explicit Control Planes.</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 3 Control Planes (The Gating Layer) */}
        <section id="control" className="mx-auto max-w-7xl px-6 py-32">
          <div className="mb-20 max-w-2xl">
            <div className="font-mono text-[10px] tracking-[0.25em] text-cyan-400 uppercase mb-3">Governance Architecture</div>
            <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-5xl">The Three Control Planes.</h2>
            <p className="text-lg font-light text-zinc-400">Autonomy is dangerous without strict boundaries. MIZOKI3 filters all agent proposals through three physical isolation zones before committing changes to operations.</p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              { id: "01", title: "Decision Control Plane", desc: "Monitors active strategic policies, delegated parameters, and routing paths. Sets risk appetite parameters before plans are initiated.", bullets: ["Policy Mapping", "Fiduciary Floor Constraints"] },
              { id: "02", title: "Verification & Arbitration", desc: "Runs cross-model validation debates. Pits Planner agents against Verifier agents in adversarial simulations to expose logical drift.", bullets: ["Adversarial Agent Debates", "Conflict State Logs"] },
              { id: "03", title: "Decision Eligibility Layer", desc: "Validates identity tags, signature tokens, and context bounds. Signs off the final action trace to generate immutable audit registries.", bullets: ["System Token Validation", "Audit Trail Registries"] },
            ].map((layer) => (
              <Card key={layer.id} className="group flex flex-col">
                <CardContent className="flex flex-1 flex-col justify-between">
                  <div>
                    <div className="mb-8 border-b border-zinc-800 pb-4 font-mono text-[9px] uppercase tracking-[0.2em] text-zinc-500">Isolation Layer {layer.id}</div>
                    <h3 className="mb-3 text-2xl font-semibold tracking-tight">{layer.title}</h3>
                    <p className="mb-8 text-sm font-light leading-relaxed text-zinc-400">{layer.desc}</p>
                  </div>
                  <ul className="space-y-3 font-mono text-xs text-zinc-500 border-t border-zinc-900 pt-6">
                    {layer.bullets.map((b) => (
                      <li key={b} className="flex items-center gap-2">
                        <div className="h-1 w-1 rounded-full bg-cyan-400/50" /> {b}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* SRPVDAL Cognitive Loop Explorer */}
        <section id="engine" className="border-t border-white/5 bg-[#050508] py-32">
          <div className="mx-auto max-w-7xl px-6">
            <div className="mb-16 flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div>
                <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-amber-400 mb-2">Cognitive Core Framework</div>
                <h2 className="text-4xl font-black">The SRPVDAL Engine</h2>
              </div>
              <p className="max-w-xl text-sm font-light leading-relaxed text-zinc-400">
                A highly structured 7-stage state machine that continuous processing cycles utilize. Interrogate each functional node below to inspect execution telemetry.
              </p>
            </div>

            <div className="grid gap-8 lg:grid-cols-12">
              {/* Dynamic Interactive Node List */}
              <div className="space-y-2.5 lg:col-span-5">
                {srpvdalNodes.map((node, idx) => {
                  const Icon = node.icon;
                  const isActive = activeNode === idx;
                  return (
                    <button
                      key={node.id}
                      onClick={() => setActiveNode(idx)}
                      className={`w-full rounded-xl border p-4 text-left transition-all ${
                        isActive 
                          ? "border-cyan-500/35 bg-cyan-950/10 shadow-[0_0_40px_rgba(34,211,238,0.05)]" 
                          : "border-zinc-900 bg-zinc-950/10 hover:border-zinc-800"
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`grid h-10 w-10 place-items-center rounded-lg ${isActive ? "bg-white text-black shadow-lg" : "border border-zinc-800 bg-black text-zinc-500"}`}>
                          <Icon className="h-4.5 w-4.5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className={`font-mono text-xs font-bold ${isActive ? "text-white" : "text-zinc-400"}`}>
                              0{idx + 1}. {node.name}
                            </h3>
                            <span className={`rounded-sm px-2 py-0.5 font-mono text-[9px] font-bold ${isActive ? "bg-cyan-500/20 text-cyan-300" : "bg-zinc-900 text-zinc-600"}`}>
                              {node.phase}
                            </span>
                          </div>
                        </div>
                        <ChevronRight className={`h-4 w-4 transition-transform ${isActive ? "text-cyan-400 translate-x-1" : "text-zinc-800"}`} />
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Cognitive Step Details Box */}
              <div className="relative flex flex-col justify-between rounded-xl border border-zinc-800 bg-[#020205] p-8 lg:col-span-7">
                <div className="absolute left-0 top-0 h-[1px] w-full bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
                
                <div>
                  <div className="flex items-center justify-between border-b border-zinc-900 pb-4 font-mono text-[9px] uppercase tracking-widest text-zinc-500">
                    <span>Active Telemetry Monitoring</span>
                    <span className="text-cyan-400">Step Verified</span>
                  </div>

                  <div className="my-10 flex items-start gap-6">
                    <div className="grid h-14 w-14 shrink-0 place-items-center rounded-xl border border-cyan-500/25 bg-cyan-500/5 text-cyan-300">
                      <ActiveIcon className="h-7 w-7" />
                    </div>
                    <div>
                      <div className="font-mono text-[9px] font-bold uppercase tracking-wider text-cyan-400">Loop Element 0{activeNode + 1}</div>
                      <h3 className="mt-1.5 text-3xl font-bold text-white tracking-tight">{active.name} Module</h3>
                      <p className="mt-4 text-sm font-light leading-relaxed text-zinc-400 max-w-xl">{active.desc}</p>
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3 border-t border-zinc-900 pt-6">
                  {[
                    ["Operational Confidence", active.metrics.confidence, "bg-cyan-400", active.metrics.wConf],
                    ["Module Latency", active.metrics.latency, "bg-amber-400", active.metrics.wLat],
                    ["Causal Alignment", active.metrics.alignment, "bg-emerald-400", active.metrics.wAl]
                  ].map(([label, val, barColor, width]) => (
                    <div key={label} className="rounded-lg border border-white/5 bg-white/[0.01] p-4 font-mono">
                      <div className="mb-2 flex justify-between text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
                        <span>{label}</span>
                        <span className="text-zinc-200">{val}</span>
                      </div>
                      <div className="h-1 rounded-full bg-zinc-950">
                        <motion.div className={`h-full rounded-full ${barColor}`} initial={{ width: 0 }} animate={{ width: width }} transition={{ duration: 0.8 }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Dual Trace Panel: Authorization Dashboard & Command Logs */}
        <section className="mx-auto max-w-7xl px-6 py-32 grid gap-8 lg:grid-cols-2">
          <div>
            <div className="font-mono text-[9px] tracking-[0.25em] text-rose-500 uppercase mb-3">Live System Inspection</div>
            <h2 className="mb-6 text-3xl font-bold tracking-tight md:text-5xl">The Execution Trace.</h2>
            <div className="space-y-4 text-zinc-400 text-sm font-light leading-relaxed">
              <p>
                To provide fiduciary guarantees, MIZOKI3 displays every step of its execution trace in clear, un-hallucinated plain text.
              </p>
              <p>
                On the right, you can watch the interactive **Decision Control Plane** evaluate a $5M dividend proposal. Below it, inspect the raw, live scrolling trace of the **V&A Layer** vetoing the transaction after cross-checking against a newly ingested debt-amendment clause.
              </p>
              <p className="border-l border-zinc-800 text-zinc-300 pl-4 py-1 italic">
                Because we do not act on correlation alone, our verifiers guarantee policy safety before any external API payload releases.
              </p>
            </div>

            <div className="mt-8">
              <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-widest mb-4">Risk Threshold Distribution</h4>
              <div className="space-y-3.5">
                {authorityBands.map(([title, score, desc, dotColor]) => (
                  <div key={title} className="rounded-lg border border-zinc-900 bg-[#040407] p-4.5 text-xs">
                    <div className="flex items-center justify-between mb-1.5 font-bold">
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${dotColor}`} />
                        <span className="text-zinc-200">{title}</span>
                      </div>
                      <span className="font-mono text-zinc-500 text-[10px]">{score}</span>
                    </div>
                    <p className="text-zinc-400 font-light leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <DcpAuthorizationPanel />
            <TerminalSimulator />
          </div>
        </section>

        {/* Interactive Domain Lenses */}
        <section id="lenses" className="border-t border-white/5 bg-[#030306] py-32">
          <div className="mx-auto max-w-7xl px-6">
            <div className="mb-14 max-w-2xl">
              <div className="font-mono text-[10px] tracking-[0.25em] text-cyan-400 uppercase mb-3">Modular Graph Lenses</div>
              <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-5xl">Specialized Domain Cells.</h2>
              <p className="text-lg font-light text-zinc-400">Our cells are not isolated software products. They are unified visual lenses pointing back into the exact same Temporal-Causal Knowledge Graph substrate.</p>
            </div>

            <div className="mb-8 flex flex-wrap gap-2 border-b border-zinc-900 pb-4">
              {Object.entries(lenses).map(([key, item]) => (
                <button
                  key={key}
                  onClick={() => setActiveLens(key)}
                  className={`rounded border px-5 py-3 font-mono text-[10px] font-bold uppercase tracking-widest transition-all ${
                    activeLens === key 
                      ? "border-white bg-white/5 text-white shadow-lg" 
                      : "border-zinc-900 bg-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-800"
                  }`}
                >
                  {item.label} Cell
                </button>
              ))}
            </div>

            <div className="grid gap-8 rounded-2xl border border-zinc-800 bg-black/60 p-8 lg:grid-cols-2">
              <div className="flex flex-col justify-between">
                <div>
                  <div className={`mb-6 flex h-12 w-12 items-center justify-center rounded-lg border ${lens.border} ${lens.bg}`}>
                    <LensIcon className={`h-6 w-6 ${lens.color}`} />
                  </div>
                  <h3 className="text-3xl font-bold text-white tracking-tight">{lens.title}</h3>
                  <p className="mt-1 text-xs font-mono font-bold uppercase tracking-widest text-amber-400">{lens.tagline}</p>
                  <p className="mt-6 text-base font-light leading-relaxed text-zinc-400">{lens.desc}</p>
                </div>

                <div className="mt-8 flex items-center gap-2 border-t border-zinc-950 pt-6">
                  <Database className="h-4 w-4 text-zinc-500" />
                  <span className="font-mono text-[10px] uppercase tracking-widest text-zinc-500">Connected to active TCKG Substrate</span>
                </div>
              </div>

              <div className="rounded-xl border border-zinc-900 bg-[#030305] p-6 font-mono text-xs">
                <div className="mb-6 text-zinc-600 font-bold">// CONTEXT_EL_CAPABILITIES_REGISTERED</div>
                <div className="space-y-2.5">
                  {lens.features.map((feat) => (
                    <div key={feat} className="flex items-center gap-3 rounded border border-white/5 bg-white/[0.01] p-4 text-zinc-300">
                      <CheckCircle2 className={`h-4.5 w-4.5 shrink-0 ${lens.color}`} />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Flight Record Decision Replay Timeline */}
        <section id="replay" className="bg-[#010102] py-32">
          <div className="mx-auto max-w-4xl px-6">
            <div className="mb-16 text-center">
              <div className="font-mono text-[10px] tracking-[0.25em] text-cyan-400 uppercase mb-3">Decision Flight Record</div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Explainable Trace Replays</h2>
              <p className="mx-auto mt-4 max-w-2xl text-base font-light text-zinc-400">Review, step-by-step, the exact sequence of historical signals, simulations, validation checks, and final execution parameters.</p>
            </div>

            <div className="relative border-l border-zinc-900 ml-4 md:ml-10 space-y-8">
              {replaySteps.map(([time, event, detail], idx) => (
                <div key={event} className="relative pl-8 md:pl-12 group">
                  {/* Timeline Node Dot */}
                  <div className="absolute -left-4 top-1.5 z-10 grid h-8 w-8 place-items-center rounded-full border-2 border-zinc-900 bg-black transition-colors group-hover:border-zinc-500">
                    <div className={`h-2.5 w-2.5 rounded-full ${idx === replaySteps.length - 1 ? "bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,1)] animate-pulse" : "bg-zinc-800"}`} />
                  </div>
                  
                  {/* Step Card Content */}
                  <Card className="border-zinc-900 bg-zinc-950/40">
                    <CardContent className="p-6">
                      <div className="mb-3 flex flex-wrap items-center gap-3">
                        <span className="font-mono text-xs text-zinc-600 font-bold">{time}</span>
                        <span className="rounded-sm bg-white/5 px-2 py-0.5 font-mono text-[9px] font-bold tracking-widest text-cyan-400 uppercase">
                          {event}
                        </span>
                      </div>
                      <p className="text-sm font-light leading-relaxed text-zinc-400">{detail}</p>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Operational KPIs */}
        <section id="kpis" className="border-t border-white/5 bg-[#030306] py-32">
          <div className="mx-auto max-w-7xl px-6">
            <div className="mb-16 max-w-2xl">
              <div className="font-mono text-[10px] tracking-[0.25em] text-amber-400 uppercase mb-3">Sovereign Performance metrics</div>
              <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-5xl">Autonomy must be measured.</h2>
              <p className="text-base font-light text-zinc-400">Every strategic decision state maintains real-world, transparent compliance tracking variables.</p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {kpis.map(([Icon, title, desc, iconColor]) => (
                <Card key={title} className="group border-zinc-900">
                  <CardContent className="p-8">
                    <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
                      <Icon className={`h-5 w-5 ${iconColor}`} />
                    </div>
                    <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
                    <p className="text-sm font-light leading-relaxed text-zinc-400">{desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Premium Core Footer CTA */}
        <section className="relative overflow-hidden bg-black py-32 text-center">
          <KnowledgeGraphBackground />
          <div className="relative z-10 mx-auto max-w-3xl px-6">
            <Sparkles className="mx-auto mb-8 h-12 w-12 text-zinc-300 animate-pulse" />
            <h2 className="text-4xl font-bold tracking-tight text-white md:text-6xl">Sovereign Enterprise Cognition.</h2>
            <p className="mx-auto mt-6 max-w-xl text-base font-light text-zinc-400 leading-relaxed">
              Stop digesting semantic text. Secure fiduciary-grade action pathways through causation-guided, threshold-aware execution loops.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row justify-center gap-4">
              <Button size="lg" className="px-10">Request Briefing</Button>
              <Button size="lg" variant="outline" className="border-zinc-800 text-zinc-300">Explore Architecture</Button>
            </div>
          </div>
        </section>
      </main>

      {/* Sovereign Footnote Layer */}
      <footer className="border-t border-white/5 bg-black py-10">
        <div className="mx-auto max-w-7xl px-6 flex flex-col items-center justify-between gap-6 font-mono text-[10px] uppercase tracking-widest text-zinc-600 md:flex-row">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-zinc-700" />
            <span>MIZOKI3 SYSTEM PLATFORM</span>
          </div>
          <div className="flex items-center gap-4">
            <span>SOC 2 Compliance Queue</span>
            <span>•</span>
            <span>GDPR COMPATIBLE</span>
          </div>
          <div>© 2026 MIZOKI3. All Rights Reserved.</div>
        </div>
      </footer>
    </div>
  );
}