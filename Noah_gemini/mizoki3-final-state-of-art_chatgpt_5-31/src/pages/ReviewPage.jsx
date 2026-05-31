import { QuestionAnswerMatrix } from "../components/QuestionAnswerMatrix";
import { StateOfArtStoryVisual } from "../components/StateOfArtStoryVisual";
import { DeploymentCta, FinalCta } from "../components/FinalCta";

export function ReviewPage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-amber-300">Self-Evaluation & Upgrade Plan</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">The site now answers the hard questions directly.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            This page evaluates the site against the review checklist and converts each answer into an improved storytelling and visual system.
          </p>
        </div>
      </section>
      <QuestionAnswerMatrix />
      <StateOfArtStoryVisual />
      <DeploymentCta />
      <FinalCta />
    </>
  );
}
