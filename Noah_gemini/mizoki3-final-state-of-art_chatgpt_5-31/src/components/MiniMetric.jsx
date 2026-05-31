import { motion } from "framer-motion";
import { cx } from "../lib/cx";

export function MiniMetric({ label, value, color = "bg-cyan-300", width = "80%" }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2 flex justify-between text-xs font-mono text-slate-400">
        <span>{label}</span>
        <span className="text-white">{value}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-900">
        <motion.div className={cx("h-full rounded-full", color)} initial={{ width: 0 }} animate={{ width }} transition={{ duration: 1 }} />
      </div>
    </div>
  );
}
