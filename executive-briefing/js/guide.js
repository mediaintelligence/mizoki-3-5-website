/* MIZOKI3 Decision Concierge — the Executive Briefing's guide agent.
 *
 * Guided-by-default for first-time executives; one click collapses it into
 * self-drive. It is a narrator and option framer riding the existing 5-stage
 * briefing: it suggests, highlights, and answers questions — the executive
 * still commits every critical action. This file NEVER programmatically
 * clicks a briefing control (test-enforced: zero click() calls in source).
 *
 * Q&A goes to /api/briefing/guide/ask — allowlist retrieval on the server
 * (mizoki_runtime/briefing_guide.py). No generative path: the concierge
 * cannot invent pricing, certifications, or customer logos. Every
 * interaction is recorded to the guide memory ledger so the briefing
 * improves from real traffic.
 *
 * Mode: window.MIZOKI_CONFIG.guideMode = "guided" (default) | "self".
 */
(function () {
  "use strict";

  if (!document.getElementById("mizoki-briefing") && !document.querySelector("[data-mizoki-briefing]") && !window.MIZOKI) {
    return; // not the briefing page
  }

  // ---- session + mode -----------------------------------------------------

  function makeSessionId() {
    try {
      var buf = new Uint8Array(8);
      crypto.getRandomValues(buf);
      return "gs_" + Array.prototype.map.call(buf, function (b) {
        return ("0" + b.toString(16)).slice(-2);
      }).join("");
    } catch (e) {
      return "gs_" + Date.now().toString(36);
    }
  }
  var SESSION = makeSessionId();

  function configuredMode() {
    try {
      var stored = sessionStorage.getItem("mizokiGuideMode");
      if (stored === "guided" || stored === "self") return stored;
    } catch (e) { /* storage unavailable */ }
    var cfg = window.MIZOKI_CONFIG || {};
    return cfg.guideMode === "self" ? "self" : "guided";
  }

  function rememberMode(mode) {
    try { sessionStorage.setItem("mizokiGuideMode", mode); } catch (e) { /* ok */ }
  }

  // ---- server calls -------------------------------------------------------

  function post(path, body) {
    try {
      return fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch (e) { return Promise.reject(e); }
  }

  function logEvent(event, payload) {
    post("/api/briefing/guide/event", {
      session: SESSION,
      event: event,
      stage: track.stageId,
      domain: track.domain,
      role: track.role,
      payload: payload || {},
    }).catch(function () { /* memory is best-effort, never blocking */ });
  }

  // ---- live briefing state (fed by the app's event bridge) ---------------

  var track = { stageId: "", domain: "", role: "", resolved: 0, decisionIntent: null, started: false };

  // ---- voice replies (OUTPUT ONLY — the concierge speaks; it never listens)
  // Web Speech synthesis on the concierge's own lines and answers. No
  // microphone, no speech recognition, no audio capture, ever. Off by
  // default; the toggle tap is the user gesture browsers require for TTS.
  // cancel() is only ever issued BEFORE queueing the next utterance — a
  // cancel landing on a just-queued utterance wedges Chrome's engine
  // (2026-07-31 regression).

  var voice = {
    ok: false,
    on: false,
    init: function () {
      this.ok = !!(window.speechSynthesis && window.SpeechSynthesisUtterance);
      if (!this.ok) return;
      try { this.on = sessionStorage.getItem("mzg-voice") === "on"; } catch (e) { this.on = false; }
      try { window.speechSynthesis.getVoices(); } catch (e) { /* warm the list */ }
    },
    say: function (text) {
      if (!this.ok || !this.on || !text) return;
      try {
        window.speechSynthesis.cancel(); // clear the queue BEFORE speaking
        var u = new SpeechSynthesisUtterance(text);
        u.lang = "en-US"; u.rate = 1.0; u.pitch = 1.0; u.volume = 1.0;
        window.speechSynthesis.speak(u);
      } catch (e) { /* the bubbles carry every word regardless */ }
    },
    stop: function () {
      if (!this.ok) return;
      try { window.speechSynthesis.cancel(); } catch (e) { /* ok */ }
    }
  };

  // ---- copy ---------------------------------------------------------------
  // Persona: calm senior operator — chief of staff for decisions. Plain
  // language first; at most one architecture name per stage. The concierge
  // suggests; you commit.

  function roleObj() {
    var roles = (window.MIZOKI && MIZOKI.ROLES) || [];
    for (var i = 0; i < roles.length; i++) if (roles[i].id === track.role) return roles[i];
    return { id: track.role, label: "operator", focus: "the outcome that matters to you" };
  }

  function domainObj() {
    var domains = (window.MIZOKI && MIZOKI.DOMAINS) || {};
    return domains[track.domain] || { name: "your domain", short: "your domain", signals: [] };
  }

  function criticalSignal() {
    var sigs = domainObj().signals || [];
    for (var i = 0; i < sigs.length; i++) if (sigs[i].severity === "critical") return sigs[i];
    return null;
  }

  var RECOMMENDED_INTENT = {
    ceo: "pilot", cfo: "board", coo: "pilot", chro: "board", cto: "deep-dive", vp: "pilot"
  };
  var INTENT_LABEL = { pilot: "a scoped pilot", board: "the board packet", "deep-dive": "a technical deep-dive" };

  function stageScript() {
    var d = domainObj();
    var r = roleObj();
    switch (track.stageId) {
      case "context":
        return {
          lines: [
            "I'm your briefing guide — think of me as a chief of staff for this decision. I'll suggest; you commit.",
            "First: who are you in the business, and which domain should we run? Your picks tune every number that follows — the domain sets which live decision loop we run, and your role sets the language of the business case.",
          ],
          suggest: { label: "Set role + domain, then begin", target: "#mb-start" },
        };
      case "exposure":
        return {
          lines: [
            "This is what the status quo already costs in " + d.short + " — modeled from your company size, before any product screens.",
            "As " + r.label + ", read it as " + r.focus + ".",
            "Does it feel high or low? Challenge it — the model is directional by design, and a pilot replaces it with your own data.",
          ],
          suggest: { label: "Continue when the number lands", target: "#mb-next" },
        };
      case "live": {
        var crit = criticalSignal();
        return {
          lines: [
            "Now the proof loop — one real decision, end to end, in the product.",
            crit
              ? "Pick the red signal — “" + crit.title + "”. That is the critical path, and it is the part I cannot do for you: you review the evidence and you commit the action."
              : "Work the signals — the red one is the critical path, and committing it is yours alone.",
            "Ask me what any signal means as you go.",
          ],
          suggest: crit
            ? { label: "Show me the red signal", target: '[data-signal="' + crit.id + '"]' }
            : { label: "Highlight the signal queue", target: "[data-signal]" },
        };
      }
      case "case":
        return {
          lines: [
            "Outcomes translated into your terms: for " + r.label + ", this case is about " + r.focus + ".",
            "Two honest framings from here — a scoped pilot that proves it on your data, or a board packet that schedules the decision properly. No urgency theater; the numbers carry it.",
          ],
          suggest: { label: "Lock the decision path", target: "#mb-next" },
        };
      case "decision": {
        var rec = RECOMMENDED_INTENT[track.role] || "pilot";
        return {
          lines: [
            "Three clean exits: pilot, board packet, or technical deep-dive.",
            "For " + r.label + ", I'd default to " + (INTENT_LABEL[rec] || rec) + " — but all three end the same way: the only open question left is how fast you start.",
          ],
          suggest: { label: "Review the three options", target: "[data-intent], #mb-next" },
        };
      }
      default:
        return {
          lines: [
            "Welcome. This is a structured nine-minute path from your domain reality to a board-ready decision — not a feature tour.",
            "I'm the Decision Concierge: I'll suggest; you commit. Start when ready, or collapse me and self-drive.",
          ],
          suggest: { label: "Begin the briefing", target: "#mb-start" },
        };
    }
  }

  var OBJECTION_CHIPS = [
    { label: "Integration risk?", q: "How risky is integration with our existing stack?" },
    { label: "We already have BI", q: "We already have BI and dashboards — why this?" },
    { label: "Security & data", q: "How is security and data privacy handled?" },
    { label: "Not right now", q: "This is interesting but the timing is not right now." },
    { label: "Who owns budget?", q: "Who typically owns the budget for this?" },
  ];

  var HANDOFF_LINE = "Locked in. Your path is captured — the follow-up arrives with this briefing attached, so nobody starts from zero. Thank you for running it properly.";
  var RESOLVED_LINE = "That commit was yours, not mine — and that is the point. The loop you just closed is the product.";

  // ---- UI -----------------------------------------------------------------

  var ui = { panel: null, tab: null, body: null, chipRow: null, qa: null, input: null, grow: null };

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }

  function css() {
    var s = el("style");
    s.textContent =
      ".mzg-panel{position:fixed;right:18px;bottom:18px;z-index:70;width:min(330px,calc(100vw - 28px));" +
      "background:var(--bg-elevated,#0B1E26);border:1px solid var(--border-strong,#2C4550);" +
      "border-top:2px solid var(--accent,#3FDCF2);border-radius:2px;display:none;" +
      "max-height:min(62vh,560px);flex-direction:column;box-shadow:0 18px 40px rgba(4,10,13,.55);}" +
      ".mzg-panel.on{display:flex;}" +
      ".mzg-head{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--border,#1C2E36);}" +
      ".mzg-dot{width:7px;height:7px;border-radius:50%;background:var(--accent,#3FDCF2);flex:0 0 auto;}" +
      ".mzg-tag{font-family:'JetBrains Mono',monospace;font-size:9.5px;font-weight:700;letter-spacing:.16em;color:var(--accent,#3FDCF2);}" +
      ".mzg-min{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.06em;" +
      "background:transparent;color:var(--fg-muted,#93A0A6);border:1px solid var(--border,#2C4550);border-radius:2px;padding:4px 10px;cursor:pointer;}" +
      ".mzg-min:hover{color:var(--fg,#F4F6F7);}" +
      ".mzg-grow{display:none;font-family:'JetBrains Mono',monospace;font-size:10px;" +
      "background:transparent;color:var(--fg-muted,#93A0A6);border:1px solid var(--border,#2C4550);" +
      "border-radius:2px;padding:4px 9px;cursor:pointer;margin-left:auto;}" +
      ".mzg-grow:hover{color:var(--accent,#3FDCF2);}" +
      ".mzg-grow + .mzg-min{margin-left:6px;}" +
      ".mzg-min + .mzg-min{margin-left:6px;}" +
      ".mzg-body{padding:12px 14px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;}" +
      ".mzg-line{font-family:'DM Sans',sans-serif;font-size:.85rem;line-height:1.55;color:var(--fg,#DCE9ED);}" +
      ".mzg-line.muted{color:var(--fg-muted,#93A0A6);}" +
      ".mzg-suggest{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.05em;text-align:left;" +
      "background:transparent;color:var(--accent,#3FDCF2);border:1px dashed rgba(63,220,242,.5);border-radius:2px;padding:8px 12px;cursor:pointer;}" +
      ".mzg-suggest:hover{border-style:solid;}" +
      ".mzg-chips{display:flex;flex-wrap:wrap;gap:6px;}" +
      ".mzg-chip{font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.04em;" +
      "background:var(--bg,#0A1418);color:var(--fg-muted,#93A0A6);border:1px solid var(--border,#2C4550);border-radius:2px;padding:5px 9px;cursor:pointer;}" +
      ".mzg-chip:hover{color:var(--accent,#3FDCF2);border-color:rgba(63,220,242,.5);}" +
      ".mzg-answer{border-left:2px solid var(--accent,#3FDCF2);padding:7px 10px;background:var(--bg,#0A1418);" +
      "font-size:.82rem;line-height:1.5;color:var(--fg,#DCE9ED);}" +
      ".mzg-answer .mzg-topic{display:block;font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:.14em;" +
      "text-transform:uppercase;color:var(--fg-subtle,#5E6E75);margin-bottom:4px;}" +
      ".mzg-ask{display:flex;gap:6px;padding:10px 14px;border-top:1px solid var(--border,#1C2E36);}" +
      ".mzg-ask input{flex:1;background:var(--bg,#0A1418);border:1px solid var(--border,#2C4550);border-radius:2px;" +
      "color:var(--fg,#F4F6F7);font-family:'DM Sans',sans-serif;font-size:.82rem;padding:8px 10px;}" +
      ".mzg-ask button{font-family:'JetBrains Mono',monospace;font-size:10.5px;background:var(--accent,#3FDCF2);" +
      "color:var(--accent-fg,#06262C);border:1px solid var(--accent,#3FDCF2);border-radius:2px;padding:8px 12px;cursor:pointer;font-weight:700;}" +
      ".mzg-disc{font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:.05em;color:var(--fg-subtle,#5E6E75);" +
      "padding:0 14px 10px;}" +
      ".mzg-tab{position:fixed;right:18px;bottom:18px;z-index:70;font-family:'JetBrains Mono',monospace;font-size:10.5px;" +
      "letter-spacing:.08em;background:var(--bg-elevated,#0B1E26);color:var(--accent,#3FDCF2);" +
      "border:1px solid var(--border-strong,#2C4550);border-left:2px solid var(--accent,#3FDCF2);" +
      "border-radius:2px;padding:9px 14px;cursor:pointer;display:none;}" +
      ".mzg-tab.on{display:block;}" +
      // Docked, never covering: while the panel is open the page reserves the
      // rail's space, so the guide can never intercept a briefing control.
      "@media (min-width:1100px){html.mzg-docked body{padding-right:376px;}" +
      ".mzg-panel{top:84px;bottom:18px;max-height:none;}}" +
      // MOBILE: an open rail that eats half a phone screen sits ON TOP of the
      // briefing's own controls — the executive cannot commit anything. On
      // small screens the guide opens as a compact peek sheet (one coach line
      // + ask box) whose exact height is reserved in the page, and expands
      // only when the visitor asks for it.
      "@media (max-width:1099px){html.mzg-docked body{padding-bottom:170px;}" +
      ".mzg-panel{left:8px;right:8px;width:auto;max-height:152px;}" +
      ".mzg-panel .mzg-body{max-height:54px;}" +
      ".mzg-disc{display:none;}" +
      // The briefing app is min-height:100dvh, so page padding alone still
      // leaves the sheet sitting on the first screenful. Shrinking the app's
      // own height box lays its controls out ABOVE the sheet.
      "html.mzg-docked #mizoki-briefing{min-height:calc(100dvh - 160px);}" +
      "html.mzg-expanded body{padding-bottom:min(70vh,520px);}" +
      "html.mzg-expanded .mzg-panel{max-height:min(68vh,500px);}" +
      "html.mzg-expanded .mzg-panel .mzg-body{max-height:none;}" +
      "html.mzg-expanded #mizoki-briefing{min-height:calc(100dvh - min(70vh,520px));}" +
      ".mzg-grow{display:inline-block;}}" +
      ".mzg-pulse{outline:2px solid var(--accent,#3FDCF2);outline-offset:3px;transition:outline-color .3s ease;}" +
      "@media (prefers-reduced-motion: no-preference){.mzg-pulse{animation:mzgPulse 1.1s ease 2;}}" +
      "@keyframes mzgPulse{0%,100%{outline-color:rgba(63,220,242,.9);}50%{outline-color:rgba(63,220,242,.15);}}";
    document.head.appendChild(s);
  }

  function build() {
    css();
    var p = el("div", "mzg-panel");
    var head = el("div", "mzg-head");
    head.appendChild(el("span", "mzg-dot"));
    head.appendChild(el("span", "mzg-tag", "DECISION CONCIERGE"));
    var grow = el("button", "mzg-grow", "expand");
    grow.type = "button";
    grow.addEventListener("click", function () {
      var on = document.documentElement.classList.toggle("mzg-expanded");
      grow.textContent = on ? "shrink" : "expand";
      if (on) ui.body.scrollTop = 0;
    });
    head.appendChild(grow);
    ui.grow = grow;
    var vbtn = el("button", "mzg-min", voice.on ? "🔊 voice replies" : "🔇 voice replies");
    vbtn.type = "button";
    vbtn.setAttribute("aria-label", "Toggle spoken replies — output-only, never a microphone");
    vbtn.addEventListener("click", function () {
      if (!voice.ok) { vbtn.textContent = "voice unavailable"; return; }
      voice.on = !voice.on;
      try { sessionStorage.setItem("mzg-voice", voice.on ? "on" : "off"); } catch (e) { /* ok */ }
      vbtn.textContent = voice.on ? "🔊 voice replies" : "🔇 voice replies";
      if (voice.on) voice.say("Voice replies on. I speak — I never listen; the bubbles carry every word.");
      else voice.stop();
    });
    head.appendChild(vbtn);
    ui.voiceBtn = vbtn;
    var min = el("button", "mzg-min", "self-drive");
    min.type = "button";
    min.addEventListener("click", collapse);
    head.appendChild(min);
    p.appendChild(head);

    ui.body = el("div", "mzg-body");
    p.appendChild(ui.body);

    var ask = el("div", "mzg-ask");
    ui.input = el("input");
    ui.input.type = "text";
    ui.input.placeholder = "Ask anything about what you're seeing…";
    ui.input.setAttribute("aria-label", "Ask the Decision Concierge a question");
    ui.input.addEventListener("keydown", function (e) { if (e.key === "Enter") submitQuestion(); });
    var send = el("button", null, "ASK");
    send.type = "button";
    send.addEventListener("click", submitQuestion);
    ask.appendChild(ui.input);
    ask.appendChild(send);
    p.appendChild(ask);
    p.appendChild(el("div", "mzg-disc", "// Answers come from the product fact pack — unknowns are logged for a human, never improvised."));

    document.body.appendChild(p);
    ui.panel = p;

    var tab = el("button", "mzg-tab", "🧭 GUIDE");
    tab.type = "button";
    tab.addEventListener("click", expand);
    document.body.appendChild(tab);
    ui.tab = tab;
  }

  function renderStage() {
    if (!ui.body) return;
    var script = stageScript();
    ui.body.textContent = "";
    script.lines.forEach(function (line, i) {
      ui.body.appendChild(el("div", "mzg-line" + (i === 0 ? "" : " muted"), line));
    });
    voice.say(script.lines[0]);
    if (script.suggest) {
      var btn = el("button", "mzg-suggest", "→ " + script.suggest.label);
      btn.type = "button";
      btn.addEventListener("click", function () {
        highlight(script.suggest.target);
        logEvent("suggestion_accepted", { suggestion: script.suggest.label, stage: track.stageId });
      });
      ui.body.appendChild(btn);
    }
    var chips = el("div", "mzg-chips");
    OBJECTION_CHIPS.forEach(function (c) {
      var chip = el("button", "mzg-chip", c.label);
      chip.type = "button";
      chip.addEventListener("click", function () { askServer(c.q); });
      chips.appendChild(chip);
    });
    ui.body.appendChild(chips);
    if (script.suggest) {
      setTimeout(function () { ensureVisible(script.suggest.target); }, 250);
    }
  }

  function isMobile() {
    try { return window.matchMedia("(max-width:1099px)").matches; } catch (e) { return false; }
  }

  // On a phone the docked sheet can sit over the stage's primary control, so
  // the first thing a visitor sees is a button they cannot press. The guide
  // scrolls it into view — a scroll only; it still never presses anything.
  function ensureVisible(selector) {
    if (!selector || !isMobile()) return;
    var target = null;
    selector.split(",").some(function (sel) {
      target = document.querySelector(sel.trim());
      return !!target;
    });
    if (!target || !ui.panel) return;
    var t = target.getBoundingClientRect();
    var p = ui.panel.getBoundingClientRect();
    var occluded = t.bottom > p.top || t.bottom > (window.innerHeight || 0) || t.top < 0;
    if (!occluded) return;
    try { target.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) { /* ok */ }
  }

  function highlight(selector) {
    // Suggest + highlight + unlock — never act. We scroll to the control and
    // pulse it; the executive presses it (or doesn't).
    var target = null;
    selector.split(",").some(function (sel) {
      target = document.querySelector(sel.trim());
      return !!target;
    });
    if (!target) return;
    try { target.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) { /* ok */ }
    target.classList.add("mzg-pulse");
    setTimeout(function () { target.classList.remove("mzg-pulse"); }, 2600);
  }

  function pushAnswer(answer) {
    var wrap = el("div", "mzg-answer");
    var topic = el("span", "mzg-topic", answer.kind === "unknown" ? "logged for follow-up" : answer.kind + " · " + answer.topic);
    wrap.appendChild(topic);
    wrap.appendChild(document.createTextNode(answer.answer));
    ui.body.appendChild(wrap);
    ui.body.scrollTop = ui.body.scrollHeight;
    voice.say(answer.answer);
  }

  function askServer(question) {
    post("/api/briefing/guide/ask", {
      session: SESSION,
      question: question,
      stage: track.stageId,
      domain: track.domain,
      role: track.role,
    })
      .then(function (r) { return r.json(); })
      .then(function (answer) { if (answer && answer.answer) pushAnswer(answer); })
      .catch(function () {
        pushAnswer({ kind: "unknown", topic: "offline", answer: "I can't reach the fact pack right now — the briefing itself keeps working, and your question is worth bringing to the deep-dive." });
      });
  }

  function submitQuestion() {
    var q = (ui.input.value || "").trim();
    if (!q) return;
    ui.input.value = "";
    askServer(q);
  }

  // ---- mode transitions ---------------------------------------------------

  var openedLogged = false;

  function expand() {
    ui.panel.classList.add("on");
    document.documentElement.classList.add("mzg-docked");
    ui.tab.classList.remove("on");
    rememberMode("guided");
    renderStage();
    if (!openedLogged) { openedLogged = true; logEvent("guide_opened", { mode: "guided" }); }
    else { logEvent("guide_resumed", {}); }
  }

  function collapse() {
    voice.stop();
    ui.panel.classList.remove("on");
    document.documentElement.classList.remove("mzg-docked");
    document.documentElement.classList.remove("mzg-expanded");
    if (ui.grow) ui.grow.textContent = "expand";
    ui.tab.classList.add("on");
    rememberMode("self");
    logEvent("guide_collapsed", {});
  }

  // ---- briefing event stream ----------------------------------------------

  var lastStage = null;

  function onBriefingEvent(e) {
    var d = e.detail || {};
    track.stageId = d.stageId || track.stageId;
    track.domain = d.domain || track.domain;
    track.role = d.role || track.role;
    track.resolved = typeof d.resolved === "number" ? d.resolved : track.resolved;
    track.decisionIntent = d.decisionIntent || track.decisionIntent;
    track.started = !!d.started;

    switch (d.event) {
      case "render":
        if (track.stageId !== lastStage) {
          lastStage = track.stageId;
          if (ui.panel && ui.panel.classList.contains("on")) renderStage();
        }
        break;
      case "stage_changed":
        logEvent("stage_changed", { stage: track.stageId });
        break;
      case "signal_resolved":
        logEvent("signal_resolved", { id: (d.detail || {}).id || "" });
        if (ui.panel && ui.panel.classList.contains("on")) {
          ui.body.appendChild(el("div", "mzg-line", RESOLVED_LINE));
          ui.body.scrollTop = ui.body.scrollHeight;
          voice.say(RESOLVED_LINE);
        }
        break;
      case "decision_intent":
        logEvent("decision_intent", { intent: (d.detail || {}).intent || d.decisionIntent || "" });
        break;
      case "decision_confirmed":
        logEvent("decision_confirmed", { intent: (d.detail || {}).intent || d.decisionIntent || "" });
        logEvent("guide_handoff", { intent: (d.detail || {}).intent || "" });
        if (ui.panel && ui.panel.classList.contains("on")) {
          ui.body.appendChild(el("div", "mzg-line", HANDOFF_LINE));
          ui.body.scrollTop = ui.body.scrollHeight;
          voice.say(HANDOFF_LINE);
        }
        break;
    }
  }

  // ---- boot ---------------------------------------------------------------

  function boot() {
    voice.init();
    build();
    document.addEventListener("mizoki:briefing", onBriefingEvent);
    if (configuredMode() === "guided") expand();
    else { ui.tab.classList.add("on"); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
