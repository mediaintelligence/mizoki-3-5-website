import { kpis } from "../data/siteData";
import { SurfaceCard } from "../components/SurfaceCard";
import { FinalCta } from "../components/FinalCta";

export function KpisPage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Operational KPIs</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">Autonomy must be measured.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            Governed autonomy is only credible when latency, confidence, overrides, outcome delta, learning velocity, and audit completeness are visible.
          </p>
        </div>
      </section>
      <section className="border-b border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto grid max-w-7xl gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {kpis.map(([Icon, title, body]) => (
            <SurfaceCard key={title} className="p-6">
              <Icon className="mb-5 h-7 w-7 text-cyan-300" />
              <h3 className="text-xl font-black">{title}</h3>
              <p className="mt-3 leading-7 text-slate-400">{body}</p>
            </SurfaceCard>
          ))}
        </div>
      </section>
      <FinalCta />
    </>
  );
}
