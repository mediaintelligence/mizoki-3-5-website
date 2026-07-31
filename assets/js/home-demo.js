/* Homepage live teaser — runs real scenarios against the public demo runtime
 * (/api/demo/<division>/run) and replays the returned trace inline. Nothing
 * here is mocked: stage summaries, funnel counts, confidence, the causal
 * truth, and the trace id all come from the same seeded engines that power
 * /demo. Vanilla JS only; honors prefers-reduced-motion; degrades to a link
 * to the full demos if the backend is unreachable.
 */
(function () {
  "use strict";

  var STAGES = ["sense", "reason", "plan", "validate", "decide", "act", "learn"];
  var SEED = 42;
  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var SCENARIOS = [
    {
      division: "capital",
      scenario: "dividend_covenant_veto",
      accent: "#34a6ff",
      label: "The covenant veto",
      blurb: "A special distribution models covenant headroom below the 15% floor. Nothing executes — the veto IS the decision.",
      desk: "/demo/capital"
    },
    {
      division: "capital",
      scenario: "debt_paydown_vs_buyback",
      accent: "#34a6ff",
      label: "Debt paydown vs buyback",
      blurb: "Retire debt or repurchase shares. The leveraged buyback models headroom at 9% — vetoed; the paydown executes.",
      desk: "/demo/capital"
    },
    {
      division: "capital",
      scenario: "growth_reallocation",
      accent: "#34a6ff",
      label: "Growth reallocation",
      blurb: "Capital shifts toward the business units clearing the ReLU gate — inside the covenant envelope.",
      desk: "/demo/capital"
    },
    {
      division: "signal",
      scenario: "ecommerce_roas",
      accent: "#f5a623",
      label: "ROAS reallocation",
      blurb: "Ads, analytics, and social events fuse into ROAS signals; the strongest campaigns win incremental budget.",
      desk: "/demo/signal"
    }
  ];

  function $(id) { return document.getElementById(id); }

  function init() {
    var els = {
      scen: $("ltScenarios"),
      stages: $("ltStages"),
      progress: $("ltProgress"),
      log: $("ltLog"),
      timer: $("ltTimer"),
      placeholder: $("ltPlaceholder"),
      result: $("ltResult"),
      status: $("ltStatus"),
      conf: $("ltConf"),
      confWrap: $("ltConfWrap"),
      action: $("ltAction"),
      truth: $("ltTruth"),
      trace: $("ltTrace"),
      open: $("ltOpen"),
      run: $("ltRun"),
      reset: $("ltReset")
    };
    if (!els.scen || !els.stages || !els.run) return;

    var state = { selected: 0, running: false, timers: [], clock: null };

    function buildScenarioCards() {
      els.scen.textContent = "";
      SCENARIOS.forEach(function (s, i) {
        var card = document.createElement("button");
        card.type = "button";
        card.className = "lt-card" + (i === state.selected ? " sel" : "");
        card.style.setProperty("--lt-accent", s.accent);
        card.setAttribute("aria-pressed", i === state.selected ? "true" : "false");

        var div = document.createElement("span");
        div.className = "lt-div";
        div.textContent = s.division;
        card.appendChild(div);

        var h = document.createElement("h4");
        h.textContent = s.label;
        card.appendChild(h);

        var p = document.createElement("p");
        p.textContent = s.blurb;
        card.appendChild(p);

        card.addEventListener("click", function () {
          if (state.running) return;
          state.selected = i;
          resetAll();
        });
        els.scen.appendChild(card);
      });
    }

    function buildStageStrip() {
      els.stages.textContent = "";
      STAGES.forEach(function (stage) {
        var node = document.createElement("div");
        node.className = "lt-stage";
        node.id = "lt-stage-" + stage;
        node.textContent = stage;
        els.stages.appendChild(node);
      });
    }

    function stopTransport() {
      state.timers.forEach(clearTimeout);
      state.timers = [];
      if (state.clock) { clearInterval(state.clock); state.clock = null; }
    }

    function resetAll() {
      stopTransport();
      state.running = false;
      els.run.disabled = false;
      els.log.textContent = "";
      els.timer.textContent = "00.0s";
      els.result.hidden = true;
      els.placeholder.hidden = false;
      if (els.progress) els.progress.style.width = "0%";
      buildScenarioCards();
      buildStageStrip();
    }

    function markDone(node) {
      if (!node || node.classList.contains("done")) return;
      node.classList.remove("lit");
      node.classList.add("done");
      node.textContent = "✓ " + node.textContent;
    }

    function logLine(stage, text, isError) {
      var row = document.createElement("div");
      if (isError) row.className = "err";
      var t = document.createElement("span");
      t.className = "t";
      t.textContent = els.timer.textContent;
      row.appendChild(t);
      if (stage) {
        var s = document.createElement("span");
        s.className = "s";
        s.textContent = stage;
        row.appendChild(s);
      }
      row.appendChild(document.createTextNode(text));
      els.log.appendChild(row);
      els.log.scrollTop = els.log.scrollHeight;
      return row;
    }

    function startClock() {
      var start = Date.now();
      state.clock = setInterval(function () {
        els.timer.textContent = ((Date.now() - start) / 1000).toFixed(1) + "s";
      }, 100);
    }

    function startRun() {
      if (state.running) return;
      resetAll();
      state.running = true;
      els.run.disabled = true;
      startClock();

      var cfg = SCENARIOS[state.selected];
      logLine(null, "POST /api/demo/" + cfg.division + "/run · scenario " +
        cfg.scenario + " · seed " + SEED);

      fetch("/api/demo/" + cfg.division + "/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: cfg.scenario, seed: SEED })
      })
        .then(function (r) {
          if (!r.ok) throw new Error("run failed: " + r.status);
          return r.json();
        })
        .then(function (run) { replay(run, cfg); })
        .catch(function () {
          stopTransport();
          state.running = false;
          els.run.disabled = false;
          var row = logLine(null, "demo runtime unreachable — ", true);
          var link = document.createElement("a");
          link.href = "/demo";
          link.textContent = "open the full demos instead →";
          row.appendChild(link);
        });
    }

    function replay(run, cfg) {
      var stageDelay = reduceMotion ? 30 : 520;
      var total = (run.stages || []).length || 1;
      var delay = 0;
      (run.stages || []).forEach(function (stage, i) {
        delay += stageDelay;
        state.timers.push(setTimeout(function () {
          if (i > 0) markDone($("lt-stage-" + run.stages[i - 1].stage));
          var node = $("lt-stage-" + stage.stage);
          if (node) node.classList.add("lit");
          if (els.progress) els.progress.style.width = (((i + 1) / total) * 100) + "%";
          logLine(stage.stage, stage.summary);
        }, delay));
      });
      delay += reduceMotion ? 30 : 640;
      state.timers.push(setTimeout(function () {
        if (run.stages && run.stages.length) {
          markDone($("lt-stage-" + run.stages[run.stages.length - 1].stage));
        }
        showOutcome(run, cfg);
      }, delay));
    }

    function showOutcome(run, cfg) {
      stopTransport();
      state.running = false;
      els.run.disabled = false;

      var card = run.decision_card || {};
      var action = card.executed_action || {};
      var funnel = card.funnel || {};
      var block = card.guardrail_block;
      var pureVeto = !action.type || (funnel.executed || 0) === 0;

      els.placeholder.hidden = true;
      els.result.hidden = false;

      els.status.textContent = "";
      if (pureVeto) {
        // The veto IS the decision — make it the hero, not a footnote.
        var held = document.createElement("span");
        held.className = "veto";
        held.textContent = "VETOED — nothing executed" +
          (block ? " · blocked by " + (block.blocked_by || []).join(", ") : "") +
          " · human override required";
        els.status.appendChild(held);
      } else {
        var ok = document.createElement("span");
        ok.className = "ok";
        ok.textContent = "EXECUTED " + (funnel.executed != null ? funnel.executed : "—") +
          " of " + (funnel.signals_formed != null ? funnel.signals_formed : "—") + " candidates";
        els.status.appendChild(ok);
        if (block) {
          els.status.appendChild(document.createTextNode(" · "));
          var veto = document.createElement("span");
          veto.className = "veto";
          veto.textContent = "1 VETOED by " + (block.blocked_by || []).join(", ");
          els.status.appendChild(veto);
        }
      }

      if (els.confWrap) els.confWrap.hidden = pureVeto;
      if (!pureVeto) animateConfidence(action.confidence);

      var magnitude = action.magnitude_pct != null
        ? " " + (action.magnitude_pct > 0 ? "+" : "") + action.magnitude_pct + "%" : "";
      els.action.textContent = pureVeto
        ? "no action executed — the operator gate holds"
        : action.type + magnitude + " → " + action.entity_id;

      els.truth.textContent = card.causal_truth || "";
      els.truth.hidden = !card.causal_truth;

      els.trace.textContent = "trace " + (card.trace_id || "—") + " · seed " + SEED +
        " — rerun it: same numbers.";
      els.open.href = cfg.desk;
      els.open.textContent = "Open the full " + cfg.division + " desk →";

      logLine(null, "run complete — every number above is reproducible with seed " + SEED);
    }

    function animateConfidence(target) {
      if (target == null) { els.conf.textContent = "—"; return; }
      if (reduceMotion) { els.conf.textContent = target.toFixed(2); return; }
      var steps = 20, i = 0;
      var timer = setInterval(function () {
        i += 1;
        els.conf.textContent = ((target * i) / steps).toFixed(2);
        if (i >= steps) clearInterval(timer);
      }, 45);
      state.timers.push(timer);
    }

    buildScenarioCards();
    buildStageStrip();
    els.run.addEventListener("click", startRun);
    els.reset.addEventListener("click", function () {
      if (!state.running) resetAll(); else { stopTransport(); state.running = false; resetAll(); }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
