import { useEffect, useState, useRef } from 'react';
import { Eye, BrainCircuit, ListChecks, ShieldCheck, CheckCircle2, Zap, RotateCw } from 'lucide-react';
import { SRPVDAL } from '../data.js';
import { Canvas } from './Overview.jsx';

const ICONS = [Eye, BrainCircuit, ListChecks, ShieldCheck, CheckCircle2, Zap, RotateCw];
const CYCLE_MS = 2500;
const PIN_MS = 8000;

export default function Orchestration() {
  const [active, setActive] = useState(0);
  const pinUntil = useRef(0);

  useEffect(() => {
    const id = setInterval(() => {
      if (Date.now() < pinUntil.current) return;
      setActive((v) => (v + 1) % SRPVDAL.length);
    }, CYCLE_MS);
    return () => clearInterval(id);
  }, []);

  const handleClick = (i) => {
    pinUntil.current = Date.now() + PIN_MS;
    setActive(i);
  };

  const stage = SRPVDAL[active];
  const ActiveIcon = ICONS[active];

  const confidence = 88 + ((active * 7) % 9);
  const policy = 100;
  const causal = 92 + ((active * 3) % 6);

  return (
    <section id="orchestration" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal mb-12">
          <div className="chapter-marker">
            <span className="ln" /><span className="num">04</span><span>SRPVDAL Orchestration</span>
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">The 7-Stage Autonomous Decision Loop</h2>
          <div className="text-ink-3 text-base">Each gate narrows uncertainty before the system commits resources.</div>
        </div>

        <div className="relative p-7 md:p-10 border border-white/10 bg-black/40 rounded-3xl shadow-2xl backdrop-blur-sm overflow-hidden">
          <div className="scanline" />

          <div className="flex flex-col lg:flex-row items-stretch gap-8">
            <div className="w-full lg:w-1/2 space-y-3">
              {SRPVDAL.map((s, i) => {
                const isActive = active === i;
                const Icon = ICONS[i];
                return (
                  <button key={s.id} onClick={() => handleClick(i)}
                          className={`w-full text-left flex items-center p-3.5 rounded-lg transition-all duration-500 border ${
                            isActive
                              ? 'bg-cyan-900/20 border-cyan-500/50 shadow-[0_0_20px_rgba(6,182,212,0.15)]'
                              : 'border-transparent hover:bg-white/5'
                          }`}>
                    <div className={`flex items-center justify-center w-10 h-10 rounded mr-4 transition-all ${
                      isActive
                        ? 'bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.5)]'
                        : 'bg-slate-900 text-slate-500 border border-white/10'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className={`text-base font-bold tracking-wide ${isActive ? 'text-white' : 'text-slate-400'}`}>
                        {s.name} <span className="text-xs text-slate-600 font-mono ml-2">{s.n}</span>
                      </h4>
                      <p className={`text-sm transition-all duration-300 overflow-hidden ${
                        isActive ? 'text-cyan-100/85 opacity-100 max-h-12 mt-1' : 'opacity-0 max-h-0'
                      }`}>
                        {s.desc}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="w-full lg:w-1/2 relative border border-white/5 rounded-xl bg-slate-950/50 flex items-center justify-center p-6 overflow-hidden min-h-[420px]">
              <div className="absolute inset-0 opacity-20 pointer-events-none">
                <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                  <path d="M 50 150 Q 200 50 350 150 T 650 150" stroke="#06b6d4" strokeWidth="2" fill="none" className="animate-pulse" />
                  <path d="M 50 250 Q 200 350 350 250 T 650 250" stroke="#f59e0b" strokeWidth="1" fill="none" className="animate-pulse" style={{ animationDelay: '1s' }} />
                </svg>
              </div>

              <div className="relative z-10 text-center w-full max-w-sm">
                <div className="mb-8">
                  <div className="w-24 h-24 mx-auto mb-4 bg-black border border-cyan-500/50 rounded-full flex items-center justify-center relative shadow-[0_0_40px_rgba(6,182,212,0.2)]">
                    <div className="absolute inset-0 rounded-full border-t-2 border-cyan-400 animate-spin" />
                    <ActiveIcon className="w-9 h-9 text-cyan-400" />
                  </div>
                  <h5 className="text-2xl font-bold text-white tracking-widest uppercase">{stage.name}</h5>
                  <div className="text-cyan-500 text-sm font-mono mt-2 flex justify-center items-center">
                    <span className="w-2 h-2 bg-cyan-500 rounded-full mr-2 animate-ping" />
                    SYSTEM {stage.name === 'Decide' ? 'AUTHORIZATION' : 'PROCESSING'}
                  </div>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  <Bar lbl="Causal Confidence" val={causal} color="amber" />
                  <Bar lbl="Policy Alignment"  val={policy}  color="cyan" />
                  <Bar lbl="Operational Conf." val={confidence} color="indigo" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-14">
          <Canvas src="/assets/04-orchestration-framework.png"
                  alt="MIZOKI3 orchestration framework — how the seven stages are coordinated"
                  cap="The orchestration framework · how the loop is coordinated, gated, and governed"
                  glow="rgba(76,201,255,0.3)" />
        </div>
        <div className="mt-14">
          <Canvas src="/assets/03-canonical-loop.png"
                  alt="MIZOKI3 canonical orchestration loop — the seven cognitive functions"
                  cap="The canonical loop · Sense → Reason → Plan → Validate → Decide → Act → Learn"
                  glow="rgba(76,201,255,0.3)" />
        </div>
      </div>
    </section>
  );
}

function Bar({ lbl, val, color }) {
  const colorMap = { amber: '#f59e0b', cyan: '#06b6d4', indigo: '#818cf8' };
  return (
    <>
      <div className="flex justify-between items-center text-slate-400 pt-1">
        <span>{lbl}</span>
        <span style={{ color: colorMap[color] }}>{val}%</span>
      </div>
      <div className="w-full h-1 bg-slate-800 rounded overflow-hidden">
        <div className="h-full rounded transition-all duration-700"
             style={{ width: `${val}%`, background: colorMap[color] }} />
      </div>
    </>
  );
}
