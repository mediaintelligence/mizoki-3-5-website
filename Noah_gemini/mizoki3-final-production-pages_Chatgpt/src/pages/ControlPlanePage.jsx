import { authorityBands } from "../data/siteData";
import { cx } from "../lib/cx";
import { SurfaceCard } from "../components/SurfaceCard";
import { DcpAuthorizationPanel } from "../components/DcpAuthorizationPanel";
import { ReplayTimeline } from "../components/ReplayTimeline";

export function ControlPlanePage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">The AI Governor</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">The Decision Control Plane decides what is allowed.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            The core question is not whether AI can act. The decisive question is whether context, identity, policy, risk, confidence, and authority thresholds are sufficient for it to act.
          </p>
        </div>
      </section>
      <section className="border-b border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[.9fr_1.1fr]">
          <div className="space-y-4">
            {authorityBands.map(([title, range, desc, color]) => (
              <SurfaceCard key={title} className="p-5">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-3"><span className={cx("h-3 w-3 rounded-full", color)} /><span className="font-black text-white">{title}</span></div>
                  <span className="font-mono text-xs text-slate-500">{range}</span>
                </div>
                <p className="text-sm leading-6 text-slate-400">{desc}</p>
              </SurfaceCard>
            ))}
          </div>
          <DcpAuthorizationPanel confidence={94} />
        </div>
      </section>
      <ReplayTimeline />
    </>
  );
}
