export default function Footer() {
  return (
    <footer className="border-t border-white/[0.08] py-12 mt-10">
      <div className="max-w-[1340px] mx-auto px-7 grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span aria-hidden className="inline-block w-2 h-2 rounded-full bg-nexus shadow-[0_0_10px_#4cc9ff]" />
            <span className="font-mono font-bold tracking-[0.2em] text-sm">
              MIZOKI<span className="text-nexus">3</span>
            </span>
          </div>
          <p className="text-xs text-ink-3 leading-relaxed max-w-xs">
            Autonomous Strategic Intelligence Infrastructure. Built on Google Cloud.
            Owned by you.
          </p>
        </div>

        <div className="font-mono text-[0.66rem] uppercase tracking-[0.16em] text-ink-3 flex flex-col gap-2">
          <a href="#manifesto" className="hover:text-nexus transition-colors">Premise</a>
          <a href="#veto" className="hover:text-nexus transition-colors">Verification & Arbitration</a>
          <a href="#divisions" className="hover:text-nexus transition-colors">Divisions</a>
          <a href="#infrastructure" className="hover:text-nexus transition-colors">Infrastructure</a>
          <a href="/console/index.html" className="hover:text-nexus transition-colors">Operations Console →</a>
        </div>

        <div className="font-mono text-[0.66rem] uppercase tracking-[0.16em] text-ink-3 md:text-right">
          <div className="mb-2">© 2026 MIZOKI3, Inc.</div>
          <div className="text-ink-4 mb-2">Miami · Connecticut</div>
          <a href="mailto:hello@mizoki3.com" className="hover:text-nexus transition-colors">hello@mizoki3.com</a>
        </div>
      </div>
    </footer>
  );
}
