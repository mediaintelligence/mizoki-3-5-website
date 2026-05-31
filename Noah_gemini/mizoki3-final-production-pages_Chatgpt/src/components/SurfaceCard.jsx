import { cx } from "../lib/cx";

export function SurfaceCard({ children, className = "" }) {
  return (
    <div
      className={cx(
        "rounded-2xl border border-white/10 bg-white/[0.035] shadow-[0_18px_80px_rgba(0,0,0,.22)]",
        className
      )}
    >
      {children}
    </div>
  );
}
