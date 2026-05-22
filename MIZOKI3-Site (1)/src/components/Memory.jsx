import { Canvas } from './Overview.jsx';

const PROPS = [
  { k: 'Bi-temporal',
    v: 'Captures both when events occurred and when they were recorded. Replay any past state of the business; reason about what was known when.' },
  { k: 'Causal, not correlative',
    v: 'Edges encode mechanism and provenance. The graph knows why one thing moved another, not just that they moved together.' },
  { k: 'Cross-domain by default',
    v: 'A Counsel update propagates Estate exposure in the same query path. One graph, many lenses — never federated, never stale.' },
];

export default function Memory() {
  return (
    <section id="memory" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[820px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">09</span>
            <span>The Memory of the System</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            A graph that <em className="serif-i">remembers, reasons, and compounds.</em>
          </h2>
          <div className="text-ink-3 text-base">
            The Temporal-Causal Knowledge Graph is the substrate beneath every cell.
            Time, identity, obligation, and causality are first-class — not retrieved,
            but resident.
          </div>
        </div>

        <Canvas src="/assets/06-knowledge-graph.png"
                alt="MIZOKI3 Temporal-Causal Knowledge Graph"
                cap="Knowledge graph substrate · bi-temporal · causality-aware · multi-domain"
                glow="rgba(124,92,255,0.32)" />

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-5 max-w-[1080px] mx-auto">
          {PROPS.map((c, i) => (
            <div key={c.k}
                 className="reveal stagger p-6 rounded-xl border border-white/10 bg-bg-1/40"
                 style={{ '--i': i }}>
              <div className="font-mono text-[0.62rem] uppercase tracking-[0.18em] text-nexus mb-2">
                Property {String(i + 1).padStart(2, '0')}
              </div>
              <h4 className="font-semibold text-base mb-2">{c.k}</h4>
              <p className="text-ink-3 text-sm leading-relaxed">{c.v}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
