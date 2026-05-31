import { useState } from "react";
import { lenses } from "../data/siteData";
import { cx } from "../lib/cx";

export function DomainLensPanel() {
  const [activeLens, setActiveLens] = useState("legal");
  const lens = lenses[activeLens];
  const LensIcon = lens.icon;

  return (
    <section className="border-y border-white/10 bg-[#030305] px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 max-w-3xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">One Brain. Many Lenses.</p>
          <h2 className="mt-4 text-4xl font-black md:text-6xl">Domain Cells are not separate apps.</h2>
          <p className="mt-5 leading-8 text-slate-300">
            They are specialized execution surfaces reading from and writing to shared system memory under Nexus orchestration.
          </p>
        </div>

        <div className="mb-8 flex flex-wrap gap-3">
          {Object.entries(lenses).map(([key, item]) => (
            <button
              key={key}
              onClick={() => setActiveLens(key)}
              className={cx(
                "rounded-xl border px-5 py-3 text-xs font-black uppercase tracking-widest transition",
                activeLens === key ? "border-cyan-300 bg-cyan-300/10 text-white" : "border-white/10 bg-white/[0.02] text-slate-500 hover:text-slate-200"
              )}
            >
              {item.label} Cell
            </button>
          ))}
        </div>

        <div className="grid gap-8 rounded-[2rem] border border-white/10 bg-black/40 p-8 lg:grid-cols-2">
          <div>
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-300/30 bg-cyan-300/10">
              <LensIcon className="h-8 w-8 text-cyan-200" />
            </div>
            <h3 className="text-3xl font-black">{lens.title}</h3>
            <p className="mt-2 text-sm font-black uppercase tracking-widest text-amber-300">{lens.tagline}</p>
            <p className="mt-6 text-lg leading-8 text-slate-300">{lens.desc}</p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-slate-950 p-6 font-mono text-sm">
            <div className="mb-6 text-cyan-300">// DOMAIN_SURFACE_CONNECTED_TO_NEXUS</div>
            <div className="space-y-3">
              {lens.features.map((f) => (
                <div key={f} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-slate-300">
                  ✓ {f}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
