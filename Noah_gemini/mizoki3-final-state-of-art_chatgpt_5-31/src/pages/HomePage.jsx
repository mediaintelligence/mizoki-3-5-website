import { Link } from "react-router-dom";
import { Activity, AlertTriangle, ArrowRight, CheckCircle2, Database, Network, Play, ShieldCheck } from "lucide-react";
import { antiDashboardCards, capabilityCards, kpis } from "../data/siteData";
import { Button } from "../components/Button";
import { SurfaceCard } from "../components/SurfaceCard";
import { KnowledgeGraphBackground } from "../components/KnowledgeGraphBackground";
import { LivingEnterpriseVisual } from "../components/LivingEnterpriseVisual";
import { SrpvdalMonitor } from "../components/SrpvdalMonitor";
import { DcpAuthorizationPanel } from "../components/DcpAuthorizationPanel";
import { EnterpriseNervousSystem } from "../components/EnterpriseNervousSystem";
import { DomainLensPanel } from "../components/DomainLensPanel";
import { ReplayTimeline } from "../components/ReplayTimeline";
import { DeploymentCta, FinalCta } from "../components/FinalCta";
import { QuestionAnswerMatrix } from "../components/QuestionAnswerMatrix";
import { StateOfArtStoryVisual } from "../components/StateOfArtStoryVisual";

export function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden border-b border-white/10 px-6 py-20 md:py-28">
        <KnowledgeGraphBackground />
        <div className="relative z-10 mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[0.86fr_1.14fr]">
          <div>
            <div className="mb-6 inline-flex items-center rounded-full border border-cyan-400/25 bg-cyan-400/10 px-4 py-2 text-xs font-black uppercase tracking-[0.24em] text-cyan-200">
              <span className="mr-2 h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_14px_rgba(34,211,238,.9)]" />
              Governed Autonomy Active
            </div>
            <h1 className="text-5xl font-black leading-[1.02] tracking-tight text-white md:text-7xl">
              Enterprise action governed by causality.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">
              MIZOKI3 is the autonomous decision intelligence layer for high-stakes enterprise execution. It does not ask whether AI can act. It determines what conditions must be true before AI is allowed to act.
            </p>
            <div className="mt-9 flex flex-wrap gap-4">
              <Link to="/simulator"><Button>Simulate Scenarios <ArrowRight className="ml-2 h-4 w-4" /></Button></Link>
              <Link to="/engine"><Button variant="outline"><Play className="mr-2 h-4 w-4 text-amber-300" /> View Architecture</Button></Link>
            </div>
            <div className="mt-10 grid gap-3 text-xs font-mono text-slate-500 sm:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-black/30 p-3">CORE: DETERMINISTIC</div>
              <div className="rounded-xl border border-white/10 bg-black/30 p-3">DCP: ENFORCED</div>
              <div className="rounded-xl border border-white/10 bg-black/30 p-3">TCKG: LIVE</div>
            </div>
          </div>
          <LivingEnterpriseVisual />
        </div>
        <div className="relative z-10 mx-auto mt-12 hidden max-w-7xl items-center justify-between border-t border-white/10 pt-5 font-mono text-[10px] uppercase tracking-widest text-slate-500 lg:flex">
          <span className="flex items-center"><Activity className="mr-2 h-3.5 w-3.5 text-amber-300" /> System Core: Running</span>
          <span className="flex items-center"><Network className="mr-2 h-3.5 w-3.5 text-cyan-300" /> Active Causal Edges: 8.4M</span>
          <span>Secure Node Connection // Trace Verified</span>
        </div>
      </section>

      <StateOfArtStoryVisual />
      <QuestionAnswerMatrix />


      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10 max-w-3xl">
            <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Anti-Dashboard Thesis</p>
            <h2 className="mt-4 text-4xl font-black md:text-6xl">Not another dashboard. A decision intelligence layer.</h2>
            <p className="mt-5 leading-8 text-slate-300">
              MIZOKI3 plugs into existing enterprise stacks and converts fragmented operational signals into governed, threshold-aware actions.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {antiDashboardCards.map(([title, body]) => (
              <SurfaceCard key={title} className="p-6">
                <Network className="mb-5 h-7 w-7 text-cyan-300" />
                <h3 className="text-xl font-black">{title}</h3>
                <p className="mt-3 leading-7 text-slate-400">{body}</p>
              </SurfaceCard>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-white/10 bg-[#030305] px-6 py-20">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-2">
          <SurfaceCard className="border-red-500/20 bg-red-950/10 p-8">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl border border-red-400/30 bg-red-400/10">
              <AlertTriangle className="h-6 w-6 text-red-300" />
            </div>
            <p className="mb-3 text-xs font-black uppercase tracking-[0.3em] text-red-300">The Status Quo</p>
            <h2 className="text-3xl font-black">Why current AI fails the enterprise.</h2>
            <div className="mt-7 space-y-5 text-slate-300">
              {["Predicts, reacts, and summarizes without proving causality.", "Creates more dashboards instead of governed operating decisions.", "Cannot explain why action was authorized, rejected, or escalated."].map((x) => (
                <div key={x} className="flex gap-3"><AlertTriangle className="mt-1 h-5 w-5 shrink-0 text-red-300" /><p>{x}</p></div>
              ))}
            </div>
          </SurfaceCard>
          <SurfaceCard className="border-cyan-400/20 bg-cyan-950/10 p-8">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl border border-cyan-400/30 bg-cyan-400/10">
              <Network className="h-6 w-6 text-cyan-300" />
            </div>
            <p className="mb-3 text-xs font-black uppercase tracking-[0.3em] text-cyan-300">The MIZOKI3 Paradigm</p>
            <h2 className="text-3xl font-black">Governed intelligence orchestration.</h2>
            <div className="mt-7 space-y-5 text-slate-300">
              {["Maintains a live temporal-causal memory of enterprise operations.", "Simulates outcomes before execution and rejects unsafe paths.", "Routes every action through authority thresholds and audit trails."].map((x) => (
                <div key={x} className="flex gap-3"><ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-cyan-300" /><p>{x}</p></div>
              ))}
            </div>
          </SurfaceCard>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {capabilityCards.map(({ icon: Icon, title, body }) => (
            <SurfaceCard key={title} className="p-6 transition-all hover:border-cyan-500/20 hover:bg-white/[0.05]">
              <div className="mb-5 inline-grid rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-2.5">
                <Icon className="h-6 w-6 text-cyan-300" />
              </div>
              <h3 className="mb-2 text-lg font-black tracking-wide">{title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{body}</p>
            </SurfaceCard>
          ))}
        </div>
      </section>

      <SrpvdalMonitor />

      <section className="border-y border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[.9fr_1.1fr]">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">The AI Governor</p>
            <h2 className="mt-4 text-4xl font-black md:text-6xl">The Decision Control Plane decides what is allowed.</h2>
            <p className="mt-6 text-lg leading-8 text-slate-300">
              The core question is not whether AI can act. The decisive question is whether context, identity, policy, risk, confidence, and authority thresholds are sufficient for it to act.
            </p>
          </div>
          <DcpAuthorizationPanel confidence={94} />
        </div>
      </section>

      <section className="bg-[#010102] px-6 py-24">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-2">
          <SurfaceCard className="p-8">
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-400/10">
              <Database className="h-8 w-8 text-indigo-300" />
            </div>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-indigo-300">The Brain</p>
            <h2 className="mt-4 text-4xl font-black">Temporal-Causal Knowledge Graph</h2>
            <p className="mt-5 leading-8 text-slate-300">
              The TCKG stores system memory, causal relationships, rejected paths, simulations, stakeholder context, execution records, policies, and outcomes.
            </p>
            <div className="mt-8 grid gap-3">
              {["Temporal memory", "Counterfactual paths", "Self-healing causal weights", "Immutable reasoning traces"].map((x) => (
                <div key={x} className="flex items-center gap-3 text-slate-200"><CheckCircle2 className="h-5 w-5 text-amber-300" />{x}</div>
              ))}
            </div>
          </SurfaceCard>
          <EnterpriseNervousSystem />
        </div>
      </section>

      <DomainLensPanel />
      <ReplayTimeline />

      <section className="border-t border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mb-14 max-w-3xl">
            <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Operational KPIs</p>
            <h2 className="mt-4 text-4xl font-black md:text-6xl">Autonomy must be measured.</h2>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {kpis.map(([Icon, title, body]) => (
              <SurfaceCard key={title} className="p-6">
                <Icon className="mb-5 h-7 w-7 text-cyan-300" />
                <h3 className="text-xl font-black">{title}</h3>
                <p className="mt-3 leading-7 text-slate-400">{body}</p>
              </SurfaceCard>
            ))}
          </div>
        </div>
      </section>

      <DeploymentCta />
      <FinalCta />
    </>
  );
}
