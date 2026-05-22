import { useEffect } from 'react';
import Nav from './components/Nav.jsx';
import Hero from './components/Hero.jsx';
import Manifesto from './components/Manifesto.jsx';
import Overview from './components/Overview.jsx';
import Flywheel from './components/Flywheel.jsx';
import Orchestration from './components/Orchestration.jsx';
import DCP from './components/DCP.jsx';
import Veto from './components/Veto.jsx';
import Divisions from './components/Divisions.jsx';
import Nexus from './components/Nexus.jsx';
import Memory from './components/Memory.jsx';
import Governance from './components/Governance.jsx';
import Infrastructure from './components/Infrastructure.jsx';
import Demo from './components/Demo.jsx';
import UseCases from './components/UseCases.jsx';
import CTA from './components/CTA.jsx';
import Footer from './components/Footer.jsx';

const RAIL = [
  { href: '#platform',       label: 'Platform' },
  { href: '#manifesto',      label: 'Premise' },
  { href: '#overview',       label: 'Overview' },
  { href: '#flywheel',       label: 'Flywheel' },
  { href: '#orchestration',  label: 'Loop' },
  { href: '#architecture',   label: 'Control Plane' },
  { href: '#veto',           label: 'The Veto' },
  { href: '#divisions',      label: 'Divisions' },
  { href: '#nexus',          label: 'Nexus' },
  { href: '#memory',         label: 'Memory' },
  { href: '#governance',     label: 'Governance' },
  { href: '#infrastructure', label: 'Architecture' },
  { href: '#contact',        label: 'Pilot' },
];

export default function App() {
  // reveal-on-scroll
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('in');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -6% 0px' }
    );
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

    // active section highlighter for the progress rail
    const railLinks = document.querySelectorAll('[data-rail-link]');
    const navLinks = document.querySelectorAll('[data-nav-link]');
    const sections = document.querySelectorAll('section[id]');
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const id = '#' + e.target.id;
            railLinks.forEach((l) =>
              l.classList.toggle('active', l.getAttribute('href') === id)
            );
            navLinks.forEach((l) =>
              l.classList.toggle('active', l.getAttribute('href') === id)
            );
          }
        });
      },
      { threshold: 0.35 }
    );
    sections.forEach((s) => obs.observe(s));

    return () => { io.disconnect(); obs.disconnect(); };
  }, []);

  return (
    <>
      <Nav />

      {/* progress rail */}
      <nav
        aria-hidden="true"
        className="fixed top-1/2 right-5 -translate-y-1/2 z-[60] hidden xl:flex flex-col gap-[13px]"
      >
        {RAIL.map((r) => (
          <a
            key={r.href}
            href={r.href}
            data-rail-link
            className="relative group block w-[7px] h-[7px] rounded-full border border-ink-4 transition-all hover:border-nexus [&.active]:bg-nexus [&.active]:border-nexus [&.active]:shadow-[0_0_9px_#4cc9ff]"
          >
            <span className="absolute right-4 top-1/2 -translate-y-1/2 font-mono text-[0.58rem] tracking-[0.12em] uppercase text-ink-2 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity bg-bg-0/95 px-2.5 py-1 rounded-full border border-white/10">
              {r.label}
            </span>
          </a>
        ))}
      </nav>

      <main>
        <Hero />
        <Manifesto />
        <Overview />
        <Flywheel />
        <Orchestration />
        <DCP />
        <Veto />
        <Divisions />
        <Nexus />
        <Memory />
        <Governance />
        <Infrastructure />
        <Demo />
        <UseCases />
        <CTA />
      </main>

      <Footer />
    </>
  );
}
