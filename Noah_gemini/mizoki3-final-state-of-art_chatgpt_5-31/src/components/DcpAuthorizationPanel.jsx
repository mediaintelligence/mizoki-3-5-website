import { motion } from "framer-motion";
import { Lock } from "lucide-react";
import { SurfaceCard } from "./SurfaceCard";
import { cx } from "../lib/cx";

export function DcpAuthorizationPanel({ confidence = 94 }) {
  const humanEscalation = confidence >= 80 ? "NO" : "YES";
  const status = confidence >= 90 ? "EXECUTE" : confidence >= 80 ? "REVIEW" : "ESCALATE";

  const rows = [
    ["Context Sufficiency", "PASS", "text-emerald-300"],
    ["Identity / RBAC", "ATTESTED", "text-emerald-300"],
    ["Policy Alignment", confidence >= 80 ? "PASS" : "REVIEW", confidence >= 80 ? "text-emerald-300" : "text-amber-300"],
    ["Regulatory Exposure", confidence >= 75 ? "LOW" : "ELEVATED", confidence >= 75 ? "text-cyan-300" : "text-red-300"],
    ["Human Escalation", humanEscalation, humanEscalation === "NO" ? "text-amber-300" : "text-red-300"],
    ["Authorization Status", status, status === "EXECUTE" ? "text-white" : "text-amber-300"],
  ];

  return (
    <SurfaceCard className="border-cyan-400/20 bg-black/45 p-6 shadow-[0_0_60px_rgba(6,182,212,.08)] backdrop-blur-md">
      <div className="mb-5 flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.28em] text-cyan-300">Decision Control Plane</div>
          <h3 className="mt-1 text-xl font-black text-white">Execution Authorization</h3>
        </div>
        <Lock className="h-6 w-6 text-amber-300" />
      </div>

      <div className="space-y-3 font-mono text-xs">
        {rows.map(([label, value, color]) => (
          <div key={label} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <span className="text-slate-400">{label}</span>
            <span className={cx("font-black", color)}>{value}</span>
          </div>
        ))}
      </div>

      <div className="mt-5 rounded-xl border border-amber-300/20 bg-amber-300/10 p-4">
        <div className="mb-2 flex items-center justify-between text-xs font-black uppercase tracking-widest text-amber-200">
          <span>Authority Threshold</span>
          <span>{confidence}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-slate-900">
          <motion.div className="h-full rounded-full bg-amber-300" initial={{ width: "0%" }} animate={{ width: `${confidence}%` }} transition={{ duration: 1.2 }} />
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-4 text-xs leading-6 text-slate-400">
        Autonomous execution remains blocked unless context, identity, policy, confidence, risk, authority, and audit gates resolve cleanly.
      </div>
    </SurfaceCard>
  );
}
