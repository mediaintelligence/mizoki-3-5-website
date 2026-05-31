import { NavLink } from "react-router-dom";

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black px-6 py-10">
      <div className="mx-auto flex max-w-7xl flex-col justify-between gap-6 text-xs text-slate-500 md:flex-row md:items-center">
        <div>
          <div className="text-lg font-black tracking-wide text-white">
            MIZ<span className="text-amber-300">OKI3</span>
          </div>
          <div className="mt-2 font-medium tracking-wide">Autonomous Decision Intelligence Infrastructure</div>
        </div>
        <div className="flex flex-wrap gap-6">
          <NavLink to="/" className="transition-colors hover:text-white">Platform</NavLink>
          <NavLink to="/simulator" className="transition-colors hover:text-white">Simulator</NavLink>
          <NavLink to="/control-plane" className="transition-colors hover:text-white">Control Plane</NavLink>
          <NavLink to="/governance" className="transition-colors hover:text-white">Governance</NavLink>
          <NavLink to="/review" className="transition-colors hover:text-white">Review</NavLink>
          <NavLink to="/story" className="transition-colors hover:text-white">Story</NavLink>
          <NavLink to="/blog" className="transition-colors hover:text-white">Blog</NavLink>
        </div>
        <div className="tabular-nums">© 2026 MIZOKI3. All security logs fully reserved.</div>
      </div>
    </footer>
  );
}
