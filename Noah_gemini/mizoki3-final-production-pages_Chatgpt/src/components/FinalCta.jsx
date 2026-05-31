import { Link } from "react-router-dom";
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "./Button";
import { KnowledgeGraphBackground } from "./KnowledgeGraphBackground";

export function DeploymentCta() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-16">
      <div className="flex flex-col items-center justify-between gap-8 rounded-[2rem] border border-amber-300/10 bg-[linear-gradient(135deg,rgba(245,158,11,.06),rgba(34,211,238,.03),rgba(0,0,0,.7))] p-8 shadow-xl md:flex-row md:p-12">
        <div className="max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-md border border-amber-300/25 bg-amber-300/10 px-3 py-1 text-xs font-bold text-amber-300">
            <ShieldCheck className="h-4 w-4" /> GRC Verified System Architecture
          </div>
          <h2 className="text-3xl font-black tracking-tight">Ready for structural deployment.</h2>
          <p className="mt-4 text-sm leading-7 text-slate-300">
            Connect your business lines, configure internal risk parameters, and let MIZOKI3 automate real-time operational decisions with extreme, human-governed clarity.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-4">
          <Link to="/simulator"><Button variant="amber">Enter Control Plane</Button></Link>
          <Link to="/contact"><Button variant="outline">Speak to Advisor</Button></Link>
        </div>
      </div>
    </section>
  );
}

export function FinalCta() {
  return (
    <section className="relative overflow-hidden bg-black px-6 py-28 text-center">
      <KnowledgeGraphBackground />
      <div className="relative z-10 mx-auto max-w-4xl">
        <Sparkles className="mx-auto mb-8 h-14 w-14 text-cyan-300" />
        <h2 className="text-4xl font-black md:text-6xl">The beginning of autonomous enterprise cognition.</h2>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          Stop summarizing data. Start governing outcomes through causal, threshold-aware, auditable execution.
        </p>
        <Link to="/simulator">
          <Button variant="amber" className="mt-9 px-8">
            Initialize Executive Demo <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </div>
    </section>
  );
}
