import { DIVISIONS, EXTENDED_DIVISIONS } from '../data.js';
import { Canvas } from './Overview.jsx';

const HEX = {
  counsel: '#a855f7',
  estate:  '#21d07a',
  capital: '#34a6ff',
  signal:  '#f5a623',
  risk:    '#f4495f',
};

const GLOW = {
  counsel: 'rgba(168,85,247,0.32)',
  estate:  'rgba(33,208,122,0.32)',
  capital: 'rgba(52,166,255,0.32)',
  signal:  'rgba(245,166,35,0.32)',
  risk:    'rgba(244,73,95,0.32)',
};

export default function Divisions() {
  return (
    <section id="divisions" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[820px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">07</span>
            <span>One Brain. Many Domain Lenses.</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            Five flagship divisions.{' '}
            <em className="serif-i">One shared substrate.</em>
          </h2>
          <div className="text-ink-3 text-base">
            The divisions are not modules — they are lenses on the same Nexus. A
            Counsel ingestion changes the Estate exposure in the same query path.
            Specialization without fragmentation.
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-[1180px] mx-auto">
          {DIVISIONS.map((d, i) => (
            <div
              key={d.key}
              className="reveal stagger group p-7 rounded-2xl border border-white/[0.08] bg-bg-1/40 hover:bg-bg-1/70 transition-all relative overflow-hidden"
              style={{ '--i': i }}
            >
              <div aria-hidden className="absolute top-0 left-0 right-0 h-px"
                   style={{ background: HEX[d.color], opacity: 0.65 }} />
              <div className="font-mono text-[0.62rem] uppercase tracking-[0.2em] mb-2"
                   style={{ color: HEX[d.color] }}>
                Division {String(i + 1).padStart(2, '0')}
              </div>
              <h3 className="font-display text-xl font-semibold mb-1">{d.name}</h3>
              <div className="text-ink-3 text-sm mb-4">{d.title}</div>
              <ul className="space-y-1.5 text-sm">
                {d.feats.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-ink-2">
                    <span aria-hidden className="mt-1.5 shrink-0 w-1 h-1 rounded-full"
                          style={{ background: HEX[d.color] }} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-16 max-w-[1180px] mx-auto reveal">
          <div className="text-center mb-7">
            <div className="eyebrow mb-2">Extensible by Design</div>
            <h3 className="text-[clamp(1.2rem,2vw,1.7rem)] font-semibold">
              Eight more domains, <em className="serif-i">same substrate.</em>
            </h3>
            <div className="text-ink-3 text-sm mt-2">
              Adding a domain doesn't add a tool. It adds a lens to the graph
              already running everything else.
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {EXTENDED_DIVISIONS.map((e, i) => (
              <div key={e.name}
                   className="reveal stagger p-4 rounded-lg border border-white/[0.06] bg-bg-1/30"
                   style={{ '--i': i }}>
                <div className="font-mono text-[0.6rem] uppercase tracking-[0.14em] text-nexus mb-1">{e.name}</div>
                <div className="text-ink-3 text-xs leading-relaxed">{e.blurb}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-20 space-y-20">
          {DIVISIONS.map((d, i) => (
            <DivisionDeepDive key={d.key} d={d} idx={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function DivisionDeepDive({ d, idx }) {
  const flip = idx % 2 === 1;
  return (
    <div className="reveal grid grid-cols-1 lg:grid-cols-12 gap-8 items-center max-w-[1180px] mx-auto">
      <div className={`lg:col-span-5 ${flip ? 'lg:col-start-8 lg:row-start-1' : ''}`}>
        <div className="font-mono text-[0.62rem] uppercase tracking-[0.2em] mb-3"
             style={{ color: HEX[d.color] }}>
          {d.name}
        </div>
        <h3 className="text-[clamp(1.3rem,2.2vw,1.9rem)] font-semibold mb-3 leading-tight">
          {d.deepHeading}
        </h3>
        <p className="text-ink-3 text-base leading-relaxed">{d.deepBody}</p>
      </div>
      <div className={`lg:col-span-7 ${flip ? 'lg:col-start-1 lg:row-start-1' : ''}`}>
        {d.img ? (
          <Canvas src={d.img} alt={`${d.name} — ${d.title}`}
                  cap={`${d.title} · ${d.name.replace('MIZOKI3 ', '')} lens`}
                  glow={GLOW[d.color]} />
        ) : (
          <CapitalChart />
        )}
      </div>
    </div>
  );
}

function CapitalChart() {
  const W = 540, H = 280, P = 40;
  const q = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6'];
  const reserves  = [12.4, 12.0, 11.6, 11.2, 10.9, 10.6];
  const afterDraw = [12.4, 12.0, 7.0, 6.4, 5.8, 5.2];
  const cov = 10.0;
  const yMin = 4, yMax = 13.5;
  const x = (i) => P + (i / (q.length - 1)) * (W - 2 * P);
  const y = (v) => H - P - ((v - yMin) / (yMax - yMin)) * (H - 2 * P);
  const path = (arr) => arr.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(v)}`).join(' ');
  const breachArea = `M ${x(2)} ${y(cov)} L ${x(2)} ${y(afterDraw[2])} L ${x(5)} ${y(afterDraw[5])} L ${x(5)} ${y(cov)} Z`;

  return (
    <div className="relative rounded-2xl border border-white/[0.08] bg-bg-1/40 p-6">
      <div className="font-mono text-[0.66rem] uppercase tracking-[0.18em] text-capital mb-2">
        Capital · Liquidity vs Covenant
      </div>
      <h4 className="text-base font-semibold mb-3">Projected breach · before V&A intervention</h4>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
        {[5, 7.5, 10, 12.5].map((g) => (
          <line key={g} x1={P} x2={W - P} y1={y(g)} y2={y(g)} stroke="#1c2543" strokeWidth="0.5" />
        ))}
        {[5, 7.5, 10, 12.5].map((g) => (
          <text key={`y-${g}`} x={P - 6} y={y(g) + 3} textAnchor="end" fontSize="9" fontFamily="JetBrains Mono" fill="#6c7799">
            ${g}M
          </text>
        ))}
        <path d={breachArea} fill="#f4495f" opacity="0.13" />
        <line x1={P} x2={W - P} y1={y(cov)} y2={y(cov)} stroke="#f5a623" strokeWidth="1.2" strokeDasharray="5 4" />
        <text x={W - P + 4} y={y(cov) + 4} fontSize="9.5" fontFamily="JetBrains Mono" fill="#f5a623">COV-01 floor $10M</text>
        <path d={path(reserves)} stroke="#34a6ff" strokeWidth="1.8" fill="none" />
        <path d={path(afterDraw)} stroke="#f4495f" strokeWidth="1.8" fill="none" strokeDasharray="5 4" />
        {q.map((label, i) => (
          <text key={label} x={x(i)} y={H - 14} textAnchor="middle" fontSize="9.5" fontFamily="JetBrains Mono" fill="#6c7799">
            {label}
          </text>
        ))}
      </svg>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[0.66rem] text-ink-3">
        <span className="flex items-center gap-2">
          <svg width="14" height="6" aria-hidden><line x1="0" y1="3" x2="14" y2="3" stroke="#34a6ff" strokeWidth="2" /></svg>
          Reserves
        </span>
        <span className="flex items-center gap-2">
          <svg width="14" height="6" aria-hidden><line x1="0" y1="3" x2="14" y2="3" stroke="#f4495f" strokeWidth="2" strokeDasharray="3 3" /></svg>
          After $5M draw
        </span>
        <span className="flex items-center gap-2">
          <svg width="14" height="6" aria-hidden><line x1="0" y1="3" x2="14" y2="3" stroke="#f5a623" strokeWidth="2" strokeDasharray="3 3" /></svg>
          Covenant floor
        </span>
      </div>
    </div>
  );
}
