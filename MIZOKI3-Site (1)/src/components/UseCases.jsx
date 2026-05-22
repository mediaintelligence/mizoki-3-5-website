import { USE_CASES } from '../data.js';

export default function UseCases() {
  return (
    <section id="usecases" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[820px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">13</span>
            <span>Who Operates With MIZOKI3</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            For organizations whose decisions <em className="serif-i">matter.</em>
          </h2>
          <div className="text-ink-3 text-base">
            Built for the operating cores of regulated, fiduciary, and
            high-consequence enterprises.
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 stagger max-w-[1180px] mx-auto">
          {USE_CASES.map((uc, i) => (
            <div key={uc.name}
                 className="reveal p-7 rounded-2xl border border-white/[0.08] bg-bg-1/40 hover:border-white/15 hover:bg-bg-1/60 transition-all"
                 style={{ '--i': i }}>
              <div className="font-mono text-[0.62rem] uppercase tracking-[0.18em] text-nexus mb-3">
                Segment {String(i + 1).padStart(2, '0')}
              </div>
              <h4 className="text-lg font-semibold mb-2.5 leading-tight">{uc.name}</h4>
              <p className="text-ink-3 text-sm leading-relaxed">{uc.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
