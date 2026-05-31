import { Link } from "react-router-dom";
import { Button } from "../components/Button";

export function NotFound() {
  return (
    <section className="min-h-[70vh] bg-black px-6 py-24 text-center">
      <h1 className="text-5xl font-black">Page not found.</h1>
      <p className="mx-auto mt-5 max-w-xl text-slate-400">Return to the platform overview or launch the simulator console.</p>
      <div className="mt-8 flex justify-center gap-4">
        <Link to="/"><Button>Platform</Button></Link>
        <Link to="/simulator"><Button variant="amber">Simulator</Button></Link>
      </div>
    </section>
  );
}
