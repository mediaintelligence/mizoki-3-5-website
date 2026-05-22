import { ArrowRight } from 'lucide-react';

const LINKS = [
  { href: '#platform',       label: 'Platform' },
  { href: '#flywheel',       label: 'Flywheel' },
  { href: '#orchestration',  label: 'Orchestration' },
  { href: '#divisions',      label: 'Divisions' },
  { href: '#nexus',          label: 'Nexus' },
  { href: '#governance',     label: 'Governance' },
  { href: '#infrastructure', label: 'Architecture' },
];

export default function Nav() {
  return (
    <header className="fixed inset-x-0 top-0 z-[100] bg-bg-0/80 backdrop-blur-xl border-b border-white/[0.07]">
      <div className="max-w-[1480px] mx-auto px-7 h-[72px] flex items-center justify-between">
        <a href="#platform" className="font-display font-bold text-[1.4rem] tracking-tight">
          MIZOKI<span className="text-nexus">3</span>
        </a>
        <ul className="hidden xl:flex gap-6 list-none">
          {LINKS.map((l) => (
            <li key={l.href}>
              <a href={l.href} data-nav-link
                 className="text-[0.85rem] font-medium text-ink-2 hover:text-ink transition-colors [&.active]:text-ink">
                {l.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-4">
          <a href="#contact" className="hidden sm:inline text-[0.85rem] font-medium text-ink-2 hover:text-ink transition">
            Sign In
          </a>
          <a href="#contact"
             className="inline-flex items-center gap-2 px-5 py-3 rounded-lg text-[0.85rem] font-semibold bg-gradient-to-br from-accent to-[#9d6bff] text-white shadow-[0_10px_34px_-10px_rgba(124,92,255,0.7)] hover:-translate-y-px hover:shadow-[0_16px_42px_-10px_rgba(124,92,255,0.9)] transition-all">
            Request Enterprise Pilot <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </header>
  );
}
