import { useEffect, useState } from 'react';
import { ArrowRight, Play, Activity, GitMerge } from 'lucide-react';

function useTicker(base, jitter, intervalMs) {
  const [v, setV] = useState(base);
  useEffect(() => {
    const id = setInterval(() => setV((x) => x + Math.floor(Math.random() * jitter) + 1), intervalMs);
    return () => clearInterval(id);
  }, [base, jitter, intervalMs]);
  return v;
}

export default function Hero() {
  const signals = useTicker(18742, 6, 3200);
  const links = useTicker(8430000, 800, 2400);

  return (
    <section id="platform" className="relative pt-[148px] pb-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="grid grid-cols-1 xl:grid-cols-[1.05fr_1fr] gap-14 items-center">
          <div className="reveal">
            <div className="eyebrow mb-6 text-accent">Autonomous Strategic Intelligence Infrastructure</div>
            <h1 className="text-[clamp(2.6rem,5.4vw,4.5rem)] font-bold leading-[1.05] tracking-tight mb-7">
              One Intelligence.<br />
              Many Domains.<br />
              <span className="bg-gradient-to-r from-counsel to-[#5b8cff] bg-clip-text text-transparent">
                Shared Causal Memory.
              </span>
            </h1>
            <p className="text-[1.06rem] text-ink-2 max-w-[560px] mb-8 leading-relaxed">
              MIZOKI3 unifies legal, financial, operational, and customer intelligence — and every other
              corporate division — into a single autonomous decision system. Built on a Temporal-Causal
              Knowledge Graph and governed by a Decision Control Plane that separates proposal from
              authorization and refuses to act on correlation alone.
            </p>
            <div className="flex flex-wrap gap-3.5 mb-10">
              <a href="#flywheel"
                 className="inline-flex items-center gap-2.5 px-5 py-3 rounded-lg text-[0.9rem] font-semibold bg-gradient-to-br from-accent to-[#9d6bff] text-white shadow-[0_10px_34px_-10px_rgba(124,92,255,0.7)] hover:-translate-y-px transition-all">
                Explore the Platform <ArrowRight className="w-3.5 h-3.5" />
              </a>
              <a href="#orchestration"
                 className="inline-flex items-center gap-2.5 px-5 py-3 rounded-lg text-[0.9rem] font-semibold bg-white/[0.04] border border-white/15 text-ink hover:border-nexus transition-all">
                <span className="w-6 h-6 rounded-full bg-white/8 border border-white/15 grid place-items-center">
                  <Play className="w-2.5 h-2.5" />
                </span>
                Watch Overview
              </a>
            </div>
            <div className="flex flex-wrap gap-6 pt-7 border-t border-white/[0.07]">
              {[
                { d: '#21d07a', t: 'Zero-Trust Deployment' },
                { d: '#21d07a', t: 'Customer-Managed Encryption' },
                { d: '#21d07a', t: 'Audit-Ready by Default' },
              ].map((b) => (
                <span key={b.t} className="font-mono text-[0.72rem] text-ink-3 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-estate shadow-[0_0_8px_#21d07a]" />
                  {b.t}
                </span>
              ))}
            </div>
          </div>

          <div className="reveal relative aspect-square">
            <svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"
                 className="w-full h-full" style={{ filter: 'drop-shadow(0 0 50px rgba(76,201,255,0.28))' }}>
              <defs>
                <radialGradient id="brainCore" cx="50%" cy="50%" r="50%">
                  <stop offset="0%"   stopColor="#fff" stopOpacity="0.95" />
                  <stop offset="35%"  stopColor="#4cc9ff" stopOpacity="0.75" />
                  <stop offset="100%" stopColor="#4cc9ff" stopOpacity="0" />
                </radialGradient>
              </defs>
              <circle cx="300" cy="300" r="250" fill="none" stroke="rgba(120,150,230,0.08)" />
              <circle cx="300" cy="300" r="180" fill="none" stroke="rgba(120,150,230,0.10)" />
              <g strokeWidth="1.2" fill="none" opacity="0.5">
                <line x1="300" y1="300" x2="300" y2="110" stroke="#a855f7" />
                <line x1="300" y1="300" x2="135" y2="215" stroke="#21d07a" />
                <line x1="300" y1="300" x2="465" y2="215" stroke="#34a6ff" />
                <line x1="300" y1="300" x2="175" y2="445" stroke="#f5a623" />
                <line x1="300" y1="300" x2="425" y2="445" stroke="#f4495f" />
              </g>
              <circle cx="300" cy="300" r="95" fill="url(#brainCore)" opacity="0.6" />
              <circle cx="300" cy="300" r="56" fill="#070b1c" stroke="rgba(76,201,255,0.5)" strokeWidth="1.5" />
              <circle cx="300" cy="300" r="56" fill="none" stroke="#4cc9ff" strokeWidth="1" opacity="0">
                <animate attributeName="r" from="56" to="120" dur="3.5s" repeatCount="indefinite" />
                <animate attributeName="opacity" from="0.6" to="0" dur="3.5s" repeatCount="indefinite" />
              </circle>
              <text x="300" y="296" fontFamily="Sora" fontSize="20" fontWeight="700" fill="#fff" textAnchor="middle">NEXUS</text>
              <text x="300" y="316" fontFamily="JetBrains Mono" fontSize="9" fill="#9aa6c8" textAnchor="middle" letterSpacing="1.5">THE BRAIN</text>

              <g>
                <circle cx="300" cy="110" r="30" fill="#070b1c" stroke="#a855f7" strokeWidth="1.6" />
                <text x="300" y="62" fontFamily="Sora" fontSize="13" fontWeight="600" fill="#fff" textAnchor="middle">COUNSEL</text>
                <text x="300" y="78" fontFamily="Inter" fontSize="9.5" fill="#9aa6c8" textAnchor="middle">Legal Intelligence</text>
              </g>
              <g>
                <circle cx="135" cy="215" r="30" fill="#070b1c" stroke="#21d07a" strokeWidth="1.6" />
                <text x="135" y="166" fontFamily="Sora" fontSize="13" fontWeight="600" fill="#fff" textAnchor="middle">ESTATE</text>
                <text x="135" y="182" fontFamily="Inter" fontSize="9.5" fill="#9aa6c8" textAnchor="middle">Wealth &amp; Trust</text>
              </g>
              <g>
                <circle cx="465" cy="215" r="30" fill="#070b1c" stroke="#34a6ff" strokeWidth="1.6" />
                <text x="465" y="166" fontFamily="Sora" fontSize="13" fontWeight="600" fill="#fff" textAnchor="middle">CAPITAL</text>
                <text x="465" y="182" fontFamily="Inter" fontSize="9.5" fill="#9aa6c8" textAnchor="middle">Financial &amp; Banking</text>
              </g>
              <g>
                <circle cx="175" cy="445" r="30" fill="#070b1c" stroke="#f5a623" strokeWidth="1.6" />
                <circle cx="175" cy="445" r="11" fill="none" stroke="#f5a623" strokeWidth="1.6" />
                <circle cx="175" cy="445" r="3" fill="#f5a623" />
                <text x="175" y="498" fontFamily="Sora" fontSize="13" fontWeight="600" fill="#fff" textAnchor="middle">SIGNAL</text>
                <text x="175" y="514" fontFamily="Inter" fontSize="9.5" fill="#9aa6c8" textAnchor="middle">Acquisition &amp; Customer</text>
              </g>
              <g>
                <circle cx="425" cy="445" r="30" fill="#070b1c" stroke="#f4495f" strokeWidth="1.6" />
                <text x="425" y="498" fontFamily="Sora" fontSize="13" fontWeight="600" fill="#fff" textAnchor="middle">RISK</text>
                <text x="425" y="514" fontFamily="Inter" fontSize="9.5" fill="#9aa6c8" textAnchor="middle">Verification &amp; Compliance</text>
              </g>
            </svg>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-col gap-2 absolute bottom-6 left-7 font-mono text-[0.72rem] text-ink-3">
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3 text-signal" /> Active Signals: <span className="text-ink tabular-nums">{signals.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2">
          <GitMerge className="w-3 h-3 text-nexus" /> Causal Links: <span className="text-ink tabular-nums">{(links / 1_000_000).toFixed(2)}M</span>
        </div>
      </div>
    </section>
  );
}
