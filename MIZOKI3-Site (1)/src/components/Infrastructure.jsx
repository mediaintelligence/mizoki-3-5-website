import { ShieldCheck, Key, Network } from 'lucide-react';

const NODES = [
  { x: 80,  y: 90,  label: 'BigQuery + Neo4j', sub: 'TCKG Substrate',       c: '#a855f7' },
  { x: 240, y: 60,  label: 'Cloud Pub/Sub',    sub: 'Nexus Event Bus',      c: '#34a6ff' },
  { x: 400, y: 90,  label: 'Google Cloud Run', sub: 'SRPVDAL Orchestrator', c: '#21d07a' },
  { x: 240, y: 160, label: 'Vertex AI',        sub: 'Isolated Reasoning',   c: '#f5a623' },
];

const EDGES = [
  [80, 90,  240, 60],
  [80, 90,  240, 160],
  [240, 60, 400, 90],
  [240, 160, 400, 90],
  [240, 60, 240, 160],
];

const CHIPS = [
  { icon: <Key className="w-4 h-4 text-nexus" />, k: 'Cloud KMS', v: 'Customer-managed key · 90-day rotation' },
  { icon: <ShieldCheck className="w-4 h-4 text-nexus" />, k: 'IAM + Workload Identity', v: 'Strict identity on every internal hop' },
  { icon: <Network className="w-4 h-4 text-nexus" />, k: 'VPC Service Controls', v: 'Data-exfiltration perimeter · enterprise SLA' },
];

const SOV = [
  { n: 'i', t: 'Sealed perimeter',
    d: 'Every Cloud Run cell sets ingress = INTERNAL_ONLY. The entire reasoning loop runs in a private subnet — no public endpoint to the brain.' },
  { n: 'ii', t: 'Owned, not rented',
    d: 'Delivered as Terraform. The enterprise provisions it in their own GCP project, holds the Cloud KMS keys, and audits every line.' },
  { n: 'iii', t: 'No training leakage',
    d: 'Reasoning routes through Claude on Vertex AI under IAM scope. Private contracts and capital telemetry are never used to train foundation models.' },
];

export default function Infrastructure() {
  return (
    <section id="infrastructure" className="py-24">
      <div className="max-w-[1340px] mx-auto px-7">
        <div className="reveal text-center max-w-[820px] mx-auto mb-14">
          <div className="chapter-marker !justify-center">
            <span className="ln" />
            <span className="num">11</span>
            <span>Fiduciary-Grade Infrastructure</span>
            <span className="ln-r" />
          </div>
          <h2 className="text-[clamp(1.7rem,2.9vw,2.6rem)] mb-2.5">
            Built on <em className="serif-i">Google Cloud,</em> owned by you.
          </h2>
          <div className="text-ink-3 text-base">
            Zero-trust VPC. Customer-managed encryption. Reasoning isolated to
            current-generation Claude on Vertex AI. Delivered as Terraform —
            provisioned in your own GCP project.
          </div>
        </div>

        <div className="reveal max-w-[1080px] mx-auto rounded-2xl border border-white/[0.08] bg-bg-1/40 p-7">
          <div className="flex items-center justify-between mb-5">
            <div className="font-mono text-[0.66rem] uppercase tracking-[0.18em] text-nexus">
              Zero-Trust GCP VPC · us-central1 · Private Subnet Only
            </div>
            <div className="font-mono text-[0.6rem] text-ink-4 flex items-center gap-2">
              <span aria-hidden className="inline-block w-2 h-2 rounded-full bg-estate" />
              CMEK · IAM · VPC-SC
            </div>
          </div>

          <div className="relative rounded-xl border border-dashed border-nexus/40 p-6">
            <svg viewBox="0 0 480 240" className="w-full h-auto">
              {EDGES.map(([x1, y1, x2, y2], i) => (
                <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke="#46506e" strokeWidth="1" strokeDasharray="3 3" />
              ))}
              {NODES.map((n, i) => (
                <g key={i}>
                  <rect x={n.x - 50} y={n.y - 22} width="100" height="44" rx="6"
                        fill="#070b1c" stroke={n.c} strokeWidth="1.5" />
                  <text x={n.x} y={n.y - 4} textAnchor="middle" fill="#f3f5fc"
                        fontSize="10" fontFamily="JetBrains Mono">{n.label}</text>
                  <text x={n.x} y={n.y + 12} textAnchor="middle" fill="#6c7799"
                        fontSize="8.5" fontFamily="JetBrains Mono">{n.sub}</text>
                </g>
              ))}
            </svg>
          </div>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
            {CHIPS.map((b) => (
              <div key={b.k} className="flex items-start gap-3 p-3 rounded-lg border border-white/[0.06]">
                <div className="shrink-0 mt-0.5">{b.icon}</div>
                <div>
                  <div className="font-mono text-[0.66rem] uppercase tracking-[0.14em] text-ink">{b.k}</div>
                  <div className="text-ink-3 text-xs leading-relaxed mt-0.5">{b.v}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-[1080px] mx-auto">
          {SOV.map((c, i) => (
            <div key={c.n}
                 className="reveal stagger p-6 rounded-xl border border-white/10 bg-bg-1/40"
                 style={{ '--i': i }}>
              <div className="font-display text-2xl italic text-nexus mb-2">{c.n}</div>
              <h4 className="font-semibold text-base mb-2">{c.t}</h4>
              <p className="text-ink-3 text-sm leading-relaxed">{c.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
