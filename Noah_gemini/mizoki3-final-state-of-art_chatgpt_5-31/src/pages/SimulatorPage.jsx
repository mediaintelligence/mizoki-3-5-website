import { SimulatorConsole } from "../components/SimulatorConsole";
import { FinalCta } from "../components/FinalCta";

export function SimulatorPage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Live Product Demo</p>
          <h1 className="mt-4 max-w-4xl text-5xl font-black md:text-7xl">Run the autonomous decision loop.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            The simulator lets buyers see the MIZOKI3 thesis in motion: signals enter, agents reason, paths are tested, thresholds are scored, and execution is authorized or escalated.
          </p>
        </div>
      </section>
      <SimulatorConsole />
      <FinalCta />
    </>
  );
}
