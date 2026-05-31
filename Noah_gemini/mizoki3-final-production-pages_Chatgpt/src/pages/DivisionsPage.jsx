import { ArrowRight, Cpu, Layers } from "lucide-react";
import { agents, divisions } from "../data/siteData";
import { SurfaceCard } from "../components/SurfaceCard";
import { DomainLensPanel } from "../components/DomainLensPanel";
import { FinalCta } from "../components/FinalCta";

export function DivisionsPage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">One Brain. Many Lenses.</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">Domain Cells are specialized execution surfaces.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            Legal, estate, risk, media, and capital cells share one Knowledge Graph core and one Nexus orchestration layer.
          </p>
        </div>
      </section>
      <section className="border-b border-white/10 bg-[#050505] px-6 py-24">
        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[.85fr_1.15fr]">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Agent Coordination</p>
            <h2 className="mt-4 text-4xl font-black md:text-6xl">Specialized agents. Governed outcomes.</h2>
            <p className="mt-6 text-lg leading-8 text-slate-300">
              Specialized intelligence cells share context, debate recommendations, verify paths, and submit only eligible actions to the Decision Control Plane.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {agents.map((agent) => (
              <SurfaceCard key={agent} className="group flex items-center gap-4 p-5 hover:border-amber-300/30 hover:bg-amber-300/5">
                <Cpu className="h-6 w-6 text-amber-300/60 transition-colors group-hover:text-amber-300" />
                <span className="font-mono text-sm uppercase tracking-wide text-slate-300 group-hover:text-white">{agent}</span>
              </SurfaceCard>
            ))}
          </div>
        </div>
      </section>
      <DomainLensPanel />
      <section className="bg-[#010102] px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mb-10">
            <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Divisions</p>
            <h2 className="mt-3 text-4xl font-black tracking-tight">Powered by shared intelligence.</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {divisions.map((division) => (
              <SurfaceCard key={division.id} className="group p-6 transition-all hover:border-cyan-400/30 hover:bg-white/[0.05]">
                <div className="mb-5 inline-grid rounded-xl border border-amber-400/20 bg-amber-400/10 p-2.5 transition-transform group-hover:scale-105">
                  <Layers className="h-5 w-5 text-amber-300" />
                </div>
                <h3 className="text-lg font-black tracking-wide transition-colors group-hover:text-cyan-300">{division.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{division.body}</p>
                <div className="mt-6 flex cursor-pointer items-center text-xs font-black uppercase tracking-wider text-cyan-300">
                  Explore Matrix <ArrowRight className="ml-1.5 h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
                </div>
              </SurfaceCard>
            ))}
          </div>
        </div>
      </section>
      <FinalCta />
    </>
  );
}
