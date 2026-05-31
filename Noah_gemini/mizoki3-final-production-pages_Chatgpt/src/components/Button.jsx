import { cx } from "../lib/cx";

export function Button({ children, className = "", variant = "primary", ...props }) {
  const variants = {
    primary: "bg-white text-black hover:bg-slate-100 shadow-[0_8px_40px_rgba(255,255,255,.14)]",
    amber: "bg-amber-300 text-black hover:bg-amber-200 shadow-[0_8px_38px_rgba(245,158,11,.20)]",
    outline: "border border-white/15 bg-white/[0.025] text-white hover:bg-white/[0.075]",
    cyan: "border border-cyan-300/30 bg-cyan-300/10 text-cyan-100 hover:bg-cyan-300/15",
  };

  return (
    <button
      className={cx(
        "inline-flex items-center justify-center rounded-xl px-6 py-3 text-xs font-black uppercase tracking-[0.18em] transition-all duration-300 hover:-translate-y-0.5",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
