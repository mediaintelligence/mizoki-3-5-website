import { FileText, ShieldCheck, UserCheck, Terminal, ArrowRight } from 'lucide-react';
import { DCP_LAYERS } from '../data.js';
import { Canvas } from './Overview.jsx';

const ICONS = { propose: FileText, verify: ShieldCheck, authorize: UserCheck, execute: Terminal };
const COLOR_HEX = { counsel: '#a855f7', nexus: '#4cc9ff', signal: '#f5a623', estate: '#21d07a' };

export default function DCP() {
  return (
    <section id="architecture" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal mb-12">
          <div className="chapter-marker">
            <span className="ln" /><span className="num">05</span><span>Decision Control Plane</span>
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">Separates Proposal from Authorization</h2>
          <div className="text-ink-3 text-base">No autonomous decision executes without verification, simulation, and authorization.</div>
        </div>

        <div className="reveal stagger grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {DCP_LAYERS.map((l, i) => {
            const Icon = ICONS[l.key];
            const hex = COLOR_HEX[l.color];
            return (
              <div
                key={l.key}
                className="relative overflow-hidden bg-[rgba(13,20,44,0.72)] border border-white/[0.07] rounded-[14px] p-6 transition hover:-translate-y-1 hover:border-white/[0.18]"
                style={{ '--i': i, color: hex }}
              >
                <div className="absolute inset-x-0 top-0 h-[3px]" style={{ background: hex }} />
                <div className="w-[42px] h-[42px] rounded-[11px] grid place-items-center bg-white/[0.04] border mb-4" style={{ borderColor: hex }}>
                  <Icon className="w-5 h-5" />
                </div>
                <h4 className="text-ink text-[1.05rem] mb-2">{l.title}</h4>
                <p className="text-[0.83rem] text-ink-3 leading-relaxed">{l.desc}</p>
              </div>
            );
          })}
        </div>

        <div className="reveal mt-6 text-center text-[0.9rem] text-ink-3 flex flex-wrap items-center justify-center gap-2.5">
          <span>Every consequential output is verified, simulated, and authorized before it acts.</span>
          <a href="/console/index.html" className="text-nexus font-semibold inline-flex items-center gap-1.5 hover:underline">
            Open the live Control Plane <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="mt-12">
          <Canvas src="/assets/05-governance.png"
                  alt="MIZOKI3 governance framework — DCP, Verification & Arbitration, Decision Eligibility Layer"
                  cap="Governed autonomy · inputs → loop → outcomes, mediated by three control layers"
                  glow="rgba(124,92,255,0.32)" />
        </div>
      </div>
    </section>
  );
}
