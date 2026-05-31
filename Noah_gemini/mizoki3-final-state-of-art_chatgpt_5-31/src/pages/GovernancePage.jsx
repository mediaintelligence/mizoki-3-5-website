import { governanceCards } from "../data/siteData";
import { SurfaceCard } from "../components/SurfaceCard";
import { DcpAuthorizationPanel } from "../components/DcpAuthorizationPanel";
import { ReplayTimeline } from "../components/ReplayTimeline";

export function GovernancePage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Technical Governance</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">Every action is gated, explained, and recorded.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            MIZOKI3 treats autonomy as an authorization problem. Context sufficiency, explainable reasoning, and immutable auditability are part of the operating fabric.
          </p>
        </div>
      </section>
      <section className="border-b border-white/10 bg-[#050505] px-6 py-24">
        <div className="mx-auto grid max-w-7xl gap-6 md:grid-cols-3">
          {governanceCards.map(([Icon, title, body]) => (
            <SurfaceCard key={title} className="p-7">
              <Icon className="mb-5 h-8 w-8 text-amber-300" />
              <h3 className="text-xl font-black">{title}</h3>
              <p className="mt-3 leading-7 text-slate-400">{body}</p>
            </SurfaceCard>
          ))}
        </div>
      </section>
      <section className="border-b border-white/10 bg-[#030305] px-6 py-24">
        <div className="mx-auto max-w-3xl">
          <DcpAuthorizationPanel confidence={94} />
        </div>
      </section>
      <ReplayTimeline />
    </>
  );
}
