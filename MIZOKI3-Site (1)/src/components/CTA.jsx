export default function CTA() {
  return (
    <section id="contact" className="py-32">
      <div className="max-w-[820px] mx-auto px-7 text-center reveal">
        <div className="chapter-marker !justify-center">
          <span className="ln" />
          <span className="num">▴</span>
          <span>Initiate Pilot</span>
          <span className="ln-r" />
        </div>
        <h2 className="text-[clamp(2rem,3.4vw,3rem)] mb-5">
          Deploy the <em className="serif-i">nervous system</em> for your enterprise.
        </h2>
        <p className="text-ink-3 text-base md:text-lg leading-relaxed mb-10 max-w-xl mx-auto">
          MIZOKI3 is delivered as governed infrastructure — Terraform into your own
          GCP project, encrypted with your own Cloud KMS keys. Pilots begin with a
          single division and expand once the substrate proves its compounding value.
        </p>
        <a
          href="mailto:hello@mizoki3.com"
          className="inline-flex items-center gap-2 px-10 py-4 bg-nexus text-bg-0 font-mono text-sm font-bold uppercase tracking-[0.18em] rounded transition-all hover:bg-white shadow-[0_0_36px_-8px_rgba(76,201,255,0.6)]"
        >
          Request Architecture Briefing →
        </a>
        <div className="mt-6 font-mono text-xs text-ink-4 tracking-wider">
          hello@mizoki3.com
        </div>
      </div>
    </section>
  );
}
