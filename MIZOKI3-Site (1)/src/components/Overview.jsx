export default function Overview() {
  return (
    <section id="overview" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[780px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" /><span className="num">02</span><span>The Complete Picture</span><span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            One System, <em className="serif-i">End to End.</em>
          </h2>
          <div className="text-ink-3 text-base">
            From fragmented enterprise, legal, financial, operational, and customer data to verified autonomous
            strategic action — the whole platform at a glance.
          </div>
        </div>

        <Canvas src="/assets/01-hero-system.png" alt="MIZOKI3 system architecture — the full platform at a glance"
                cap="System architecture · Nexus · five domain lenses · governed autonomy" glow="rgba(76,201,255,0.3)" />

        <div className="mt-14">
          <Canvas src="/assets/02-editorial-overview.png" alt="MIZOKI3 editorial overview — how every layer connects"
                  cap="Editorial overview · how data, reasoning, governance, and action connect" glow="rgba(124,92,255,0.32)" />
        </div>
      </div>
    </section>
  );
}

export function Canvas({ src, alt, cap, glow = 'rgba(76,201,255,0.3)' }) {
  return (
    <div className="reveal relative max-w-[1180px] mx-auto">
      <div aria-hidden
           className="absolute -inset-7 rounded-[28px] pointer-events-none opacity-50 blur-[38px]"
           style={{ background: `radial-gradient(560px 280px at 50% 50%, ${glow}, transparent 70%)` }} />
      <img src={src} alt={alt} loading="lazy"
           className="relative z-[1] w-full h-auto block rounded-[20px] border border-white/[0.07]"
           style={{ boxShadow: `0 40px 100px -34px rgba(0,0,0,0.75), 0 0 90px -30px ${glow}` }} />
      <div className="mt-4 text-center font-mono text-[0.68rem] tracking-[0.14em] uppercase text-ink-4">
        <span className="text-ink-3">{cap.split(' · ')[0]}</span>
        {cap.includes(' · ') && ' · ' + cap.split(' · ').slice(1).join(' · ')}
      </div>
    </div>
  );
}
