/* MIZOKI3 Boss Docent — voice-guided demo tour.
 *
 * The Boss agent narrates a live demo run: it presses Start itself, watches
 * the same DOM the visitor watches, and explains each action using the run's
 * OWN numbers (gate rows, guardrail veto text, causal truth) — never invented
 * figures. Output-only voice: Web Speech synthesis (TTS). No microphone, no
 * audio capture, ever — the tour speaks; it never listens.
 *
 * Claims discipline (binding, tested in tests/test_boss_docent.py):
 *   - anticipatory intent with proof of causal lift — never mind-reading
 *   - calibrated probabilities — an account is never promised to buy
 *   - figures are illustrative scenario output, never a promise of results
 *   - exactly one soft call-to-action, at the end; no pressure language
 *
 * Zero dependencies, zero changes to the demo player (demo-signal.js).
 * Degrades to captions-only when speech synthesis is unavailable.
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
    launch: "Guided tour — let the Boss walk you through",
    label: "BOSS AGENT — GUIDED TOUR",
    disclosure: "Voice is output-only. I speak — I never listen. No microphone is used.",
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
    gateIntro: [
      "Now the ReLU gate — the first honest moment of this pipeline.",
      "A signal passes only if uplift, confidence, and sample size all clear their thresholds. Weak evidence is filtered out, with its reason recorded."
    ],
    gateFilteredFrame: "I want you to notice what we rejected: ",
    gateFilteredClose: "Most platforms would have acted on that anyway. We would rather show you what we filter than inflate what we accept.",
    validate: [
      "Here is the part most demos hide: the validation stage just blocked something, deliberately, in red.",
      "The veto is not an opinion — it is arithmetic against a guardrail. The trace is open below — read the check for yourself."
    ],
    decisionIntro: "The decision card. One action earned execution, and it carries its full provenance chain — raw event to canonical envelope to signal to gate to guardrails to decision.",
    causalIntro: "And this is the causal truth, composed from the run data itself: ",
    replayNote: "Every number I just read came from this run's trace. Re-run the same seed and I will say exactly the same thing — that is what auditable means.",
    close: [
      "That's the factory: raw signals in, governed decisions out, one deliberate refusal on the record.",
      "The figures are an illustrative scenario — in a pilot, your own signals would do the talking.",
      "If this discipline is what your team is missing, the executive briefing takes about nine minutes, or you can request a pilot below. No pressure — the trace speaks for itself."
    ],
    interrupted: "Taking my hands off the controls — it's your run now.",
    trouble: "The runtime isn't responding from your network right now, so I'll stop the tour here. The controls above work the moment it's back.",
    chips: [
      { label: "▶ Replay remixed (new seed)", act: "rerun" },
      { label: "Executive briefing →", href: "/executive-briefing/" },
      { label: "Request a pilot →", href: "/contact?source=demo-signal-docent" }
    ]
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

  // ---- speech engine (TTS output only; captions always) -------------------

  var speech = {
    available: false,
    enabled: true,
    voice: null,
    utter: null,
    timer: null,

    init: function () {
      this.available = !!(window.speechSynthesis && window.SpeechSynthesisUtterance);
      if (!this.available) { this.enabled = false; return; }
      var self = this;
      function pick() {
        var voices = window.speechSynthesis.getVoices() || [];
        var ranked = [
          /Google US English/i, /Microsoft (Aria|Jenny|Guy)/i, /Samantha/i,
          /en[-_]US/i, /^en/i
        ];
        for (var i = 0; i < ranked.length && !self.voice; i++) {
          for (var v = 0; v < voices.length; v++) {
            var name = (voices[v].name || "") + " " + (voices[v].lang || "");
            if (ranked[i].test(name)) { self.voice = voices[v]; break; }
          }
        }
      }
      pick();
      try { window.speechSynthesis.onvoiceschanged = pick; } catch (e) { /* ok */ }
    },

    cancel: function () {
      if (this.timer) { clearTimeout(this.timer); this.timer = null; }
      if (this.available) { try { window.speechSynthesis.cancel(); } catch (e) { /* ok */ } }
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
      var u = new SpeechSynthesisUtterance(text);
      if (this.voice) u.voice = this.voice;
      u.rate = 1.0; u.pitch = 1.0;
      u.onend = finish;
      u.onerror = finish;
      this.utter = u;
      try { window.speechSynthesis.speak(u); } catch (e) { finish(); return; }
      this.timer = setTimeout(finish, readMs * 2 + 4000); // safety net
    }
  };

  // ---- docent UI (self-injected, dossier vocabulary) ----------------------

  var ui = {
    bar: null, caption: null, chipRow: null, voiceBtn: null, stopBtn: null, launchBtn: null,

    css: function () {
      var s = el("style");
      s.textContent =
        ".bd-launch{display:inline-flex;align-items:center;gap:10px;margin:6px 0 18px;" +
        "font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.08em;" +
        "background:#0B1E26;color:#DCE9ED;border:1px solid #2C4550;border-left:2px solid #9D7BE8;" +
        "border-radius:2px;padding:11px 18px;cursor:pointer;transition:border-color .2s ease;}" +
        ".bd-launch:hover{border-color:#9D7BE8;color:#F4F6F7;}" +
        ".bd-launch .bd-note{color:#5E7780;font-size:10px;letter-spacing:.05em;}" +
        ".bd-bar{position:fixed;left:0;right:0;bottom:0;z-index:60;background:#0B1E26;" +
        "border-top:1px solid #2C4550;padding:12px 5% 14px;display:none;}" +
        ".bd-bar.on{display:block;}" +
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
        ".bd-disc{font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.06em;" +
        "color:#5E7780;margin-top:5px;}" +
        ".bd-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:9px;}" +
        ".bd-chip{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.06em;" +
        "background:#0A1418;color:#3FDCF2;border:1px solid rgba(63,220,242,.45);" +
        "border-radius:2px;padding:7px 14px;cursor:pointer;text-decoration:none;display:inline-block;}" +
        ".bd-chip:hover{border-color:#3FDCF2;}" +
        "@media (max-width:640px){.bd-cap{font-size:.87rem;}.bd-ctl{gap:5px;}}";
      document.head.appendChild(s);
    },

    build: function (onLaunch, onVoice, onStop) {
      this.css();
      // Launch button, injected after the demo controls row.
      var controls = document.querySelector(".sf-controls");
      var btn = el("button", "bd-launch");
      btn.type = "button";
      btn.appendChild(el("span", null, "🎙 " + COPY.launch));
      btn.appendChild(el("span", "bd-note", "// voice is output-only — no microphone"));
      btn.addEventListener("click", onLaunch);
      if (controls && controls.parentNode) {
        controls.parentNode.insertBefore(btn, controls.nextSibling);
      } else {
        document.body.appendChild(btn);
      }
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
      this.chipRow = el("div", "bd-chips");
      bar.appendChild(this.chipRow);
      document.body.appendChild(bar);
      this.bar = bar;
    },

    show: function () { this.bar.classList.add("on"); },
    hide: function () { this.bar.classList.remove("on"); this.chips([]); },
    speaking: function (on) { this.bar.classList.toggle("speaking", !!on); },
    say: function (text) { this.caption.textContent = text; },

    chips: function (list, onRerun) {
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
          if (c.act === "rerun" && onRerun) chip.addEventListener("click", onRerun);
        }
        self.chipRow.appendChild(chip);
      });
    }
  };

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

  // ---- the tour -----------------------------------------------------------

  // epoch: every (re)start bumps it; callbacks from an older generation
  // abort, so a stopped tour's pending timers can never leak into a new one.
  var tour = { running: false, stopped: true, userTookOver: false, selfClick: false, epoch: 0 };

  function stale(ep) { return tour.stopped || ep !== tour.epoch; }

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

  function stopTour(finalLine) {
    if (tour.stopped) return;
    tour.stopped = true;
    tour.running = false;
    speech.cancel();
    ui.speaking(false);
    if (finalLine) ui.say(finalLine);
    else ui.hide();
  }

  function beginTour() {
    if (tour.running) return;
    tour.running = true;
    tour.stopped = false;
    tour.userTookOver = false;
    tour.epoch += 1;
    var ep = tour.epoch;
    speech.cancel();
    ui.show();
    ui.chips([]);

    var startBtn = $("startBtn");
    var resetBtn = $("resetBtn");

    speakSeq(ep, COPY.intro, function () {
      docentClick(resetBtn);
      docentClick(startBtn);

      waitFor(ep, function () { return $("eventRail") && $("eventRail").children.length >= 3; }, 9000, function (ok) {
        if (!ok) { stopTour(COPY.trouble); return; }
        speakSeq(ep, COPY.rail, function () {

          waitFor(ep, function () { return $("gateOut") && $("gateOut").children.length >= 1; }, 12000, function (ok2) {
            if (!ok2) { stopTour(COPY.trouble); return; }
            speakSeq(ep, COPY.gateIntro.concat(readGate()), function () {

              waitFor(ep, function () { return !!stageLit("validate"); }, 15000, function (ok3) {
                // The player auto-opens the red validate panel; click only if
                // it is somehow closed (clicking an open one would close it).
                var vNode = stageLit("validate");
                var vPanel = $("panel-validate");
                if (ok3 && vNode && vPanel && !vPanel.classList.contains("open")) vNode.click();
                speakSeq(ep, COPY.validate.concat(readValidateDetail()), function () {

                  waitFor(ep, function () { return $("decisionCard") && $("decisionCard").classList.contains("on"); }, 15000, function (ok4) {
                    if (!ok4) { stopTour(COPY.trouble); return; }
                    speakSeq(ep, readDecision(), function () {
                      speakSeq(ep, COPY.close, function () {
                        ui.chips(COPY.chips, function () {
                          var seed = $("seedInput");
                          if (seed) seed.value = String((parseInt(seed.value, 10) || 42) + 7);
                          tour.running = false;
                          beginTour();
                        });
                        tour.running = false;
                        tour.stopped = true;
                      });
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

  // ---- init ---------------------------------------------------------------

  function init() {
    if (!$("startBtn") || !$("stageStrip")) return; // not a demo page
    speech.init();
    ui.build(
      function () { beginTour(); },
      function () {
        if (!speech.available) return;
        speech.enabled = !speech.enabled;
        if (!speech.enabled) speech.cancel();
        ui.voiceBtn.textContent = "voice: " + (speech.enabled ? "on" : "off — captions");
      },
      function () { stopTour(); }
    );

    // Visitor takes the controls mid-tour → the Boss yields, politely, once.
    ["startBtn", "resetBtn", "scenario"].forEach(function (id) {
      var node = $(id);
      if (!node) return;
      node.addEventListener("click", function () {
        if (tour.selfClick) return; // the Boss driving is not a take-over
        if (tour.running && !tour.stopped && !tour.userTookOver) {
          tour.userTookOver = true;
          stopTour(COPY.interrupted);
        }
      });
    });
  }

  window.MizokiBossDocent = {
    init: function () {
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
      } else {
        init();
      }
    }
  };
})();
