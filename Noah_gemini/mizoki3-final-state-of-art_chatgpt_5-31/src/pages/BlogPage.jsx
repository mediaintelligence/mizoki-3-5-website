import { blogArticle } from "../data/siteData";
import { FinalCta } from "../components/FinalCta";

export function BlogPage() {
  return (
    <>
      <article className="border-b border-white/10 bg-black px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <p className="text-xs font-black uppercase tracking-[0.3em] text-cyan-300">Strategic Blog</p>
          <h1 className="mt-4 text-4xl font-black md:text-6xl">{blogArticle.title}</h1>
          <p className="mt-5 text-sm font-bold uppercase tracking-widest text-amber-300">{blogArticle.author}</p>
          <div className="mt-12 space-y-10">
            {blogArticle.sections.map((section) => (
              <section key={section.heading}>
                <h2 className="text-2xl font-black text-white">{section.heading}</h2>
                <p className="mt-4 text-lg leading-9 text-slate-300">{section.body}</p>
              </section>
            ))}
          </div>
        </div>
      </article>
      <FinalCta />
    </>
  );
}
