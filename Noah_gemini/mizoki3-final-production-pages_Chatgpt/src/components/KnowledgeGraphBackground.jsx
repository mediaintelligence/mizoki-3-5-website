import { motion } from "framer-motion";
import { cx } from "../lib/cx";

export function KnowledgeGraphBackground({ opacity = "opacity-30" }) {
  return (
    <div className={cx("pointer-events-none absolute inset-0 overflow-hidden", opacity)}>
      <motion.div
        className="absolute left-1/4 top-1/4 h-[32rem] w-[32rem] rounded-full bg-cyan-600/30 blur-[140px]"
        animate={{ opacity: [0.32, 0.62, 0.32] }}
        transition={{ duration: 6, repeat: Infinity }}
      />
      <motion.div
        className="absolute right-1/4 top-1/2 h-[36rem] w-[36rem] rounded-full bg-indigo-900/40 blur-[160px]"
        animate={{ opacity: [0.22, 0.54, 0.22] }}
        transition={{ duration: 7.5, repeat: Infinity, delay: 1.2 }}
      />
      <motion.div
        className="absolute bottom-1/4 left-1/3 h-[28rem] w-[28rem] rounded-full bg-amber-600/20 blur-[130px]"
        animate={{ opacity: [0.18, 0.42, 0.18] }}
        transition={{ duration: 8, repeat: Infinity, delay: 2.1 }}
      />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(30,41,59,.85)_1px,transparent_1px),linear-gradient(to_bottom,rgba(30,41,59,.85)_1px,transparent_1px)] bg-[size:5rem_5rem] opacity-30 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]" />
    </div>
  );
}
