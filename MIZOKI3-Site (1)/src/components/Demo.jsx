import { DEMO_STEPS } from '../data.js';

export default function Demo() {
  return (
    <section id="demo" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[780px] mx-auto mb-12">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">12</span>
            <span>How a Pilot Begins</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            From signal to <em className="serif-i">compounding intelligence,</em>{' '}
            in six steps.
          </h2>
          <div className="text-ink-3 text-base">
            The pilot follows the same canonical loop the system runs in production.
          </div>
        </div>

        <div className="relative max-w-[920px] mx-auto">
          <div
            aria-hidden
            className="hidden md:block absolute left-[27px] top-12 bottom-12 w-px bg-gradient-to-b from-counsel via-nexus to-estate opacity-40"
          />
          <ol className="space-y-5">
            {DEMO_STEPS.map((s, i) => (
              <li
                key={s.n}
                className="reveal stagger flex gap-6 items-start"
                style={{ '--i': i }}
              >
                <div className="relative shrink-0 w-14 h-14 rounded-full bg-bg-1 border border-white/15 flex items-center justify-center font-mono text-sm font-bold text-nexus shadow-[0_0_24px_-8px_rgba(76,201,255,0.6)]">
                  {s.n}
                </div>
                <div className="flex-1 pt-2.5">
                  <h4 className="text-lg font-semibold mb-1">{s.name}</h4>
                  <p className="text-ink-3 text-sm leading-relaxed">{s.desc}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
