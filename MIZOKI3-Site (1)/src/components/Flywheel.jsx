import { Check } from 'lucide-react';
import { FLYWHEEL_STEPS, FLYWHEEL_RESULTS, FLYWHEEL_STATS } from '../data.js';

export default function Flywheel() {
  return (
    <section id="flywheel" className="py-24"
             style={{ background: 'linear-gradient(180deg,transparent,rgba(11,18,40,0.5),transparent)' }}>
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal mb-12">
          <div className="chapter-marker">
            <span className="ln" /><span className="num">03</span><span>The Compounding Engine</span>
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">The MIZOKI3 Flywheel</h2>
          <div className="text-ink-3 text-base">Every interaction compounds the intelligence of the whole.</div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[300px_minmax(0,1fr)_230px] gap-10 items-center">
          <div className="reveal stagger flex flex-col gap-3.5">
            {FLYWHEEL_STEPS.map((s, i) => (
              <div key={s.n} className="flex gap-3.5 items-start" style={{ '--i': i }}>
                <div className="w-[30px] h-[30px] flex-shrink-0 rounded-[9px] grid place-items-center font-mono text-[0.78rem] font-bold bg-accent/10 border text-white"
                     style={{ borderColor: `var(--tw-color, ${cssColor(s.color)})`, ['--tw-color']: cssColor(s.color) }}>
                  {s.n}
                </div>
                <div>
                  <h4 className="text-[0.92rem] mb-0.5">{s.name}</h4>
                  <p className="text-[0.79rem] text-ink-3 leading-snug">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="reveal relative aspect-square max-w-[440px] mx-auto xl:max-w-none">
            <svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className="w-full h-full">
              <defs>
                <radialGradient id="flyCore" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#4cc9ff" stopOpacity="0.5" />
                  <stop offset="100%" stopColor="#4cc9ff" stopOpacity="0" />
                </radialGradient>
                <marker id="flyArr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
                  <path d="M0 0L8 4L0 8z" fill="#5b8cff" />
                </marker>
              </defs>
              <g fill="none" stroke="#5b8cff" strokeWidth="2" opacity="0.7" markerEnd="url(#flyArr)">
                <path d="M250 92 A158 158 0 0 1 400 207" />
                <path d="M404 230 A158 158 0 0 1 330 392" />
                <path d="M307 400 A158 158 0 0 1 138 345" />
                <path d="M120 325 A158 158 0 0 1 110 175" />
                <path d="M125 155 A158 158 0 0 1 228 96" />
              </g>
              <circle cx="250" cy="250" r="78" fill="url(#flyCore)" />
              <circle cx="250" cy="250" r="48" fill="#070b1c" stroke="rgba(76,201,255,0.5)" strokeWidth="1.4" />
              <text x="250" y="246" fontFamily="Sora" fontSize="15" fontWeight="700" fill="#fff" textAnchor="middle">NEXUS</text>
              <text x="250" y="261" fontFamily="JetBrains Mono" fontSize="7" fill="#9aa6c8" textAnchor="middle">SHARED CAUSAL</text>
              <text x="250" y="271" fontFamily="JetBrains Mono" fontSize="7" fill="#9aa6c8" textAnchor="middle">MEMORY</text>
              <g fontFamily="Sora" fontSize="10" fontWeight="600" fill="#fff" textAnchor="middle">
                <circle cx="250" cy="78" r="24" fill="#070b1c" stroke="#a855f7" strokeWidth="1.6" />
                <text x="250" y="82">CNSL</text>
                <circle cx="412" cy="196" r="24" fill="#070b1c" stroke="#34a6ff" strokeWidth="1.6" />
                <text x="412" y="200">CAP</text>
                <circle cx="350" cy="388" r="24" fill="#070b1c" stroke="#f4495f" strokeWidth="1.6" />
                <text x="350" y="392">RISK</text>
                <circle cx="150" cy="388" r="24" fill="#070b1c" stroke="#f5a623" strokeWidth="1.6" />
                <text x="150" y="392">SGNL</text>
                <circle cx="88" cy="196" r="24" fill="#070b1c" stroke="#21d07a" strokeWidth="1.6" />
                <text x="88" y="200">EST</text>
              </g>
            </svg>
          </div>

          <div className="reveal bg-[rgba(13,20,44,0.72)] border border-white/[0.07] rounded-[14px] p-6">
            <h4 className="font-mono text-[0.68rem] tracking-[0.16em] uppercase text-counsel mb-4">Compounding Result</h4>
            <ul className="list-none flex flex-col gap-3">
              {FLYWHEEL_RESULTS.map((r) => (
                <li key={r} className="flex gap-2.5 items-center text-[0.85rem] text-ink-2">
                  <Check className="w-4 h-4 text-estate flex-shrink-0" /> {r}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="reveal mt-9 grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-px bg-white/[0.07] border border-white/[0.07] rounded-[14px] overflow-hidden">
          {FLYWHEEL_STATS.map((s) => (
            <div key={s.lbl} className="bg-bg-1 p-5">
              <div className="font-mono text-[0.6rem] tracking-[0.13em] uppercase text-ink-3 mb-2">{s.lbl}</div>
              <div className="font-display text-[1.65rem] font-bold">{s.val}</div>
              <div className={`font-mono text-[0.66rem] mt-1 ${s.tone === 'up' ? 'text-estate' : s.tone === 'down' ? 'text-risk' : 'text-nexus'}`}>{s.delta}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function cssColor(name) {
  return ({
    counsel: '#a855f7', estate: '#21d07a', capital: '#34a6ff', signal: '#f5a623', risk: '#f4495f',
  })[name] || '#9aa6c8';
}
