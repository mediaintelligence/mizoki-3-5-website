import { StateOfArtStoryVisual } from "../components/StateOfArtStoryVisual";
import { QuestionAnswerMatrix } from "../components/QuestionAnswerMatrix";
import { FinalCta } from "../components/FinalCta";

export function StoryPage() {
  return (
    <>
      <section className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Narrative System</p>
          <h1 className="mt-4 max-w-5xl text-5xl font-black md:text-7xl">From signal pressure to governed enterprise action.</h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
            This is the story structure the site should carry across every page, visual, animation, demo, and investor deck.
          </p>
        </div>
      </section>
      <StateOfArtStoryVisual />
      <QuestionAnswerMatrix />
      <FinalCta />
    </>
  );
}
