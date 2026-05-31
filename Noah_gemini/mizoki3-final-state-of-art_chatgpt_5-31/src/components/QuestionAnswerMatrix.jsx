import {
  Activity,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Eye,
  Gauge,
  Network,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import { SurfaceCard } from "./SurfaceCard";

const answers = [
  {
    question: "Does the homepage immediately feel more enterprise-grade?",
    verdict: "Yes — now sharpened.",
    answer:
      "The hero positions MIZOKI3 as infrastructure, not a chatbot. The new state-of-the-art upgrade adds board-level language, system status telemetry, and a clear causal-governance thesis above the fold.",
    upgrade:
      "Make the first screen feel like an enterprise command environment: causality, authority, traceability, and operating status should be visible before any user scrolls.",
    icon: Sparkles,
  },
  {
    question: "Does the site explain why MIZOKI3 is not just another AI dashboard?",
    verdict: "Yes — now explicit.",
    answer:
      "The Anti-Dashboard Thesis now says MIZOKI3 does not summarize data; it converts signals into governed, threshold-aware actions through a plug-in decision layer.",
    upgrade:
      "Frame dashboards as passive observation and MIZOKI3 as active operational governance. This contrast gives the buyer a reason to care immediately.",
    icon: Network,
  },
  {
    question: "Does the simulator make the product feel real?",
    verdict: "Yes — strongest proof point.",
    answer:
      "The simulator is the product demo moment. It lets a user choose Capital, Media, or Counsel, adjust risk bounds, select counterfactual paths, execute the loop, and watch audit logs populate.",
    upgrade:
      "Treat the simulator as the sales engine of the site. It turns abstract architecture into a tangible autonomous-decision experience.",
    icon: Activity,
  },
  {
    question: "Does the Decision Control Plane feel like the AI governor?",
    verdict: "Yes — now needs to stay central.",
    answer:
      "The DCP now reads like an authorization firewall: context sufficiency, identity, policy, risk, confidence, escalation, and execution all become explicit gates.",
    upgrade:
      "Never describe autonomy without showing the control layer. The DCP is the trust object executives, CISOs, boards, and counsel will remember.",
    icon: ShieldCheck,
  },
  {
    question: "Does the SRPVDAL loop feel understandable and visual?",
    verdict: "Yes — now operational.",
    answer:
      "SRPVDAL now appears as both an interactive engine monitor and a simulator stepper. Users can see Sense, Reason, Plan, Validate, Decide, Act, and Learn as sequential operating states.",
    upgrade:
      "Keep the loop visible in multiple contexts: architecture, simulator, decision replay, governance, and learning. Repetition makes the model memorable.",
    icon: Workflow,
  },
  {
    question: "Does the site clearly say AI should not act unless the right conditions are true?",
    verdict: "Yes — now the core philosophy.",
    answer:
      "The decisive question is now directly stated: not whether AI can act, but what must be true before it is allowed to act.",
    upgrade:
      "Turn that sentence into the brand moat. It separates MIZOKI3 from copilots, agents, dashboards, and workflow automation.",
    icon: Gauge,
  },
  {
    question: "Does the visual system feel premium, institutional, and credible?",
    verdict: "Yes — now more defensible.",
    answer:
      "The design language uses dark institutional surfaces, cyan/amber control colors, command-center cards, terminal logs, authorization panels, and motion that implies live intelligence.",
    upgrade:
      "Maintain restraint: fewer decorative graphics, more operational visuals. Every visual should explain causality, authorization, traceability, or learning.",
    icon: Eye,
  },
];

export function QuestionAnswerMatrix() {
  return (
    <section className="border-y border-white/10 bg-[#030305] px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-14 max-w-4xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Final Review Answered</p>
          <h2 className="mt-4 text-4xl font-black md:text-6xl">Seven questions. Seven upgrades. One state-of-the-art story.</h2>
          <p className="mt-5 text-lg leading-8 text-slate-300">
            This section answers the evaluation questions directly and converts each answer into a concrete design and storytelling improvement.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          {answers.map((item, index) => {
            const Icon = item.icon;
            return (
              <SurfaceCard key={item.question} className="group overflow-hidden p-6 transition-all hover:border-cyan-300/25 hover:bg-white/[0.05]">
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10">
                      <Icon className="h-6 w-6 text-cyan-300" />
                    </div>
                    <div>
                      <p className="font-mono text-xs uppercase tracking-widest text-slate-500">Review Question 0{index + 1}</p>
                      <p className="mt-1 text-sm font-black uppercase tracking-wider text-emerald-300">{item.verdict}</p>
                    </div>
                  </div>
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-300" />
                </div>

                <h3 className="text-xl font-black leading-snug text-white">{item.question}</h3>
                <p className="mt-4 leading-7 text-slate-300">{item.answer}</p>

                <div className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/5 p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-amber-300">
                    <ArrowRight className="h-4 w-4" /> State-of-the-art implementation
                  </div>
                  <p className="text-sm leading-6 text-slate-400">{item.upgrade}</p>
                </div>
              </SurfaceCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
