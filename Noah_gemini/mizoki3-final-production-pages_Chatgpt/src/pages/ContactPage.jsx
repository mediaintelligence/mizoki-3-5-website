import { Button } from "../components/Button";
import { SurfaceCard } from "../components/SurfaceCard";

export function ContactPage() {
  return (
    <section className="min-h-[70vh] bg-black px-6 py-20">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[.8fr_1.2fr]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Executive Demo</p>
          <h1 className="mt-4 text-5xl font-black md:text-7xl">Talk to the MIZOKI3 team.</h1>
          <p className="mt-6 text-lg leading-8 text-slate-300">
            Use this placeholder form as the front-end shell. Connect it to HubSpot, Supabase, Salesforce, or a backend endpoint when ready.
          </p>
        </div>
        <SurfaceCard className="p-8">
          <form className="space-y-5">
            {["Name", "Company", "Email", "Role"].map((label) => (
              <label key={label} className="block">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{label}</span>
                <input className="mt-2 w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-white outline-none focus:border-cyan-300" placeholder={label} />
              </label>
            ))}
            <label className="block">
              <span className="text-xs font-bold uppercase tracking-widest text-slate-500">Deployment Interest</span>
              <textarea className="mt-2 min-h-32 w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-white outline-none focus:border-cyan-300" placeholder="Describe the operating domain, systems, or decision workflows you want to govern." />
            </label>
            <Button variant="amber" type="button">Request Executive Demo</Button>
          </form>
        </SurfaceCard>
      </div>
    </section>
  );
}
