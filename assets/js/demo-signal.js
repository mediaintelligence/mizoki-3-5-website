/* Signal Factory demo — consumes the SSE stream from the MIZ OKI runtime.
 *
 * Vanilla JS only. Primary transport: EventSource on
 * /api/demo/signal/stream. Fallback: POST /api/demo/signal/run and replay
 * the run locally with setTimeout pacing. Respects prefers-reduced-motion.
 */
(function () {
  "use strict";

  var STAGES = ["sense", "reason", "plan", "validate", "decide", "act", "learn"];
  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var els = {};
  var state = { source: null, timers: [], running: false };

  function $(id) { return document.getElementById(id); }

  function currentSeed() {
    var input = $("seedInput");
    var value = input ? parseInt(input.value, 10) : NaN;
    return isNaN(value) ? 42 : value;
  }

  function emit(name, detail) {
    try {
      document.dispatchEvent(new CustomEvent(name, { detail: detail || {} }));
    } catch (err) { /* older browsers: telemetry only */ }
  }

  function init() {
    els.scenario = $("scenario");
    els.start = $("startBtn");
    els.reset = $("resetBtn");
    els.status = $("status");
    els.rail = $("eventRail");
    els.gateIn = $("gateIn");
    els.gateOut = $("gateOut");
    els.gateFiltered = $("gateFiltered");
    els.filterTray = $("filterTray");
    els.stageStrip = $("stageStrip");
    els.stagePanels = $("stagePanels");
    els.card = $("decisionCard");

    buildStageStrip();
    loadScenarios();

    els.start.addEventListener("click", startRun);
    els.reset.addEventListener("click", resetAll);
  }

  function loadScenarios() {
    fetch("/api/demo/signal/scenarios")
      .then(function (r) { return r.json(); })
      .then(function (body) {
        (body.scenarios || []).forEach(function (s) {
          var opt = document.createElement("option");
          opt.value = s.id;
          opt.textContent = s.name;
          els.scenario.appendChild(opt);
        });
      })
      .catch(function () { setStatus("could not load scenarios", false); });
  }

  function buildStageStrip() {
    els.stageStrip.textContent = "";
    els.stagePanels.textContent = "";
    STAGES.forEach(function (stage) {
      var node = document.createElement("div");
      node.className = "stage-node";
      node.id = "node-" + stage;
      node.setAttribute("role", "button");
      node.setAttribute("tabindex", "0");
      var dot = document.createElement("span");
      dot.className = "dot";
      node.appendChild(dot);
      node.appendChild(document.createTextNode(stage));
      node.addEventListener("click", function () { togglePanel(stage); });
      node.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); togglePanel(stage); }
      });
      els.stageStrip.appendChild(node);

      var panel = document.createElement("div");
      panel.className = "stage-panel";
      panel.id = "panel-" + stage;
      els.stagePanels.appendChild(panel);
    });
  }

  function togglePanel(stage) {
    var node = $("node-" + stage);
    var panel = $("panel-" + stage);
    if (!node.classList.contains("lit")) return;
    var wasOpen = panel.classList.contains("open");
    STAGES.forEach(function (s) {
      $("panel-" + s).classList.remove("open");
      $("node-" + s).classList.remove("open");
    });
    if (!wasOpen) {
      panel.classList.add("open");
      node.classList.add("open");
    }
  }

  function setStatus(text, live) {
    els.status.textContent = "";
    var span = document.createElement("span");
    span.textContent = text;
    if (live) span.className = "live";
    els.status.appendChild(span);
  }

  function resetAll() {
    stopTransport();
    state.running = false;
    els.start.disabled = false;
    els.rail.textContent = "";
    els.gateIn.textContent = "";
    els.gateOut.textContent = "";
    els.gateFiltered.textContent = "";
    els.filterTray.hidden = true;
    els.card.classList.remove("on");
    buildStageStrip();
    setStatus("idle", false);
  }

  function stopTransport() {
    if (state.source) { state.source.close(); state.source = null; }
    state.timers.forEach(clearTimeout);
    state.timers = [];
  }

  function startRun() {
    if (state.running) return;
    resetAll();
    state.running = true;
    els.start.disabled = true;
    var scenario = els.scenario.value || "ecommerce_roas";
    setStatus("streaming · " + scenario, true);
    emit("mizoki:demo-started", { scenario: scenario, seed: currentSeed() });

    if (!window.EventSource) { fallbackRun(scenario); return; }

    var source = new EventSource(
      "/api/demo/signal/stream?scenario=" + encodeURIComponent(scenario) +
      "&seed=" + currentSeed()
    );
    state.source = source;
    var gotFrame = false;

    ["raw_event", "canonical_event", "signal_gate", "stage", "decision_card"].forEach(function (type) {
      source.addEventListener(type, function (evt) {
        gotFrame = true;
        handleFrame(type, JSON.parse(evt.data));
      });
    });
    source.addEventListener("done", function (evt) {
      gotFrame = true;
      handleFrame("done", JSON.parse(evt.data));
      source.close();
      state.source = null;
    });
    source.onerror = function () {
      source.close();
      state.source = null;
      if (!gotFrame && state.running) {
        // Graceful fallback: fetch the whole run and replay it locally.
        fallbackRun(scenario);
      } else if (state.running) {
        setStatus("stream interrupted — press Reset to try again", false);
        state.running = false;
        els.start.disabled = false;
      }
    };
  }

  function fallbackRun(scenario) {
    setStatus("replaying · " + scenario + " (fallback)", true);
    fetch("/api/demo/signal/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenario, seed: currentSeed() })
    })
      .then(function (r) {
        if (!r.ok) throw new Error("run failed: " + r.status);
        return r.json();
      })
      .then(function (run) { replayLocally(run); })
      .catch(function () {
        setStatus("demo backend unavailable", false);
        state.running = false;
        els.start.disabled = false;
      });
  }

  function replayLocally(run) {
    var frames = [];
    var sense = findStage(run, "sense");
    (sense ? sense.items : []).forEach(function (pair) {
      frames.push(["raw_event", pair.raw, 120]);
    });
    (sense ? sense.items : []).forEach(function (pair) {
      frames.push(["canonical_event", pair.canonical, 100]);
    });
    var reason = findStage(run, "reason");
    (reason ? reason.items : []).forEach(function (item) {
      if (item.signal) frames.push(["signal_gate", item, 350]);
    });
    (run.stages || []).forEach(function (stage) {
      frames.push(["stage", stage, 600]);
    });
    frames.push(["decision_card", run.decision_card, 800]);
    frames.push(["done", { trace_id: run.trace_id }, 0]);

    var delay = 0;
    frames.forEach(function (frame) {
      delay += reduceMotion ? 15 : frame[2];
      state.timers.push(setTimeout(function () {
        handleFrame(frame[0], frame[1]);
      }, delay));
    });
  }

  function findStage(run, name) {
    return (run.stages || []).filter(function (s) { return s.stage === name; })[0] || null;
  }

  // ---- frame handlers -----------------------------------------------------

  var handlers = {
    raw_event: function (data) {
      var chip = document.createElement("div");
      chip.className = "evt-chip";
      chip.id = "chip-" + data.event_id;

      var src = document.createElement("span");
      src.className = "src src-" + data.source;
      src.textContent = data.source;
      chip.appendChild(src);

      var ent = document.createElement("div");
      ent.className = "ent";
      ent.textContent = data.entity_id;
      chip.appendChild(ent);

      var meta = document.createElement("div");
      meta.textContent = data.event_type + " · v=" + data.value;
      chip.appendChild(meta);

      var canTag = document.createElement("div");
      canTag.className = "can-tag";
      canTag.textContent = "→ canonical";
      chip.appendChild(canTag);

      els.rail.appendChild(chip);
      requestAnimationFrame(function () { chip.classList.add("on"); });
      els.rail.scrollLeft = els.rail.scrollWidth;
    },

    canonical_event: function (data) {
      var rawId = String(data.canonical_id || "").replace(/^can_/, "");
      var chip = $("chip-" + rawId);
      if (!chip) return;
      chip.classList.add("canonical");
      var tag = chip.querySelector(".can-tag");
      if (tag) tag.textContent = "→ " + data.canonical_id + " · conf " + data.confidence;
    },

    signal_gate: function (data) {
      var sig = data.signal || {};
      var row = document.createElement("div");
      row.className = "sig-row " + (data.passed ? "pass" : "fail");

      var head = document.createElement("div");
      head.textContent = (sig.entity_id || data.entity_id) + " · " + (sig.metric || "");
      row.appendChild(head);

      var score = document.createElement("span");
      score.className = "score";
      score.textContent =
        "uplift " + pct(sig.uplift) + " · conf " + sig.confidence +
        " · n=" + sig.sample_size + " · score " + round2(data.score);
      row.appendChild(score);

      var track = document.createElement("div");
      track.className = "bar-track";
      var bar = document.createElement("div");
      bar.className = "bar";
      track.appendChild(bar);
      row.appendChild(track);

      if (!data.passed) {
        var why = document.createElement("span");
        why.className = "why";
        why.textContent = "✕ " + (data.reasons || [data.reason]).join(" · ");
        row.appendChild(why);
        els.filterTray.hidden = false;
        els.gateFiltered.appendChild(row);
      } else {
        els.gateOut.appendChild(row);
      }

      var mirror = row.cloneNode(true);
      mirror.classList.remove("pass", "fail");
      els.gateIn.appendChild(mirror);
      mirror.classList.add("on");
      var mBar = mirror.querySelector(".bar");
      if (mBar) mBar.style.width = barWidth(data.score);

      requestAnimationFrame(function () {
        row.classList.add("on");
        bar.style.width = barWidth(data.score);
      });
    },

    stage: function (data) {
      var node = $("node-" + data.stage);
      var panel = $("panel-" + data.stage);
      if (!node || !panel) return;
      node.classList.add("lit");
      renderStagePanel(data, panel);
      if (data.stage === "validate" && (data.counts || {}).blocked > 0) {
        node.classList.add("blocked");
        togglePanel("validate"); // auto-open the red moment
      }
    },

    decision_card: function (data) {
      renderDecisionCard(data);
    },

    done: function (data) {
      setStatus(
        "run complete — every number above is reproducible with seed " + currentSeed(),
        true
      );
      state.running = false;
      els.start.disabled = false;
      emit("mizoki:demo-completed", data || {});
    }
  };

  function handleFrame(type, data) {
    if (handlers[type]) handlers[type](data);
  }

  // ---- rendering ----------------------------------------------------------

  function renderStagePanel(stage, panel) {
    panel.textContent = "";
    var summary = document.createElement("p");
    summary.className = "summary";
    summary.textContent = stage.summary;
    panel.appendChild(summary);

    var items = document.createElement("div");
    items.className = "items";

    (stage.items || []).slice(0, 40).forEach(function (item) {
      if (stage.stage === "validate") { items.appendChild(renderValidation(item)); return; }
      var row = document.createElement("div");
      row.className = "row";
      row.textContent = describeItem(stage.stage, item);
      items.appendChild(row);
    });
    panel.appendChild(items);
  }

  function renderValidation(item) {
    var wrap = document.createElement("div");
    wrap.className = "row";
    var title = document.createElement("div");
    title.textContent = item.action_id + " · " + item.type + " → " + item.entity_id;
    title.style.color = item.blocked ? "#fca5a5" : "#DCE9ED";
    wrap.appendChild(title);

    (item.checks || []).forEach(function (check) {
      var line = document.createElement("div");
      line.className = "guard-check " + (check.passed ? "ok" : "bad");
      var mark = document.createElement("span");
      mark.className = "mark";
      mark.textContent = check.passed ? "✓" : "✕";
      line.appendChild(mark);
      var text = document.createElement("span");
      text.textContent = check.name + " — " + check.detail;
      line.appendChild(text);
      wrap.appendChild(line);
    });

    if (item.blocked) {
      var banner = document.createElement("div");
      banner.className = "guard-block-banner";
      banner.textContent =
        "BLOCKED before execution — " + (item.blocked_by || []).join(", ") +
        ". This action never reaches the Act stage.";
      wrap.appendChild(banner);
    }
    return wrap;
  }

  function describeItem(stageName, item) {
    if (stageName === "sense" && item.raw) {
      return item.raw.event_id + " " + item.raw.source + "/" + item.raw.event_type +
        " → " + (item.canonical || {}).canonical_id;
    }
    if (stageName === "reason") {
      if (item.hypothesis) {
        return "☼ " + item.hypothesis.hypothesis + " (conf " + item.hypothesis.confidence + ")";
      }
      return (item.passed ? "✓ " : "✕ ") + item.entity_id + " score=" + round2(item.score) +
        (item.passed ? "" : " — " + (item.reasons || []).join("; "));
    }
    if (stageName === "plan") {
      return item.action_id + " · " + item.type + " " + fmtMag(item) + " → " +
        item.entity_id + " (EV $" + item.expected_value + ", conf " + item.confidence + ")";
    }
    if (stageName === "decide") {
      return "#" + item.rank + " " + item.action_id + " · score " + item.decision_score;
    }
    if (stageName === "act") {
      return item.action_id + " · " + item.mode + " · " + item.status +
        " · rollback " + item.rollback_token;
    }
    if (stageName === "learn") {
      if (item.learning_note) return "◈ " + item.learning_note;
      return item.action_id + " · predicted " + item.predicted_delta +
        " vs actual " + item.simulated_actual_delta + " (" + item.error_pct + "%)";
    }
    return JSON.stringify(item).slice(0, 140);
  }

  function renderDecisionCard(card) {
    els.card.classList.add("on");
    var action = card.executed_action || {};
    $("dcTitle").textContent = action.type
      ? action.type + " " + fmtMag(action) + " → " + action.entity_id
      : "No action executed — the veto held";
    $("dcTrace").textContent =
      "trace " + card.trace_id + " · scenario " + card.scenario +
      (card.guardrail_block
        ? " · blocked: " + card.guardrail_block.action_id + " (" + card.guardrail_block.blocked_by.join(", ") + ")"
        : "");

    var funnel = $("dcFunnel");
    funnel.textContent = "";
    var order = ["events_sensed", "signals_formed", "passed_gate", "validated", "executed"];
    order.forEach(function (key) {
      var cell = document.createElement("div");
      cell.className = "cell";
      var num = document.createElement("div");
      num.className = "num";
      num.textContent = "0";
      cell.appendChild(num);
      var cap = document.createElement("div");
      cap.className = "cap";
      cap.textContent = key.replace(/_/g, " ");
      cell.appendChild(cap);
      funnel.appendChild(cell);
      animateCount(num, (card.funnel || {})[key] || 0);
    });

    var chain = $("dcChain");
    chain.textContent = "";
    (card.provenance_chain || []).forEach(function (step) {
      var row = document.createElement("div");
      row.className = "prov-step";
      var tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = step.stage;
      row.appendChild(tag);
      var detail = document.createElement("span");
      detail.textContent = step.detail + (step.ref ? "  [" + step.ref + "]" : "");
      row.appendChild(detail);
      chain.appendChild(row);
    });

    var truthWrap = $("dcTruthWrap");
    var truthText = $("dcTruth");
    if (truthWrap && truthText) {
      if (card.causal_truth) {
        truthText.textContent = card.causal_truth;
        truthWrap.hidden = false;
      } else {
        truthWrap.hidden = true;
      }
    }
  }

  function animateCount(el, target) {
    if (reduceMotion || target <= 0) { el.textContent = String(target); return; }
    var steps = Math.min(target, 24);
    var i = 0;
    var timer = setInterval(function () {
      i += 1;
      el.textContent = String(Math.round((target * i) / steps));
      if (i >= steps) clearInterval(timer);
    }, 40);
    state.timers.push(timer);
  }

  // ---- tiny utils ---------------------------------------------------------

  function pct(x) { return x == null ? "—" : (x * 100).toFixed(0) + "%"; }
  function round2(x) { return x == null ? "—" : Math.round(x * 100) / 100; }
  function barWidth(score) {
    var w = Math.min(100, Math.max(4, (score || 0) * 140));
    return w + "%";
  }
  function fmtMag(action) {
    if (!action || action.magnitude_pct == null) return "";
    if (action.type === "creative_rotate" || action.type === "suppress_segment") return "";
    var v = action.magnitude_pct;
    return (v > 0 ? "+" : "") + v + "%";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
