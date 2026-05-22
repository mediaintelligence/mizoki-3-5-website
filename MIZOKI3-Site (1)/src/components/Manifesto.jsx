export default function Manifesto() {
  return (
    <section id="manifesto" className="py-24 border-y border-white/[0.07] text-center"
             style={{ background: 'radial-gradient(900px 480px at 50% 50%, rgba(244,73,95,0.06), transparent 65%), rgba(7,11,28,0.5)' }}>
      <div className="max-w-[1000px] mx-auto px-7">
        <div className="reveal chapter-marker !justify-center">
          <span className="ln" /><span className="num">01</span><span>The Premise</span><span className="ln-r" />
        </div>
        <h2 className="reveal text-[clamp(2rem,4.2vw,3.4rem)] font-bold mb-7">
          You cannot run a $10B enterprise<br />on <span className="relative whitespace-nowrap after:content-[''] after:absolute after:left-[-3%] after:right-[-3%] after:top-[56%] after:h-[3px] after:bg-risk after:scale-x-100 after:origin-left">correlation.</span>
        </h2>
        <p className="reveal text-[1.12rem] text-ink-2 max-w-[740px] mx-auto mb-10 leading-[1.65]">
          Standard generative AI predicts the next token by semantic similarity. It runs on{' '}
          <span className="text-ink font-semibold">correlation</span> — which guarantees hallucination.
          MIZOKI3 runs on <span className="text-ink font-semibold">causation</span>. By enforcing a
          Temporal-Causal Knowledge Graph, every legal clause and financial covenant becomes{' '}
          <em className="serif-i text-ink">executable enterprise physics</em> — a constraint the system
          cannot violate, not a suggestion it might ignore.
        </p>
        <div className="reveal grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] max-w-[820px] mx-auto">
          <div className="p-7 border border-white/[0.07] text-left rounded-l-[20px] bg-[rgba(244,73,95,0.04)] md:rounded-r-none md:rounded-l-[20px] rounded-t-[20px] rounded-b-none md:rounded-tr-none md:rounded-bl-[20px]">
            <div className="font-mono text-[0.62rem] tracking-[0.16em] uppercase mb-2.5 text-risk">Correlation AI</div>
            <h4 className="text-[1.05rem] font-semibold mb-1.5">Predicts what looks likely</h4>
            <p className="text-[0.84rem] text-ink-3">Pattern-matches plausible output. Fluent, confident, and structurally unable to know when it is wrong.</p>
          </div>
          <div className="flex items-center justify-center w-full md:w-[54px] h-[42px] md:h-auto serif-i text-[1.2rem] text-ink-4 bg-bg-0 border-y md:border-x md:border-y-0 border-white/[0.07]">vs</div>
          <div className="p-7 border border-white/[0.07] md:border-l-0 text-left bg-[rgba(76,201,255,0.05)] md:rounded-r-[20px] md:rounded-l-none rounded-b-[20px] rounded-t-none md:rounded-bl-none md:rounded-tr-[20px]">
            <div className="font-mono text-[0.62rem] tracking-[0.16em] uppercase mb-2.5 text-nexus">MIZOKI3 — Causal</div>
            <h4 className="text-[1.05rem] font-semibold mb-1.5">Proves what is permitted</h4>
            <p className="text-[0.84rem] text-ink-3">Reasons over a governed causal graph. Every action is checked against covenants, policy, and lineage before it executes.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
