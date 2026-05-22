// Governance — Counterfactual Simulation Engine + Decision Eligibility Layer

export default function Governance() {
  return (
    <section id="governance" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[820px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">10</span>
            <span>Governed Autonomy</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            Autonomy <em className="serif-i">measured, not assumed.</em>
          </h2>
          <div className="text-ink-3 text-base">
            Two engines anchor governance: the{' '}
            <strong className="text-ink">Counterfactual Simulation Engine</strong>{' '}
            tests futures before they happen; the{' '}
            <strong className="text-ink">Decision Eligibility Layer</strong> scores
            every action's eligibility before authorization.
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-[1180px] mx-auto">
          <div className="reveal rounded-2xl border border-white/[0.08] bg-bg-1/40 p-6">
            <div className="font-mono text-[0.66rem] uppercase tracking-[0.18em] text-counsel mb-2">
              CSE · Counterfactual Simulation Engine
            </div>
            <h3 className="text-lg font-semibold mb-3">Refinancing decision · projected DSCR</h3>
            <CSEChart />
            <div className="mt-3 grid grid-cols-3 gap-3 font-mono text-[0.65rem]">
              <Legend c="#21d07a" t="Refi @ 5.4%" />
              <Legend c="#34a6ff" t="Hold current" />
              <Legend c="#f4495f" t="Refi @ 6.8%" />
            </div>
            <p className="text-ink-3 text-sm mt-4 leading-relaxed">
              Four counterfactuals simulated against the covenant threshold
              (DSCR ≥ 1.20). Only the Refi @ 5.4% scenario preserves compliance
              through Q4. The DCP authorizes that path.
            </p>
          </div>

          <div className="reveal rounded-2xl border border-white/[0.08] bg-bg-1/40 p-6 flex flex-col">
            <div className="font-mono text-[0.66rem] uppercase tracking-[0.18em] text-signal mb-2">
              DEL · Decision Eligibility Layer
            </div>
            <h3 className="text-lg font-semibold mb-6">Authorize-readiness score · current decision</h3>
            <DELGauge score={87} />
            <div className="mt-6 grid grid-cols-3 gap-3">
              {[
                { k: 'Causal Confidence', v: '94.2%' },
                { k: 'Policy Alignment',  v: '100%' },
                { k: 'Audit Coverage',    v: 'Full' },
              ].map((m) => (
                <div key={m.k} className="text-center">
                  <div className="font-mono text-[0.6rem] uppercase tracking-[0.14em] text-ink-3 mb-1">{m.k}</div>
                  <div className="font-display text-base font-semibold text-nexus">{m.v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Legend({ c, t }) {
  return (
    <div className="flex items-center gap-2 text-ink-3">
      <span aria-hidden className="inline-block w-3 h-[2px]" style={{ background: c }} />
      <span>{t}</span>
    </div>
  );
}

function CSEChart() {
  const W = 460, H = 220, P = 32;
  const lines = [
    { c: '#21d07a', d: [1.40, 1.38, 1.35, 1.34, 1.32, 1.31, 1.30, 1.28] },
    { c: '#34a6ff', d: [1.28, 1.24, 1.20, 1.16, 1.12, 1.08, 1.04, 1.00] },
    { c: '#f4495f', d: [1.22, 1.16, 1.10, 1.04, 0.98, 0.92, 0.86, 0.82] },
  ];
  const yMin = 0.7, yMax = 1.5;
  const x = (i) => P + (i / 7) * (W - 2 * P);
  const y = (v) => H - P - ((v - yMin) / (yMax - yMin)) * (H - 2 * P);
  const cov = y(1.20);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
      {[0.8, 1.0, 1.2, 1.4].map((g) => (
        <line key={g} x1={P} x2={W - P} y1={y(g)} y2={y(g)} stroke="#1c2543" strokeWidth="0.5" />
      ))}
      {[0.8, 1.0, 1.2, 1.4].map((g) => (
        <text key={`y-${g}`} x={P - 6} y={y(g) + 3} textAnchor="end" fontSize="9" fontFamily="JetBrains Mono" fill="#6c7799">
          {g.toFixed(1)}
        </text>
      ))}
      <line x1={P} x2={W - P} y1={cov} y2={cov} stroke="#f5a623" strokeWidth="1" strokeDasharray="4 4" opacity="0.7" />
      <text x={W - P + 4} y={cov + 4} fontSize="9" fontFamily="JetBrains Mono" fill="#f5a623">cov 1.20</text>
      {lines.map((ln, i) => (
        <path key={i}
              d={ln.d.map((v, j) => `${j === 0 ? 'M' : 'L'} ${x(j)} ${y(v)}`).join(' ')}
              stroke={ln.c} strokeWidth="1.8" fill="none" />
      ))}
      {[0, 1, 2, 3, 4, 5, 6, 7].map((q) => (
        <text key={q} x={x(q)} y={H - 10} textAnchor="middle" fontSize="9" fontFamily="JetBrains Mono" fill="#6c7799">
          Q{q + 1}
        </text>
      ))}
    </svg>
  );
}

function DELGauge({ score }) {
  const R = 90;
  const angle = (score / 100) * 180;
  const rad = (deg) => ((deg - 180) * Math.PI) / 180;
  const x = 120 + R * Math.cos(rad(angle));
  const y = 120 + R * Math.sin(rad(angle));
  const arcLarge = angle > 180 ? 1 : 0;
  const arcPath = `M ${120 - R} 120 A ${R} ${R} 0 ${arcLarge} 1 ${x} ${y}`;

  return (
    <svg viewBox="0 0 240 150" className="w-full max-w-[280px] mx-auto">
      <path d="M 30 120 A 90 90 0 0 1 210 120" stroke="#1c2543" strokeWidth="10" fill="none" strokeLinecap="round" />
      <path d={arcPath} stroke="#21d07a" strokeWidth="10" fill="none" strokeLinecap="round" />
      <circle cx={x} cy={y} r="6" fill="#21d07a" />
      <text x="120" y="100" textAnchor="middle" fontSize="32" fontFamily="Sora" fontWeight="700" fill="#f3f5fc">{score}</text>
      <text x="120" y="120" textAnchor="middle" fontSize="9" fontFamily="JetBrains Mono" fill="#6c7799">/ 100 ELIGIBLE</text>
    </svg>
  );
}
