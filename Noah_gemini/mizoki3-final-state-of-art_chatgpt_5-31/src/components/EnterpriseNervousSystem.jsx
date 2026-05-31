import { motion } from "framer-motion";
import { Workflow } from "lucide-react";

export function EnterpriseNervousSystem() {
  const nodes = ["ERP", "CRM", "SIEM", "Data Lake", "Legal", "Media", "Finance", "Ops"];

  return (
    <div className="relative min-h-[420px] overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_center,rgba(34,211,238,.18),rgba(255,255,255,.03)_45%,rgba(0,0,0,.4))] p-8">
      <div className="relative z-10">
        <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Enterprise Nervous System</p>
        <h2 className="mt-4 max-w-xl text-4xl font-black">One shared brain across every operating lens.</h2>
      </div>

      <div className="relative z-10 mt-9 grid gap-4 sm:grid-cols-2">
        {nodes.map((x) => (
          <motion.div key={x} className="rounded-xl border border-white/10 bg-black/30 p-4 font-mono text-sm text-slate-300" whileHover={{ y: -4 }} transition={{ duration: 0.2 }}>
            {x} <span className="text-cyan-300">→</span> Nexus Core
          </motion.div>
        ))}
      </div>

      <div className="absolute bottom-6 right-6 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-5">
        <Workflow className="mb-3 h-7 w-7 text-amber-300" />
        <div className="text-xs font-black uppercase tracking-widest text-amber-200">Plug-in architecture</div>
      </div>
    </div>
  );
}
