/* MIZOKI3 Boss Docent — voice-guided tours + Ask-the-Boss, across the demo platform.
 *
 * The Boss agent narrates a live demo run on every desk: it presses Start
 * itself, watches the same DOM the visitor watches, and explains each action
 * using the run's OWN numbers (gate rows, guardrail veto text, causal truth,
 * finale cards) — never invented figures. It also answers typed questions out
 * loud from the server-side vetted briefing pack (/api/briefing/guide/ask —
 * allowlist retrieval, no generative path). Output-only voice: Web Speech
 * synthesis (TTS). No microphone, no audio capture, ever — the Boss speaks;
 * it never listens.
 *
 * Claims discipline (binding, tested in tests/test_boss_docent.py):
 *   - anticipatory intent with proof of causal lift — never mind-reading
 *   - calibrated probabilities — an account is never promised to buy
 *   - figures are illustrative scenario output, never a promise of results
 *   - exactly one soft call-to-action construction, at the end; no pressure
 *
 * Zero dependencies, zero changes to the demo players. Degrades to
 * captions-only when speech synthesis is unavailable.
 */
(function () {
  "use strict";

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) { /* older browsers */ }

  // ---- narration copy (static frame — dynamic slots read from the DOM) ----
  // Every sentence here is pre-vetted marketing copy. Do not ad-lib additions
  // without re-running the claims-lint test.
  var COPY = {
    label: "BOSS AGENT — GUIDED TOUR",
    disclosure: "Voice is output-only. I speak — I never listen. No microphone is used.",
    interrupted: "Taking my hands off the controls — it's your run now. Ask me anything below.",
    trouble: "The runtime isn't responding from your network right now, so I'll stop the tour here. The controls above work the moment it's back.",
    stoppedLine: "Tour stopped — the desk is yours. Ask me anything below, or restart the tour when you like.",
    closeShared: "If this discipline is what your team is missing, the executive briefing takes about nine minutes, or you can request a pilot below. No pressure — the trace speaks for itself.",

    gateIntro: [
      "Now the ReLU gate — the first honest moment of this pipeline.",
      "A signal passes only if uplift, confidence, and sample size all clear their thresholds. Weak evidence is filtered out, with its reason recorded."
    ],
    gateFilteredFrame: "I want you to notice what we rejected: ",
    gateFilteredClose: "Most platforms would have acted on that anyway. We would rather show you what we filter than inflate what we accept.",
    decisionIntro: "The decision card. One action earned execution, and it carries its full provenance chain — raw event to canonical envelope to signal to gate to guardrails to decision.",
    causalIntro: "And this is the causal truth, composed from the run data itself: ",
    replayNote: "Every number I just read came from this run's trace. Re-run the same seed and I will say exactly the same thing — that is what auditable means.",

    askTag: "ASK THE BOSS",
    askPlaceholder: "Type a question — I answer out loud. I never listen.",
    askThinking: "Checking the briefing pack…",
    askFail: "I can't reach the runtime from your network right now — try the question again in a moment.",

    chipRemix: "▶ Replay remixed (new seed)",
    chipRestart: "▶ Restart the guided tour",
    chipBriefing: "Executive briefing →",
    chipPilot: "Request a pilot →",
    chipSignal: "Open the Signal Factory →"
  };

  // ---- per-desk profiles ----------------------------------------------------
  // kind: "pipeline" (signal/capital share the SRPVDAL pipeline DOM),
  //       "watch"    (start the run, narrate, read the finale card),
  //       "counsel"  (consult the experts, read the synthesis),
  //       "welcome"  (the /demo hub — orientation, no run to drive).
  var PROFILES = {
    hub: {
      key: "hub", kind: "welcome", watch: [],
      launch: "Hear the Boss — a voice tour of this hub",
      intro: [
        "Hello — I'm the Boss agent, the orchestration layer this platform runs on.",
        "This hub is the technical track: six live desks — Signal, Capital, Counsel, Estate, Risk, and the Nexus boardroom. Every one is an illustrative scenario executed on the production runtime — deterministic and seeded, so you can replay any run and check it.",
        "If you want the fastest proof, open the Signal Factory: raw events become one governed decision in about a minute, including a deliberate red veto most demos would hide.",
        "For decision-makers there is a nine-minute executive briefing — the second chip below.",
        "And you can ask me anything in the box on this bar. Voice is output-only — I speak; I never listen."
      ],
      close: []
    },
    signal: {
      key: "signal", kind: "pipeline",
      need: ["startBtn", "stageStrip"], watch: ["startBtn", "resetBtn", "scenario"],
      launch: "Guided tour — let the Boss walk you through",
      intro: [
        "Hello — I'm the Boss agent, the orchestration layer this platform runs on.",
        "I'll start a live run of the Signal Factory and explain every action as it happens, using this run's own numbers.",
        "Everything you'll see is an illustrative scenario executed on the production runtime — deterministic and seeded, so you can replay it and check me.",
        "You can pause me or take the controls at any time. Starting the run now."
      ],
      rail: [
        "Raw events are arriving on the factory floor from the connectors — ads, analytics, email, CRM.",
        "Watch the cyan seam on each card: nothing downstream is allowed to touch an event until it is normalized into a canonical envelope.",
        "That rule is structural. No connector ever talks straight to an action."
      ],
      validate: [
        "Here is the part most demos hide: the validation stage just blocked something, deliberately, in red.",
        "The veto is not an opinion — it is arithmetic against a guardrail. The trace is open below — read the check for yourself."
      ],
      close: [
        "That's the factory: raw signals in, governed decisions out, one deliberate refusal on the record.",
        "The figures are an illustrative scenario — in a pilot, your own signals would do the talking."
      ]
    },
    capital: {
      key: "capital", kind: "pipeline",
      need: ["startBtn", "stageStrip"], watch: ["startBtn", "resetBtn", "scenario"],
      launch: "Guided tour — the Boss runs the Capital Desk",
      intro: [
        "Hello — I'm the Boss agent. This is the Capital Desk: treasury and portfolio moves running through the platform's governed pipeline.",
        "I'll start a live run and explain each action with this run's own numbers — an illustrative scenario on the production runtime, deterministic and seeded.",
        "Watch for the covenant guardrail: any move that would drop modeled headroom below the floor is blocked in red before it can execute. Starting the run now."
      ],
      rail: [
        "Ledger entries, covenant snapshots, and market quotes are streaming onto the desk from the connectors.",
        "Each one is normalized into a canonical envelope before anything downstream may touch it — no connector ever talks straight to an action.",
        "Return signals form next, and they face the same ReLU gate as every other division."
      ],
      validate: [
        "Here is the moment this desk exists for: the covenant guardrail just blocked a move, deliberately, in red.",
        "Any move that drops modeled covenant headroom below the floor is vetoed before it can execute — arithmetic against the covenant, not an opinion."
      ],
      close: [
        "That's the Capital Desk: market data in, governed treasury moves out, and the covenant floor enforced in the open.",
        "The figures are an illustrative scenario — in a pilot, your own ledger would do the talking."
      ]
    },
    estate: {
      key: "estate", kind: "watch",
      need: ["startBtn"], watch: ["startBtn", "resetBtn", "scenario"],
      finale: "finaleCard", read: "finale",
      launch: "Guided tour — the Boss walks the Estate Room",
      intro: [
        "Hello — I'm the Boss agent. This is the Estate Room: statutory timelines, dynasty graphs, and basis step-up tables, drawn live.",
        "Everything is an illustrative scenario on the production runtime — deterministic and seeded — and every output on this desk is flagged for attorney review. Starting the run now."
      ],
      mid: [
        "Watch the instrument draw itself — the statutory clock, the dynasty graph, or the step-up table, depending on the scenario.",
        "Every node carries its authority: the statute, the code section, or the governing document it came from.",
        "Nothing on this desk self-executes. The platform prepares the analysis; counsel decides."
      ],
      finaleIntro: "The room has finished. ",
      close: [
        "That's the Estate Room: authority-linked analysis, drawn from the scenario's own record, always routed to a human."
      ]
    },
    risk: {
      key: "risk", kind: "watch",
      need: ["startBtn"], watch: ["startBtn", "resetBtn", "scenario"],
      finale: "finaleCard", read: "finale",
      launch: "Guided tour — the Boss walks the Risk Desk",
      intro: [
        "Hello — I'm the Boss agent. This is the Risk Desk: enterprise events landing on a five-by-five severity and likelihood matrix, cell by cell.",
        "It's an illustrative scenario on the production runtime — deterministic and seeded. Starting the run now."
      ],
      mid: [
        "Contract clause changes, spend spikes, access anomalies, covenant drift — each event is scored onto the matrix as it lands.",
        "Exactly two will earn an escalation: one auto-mitigates quietly in green, and one is vetoed loudly in red — with a rule id, an evidence chain, and a rollback token.",
        "That red veto is the point: governance you can read, not a black box."
      ],
      finaleIntro: "The run is complete. ",
      close: [
        "That's the Risk Desk: one quiet mitigation, one loud refusal, and the evidence to prove why."
      ]
    },
    nexus: {
      key: "nexus", kind: "watch",
      need: ["startBtn"], watch: ["startBtn", "resetBtn", "scenario"],
      finale: "provenancePanel", read: "nexus",
      launch: "Guided tour — the Boss runs the Nexus",
      intro: [
        "Hello — I'm the Boss agent. This is the Nexus: one trigger enters, and it ripples through all five divisions under a single trace id.",
        "It's an illustrative scenario on the production runtime — deterministic and seeded. Starting explore mode now."
      ],
      mid: [
        "Signal reallocates. Capital re-checks the covenant envelope. Risk vetoes the aggressive variant. Counsel flags the indemnity clause — and Estate records that nothing needed to fire.",
        "Same runtime, same governance, shared causal memory — that is what one intelligence across many domains means."
      ],
      finaleIntro: "The ripple is complete. ",
      finaleLines: [
        "Open any division panel to read its slice of the same trace — or put Boardroom mode on the projector."
      ],
      close: [
        "That's the Nexus: five divisions, one trigger, one trace id."
      ]
    },
    counsel: {
      key: "counsel", kind: "counsel",
      need: ["scenarioGrid", "askBtn"], watch: ["askBtn"],
      launch: "Guided tour — the Boss consults the experts",
      intro: [
        "Hello — I'm the Boss agent. This is the Counsel Room: a legal scenario fans out to four domain experts — Connecticut, Trust, Estate, and Tax.",
        "Each expert returns an IRAC analysis with real statutory authorities, and a synthesizer reconciles them and surfaces cross-domain conflicts.",
        "Everything is an illustrative scenario, flagged for attorney review. I'll run a scripted Connecticut scenario now."
      ],
      mid: [
        "The router is scoring the four experts for relevance — experts under the threshold are listed but not consulted.",
        "Now the consulted experts return their analyses: issue, rule, application, conclusion — each with its authorities cited."
      ],
      close: [
        "That's the Counsel Room: four experts, one reconciled playbook, and the conflicts surfaced instead of smoothed over."
      ]
    }
  };

  // ---- tiny DOM helpers ---------------------------------------------------

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }
  function txt(node) { return node ? (node.textContent || "").replace(/\s+/g, " ").trim() : ""; }
  function clip(s, max) {
    if (!s) return "";
    if (s.length <= max) return s;
    var cut = s.slice(0, max);
    var sp = cut.lastIndexOf(" ");
    return (sp > 40 ? cut.slice(0, sp) : cut) + "…";
  }

  function sessionId() {
    try {
      var sid = sessionStorage.getItem("mzd_session");
      if (!sid) {
        sid = "ds_" + Math.random().toString(16).slice(2, 10) + Date.now().toString(16).slice(-4);
        sessionStorage.setItem("mzd_session", sid);
      }
      return sid;
    } catch (e) { return "ds_anon"; }
  }

  // ---- speech engine (TTS output only; captions always) -------------------

  var speech = {
    available: false,
    enabled: true,
    voice: null,
    utter: null,
    timer: null,
    beat: null,
    errors: 0,
    onProblem: null,

    init: function () {
      this.available = !!(window.speechSynthesis && window.SpeechSynthesisUtterance);
      if (!this.available) { this.enabled = false; return; }
      // Warm the voice list — several browsers populate it asynchronously and
      // return [] on the first synchronous call. The voice itself is resolved
      // fresh at speak time (pickVoice), never cached across list refreshes.
      var self = this;
      function warm() { self.voices(); }
      warm();
      try { window.speechSynthesis.onvoiceschanged = warm; } catch (e) { /* ok */ }
    },

    cancel: function () {
      if (this.timer) { clearTimeout(this.timer); this.timer = null; }
      this.stopHeartbeat();
      if (this.available) { try { window.speechSynthesis.cancel(); } catch (e) { /* ok */ } }
    },

    // iOS unlock note: the FIRST speak() must happen inside a real user
    // gesture — which it does, because the launch tap calls beginTour ->
    // speakSeq -> sentence synchronously. Do NOT add a separate "silent
    // unlock" utterance here: a cancel() landing on a just-queued utterance
    // wedges Chrome's synthesis engine and silences everything after it
    // (2026-07-31 regression — voice died on desktop and mobile).

    voices: function () {
      try { return window.speechSynthesis.getVoices() || []; } catch (e) { return []; }
    },

    // Chrome silences an utterance whose .voice is a stale object from an
    // earlier getVoices() list, so re-resolve against the live list.
    pickVoice: function () {
      var list = this.voices();
      if (!list.length) return null;
      var ranked = [/Google US English/i, /Microsoft (Aria|Jenny|Guy)/i, /Samantha/i, /en[-_]US/i, /^en/i];
      for (var i = 0; i < ranked.length; i++) {
        for (var v = 0; v < list.length; v++) {
          var label = (list[v].name || "") + " " + (list[v].lang || "");
          if (ranked[i].test(label)) return list[v];
        }
      }
      return list[0] || null;
    },

    // Chrome (desktop and Android) silently stops synthesis after ~15s.
    // A periodic pause/resume keeps long narration alive; harmless elsewhere.
    startHeartbeat: function () {
      if (!this.available || this.beat) return;
      var self = this;
      this.beat = setInterval(function () {
        try {
          if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
          }
        } catch (e) { self.stopHeartbeat(); }
      }, 9000);
    },

    stopHeartbeat: function () {
      if (this.beat) { clearInterval(this.beat); this.beat = null; }
    },

    // Never leave the visitor guessing why it is quiet: if the engine refuses
    // an utterance (no installed voices, muted platform, policy block), say so
    // in the control instead of silently running captions.
    fail: function () {
      this.errors += 1;
      if (this.errors === 1 && this.onProblem) { try { this.onProblem(); } catch (e) { /* ok */ } }
    },

    // Speak one sentence; ALWAYS calls done exactly once (speech end, caption
    // timer, or safety timeout — synthesis can stall in background tabs).
    // A minimum reading time is enforced even when synthesis "finishes"
    // instantly (browsers that expose speechSynthesis with no working voice
    // error out per-utterance) so captions stay readable in every mode.
    sentence: function (text, done) {
      var self = this;
      var finished = false;
      var startedAt = Date.now();
      var minMs = reduceMotion ? 500 : Math.max(1400, text.length * 45);
      function finish() {
        if (finished) return;
        finished = true;
        if (self.timer) { clearTimeout(self.timer); self.timer = null; }
        var remaining = minMs - (Date.now() - startedAt);
        if (remaining > 0) { setTimeout(done, remaining); } else { done(); }
      }
      var readMs = Math.max(1600, text.length * 62);
      if (!this.available || !this.enabled) {
        this.timer = setTimeout(finish, reduceMotion ? 500 : readMs);
        return;
      }
      var u;
      try {
        u = new SpeechSynthesisUtterance(text);
        u.lang = "en-US";
        // A voice assignment can THROW (stale object from an earlier
        // getVoices() generation). If it escaped here before the safety
        // timer is armed, the whole tour would wedge — so it never escapes.
        try {
          var picked = this.pickVoice();
          if (picked) u.voice = picked;
        } catch (ve) { /* engine default voice */ }
        u.rate = 1.0; u.pitch = 1.0; u.volume = 1.0;
        u.onend = finish;
        u.onerror = function () { self.fail(); finish(); };
      } catch (ce) { this.fail(); this.timer = setTimeout(finish, readMs); return; }
      this.utter = u;
      try { window.speechSynthesis.speak(u); this.startHeartbeat(); } catch (e) { this.fail(); finish(); return; }
      this.timer = setTimeout(finish, readMs * 2 + 4000); // safety net
    }
  };

  // ---- docent UI (self-injected, dossier vocabulary) ----------------------

  var prof = null;

  var ui = {
    bar: null, caption: null, chipRow: null, voiceBtn: null, stopBtn: null,
    launchBtn: null, askInput: null,

    css: function () {
      var s = el("style");
      s.textContent =
        // The launcher is a fixed pill on EVERY viewport — the voice must be
        // discoverable without scrolling, on the hub and all six desks alike.
        ".bd-launch{position:fixed;right:12px;bottom:12px;z-index:71;display:inline-flex;" +
        "align-items:center;gap:10px;margin:0;" +
        "font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.08em;" +
        "background:#0B1E26;color:#DCE9ED;border:1px solid #2C4550;border-left:2px solid #9D7BE8;" +
        "border-radius:2px;padding:12px 16px;cursor:pointer;transition:border-color .2s ease;" +
        "box-shadow:0 8px 24px rgba(4,10,13,.5);}" +
        ".bd-launch:hover{border-color:#9D7BE8;color:#F4F6F7;}" +
        ".bd-launch .bd-note{color:#5E7780;font-size:10px;letter-spacing:.05em;}" +
        "@media (prefers-reduced-motion: no-preference){.bd-launch{animation:bdNudge 2.2s ease 2;}}" +
        "@keyframes bdNudge{0%,100%{border-left-color:#9D7BE8;}50%{border-left-color:#3FDCF2;}}" +
        ".bd-bar{position:fixed;left:0;right:0;bottom:0;z-index:72;background:#0B1E26;" +
        "border-top:1px solid #2C4550;padding:12px 5% 14px;display:none;}" +
        ".bd-bar.on{display:block;}" +
        ".bd-bar.on ~ .bd-launch{display:none;}" +
        ".bd-head{display:flex;align-items:center;gap:10px;margin-bottom:6px;}" +
        ".bd-dot{width:8px;height:8px;border-radius:50%;background:#9D7BE8;flex:0 0 auto;}" +
        ".bd-bar.speaking .bd-dot{background:#3FDCF2;}" +
        ".bd-tag{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;" +
        "letter-spacing:.18em;color:#9D7BE8;}" +
        ".bd-ctl{margin-left:auto;display:flex;gap:8px;}" +
        ".bd-btn{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.08em;" +
        "background:transparent;color:#93A0A6;border:1px solid #2C4550;border-radius:2px;" +
        "padding:5px 12px;cursor:pointer;}" +
        ".bd-btn:hover{color:#F4F6F7;border-color:#93A0A6;}" +
        ".bd-cap{font-family:'DM Sans',sans-serif;font-size:.95rem;color:#DCE9ED;" +
        "line-height:1.5;min-height:1.5em;max-width:1100px;}" +
        // While the bar is up, reserve its space so it never sits on top of
        // the demo controls (fixed bars cover content otherwise).
        "html.bd-open body{padding-bottom:265px;}" +
        "html.bd-open .bd-launch{display:none;}" +
        ".bd-disc{font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.06em;" +
        "color:#5E7780;margin-top:5px;}" +
        ".bd-ask{display:flex;gap:8px;margin-top:10px;max-width:760px;align-items:center;}" +
        ".bd-ask .bd-ask-tag{font-family:'JetBrains Mono',monospace;font-size:9.5px;font-weight:700;" +
        "letter-spacing:.14em;color:#3FDCF2;flex:0 0 auto;}" +
        ".bd-ask input{flex:1;min-width:0;background:#0A1418;border:1px solid #2C4550;color:#DCE9ED;" +
        "font-family:'DM Sans',sans-serif;font-size:.9rem;padding:8px 10px;border-radius:2px;}" +
        ".bd-ask input:focus{outline:none;border-color:#3FDCF2;}" +
        ".bd-ask button{font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;" +
        "letter-spacing:.08em;background:#0A1418;color:#3FDCF2;border:1px solid rgba(63,220,242,.45);" +
        "border-radius:2px;padding:8px 14px;cursor:pointer;}" +
        ".bd-ask button:hover{border-color:#3FDCF2;}" +
        ".bd-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:9px;}" +
        ".bd-chip{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.06em;" +
        "background:#0A1418;color:#3FDCF2;border:1px solid rgba(63,220,242,.45);" +
        "border-radius:2px;padding:7px 14px;cursor:pointer;text-decoration:none;display:inline-block;}" +
        ".bd-chip:hover{border-color:#3FDCF2;}" +
        // MOBILE: tighter paddings; the caption scrolls instead of growing.
        "@media (max-width:900px){" +
        ".bd-launch{position:fixed;right:12px;bottom:12px;}" +
        ".bd-launch .bd-note{display:none;}" +
        "html.bd-open body{padding-bottom:305px;}" +
        ".bd-bar{padding:10px 4% 12px;}" +
        ".bd-cap{max-height:22vh;overflow-y:auto;}" +
        ".bd-ask .bd-ask-tag{display:none;}" +
        "}" +
        "@media (max-width:640px){.bd-cap{font-size:.87rem;}.bd-ctl{gap:5px;}}";
      document.head.appendChild(s);
    },

    build: function (onLaunch, onVoice, onStop, onAsk) {
      this.css();
      // Launch pill — fixed bottom-right on every page.
      var btn = el("button", "bd-launch");
      btn.type = "button";
      btn.appendChild(el("span", null, "🎙 " + prof.launch));
      btn.appendChild(el("span", "bd-note", "// voice is output-only — no microphone"));
      btn.addEventListener("click", onLaunch);
      document.body.appendChild(btn);
      this.launchBtn = btn;

      // Docent bar.
      var bar = el("div", "bd-bar");
      var head = el("div", "bd-head");
      head.appendChild(el("span", "bd-dot"));
      head.appendChild(el("span", "bd-tag", COPY.label));
      var ctl = el("div", "bd-ctl");
      this.voiceBtn = el("button", "bd-btn", speech.available ? "voice: on" : "voice: unavailable — captions");
      this.voiceBtn.type = "button";
      this.voiceBtn.addEventListener("click", onVoice);
      this.stopBtn = el("button", "bd-btn", "stop tour");
      this.stopBtn.type = "button";
      this.stopBtn.addEventListener("click", onStop);
      ctl.appendChild(this.voiceBtn);
      ctl.appendChild(this.stopBtn);
      head.appendChild(ctl);
      bar.appendChild(head);
      this.caption = el("div", "bd-cap");
      this.caption.setAttribute("aria-live", "polite");
      bar.appendChild(this.caption);
      bar.appendChild(el("div", "bd-disc", "// " + COPY.disclosure + " Illustrative scenario on the production runtime."));

      // Ask the Boss — typed in, answered aloud (and always captioned).
      var ask = el("div", "bd-ask");
      ask.appendChild(el("span", "bd-ask-tag", COPY.askTag));
      this.askInput = el("input");
      this.askInput.type = "text";
      this.askInput.maxLength = 500;
      this.askInput.placeholder = COPY.askPlaceholder;
      this.askInput.setAttribute("aria-label", "Ask the Boss a question — answered out loud and in captions");
      this.askInput.addEventListener("keydown", function (e) { if (e.key === "Enter") onAsk(); });
      var send = el("button", null, "ASK");
      send.type = "button";
      send.addEventListener("click", onAsk);
      ask.appendChild(this.askInput);
      ask.appendChild(send);
      bar.appendChild(ask);

      this.chipRow = el("div", "bd-chips");
      bar.appendChild(this.chipRow);
      document.body.appendChild(bar);
      this.bar = bar;
    },

    show: function () {
      this.bar.classList.add("on");
      document.documentElement.classList.add("bd-open");
      if (this.launchBtn) this.launchBtn.style.display = "none";
    },
    hide: function () {
      this.bar.classList.remove("on");
      document.documentElement.classList.remove("bd-open");
      if (this.launchBtn) this.launchBtn.style.display = "";
      this.chips([]);
    },
    speaking: function (on) { this.bar.classList.toggle("speaking", !!on); },
    say: function (text) { this.caption.textContent = text; },
    stopLabel: function (touring) { if (this.stopBtn) this.stopBtn.textContent = touring ? "stop tour" : "close"; },

    chips: function (list, onAct) {
      this.chipRow.textContent = "";
      var self = this;
      (list || []).forEach(function (c) {
        var chip;
        if (c.href) {
          chip = el("a", "bd-chip", c.label);
          chip.href = c.href;
        } else {
          chip = el("button", "bd-chip", c.label);
          chip.type = "button";
          if (c.act && onAct) chip.addEventListener("click", function () { onAct(c.act); });
        }
        self.chipRow.appendChild(chip);
      });
    }
  };

  // The single soft CTA — built exactly once, per-desk source tag.
  function pilotChip() {
    return { label: COPY.chipPilot, href: "/contact?source=demo-" + prof.key + "-docent" };
  }
  function briefingChip() { return { label: COPY.chipBriefing, href: "/executive-briefing/" }; }

  function endChips() {
    var chips = [];
    if (prof.kind === "welcome") chips.push({ label: COPY.chipSignal, href: "/demo/signal" });
    else if ($("seedInput") && prof.kind !== "counsel") chips.push({ label: COPY.chipRemix, act: "remix" });
    else chips.push({ label: COPY.chipRestart, act: "restart" });
    chips.push(briefingChip());
    chips.push(pilotChip());
    return chips;
  }
  function stopChips() {
    return [{ label: COPY.chipRestart, act: "restart" }, briefingChip(), pilotChip()];
  }

  function onChipAct(act) {
    if (act === "remix") {
      var seed = $("seedInput");
      if (seed) seed.value = String((parseInt(seed.value, 10) || 42) + 7);
      beginTour();
    } else if (act === "restart") {
      beginTour();
    }
  }

  // ---- dynamic slot readers (the run's own numbers, straight off the DOM) --

  function readGate() {
    var out = [];
    var passed = ($("gateOut") || el("div")).querySelectorAll(".sig-row");
    if (passed.length) {
      out.push(passed.length + (passed.length === 1 ? " signal" : " signals") + " cleared the gate.");
      var first = passed[0];
      var line = txt(first).replace(/score[\s\S]*$/i, "").trim();
      if (line) out.push("For example: " + line + " — it clears every threshold.");
    }
    var filtered = ($("gateFiltered") || el("div")).querySelectorAll(".sig-row");
    if (filtered.length) {
      var f = filtered[0];
      var why = txt(f.querySelector(".why"));
      var name = txt(f).split("uplift")[0].trim();
      out.push(COPY.gateFilteredFrame + (name || "one signal") + " was filtered — " +
        (why ? "the engine's own reason: " + why : "it failed a threshold, and the reason is on the card") + ".");
      out.push(COPY.gateFilteredClose);
    }
    return out;
  }

  function readValidateDetail() {
    var banner = document.querySelector(".guard-block-banner");
    return banner ? ["The blocked check, verbatim: " + txt(banner)] : [];
  }

  function readDecision() {
    var out = [COPY.decisionIntro];
    var title = txt($("dcTitle"));
    if (title && title !== "—") out.push("The executed action: " + title + ".");
    var truth = txt($("dcTruth"));
    if (truth) out.push(COPY.causalIntro + truth);
    out.push(COPY.replayNote);
    return out;
  }

  function readWatchFinale() {
    var out = [];
    if (prof.read === "nexus") {
      var trig = clip(txt($("triggerCard")), 220);
      if (trig) out.push((prof.finaleIntro || "") + "The trigger on the record: " + trig);
    } else {
      var head = txt($("finaleHead"));
      var sum = clip(txt($("finaleSummary")), 260);
      if (head) out.push((prof.finaleIntro || "") + head + ".");
      if (sum) out.push(sum);
    }
    return out.concat(prof.finaleLines || []);
  }

  function readCounselFinale() {
    var out = [];
    var cb = $("conflictBanner");
    if (cb && cb.classList.contains("on")) {
      out.push("The room surfaced a cross-domain conflict — verbatim: " + clip(txt(cb), 220));
    }
    out.push("The synthesized playbook is on screen — deadline-stamped, with each expert's authorities cited.");
    out.push("Try your own situation in the free-text box; it routes by keyword to the closest scripted scenario.");
    return out;
  }

  // ---- wait helpers -------------------------------------------------------

  function waitFor(ep, check, timeoutMs, done) {
    var start = Date.now();
    (function poll() {
      if (stale(ep)) return;
      if (check()) { done(true); return; }
      if (Date.now() - start > timeoutMs) { done(false); return; }
      setTimeout(poll, 200);
    })();
  }

  function stageLit(name) {
    var nodes = document.querySelectorAll("#stageStrip .stage-node.lit");
    for (var i = 0; i < nodes.length; i++) {
      if (txt(nodes[i]).toLowerCase().indexOf(name) !== -1) return nodes[i];
    }
    return null;
  }

  function finaleOn() {
    var f = $(prof.finale);
    return !!(f && f.classList.contains("on"));
  }

  // ---- the tour -----------------------------------------------------------

  // epoch: every (re)start, stop, and ask bumps it; callbacks from an older
  // generation abort, so pending timers can never leak into a new sequence.
  var tour = { running: false, userTookOver: false, selfClick: false, epoch: 0 };
  var ask = { busy: false };

  function stale(ep) { return ep !== tour.epoch; }

  function docentClick(node) {
    if (!node) return;
    tour.selfClick = true;
    try { node.click(); } finally { tour.selfClick = false; }
  }

  function speakSeq(ep, sentences, done) {
    var queue = sentences.slice();
    (function next() {
      if (stale(ep)) return;
      if (!queue.length) { ui.speaking(false); if (done) done(); return; }
      var s = queue.shift();
      ui.say(s);
      ui.speaking(true);
      speech.sentence(s, next);
    })();
  }

  function closeFor() { return (prof.close || []).concat([COPY.closeShared]); }

  function endTour() {
    tour.running = false;
    tour.epoch += 1;
    ui.chips(endChips(), onChipAct);
    ui.stopLabel(false);
  }

  function stopTour(finalLine) {
    var wasRunning = tour.running;
    tour.running = false;
    tour.epoch += 1;
    speech.cancel();
    ui.speaking(false);
    if (wasRunning || finalLine) {
      ui.say(finalLine || COPY.stoppedLine);
      ui.chips(stopChips(), onChipAct);
    }
    ui.stopLabel(false);
  }

  // Beat runners per profile kind ------------------------------------------

  function runPipeline(ep) {
    var startBtn = $("startBtn");
    var resetBtn = $("resetBtn");
    speakSeq(ep, prof.intro, function () {
      docentClick(resetBtn);
      docentClick(startBtn);

      waitFor(ep, function () { return $("eventRail") && $("eventRail").children.length >= 3; }, 9000, function (ok) {
        if (!ok) { stopTour(COPY.trouble); return; }
        speakSeq(ep, prof.rail, function () {

          waitFor(ep, function () { return $("gateOut") && $("gateOut").children.length >= 1; }, 12000, function (ok2) {
            if (!ok2) { stopTour(COPY.trouble); return; }
            speakSeq(ep, COPY.gateIntro.concat(readGate()), function () {

              waitFor(ep, function () { return !!stageLit("validate"); }, 15000, function (ok3) {
                // The player auto-opens the red validate panel; click only if
                // it is somehow closed (clicking an open one would close it).
                var vNode = stageLit("validate");
                var vPanel = $("panel-validate");
                if (ok3 && vNode && vPanel && !vPanel.classList.contains("open")) docentClick(vNode);
                speakSeq(ep, prof.validate.concat(readValidateDetail()), function () {

                  waitFor(ep, function () { return $("decisionCard") && $("decisionCard").classList.contains("on"); }, 15000, function (ok4) {
                    if (!ok4) { stopTour(COPY.trouble); return; }
                    speakSeq(ep, readDecision(), function () {
                      speakSeq(ep, closeFor(), endTour);
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  }

  function runWatch(ep) {
    var startBtn = $("startBtn");
    var resetBtn = $("resetBtn");
    speakSeq(ep, prof.intro, function () {
      docentClick(resetBtn);
      docentClick(startBtn);
      speakSeq(ep, prof.mid, function () {
        waitFor(ep, finaleOn, 60000, function (ok) {
          if (!ok) { stopTour(COPY.trouble); return; }
          speakSeq(ep, readWatchFinale(), function () {
            speakSeq(ep, closeFor(), endTour);
          });
        });
      });
    });
  }

  function runCounsel(ep) {
    speakSeq(ep, prof.intro, function () {
      waitFor(ep, function () { return !!document.querySelector("#scenarioGrid .scn-card"); }, 8000, function (ok) {
        if (!ok) { stopTour(COPY.trouble); return; }
        docentClick(document.querySelector("#scenarioGrid .scn-card"));
        speakSeq(ep, prof.mid, function () {
          waitFor(ep, function () {
            var sp = $("synthPanel");
            return !!(sp && sp.classList.contains("on"));
          }, 30000, function (ok2) {
            if (!ok2) { stopTour(COPY.trouble); return; }
            speakSeq(ep, readCounselFinale(), function () {
              speakSeq(ep, closeFor(), endTour);
            });
          });
        });
      });
    });
  }

  function runWelcome(ep) {
    speakSeq(ep, prof.intro.concat([COPY.closeShared]), endTour);
  }

  function beginTour() {
    if (tour.running) return;
    tour.running = true;
    tour.userTookOver = false;
    tour.epoch += 1;
    var ep = tour.epoch;
    speech.cancel();
    ui.show();
    ui.chips([]);
    ui.stopLabel(true);

    if (prof.kind === "pipeline") runPipeline(ep);
    else if (prof.kind === "watch") runWatch(ep);
    else if (prof.kind === "counsel") runCounsel(ep);
    else runWelcome(ep);
  }

  // ---- Ask the Boss (typed in — answered aloud, always captioned) ---------

  function submitAsk() {
    var q = (ui.askInput.value || "").trim();
    if (!q || ask.busy) return;
    ui.askInput.value = "";
    ask.busy = true;
    tour.running = false;
    tour.epoch += 1; // silences any tour narration cleanly
    var ep = tour.epoch;
    speech.cancel();
    ui.show();
    ui.speaking(false);
    ui.stopLabel(false);
    ui.say(COPY.askThinking);

    var body = JSON.stringify({
      session: sessionId(),
      question: q.slice(0, 500),
      stage: "demo",
      domain: prof.key
    });
    fetch("/api/briefing/guide/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body
    })
      .then(function (r) { return r.json(); })
      .then(function (a) {
        ask.busy = false;
        if (stale(ep)) return;
        var answer = (a && a.answer) ? a.answer : COPY.askFail;
        speakSeq(ep, [answer], function () { ui.chips(stopChips(), onChipAct); });
      })
      .catch(function () {
        ask.busy = false;
        if (stale(ep)) return;
        speakSeq(ep, [COPY.askFail], function () { ui.chips(stopChips(), onChipAct); });
      });
  }

  // ---- init ---------------------------------------------------------------

  function resolveProfile(opts) {
    if (opts && opts.page && PROFILES[opts.page]) return PROFILES[opts.page];
    // Legacy no-arg call (cached demo-signal.html): the signal desk's DOM.
    if ($("startBtn") && $("stageStrip") && document.querySelector(".sf-controls")) return PROFILES.signal;
    var p = (location.pathname || "").toLowerCase();
    var keys = ["signal", "capital", "estate", "risk", "nexus", "counsel"];
    for (var i = 0; i < keys.length; i++) {
      if (p.indexOf(keys[i]) !== -1) return PROFILES[keys[i]];
    }
    if (p.indexOf("/demo") !== -1) return PROFILES.hub;
    return null;
  }

  function init(opts) {
    prof = resolveProfile(opts);
    if (!prof) return; // not a demo page
    var need = prof.need || [];
    for (var i = 0; i < need.length; i++) {
      if (!$(need[i])) return; // the desk this profile narrates isn't here
    }
    speech.init();
    speech.onProblem = function () {
      if (ui.voiceBtn) ui.voiceBtn.textContent = "voice unavailable — captions";
    };
    ui.build(
      function () { beginTour(); },
      function () {
        if (!speech.available) return;
        speech.enabled = !speech.enabled;
        if (!speech.enabled) speech.cancel();
        ui.voiceBtn.textContent = "voice: " + (speech.enabled ? "on" : "off — captions");
      },
      function () {
        if (tour.running) { stopTour(); } else { ui.hide(); }
      },
      submitAsk
    );

    // Visitor takes the controls mid-tour → the Boss yields, politely, once.
    function yieldToVisitor() {
      if (tour.selfClick) return; // the Boss driving is not a take-over
      if (tour.running && !tour.userTookOver) {
        tour.userTookOver = true;
        stopTour(COPY.interrupted);
      }
    }
    (prof.watch || []).forEach(function (id) {
      var node = $(id);
      if (node) node.addEventListener("click", yieldToVisitor);
    });
    if (prof.kind === "counsel") {
      var grid = $("scenarioGrid");
      if (grid) grid.addEventListener("click", yieldToVisitor);
    }
  }

  window.MizokiBossDocent = {
    init: function (opts) {
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(opts); });
      } else {
        init(opts);
      }
    }
  };
})();
