import { useEffect, useRef, useState } from 'react';
import { RefreshCw, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { VETO_TRACE, REPLAY_TIMELINE } from '../data.js';

const STATE_STYLE = {
  idle: { border: 'rgba(120,150,230,0.13)', text: '#6c7799', dot: '#46506e', glow: 'none', label: 'Standby' },
  active: { border: '#4cc9ff', text: '#4cc9ff', dot: '#4cc9ff', glow: '0 0 24px -10px rgba(76,201,255,0.6)', label: 'Verifying' },
  flag: { border: '#f5a623', text: '#f5a623', dot: '#f5a623', glow: '0 0 24px -10px rgba(245,166,35,0.6)', label: 'Conflict' },
  veto: { border: '#f4495f', text: '#f4495f', dot: '#f4495f', glow: '0 0 28px -8px rgba(244,73,95,0.7)', label: 'Vetoed' },
};

const LINE_TONE = {
  warn: 'text-signal',
  bad: 'text-risk font-bold',
  good: 'text-estate',
  dim: 'text-ink-3',
  rule: 'text-ink-4',
};

export default function Veto() {
  const sectionRef = useRef(null);
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(-1);
  const [layers, setLayers] = useState({ dcp: 'idle', va: 'idle', del: 'idle' });
  const [showStamp, setShowStamp] = useState(false);
  const [showOutcome, setShowOutcome] = useState({ blocked: false, executed: false });

  const reset = () => {
    setStep(-1);
    setLayers({ dcp: 'idle', va: 'idle', del: 'idle' });
    setShowStamp(false);
    setShowOutcome({ blocked: false, executed: false });
  };

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && step === -1) {
          setRunning(true);
          io.unobserve(el);
        }
      },
      { threshold: 0.35 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [step]);

  useEffect(() => {
    if (!running) return;
    setStep(0);
    setLayers((l) => ({ ...l, dcp: 'active', va: 'active' }));
  }, [running]);

  useEffect(() => {
    if (step < 0 || step >= VETO_TRACE.length) return;
    const line = VETO_TRACE[step];
    if (line.layer) setLayers((l) => ({ ...l, ...line.layer }));
    if (line.stamp) setShowStamp(true);
    if (line.body && line.body.includes('re-route')) setShowOutcome((o) => ({ ...o, blocked: true }));
    if (line.body && line.body.includes('executed: defer')) setShowOutcome((o) => ({ ...o, executed: true }));

    const delay = line.cls === 'rule' ? 220 : line.body.includes('CONFLICT') ? 700 : line.cls === 'bad' ? 620 : 420;
    const id = setTimeout(() => setStep((s) => s + 1), delay);
    return () => clearTimeout(id);
  }, [step]);

  const replay = () => {
    reset();
    setTimeout(() => {
      setLayers({ dcp: 'active', va: 'active', del: 'idle' });
      setStep(0);
    }, 200);
  };

  return (
    <section id="veto" ref={sectionRef} className="py-24"
             style={{ background: 'linear-gradient(180deg,transparent,rgba(11,18,40,0.5),transparent)' }}>
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal mb-12">
          <div className="chapter-marker">
            <span className="ln" /><span className="num">06</span><span>Verification &amp; Arbitration</span>
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            The moat isn't the loop. <em className="serif-i">It's the veto.</em>
          </h2>
          <div className="text-ink-3 text-base">
            Any system can run an agent loop. MIZOKI3 can stop one — mathematically — before it acts.
            Watch a $5M distribution proposed, cross-checked, and vetoed against the covenant it would have breached.
          </div>
        </div>

        <div className="reveal max-w-[1080px] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 mb-4">
            {[
              { key: 'dcp', name: 'Layer 01', title: 'Decision Control Plane' },
              { key: 'va', name: 'Layer 02', title: 'Verification & Arbitration' },
              { key: 'del', name: 'Layer 03', title: 'Decision Eligibility' },
            ].map((L) => {
              const st = STATE_STYLE[layers[L.key]];
              return (
                <div key={L.key}
                     className="bg-[rgba(13,20,44,0.72)] rounded-[14px] p-4 transition-all duration-500 border"
                     style={{ borderColor: st.border, boxShadow: st.glow }}>
                  <div className="font-mono text-[0.59rem] tracking-[0.16em] uppercase text-ink-4 mb-1.5">{L.name}</div>
                  <h4 className="text-[0.93rem] mb-2">{L.title}</h4>
                  <div className="font-mono text-[0.64rem] font-bold tracking-[0.1em] uppercase flex items-center gap-2"
                       style={{ color: st.text }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: st.dot, boxShadow: `0 0 8px ${st.dot}` }} />
                    {st.label}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-[#02030a] border border-white/15 rounded-[14px] overflow-hidden shadow-[0_40px_90px_-44px_rgba(0,0,0,0.95)]">
            <div className="flex items-center gap-3.5 px-4 py-3 bg-[rgba(13,20,44,0.7)] border-b border-white/[0.07]">
              <div className="flex gap-1.5">
                <i className="w-2.5 h-2.5 rounded-full bg-risk" />
                <i className="w-2.5 h-2.5 rounded-full bg-signal" />
                <i className="w-2.5 h-2.5 rounded-full bg-estate" />
              </div>
              <span className="font-mono text-[0.7rem] text-ink-3 flex-grow tracking-wide">
                srpvdal — execution trace · ACT-991
              </span>
              <button onClick={replay}
                      className="font-mono text-[0.66rem] font-bold text-nexus bg-nexus/[0.08] border border-white/15 rounded-md px-3 py-1.5 hover:bg-nexus/[0.18] inline-flex items-center gap-1.5">
                <RefreshCw className="w-3 h-3" /> Replay
              </button>
            </div>

            <div className="relative font-mono text-[0.8rem] leading-[1.95] min-h-[440px] p-6 md:p-7">
              {VETO_TRACE.map((line, i) => {
                const visible = i <= step;
                if (!visible && step < 0) return null;
                const tone = LINE_TONE[line.cls] || 'text-ink-2';
                return (
                  <div key={i}
                       className={`whitespace-pre-wrap transition-all duration-300 ${tone} ${line.cls === 'rule' ? '' : ''}`}
                       style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(3px)' }}>
                    <span className="inline-block w-[78px] text-nexus font-bold">{line.stg}</span>
                    {line.cls === 'cursor' ? (
                      <span className="inline-block text-nexus animate-pulse">▋</span>
                    ) : (
                      line.body
                    )}
                  </div>
                );
              })}

              <div className="absolute top-[44%] left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-12 font-display font-bold text-[2.4rem] tracking-[0.05em] uppercase text-risk border-4 border-risk rounded-[9px] px-6 py-2 bg-[rgba(8,3,6,0.7)] shadow-[0_0_50px_rgba(244,73,95,0.45)] pointer-events-none transition-all duration-500"
                   style={{
                     opacity: showStamp ? 0.97 : 0,
                     transform: `translate(-50%,-50%) rotate(-12deg) scale(${showStamp ? 1 : 1.7})`,
                   }}>
                VETOED
              </div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3.5">
            <OutcomeCard show={showOutcome.blocked} tone="blocked" label="Option A"
                         title="Blocked before execution"
                         body="$5.0M distribution would have breached COV-01 by $3.0M. Authorization withheld." />
            <OutcomeCard show={showOutcome.executed} tone="executed" label="Option B"
                         title="Executed safely"
                         body="Distribution deferred one quarter. Liquidity held at $12.0M. Covenant preserved." />
          </div>
        </div>

        <div className="mt-20 max-w-[1080px] mx-auto">
          <div className="reveal text-center mb-10">
            <div className="font-mono text-[0.66rem] tracking-[0.2em] uppercase text-nexus mb-2">The Flight Recorder</div>
            <h3 className="text-[clamp(1.3rem,2.2vw,1.9rem)] font-semibold mb-2">Every Decision is Replayable.</h3>
            <p className="text-ink-3 text-base max-w-[640px] mx-auto">
              Total transparency. Replay signals, reasoning, rejected alternate paths, policy checks,
              confidence scoring, and final execution logs — for any decision the system made.
            </p>
          </div>

          <div className="relative p-7 md:p-10 border border-white/10 bg-black rounded-2xl shadow-2xl">
            <div className="absolute left-[3.25rem] md:left-[4.25rem] top-12 bottom-12 w-px bg-gradient-to-b from-cyan-500/50 via-rose-500/50 to-emerald-500/50" />
            {REPLAY_TIMELINE.map((step, i) => (
              <ReplayStep key={i} step={step} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function OutcomeCard({ show, tone, label, title, body }) {
  const isBlocked = tone === 'blocked';
  const color = isBlocked ? 'rgba(244,73,95,0.3)' : 'rgba(33,208,122,0.3)';
  const text = isBlocked ? 'text-risk' : 'text-estate';
  const Icon = isBlocked ? AlertOctagon : CheckCircle2;
  return (
    <div className="rounded-[14px] p-5 bg-[rgba(13,20,44,0.72)] border transition-all duration-700"
         style={{
           borderColor: color,
           opacity: show ? 1 : 0,
           transform: show ? 'translateY(0)' : 'translateY(10px)',
         }}>
      <div className={`font-mono text-[0.61rem] tracking-[0.14em] uppercase mb-2 flex items-center gap-2 ${text}`}>
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <h4 className="text-[1rem] mb-1">{title}</h4>
      <p className="text-[0.81rem] text-ink-3 leading-snug">{body}</p>
    </div>
  );
}

function ReplayStep({ step }) {
  const TONE = {
    neutral: { text: 'text-slate-300', dot: 'bg-slate-500', border: 'border-slate-800' },
    plan:    { text: 'text-indigo-400', dot: 'bg-indigo-500', border: 'border-indigo-500/40' },
    warn:    { text: 'text-amber-400',  dot: 'bg-amber-500',  border: 'border-amber-500/40' },
    bad:     { text: 'text-rose-400',   dot: 'bg-rose-500',   border: 'border-rose-500/40' },
    good:    { text: 'text-cyan-400',   dot: 'bg-cyan-500',   border: 'border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.5)]' },
  }[step.tone] || {};
  return (
    <div className="relative flex items-start mb-8 last:mb-0 group">
      <div className={`w-10 h-10 rounded-full bg-black border-2 ${TONE.border} flex items-center justify-center relative z-10 mr-5 mt-1 transition`}>
        <div className={`w-2.5 h-2.5 rounded-full ${TONE.dot}`} />
      </div>
      <div className="flex-1 bg-white/5 border border-white/5 p-4 rounded-lg group-hover:bg-white/10 transition">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:gap-4 mb-1.5">
          <span className="font-mono text-xs text-slate-500">{step.t}</span>
          <span className={`font-bold uppercase tracking-widest text-sm ${TONE.text}`}>{step.event}</span>
        </div>
        <p className="text-slate-400 text-sm md:text-base">{step.detail}</p>
      </div>
    </div>
  );
}
