import { NavLink } from "react-router-dom";
import { GlobeLock, Play } from "lucide-react";
import { cx } from "../lib/cx";

const navItems = [
  ["/", "Platform"],
  ["/simulator", "Simulator"],
  ["/engine", "Engine"],
  ["/control-plane", "Control Plane"],
  ["/divisions", "Divisions"],
  ["/governance", "Governance"],
  ["/blog", "Blog"],
];

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-black/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <NavLink to="/" className="flex items-center gap-3" aria-label="MIZOKI3 home">
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-cyan-300/40 bg-cyan-400/10 shadow-[0_0_25px_rgba(34,211,238,.16)]">
            <GlobeLock className="h-5 w-5 text-cyan-300" />
          </div>
          <div className="text-lg font-black tracking-[0.22em] text-white">
            MIZOKI<span className="text-cyan-300">3</span>
          </div>
        </NavLink>

        <nav className="hidden gap-6 text-[11px] font-black uppercase tracking-[0.20em] text-slate-400 xl:flex">
          {navItems.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cx("transition-colors hover:text-cyan-300", isActive && "text-cyan-300")
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <NavLink
          to="/simulator"
          className="inline-flex items-center gap-2 rounded-xl bg-amber-300 px-5 py-2.5 text-xs font-black uppercase tracking-wider text-black transition-all hover:bg-amber-200"
        >
          Launch Console <Play className="h-3.5 w-3.5 fill-current" />
        </NavLink>
      </div>
    </header>
  );
}
