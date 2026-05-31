import { motion } from "framer-motion";
import { BrainCircuit } from "lucide-react";
import { cx } from "../lib/cx";
import { KnowledgeGraphBackground } from "./KnowledgeGraphBackground";

export function LivingEnterpriseVisual() {
  const systems = [
    ["ERP", "left-[8%] top-[21%]", "cyan"],
    ["CRM", "left-[18%] top-[70%]", "amber"],
    ["SIEM", "right-[10%] top-[17%]", "cyan"],
    ["Legal", "right-[19%] top-[72%]", "amber"],
    ["Data Lake", "left-[42%] bottom-[7%]", "cyan"],
    ["Media", "left-[44%] top-[7%]", "amber"],
  ];

  return (
    <div className="relative min-h-[560px] overflow-hidden rounded-[2rem] border border-cyan-400/20 bg-[#020711] shadow-2xl">
      <KnowledgeGraphBackground opacity="opacity-35" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_48%,rgba(34,211,238,.22),transparent_28%),linear-gradient(135deg,#020617_0%,#06111f_55%,#000_100%)]" />

      <svg className="absolute inset-0 h-full w-full opacity-80" viewBox="0 0 1000 560" preserveAspectRatio="none">
        {[
          "M100 145 C260 205, 370 250, 500 280",
          "M200 420 C340 360, 405 310, 500 280",
          "M880 125 C690 180, 610 235, 500 280",
          "M805 430 C690 365, 610 315, 500 280",
          "M500 520 C500 410, 500 350, 500 280",
          "M500 55 C500 140, 500 215, 500 280",
        ].map((d, i) => (
          <motion.path
            key={d}
            d={d}
            fill="none"
            stroke={i % 2 ? "rgba(245,158,11,.78)" : "rgba(34,211,238,.86)"}
            strokeWidth="1.6"
            strokeDasharray="8 12"
            animate={{ strokeDashoffset: [0, -120] }}
            transition={{ duration: 4 + i, repeat: Infinity, ease: "linear" }}
          />
        ))}
      </svg>

      <motion.div
        className="absolute left-1/2 top-1/2 h-80 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/35"
        animate={{ rotate: 360 }}
        transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute left-1/2 top-1/2 h-[28rem] w-[28rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-amber-300/20"
        animate={{ rotate: -360 }}
        transition={{ duration: 42, repeat: Infinity, ease: "linear" }}
      />

      <div className="absolute left-1/2 top-1/2 grid h-44 w-44 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-cyan-300/60 bg-black/60 text-center shadow-[0_0_90px_rgba(34,211,238,.35)] backdrop-blur-md">
        <BrainCircuit className="mx-auto mb-2 h-10 w-10 text-cyan-200" />
        <div className="text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-400">Shared Memory</div>
        <div className="text-sm font-black uppercase tracking-[0.18em] text-white">TCKG Core</div>
      </div>

      {systems.map(([label, pos, color]) => (
        <div key={label} className={cx("absolute rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-md", pos)}>
          <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Connected</div>
          <div className="font-bold text-white">{label}</div>
          <div className={cx("mt-2 h-1 rounded-full", color === "cyan" ? "bg-cyan-300" : "bg-amber-300")} />
        </div>
      ))}

      <div className="absolute bottom-5 left-5 right-5 grid gap-3 md:grid-cols-4">
        {["No rip-and-replace", "Shared system memory", "Threshold-aware action", "Immutable trace"].map((m) => (
          <div key={m} className="rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-xs font-bold text-slate-200 backdrop-blur-md">
            {m}
          </div>
        ))}
      </div>
    </div>
  );
}
