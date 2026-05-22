import { useEffect, useState } from 'react';
import { Canvas } from './Overview.jsx';

const NODES = [
  { x: 260, y: 40,  label: 'Acme Holdings', sub: 'Parent Entity',    c: '#4cc9ff' },
  { x: 120, y: 140, label: 'Counsel',       sub: '12 contracts',     c: '#a855f7' },
  { x: 260, y: 140, label: 'Capital',       sub: '$12.0M reserves',  c: '#34a6ff' },
  { x: 400, y: 140, label: 'Estate',        sub: '3 trusts',         c: '#21d07a' },
  { x: 260, y: 240, label: 'Risk · V&A',    sub: 'authoritative',    c: '#f4495f' },
];

const EDGES = [
  [260, 40, 120, 140],
  [260, 40, 260, 140],
  [260, 40, 400, 140],
  [120, 140, 260, 240],
  [260, 140, 260, 240],
  [400, 140, 260, 240],
  [120, 140, 400, 140],
];

const STATS = [
  { k: 'Nodes resident',  v: '14,291', c: 'text-nexus' },
  { k: 'Causal links',    v: '8.43M',  c: 'text-counsel' },
  { k: 'Domains unified', v: '5 + 8',  c: 'text-estate' },
  { k: 'Veto authority',  v: 'Risk',   c: 'text-risk' },
];

export default function Nexus() {
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setPulse((p) => (p + 1) % NODES.length), 1400);
    return () => clearInterval(id);
  }, []);

  return (
    <section id="nexus" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[820px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">08</span>
            <span>The Central Nervous System</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            One Nexus. <em className="serif-i">Every cell connected.</em>
          </h2>
          <div className="text-ink-3 text-base">
            Every division writes to and reads from the Nexus. Counsel updates ripple
            to Estate; Capital telemetry informs Signal; Risk holds the veto. Insight
            in any domain becomes intelligence in all.
          </div>
        </div>

        <Canvas src="/assets/11-nexus.png"
                alt="MIZOKI3 Nexus — the central nervous system connecting every division"
                cap="The Nexus · shared substrate · cross-domain propagation"
                glow="rgba(76,201,255,0.32)" />

        <div className="mt-14 grid grid-cols-1 lg:grid-cols-5 gap-5 max-w-[1180px] mx-auto">
          <div className="lg:col-span-3 reveal relative rounded-2xl border border-white/[0.08] bg-bg-1/40 p-6 overflow-hidden">
            <div className="absolute top-0 left-0 right-0 scanline" />
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono text-[0.66rem] uppercase tracking-[0.18em] text-nexus">
                Live Snapshot · Acme Holdings
              </div>
              <div className="font-mono text-[0.6rem] text-ink-4 flex items-center gap-2">
                <span aria-hidden className="inline-block w-2 h-2 rounded-full bg-estate animate-pulse" />
                NEXUS ACTIVE
              </div>
            </div>

            <svg viewBox="0 0 520 280" className="w-full h-auto">
              <defs>
                <marker id="nx-arr" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 z" fill="#46506e" />
                </marker>
              </defs>

              {EDGES.map(([ax, ay, bx, by], i) => (
                <line key={i} x1={ax} y1={ay} x2={bx} y2={by}
                      stroke="#46506e" strokeWidth="1.3" strokeDasharray="3 4"
                      markerEnd="url(#nx-arr)"
                      opacity={pulse === i % NODES.length ? 1 : 0.45}
                      style={{ transition: 'opacity 0.6s' }} />
              ))}

              {NODES.map((n, i) => (
                <g key={i}>
                  <circle cx={n.x} cy={n.y} r={pulse === i ? 32 : 22}
                          fill="none" stroke={n.c} strokeWidth="1"
                          opacity={pulse === i ? 0.5 : 0}
                          style={{ transition: 'all 0.6s' }} />
                  <circle cx={n.x} cy={n.y} r="22" fill="#070b1c" stroke={n.c} strokeWidth="1.5" />
                  <text x={n.x} y={n.y + 4} textAnchor="middle" fill="#f3f5fc"
                        fontSize="9" fontFamily="JetBrains Mono">{n.label}</text>
                  <text x={n.x} y={n.y + 40} textAnchor="middle" fill="#6c7799"
                        fontSize="8.5" fontFamily="JetBrains Mono">{n.sub}</text>
                </g>
              ))}
            </svg>
          </div>

          <div className="lg:col-span-2 reveal flex flex-col gap-4">
            {STATS.map((s) => (
              <div key={s.k}
                   className="p-5 rounded-xl border border-white/10 bg-bg-1/40 flex items-baseline justify-between">
                <span className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-ink-3">{s.k}</span>
                <span className={`font-display text-xl font-semibold ${s.c}`}>{s.v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
