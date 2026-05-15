/* ==========================================================================
   MIZOKI3 — Animated Nexus visualization (Canvas)
   - Slowly rotating constellation of 5 domain layers around the NEXUS brain
   - Three signal types: memory updates (inbound), actions (outbound), and
     verification pulses (white, governed by Risk)
   - Dashed Risk connection signifies governance gating
   - Faint cross-domain links suggest simulation branches
   ========================================================================== */

(function () {
  const canvas = document.getElementById('nexusCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width, height, cx, cy, ORBIT_RADIUS;
  const NEXUS_RADIUS = 44;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  function resize() {
    const stage = canvas.parentElement;
    width  = stage.clientWidth;
    height = stage.clientHeight;
    canvas.width  = width  * dpr;
    canvas.height = height * dpr;
    canvas.style.width  = width  + 'px';
    canvas.style.height = height + 'px';
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    cx = width / 2;
    cy = height / 2;
    ORBIT_RADIUS = Math.min(width, height) * 0.36;
  }
  window.addEventListener('resize', resize);
  resize();

  // Domain layers — colors from the user palette
  // Order around the ring: Counsel (top), Estate, Capital, Signal, Risk
  const domains = [
    { id: 'counsel', name: 'COUNSEL', color: '#3b82f6', baseAngle: -Math.PI / 2 + (Math.PI * 2 / 5) * 0 },
    { id: 'estate',  name: 'ESTATE',  color: '#10b981', baseAngle: -Math.PI / 2 + (Math.PI * 2 / 5) * 1 },
    { id: 'capital', name: 'CAPITAL', color: '#f59e0b', baseAngle: -Math.PI / 2 + (Math.PI * 2 / 5) * 2 },
    { id: 'signal',  name: 'SIGNAL',  color: '#a855f7', baseAngle: -Math.PI / 2 + (Math.PI * 2 / 5) * 3 },
    { id: 'risk',    name: 'RISK',    color: '#f43f5e', baseAngle: -Math.PI / 2 + (Math.PI * 2 / 5) * 4 },
  ];

  let time = 0;
  let signals = [];

  function spawnSignal() {
    if (Math.random() > 0.4) return;
    const domain = domains[Math.floor(Math.random() * domains.length)];
    const isRisk = domain.id === 'risk';
    const r = Math.random();

    let type, startNode, endNode, color, size, speed;
    if (isRisk && r > 0.4) {
      // Verification pulse — white, glow, runs on the Risk channel
      type = 2;
      startNode = { x: cx, y: cy };
      endNode = domain;
      color = '#ffffff';
      size = 3.5;
      speed = 0.014;
    } else if (r > 0.5) {
      // Memory update / Sense — flows inbound to NEXUS
      type = 0;
      startNode = domain;
      endNode = { x: cx, y: cy };
      color = domain.color;
      size = 2.6;
      speed = 0.010;
    } else {
      // Action / Plan — flows outbound from NEXUS
      type = 1;
      startNode = { x: cx, y: cy };
      endNode = domain;
      color = domain.color;
      size = 2.6;
      speed = 0.012;
    }
    signals.push({ startNode, endNode, progress: 0, speed, color, size, type });
  }
  setInterval(spawnSignal, 150);

  function draw() {
    ctx.clearRect(0, 0, width, height);
    time += 0.005;

    // Update domain positions (slow rotation)
    domains.forEach((d) => {
      const a = d.baseAngle + time * 0.15;
      d.x = cx + Math.cos(a) * ORBIT_RADIUS;
      d.y = cy + Math.sin(a) * ORBIT_RADIUS;
    });

    // Connectors (TCKG substrate) — center to each domain
    ctx.lineWidth = 1;
    domains.forEach((d, i) => {
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(d.x, d.y);
      if (d.id === 'risk') {
        ctx.strokeStyle = 'rgba(244, 63, 94, 0.28)';
        ctx.setLineDash([5, 5]);
        ctx.stroke();
        ctx.setLineDash([]);
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.stroke();
      }
      // Cross-layer simulation branches
      const next = domains[(i + 1) % domains.length];
      ctx.beginPath();
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(next.x, next.y);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
      ctx.stroke();
    });

    // Signals
    for (let i = signals.length - 1; i >= 0; i--) {
      const s = signals[i];
      s.progress += s.speed;
      if (s.progress >= 1) { signals.splice(i, 1); continue; }
      // ease in-out quad
      const p = s.progress;
      const e = p < 0.5 ? 2 * p * p : -1 + (4 - 2 * p) * p;
      const sx = (s.startNode.x !== undefined) ? s.startNode.x : cx;
      const sy = (s.startNode.y !== undefined) ? s.startNode.y : cy;
      const ex = (s.endNode.x   !== undefined) ? s.endNode.x   : cx;
      const ey = (s.endNode.y   !== undefined) ? s.endNode.y   : cy;
      const x = sx + (ex - sx) * e;
      const y = sy + (ey - sy) * e;
      ctx.beginPath();
      ctx.arc(x, y, s.size, 0, Math.PI * 2);
      ctx.fillStyle = s.color;
      ctx.shadowBlur = (s.type === 2) ? 16 : 10;
      ctx.shadowColor = s.color;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // Domain nodes (ring + dot + label)
    domains.forEach((d) => {
      ctx.beginPath();
      ctx.arc(d.x, d.y, 12, 0, Math.PI * 2);
      ctx.fillStyle = '#050505';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = d.color;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(d.x, d.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = d.color;
      ctx.shadowBlur = 12;
      ctx.shadowColor = d.color;
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#e4e4e7';
      ctx.font = "600 12px 'Inter', sans-serif";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const labelDist = 32;
      const a = Math.atan2(d.y - cy, d.x - cx);
      ctx.fillText(d.name, d.x + Math.cos(a) * labelDist, d.y + Math.sin(a) * labelDist);
    });

    // Central NEXUS — pulsing
    const pulse = Math.sin(time * 5) * 4;

    ctx.beginPath();
    ctx.arc(cx, cy, NEXUS_RADIUS + 16 + pulse, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(168, 85, 247, 0.05)';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(cx, cy, NEXUS_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = '#050505';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx, cy, NEXUS_RADIUS - 10, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(168, 85, 247, 0.12)';
    ctx.shadowBlur = 30 + pulse;
    ctx.shadowColor = '#a855f7';
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.fillStyle = '#ffffff';
    ctx.font = "bold 14px 'JetBrains Mono', monospace";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('NEXUS', cx, cy - 2);

    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.fillText('TCKG', cx, cy + 18);

    requestAnimationFrame(draw);
  }
  draw();
})();
