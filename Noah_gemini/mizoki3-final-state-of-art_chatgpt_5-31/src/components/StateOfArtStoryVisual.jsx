import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  FileCheck,
  Network,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { SurfaceCard } from "./SurfaceCard";

const arc = [
  {
    label: "Signal Pressure",
    title: "The enterprise feels the event first.",
    body: "Telemetry, contracts, customers, market movement, risk, and media signals arrive continuously.",
    icon: AlertTriangle,
  },
  {
    label: "Causal World Model",
    title: "The graph asks why it matters.",
    body: "The TCKG connects events to obligations, dependencies, precedent, exposure, and outcomes.",
    icon: Network,
  },
  {
    label: "Options & Counterfactuals",
    title: "Agents build competing futures.",
    body: "Multiple paths are proposed, scored, rejected, modified, or escalated before action.",
    icon: BrainCircuit,
  },
  {
    label: "Authority Gate",
    title: "The DCP decides what is allowed.",
    body: "Context, identity, policy, risk, confidence, and authority thresholds must resolve cleanly.",
    icon: ShieldCheck,
  },
  {
    label: "Governed Action",
    title: "Execution happens only after clearance.",
    body: "Approved workflows execute through APIs and operating systems with circuit breakers and trace IDs.",
    icon: Zap,
  },
  {
    label: "Replay & Learn",
    title: "The outcome becomes memory.",
    body: "The decision is replayable, measurable, and fed back into policies, weights, and graph memory.",
    icon: FileCheck,
  },
];

export function StateOfArtStoryVisual() {
  return (
    <section className="relative overflow-hidden bg-black px-6 py-24">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_25%,rgba(34,211,238,.12),transparent_30%),radial-gradient(circle_at_80%_60%,rgba(245,158,11,.10),transparent_35%)]" />
      <div className="relative z-10 mx-auto max-w-7xl">
        <div className="mb-14 max-w-4xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">State-of-the-Art Storytelling System</p>
          <h2 className="mt-4 text-4xl font-black md:text-6xl">The story is no longer “AI automation.” The story is permissioned enterprise cognition.</h2>
          <p className="mt-5 text-lg leading-8 text-slate-300">
            The visual system should make one idea impossible to miss: MIZOKI3 does not merely recommend action. It proves whether action is allowed.
          </p>
        </div>

        <div className="relative">
          <div className="absolute left-6 right-6 top-12 hidden h-px bg-gradient-to-r from-cyan-300/0 via-cyan-300/40 to-amber-300/0 lg:block" />
          <div className="grid gap-5 lg:grid-cols-6">
            {arc.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.label}
                  initial={{ opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-80px" }}
                  transition={{ duration: 0.45, delay: index * 0.06 }}
                >
                  <SurfaceCard className="relative h-full p-5">
                    <div className="mb-5 flex items-center justify-between">
                      <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10">
                        <Icon className="h-6 w-6 text-cyan-300" />
                      </div>
                      <span className="font-mono text-xs text-slate-600">0{index + 1}</span>
                    </div>
                    <p className="text-xs font-black uppercase tracking-widest text-amber-300">{step.label}</p>
                    <h3 className="mt-3 text-lg font-black leading-tight text-white">{step.title}</h3>
                    <p className="mt-3 text-sm leading-6 text-slate-400">{step.body}</p>
                  </SurfaceCard>
                </motion.div>
              );
            })}
          </div>
        </div>

        <div className="mt-10 rounded-[2rem] border border-cyan-300/20 bg-cyan-300/5 p-6">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Final Narrative Rule</p>
              <h3 className="mt-2 text-2xl font-black text-white">
                Every visual must prove one of four things: causality, authorization, traceability, or learning.
              </h3>
            </div>
            <CheckCircle2 className="h-10 w-10 shrink-0 text-emerald-300" />
          </div>
        </div>
      </div>
    </section>
  );
}
