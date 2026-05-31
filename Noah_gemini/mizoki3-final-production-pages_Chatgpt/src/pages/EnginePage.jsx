import { SrpvdalMonitor } from "../components/SrpvdalMonitor";
import { srpvdalNodes } from "../data/siteData";
import { SurfaceCard } from "../components/SurfaceCard";
import { DeploymentCta } from "../components/FinalCta";

export function EnginePage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">The Canonical Loop</p>
          <h1 className="mt-4 max-w-4xl text-5xl font-black md:text-7xl">Sense → Reason → Plan → Validate → Decide → Act → Learn.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            SRPVDAL is the deterministic cognitive loop that prevents prompt-to-action fragility.
          </p>
        </div>
      </section>
      <SrpvdalMonitor />
      <section className="border-y border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 max-w-3xl">
            <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Stage Detail</p>
            <h2 className="mt-4 text-4xl font-black md:text-6xl">Every phase has a job.</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {srpvdalNodes.map((node, idx) => {
              const Icon = node.icon;
              return (
                <SurfaceCard key={node.key} className={idx === 4 ? "border-amber-300/30 bg-amber-300/5 p-6" : "p-6"}>
                  <Icon className="mb-5 h-7 w-7 text-cyan-300" />
                  <p className="text-xs font-mono text-slate-500">0{idx + 1} / {node.phase}</p>
                  <h3 className="mt-2 text-2xl font-black">{node.name}</h3>
                  <p className="mt-3 leading-7 text-slate-400">{node.desc}</p>
                </SurfaceCard>
              );
            })}
          </div>
        </div>
      </section>
      <DeploymentCta />
    </>
  );
}
