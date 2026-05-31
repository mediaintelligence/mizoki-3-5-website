import { useEffect, useMemo, useState } from "react";
import { BarChart3, Cpu, Database, Info, Play, RefreshCw, ShieldAlert, ShieldCheck, Sliders, Zap } from "lucide-react";
import { Button } from "./Button";
import { SurfaceCard } from "./SurfaceCard";
import { cx } from "../lib/cx";
import { simulationScenarios, srpvdalNodes } from "../data/siteData";

export function SimulatorConsole() {
  const [selectedScenario, setSelectedScenario] = useState("capital");
  const [currentStageIndex, setCurrentStageIndex] = useState(-1);
  const [isRunning, setIsRunning] = useState(false);
  const [riskTolerance, setRiskTolerance] = useState(50);
  const [simulationLogs, setSimulationLogs] = useState([]);
  const [activePathSelection, setActivePathSelection] = useState("A");

  const scenario = simulationScenarios[selectedScenario];

  const reset = () => {
    setIsRunning(false);
    setCurrentStageIndex(-1);
    setSimulationLogs([]);
  };

  const start = () => {
    setCurrentStageIndex(-1);
    setSimulationLogs([]);
    setIsRunning(true);
  };

  useEffect(() => {
    let interval;
    if (isRunning) {
      if (currentStageIndex < srpvdalNodes.length - 1) {
        interval = setInterval(() => {
          setCurrentStageIndex((prev) => {
            const next = prev + 1;
            const nextLog = simulationScenarios[selectedScenario].logs[next];
            setSimulationLogs((oldLogs) => (nextLog ? [...oldLogs, nextLog] : oldLogs));
            return next;
          });
        }, 1200);
      } else {
        setIsRunning(false);
      }
    }
    return () => clearInterval(interval);
  }, [isRunning, currentStageIndex, selectedScenario]);

  const dynamicConfidence = useMemo(() => {
    const path = scenario.paths.find((p) => p.id === activePathSelection) || scenario.paths[0];

    let modifier = 0;
    if (path.risk === "High") modifier = (riskTolerance - 50) * 0.3;
    if (path.risk === "Medium") modifier = (riskTolerance - 50) * 0.12;
    if (path.risk === "Low" || path.risk === "Minimal") modifier = (50 - riskTolerance) * 0.15;

    return Math.min(Math.max(Math.round(path.confidence + modifier), 40), 100);
  }, [scenario, activePathSelection, riskTolerance]);

  return (
    <section className="scroll-mt-24 border-y border-cyan-400/10 bg-[#020612] px-6 py-24">
      <div className="mx-auto max-w-7xl overflow-hidden rounded-[2.5rem] border border-cyan-400/20 bg-[#040813]/90 shadow-2xl">
        <div className="border-b border-white/10 bg-gradient-to-r from-cyan-950/20 to-amber-950/10 p-8">
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-md border border-cyan-800/40 bg-cyan-950 px-3 py-1 text-xs font-bold text-cyan-300">
                <Sliders className="h-3.5 w-3.5" /> Interactive Sandbox
              </div>
              <h2 className="text-3xl font-black tracking-tight md:text-5xl">MIZOKI3 Simulation Console</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Trigger live scenarios, alter policy bounds, choose a counterfactual path, and watch the SRPVDAL loop resolve tradeoffs.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {Object.keys(simulationScenarios).map((key) => (
                <button
                  key={key}
                  onClick={() => {
                    setSelectedScenario(key);
                    reset();
                  }}
                  className={cx(
                    "rounded-xl border px-4 py-2 text-xs font-black uppercase tracking-wider transition-all",
                    selectedScenario === key ? "border-cyan-300 bg-cyan-300 text-black shadow-[0_0_15px_rgba(34,211,238,.2)]" : "border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/10"
                  )}
                >
                  {key} Node
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-px bg-white/10 lg:grid-cols-12">
          <div className="space-y-6 bg-[#020612] p-8 lg:col-span-4">
            <div>
              <div className="mb-4 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-cyan-300">
                <Database className="h-4 w-4" /> System Ingestion Layer
              </div>
              <h3 className="text-xl font-bold">{scenario.title}</h3>
              <p className="mt-2 text-xs leading-6 text-slate-400">Incoming streams triggering automatic loop execution:</p>

              <div className="mt-4 space-y-2">
                {scenario.signals.map((signal) => (
                  <div key={signal} className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] p-2 text-xs text-slate-200">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-300 shadow-[0_0_12px_rgba(245,158,11,.8)]" />
                    <span>{signal}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-white/10 pt-6">
              <div className="mb-3 flex items-center justify-between">
                <span className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-cyan-300">
                  <ShieldAlert className="h-4 w-4" /> Policy Bounds
                </span>
                <span className="text-xs font-black text-slate-300">{riskTolerance}% Tolerance</span>
              </div>
              <input
                type="range"
                min="10"
                max="90"
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(Number(e.target.value))}
                className="h-1 w-full cursor-pointer appearance-none rounded-lg bg-cyan-950 accent-cyan-300"
              />
              <div className="mt-2 flex justify-between text-[9px] font-bold uppercase text-slate-500">
                <span>Governed</span><span>Neutral</span><span>Aggressive</span>
              </div>
              <p className="mt-3 text-[11px] leading-5 text-slate-400">
                Higher tolerance permits larger potential rewards, but lower path verification confidence may trigger escalation.
              </p>
            </div>

            <div className="border-t border-white/10 pt-6">
              <span className="mb-3 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-cyan-300">
                <BarChart3 className="h-4 w-4" /> Counterfactual Paths
              </span>
              <div className="grid grid-cols-3 gap-2">
                {scenario.paths.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setActivePathSelection(p.id)}
                    className={cx(
                      "rounded-xl border p-3 text-center transition-all",
                      activePathSelection === p.id ? "border-amber-300 bg-amber-300/10 text-amber-200" : "border-white/10 bg-white/[0.02] text-slate-400 hover:border-white/20"
                    )}
                  >
                    <div className="text-xs font-black">Path {p.id}</div>
                    <div className="mt-1 text-[10px] text-slate-400">{p.risk}</div>
                  </button>
                ))}
              </div>

              <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.025] p-3 text-xs text-slate-300">
                <div className="font-bold text-white">Target Proposal:</div>
                <p className="mt-1 text-[11px] leading-5 text-slate-400">
                  {scenario.paths.find((p) => p.id === activePathSelection)?.desc}
                </p>
              </div>
            </div>

            {!isRunning ? (
              <Button variant="cyan" onClick={start} className="w-full py-3.5">
                <Play className="mr-2 h-4 w-4 fill-current" /> Execute Autonomous Loop
              </Button>
            ) : (
              <Button variant="outline" onClick={reset} className="w-full border-red-500/40 bg-red-500/10 py-3.5 text-red-200 hover:bg-red-500/20">
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> Stop & Reset
              </Button>
            )}
          </div>

          <div className="flex flex-col justify-between bg-[#040815] p-8 lg:col-span-8">
            <div>
              <div className="mb-6 flex flex-col justify-between gap-3 md:flex-row md:items-center">
                <span className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-amber-300">
                  <Zap className="h-4 w-4" /> Engine Operating Pipeline
                </span>
                <span className="text-[11px] text-slate-400">
                  Scenario Context: <strong className="text-white">{scenario.subtitle}</strong>
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-7">
                {srpvdalNodes.map((stage, idx) => {
                  const isActive = idx === currentStageIndex;
                  const isCompleted = idx < currentStageIndex;
                  return (
                    <div
                      key={stage.key}
                      className={cx(
                        "rounded-xl border p-3 text-center transition-all duration-300",
                        isActive ? "scale-105 border-cyan-300 bg-cyan-300/10 text-cyan-200 shadow-[0_0_15px_rgba(34,211,238,.1)]" :
                        isCompleted ? "border-amber-300/40 bg-amber-300/5 text-amber-200" :
                        "border-white/10 bg-white/[0.01] text-slate-500"
                      )}
                    >
                      <div className="mx-auto flex h-7 w-7 items-center justify-center rounded-full border border-current text-[10px] font-black">
                        {stage.id}
                      </div>
                      <div className="mt-1.5 text-[10px] font-black uppercase">{stage.name.split(" ")[0]}</div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <SurfaceCard className="bg-black/40 p-5">
                  <div className="mb-3 text-xs font-bold text-slate-400">Agent Arbitration Agreement</div>
                  <div className="space-y-2">
                    {scenario.agents.map((agent) => (
                      <div key={agent} className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-2 text-slate-300">
                          <Cpu className="h-3.5 w-3.5 text-cyan-300" /> {agent}
                        </span>
                        <span className={cx("rounded px-2 py-0.5 font-mono text-[10px]", currentStageIndex >= 1 ? "bg-emerald-500/10 text-emerald-300" : "bg-slate-800 text-slate-400")}>
                          {currentStageIndex >= 1 ? "AGREE" : "STAGING"}
                        </span>
                      </div>
                    ))}
                  </div>
                </SurfaceCard>

                <SurfaceCard className="bg-black/40 p-5">
                  <div className="text-xs font-bold text-slate-400">Governed Authorization Score</div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-5xl font-black tracking-tight text-white">{dynamicConfidence}%</span>
                    <span className="text-xs text-slate-400">Confidence Target</span>
                  </div>
                  <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] p-3 text-[11px] leading-5 text-slate-400">
                    <div className="flex items-start gap-2">
                      <ShieldCheck className={cx("mt-0.5 h-4 w-4 shrink-0", dynamicConfidence >= 80 ? "text-emerald-300" : "text-amber-300")} />
                      <span>
                        {dynamicConfidence >= 80 ? "Verification complete. Pathway eligible for authorization with ledger receipt." : "Risk ceiling pressure detected. Staging for human authorization check."}
                      </span>
                    </div>
                  </div>
                </SurfaceCard>
              </div>
            </div>

            <div className="mt-6">
              <div className="flex items-center justify-between px-2 pb-2 font-mono text-[10px] font-bold uppercase text-slate-500">
                <span>Terminal Stream: logs_stdout</span>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,.8)]" />
                  Connection Live
                </span>
              </div>
              <div className="h-40 overflow-y-auto rounded-xl border border-white/10 bg-black p-4 font-mono text-[11px] text-slate-300">
                {simulationLogs.length === 0 && (
                  <div className="flex items-center gap-2 italic text-slate-500">
                    <Info className="h-4 w-4" /> Loop idle. Trigger “Execute Autonomous Loop” to watch logs populate.
                  </div>
                )}
                <div className="space-y-2.5">
                  {simulationLogs.map((log, i) => (
                    <div key={`${log}-${i}`} className="flex items-start gap-2.5">
                      <span className="select-none font-bold text-amber-300">[SEC_{i + 1}]</span>
                      <p>{log}</p>
                    </div>
                  ))}
                  {isRunning && (
                    <div className="flex items-center gap-2 text-[10px] text-cyan-300">
                      <RefreshCw className="h-3 w-3 animate-spin" /> Fetching multi-agent trade signals...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
