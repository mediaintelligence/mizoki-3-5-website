import { Network, CheckCircle2, Database } from "lucide-react";
import { antiDashboardCards } from "../data/siteData";
import { SurfaceCard } from "../components/SurfaceCard";
import { EnterpriseNervousSystem } from "../components/EnterpriseNervousSystem";
import { DeploymentCta } from "../components/FinalCta";

export function PlatformPage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Platform Architecture</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">The autonomous decision intelligence layer.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            MIZOKI3 connects existing enterprise systems into one causal memory and one governed execution layer.
          </p>
        </div>
      </section>
      <section className="border-b border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto max-w-7xl">
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
      <section className="bg-[#010102] px-6 py-24">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-2">
          <SurfaceCard className="p-8">
            <Database className="mb-6 h-10 w-10 text-indigo-300" />
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
      <DeploymentCta />
    </>
  );
}
