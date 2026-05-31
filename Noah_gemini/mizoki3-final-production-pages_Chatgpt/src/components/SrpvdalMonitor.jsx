import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { cx } from "../lib/cx";
import { srpvdalNodes } from "../data/siteData";
import { SurfaceCard } from "./SurfaceCard";
import { MiniMetric } from "./MiniMetric";

export function SrpvdalMonitor() {
  const [activeNode, setActiveNode] = useState(0);
  const active = srpvdalNodes[activeNode];
  const ActiveIcon = active.icon;

  useEffect(() => {
    const timer = setInterval(() => setActiveNode((prev) => (prev + 1) % srpvdalNodes.length), 3200);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="bg-[#010102] px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Cognitive Framework</p>
            <h2 className="mt-4 text-4xl font-black md:text-6xl">The SRPVDAL Engine</h2>
          </div>
          <p className="max-w-xl leading-8 text-slate-400">
            Every business signal moves through a deterministic seven-stage operational loop: Sense, Reason, Plan, Validate / Verify, Decide, Act, and Learn.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-12">
          <div className="space-y-3 lg:col-span-5">
            {srpvdalNodes.map((node, idx) => {
              const Icon = node.icon;
              const isActive = activeNode === idx;
              return (
                <button
                  key={node.id}
                  onClick={() => setActiveNode(idx)}
                  className={cx(
                    "w-full rounded-xl border p-4 text-left transition-all duration-300",
                    isActive ? "border-cyan-400/50 bg-cyan-950/25 shadow-[0_0_35px_rgba(6,182,212,.08)]" : "border-white/10 bg-white/[0.02] hover:border-white/20"
                  )}
                >
                  <div className="flex items-center gap-4">
                    <div className={cx("grid h-11 w-11 place-items-center rounded-xl", isActive ? "bg-cyan-300 text-black" : "border border-white/10 bg-black/40 text-slate-500")}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between gap-4">
                        <h3 className={cx("font-black", isActive ? "text-white" : "text-slate-400")}>0{idx + 1}. {node.name}</h3>
                        <span className={cx("rounded-full px-2 py-1 text-[10px] font-mono", isActive ? "bg-cyan-300/10 text-cyan-200" : "text-slate-600")}>
                          {node.phase}
                        </span>
                      </div>
                    </div>
                    <ChevronRight className={cx("h-4 w-4", isActive ? "text-cyan-300" : "text-slate-700")} />
                  </div>
                </button>
              );
            })}
          </div>

          <SurfaceCard className="relative min-h-[500px] overflow-hidden bg-gradient-to-b from-slate-950 to-black p-8 lg:col-span-7">
            <motion.div className="absolute left-0 top-0 h-px w-full bg-gradient-to-r from-transparent via-cyan-300 to-transparent" animate={{ y: [0, 500], opacity: [0, 1, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} />
            <div className="flex items-center justify-between border-b border-white/10 pb-4 font-mono text-[10px] uppercase tracking-widest text-slate-500">
              <span>Cognitive Step Monitor</span>
              <span>Trace Verified</span>
            </div>

            <div className="my-12 flex items-start gap-5">
              <div className="grid h-16 w-16 place-items-center rounded-2xl border border-cyan-400/30 bg-cyan-400/10 text-cyan-200">
                <ActiveIcon className="h-8 w-8" />
              </div>
              <div>
                <p className="text-xs font-mono uppercase tracking-[0.24em] text-cyan-300">Function 0{activeNode + 1}</p>
                <h3 className="mt-2 text-4xl font-black">{active.name} Module</h3>
                <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">{active.desc}</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <MiniMetric label="Causal Confidence" value="94.2%" color="bg-amber-300" width="94%" />
              <MiniMetric label="Decision Latency" value="142ms" color="bg-cyan-300" width="72%" />
              <MiniMetric label="Policy Alignment" value="100%" color="bg-emerald-300" width="100%" />
            </div>
          </SurfaceCard>
        </div>
      </div>
    </section>
  );
}
