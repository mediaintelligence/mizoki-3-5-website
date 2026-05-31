import { replaySteps } from "../data/siteData";
import { cx } from "../lib/cx";

export function ReplayTimeline() {
  return (
    <section className="bg-[#010102] px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Decision Replay</p>
          <h2 className="mt-4 text-4xl font-black md:text-6xl">Every decision is explainable.</h2>
          <p className="mx-auto mt-5 max-w-2xl leading-8 text-slate-300">
            Replay signals, reasoning, rejected paths, validation challenges, confidence scores, final authorization, and operational outcomes.
          </p>
        </div>

        <div className="relative rounded-[2rem] border border-white/10 bg-black p-8">
          <div className="absolute bottom-12 left-12 top-12 w-px bg-gradient-to-b from-cyan-300 via-indigo-400 to-amber-300" />
          <div className="space-y-6">
            {replaySteps.map(([time, event, detail], idx) => (
              <div key={event} className="relative flex gap-6">
                <div className={cx("z-10 grid h-9 w-9 shrink-0 place-items-center rounded-full border-2 bg-black", idx === replaySteps.length - 1 ? "border-cyan-300 shadow-[0_0_18px_rgba(34,211,238,.7)]" : "border-slate-700")}>
                  <span className="h-2.5 w-2.5 rounded-full bg-cyan-300" />
                </div>
                <div className="flex-1 rounded-2xl border border-white/10 bg-white/[0.035] p-5">
                  <div className="mb-2 flex flex-wrap gap-3">
                    <span className="font-mono text-xs text-slate-500">{time}</span>
                    <span className="text-xs font-black uppercase tracking-widest text-cyan-300">{event}</span>
                  </div>
                  <p className="text-slate-300">{detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
