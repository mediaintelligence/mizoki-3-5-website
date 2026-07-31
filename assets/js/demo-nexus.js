/* The Nexus Run — flagship demo front end.
 *
 * Explore mode: five division panels fill from the SSE stream (or a
 * POST+replay fallback). Boardroom mode: full-screen, auto-playing,
 * ≤ 90 s end-to-end, hotkeys (Space advance · R restart · Esc exit),
 * a progress rail of five division dots, projector-friendly type.
 *
 * Vanilla JS only; textContent everywhere; honors prefers-reduced-motion.
 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var ACCENTS = {
    signal: "#9D7BE8", capital: "#D9A83C", risk: "#FF6B7C",
    counsel: "#5FA0DC", estate: "#41D695"
  };

  var els = {};
  var state = { source: null, timers: [], running: false, run: null, board: null };

  function $(id) { return document.getElementById(id); }

  function emit(name, detail) {
    try {
      document.dispatchEvent(new CustomEvent(name, { detail: detail || {} }));
    } catch (err) { /* telemetry only */ }
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function later(fn, delay) { state.timers.push(setTimeout(fn, delay)); }
  function clearTimers() { state.timers.forEach(clearTimeout); state.timers = []; }

  function currentSeed() {
    var input = $("seedInput");
    var value = input ? parseInt(input.value, 10) : NaN;
    return isNaN(value) ? 42 : value;
  }

  function currentScenario() {
    return (els.scenario && els.scenario.value) || "cpm_shock";
  }

  function setStatus(text, live) {
    els.status.textContent = "";
    els.status.appendChild(el("span", live ? "live" : "", text));
  }

  function init() {
    els.scenario = $("scenario");
    els.start = $("startBtn");
    els.reset = $("resetBtn");
    els.board = $("boardroomBtn");
    els.status = $("status");
    els.trigger = $("triggerCard");
    els.panels = $("divisionPanels");
    els.provenance = $("provenancePanel");
    els.overlay = $("boardroom");

    fetch("/api/demo/nexus/scenarios")
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

    els.start.addEventListener("click", startExplore);
    els.reset.addEventListener("click", resetAll);
    els.board.addEventListener("click", enterBoardroom);
    document.addEventListener("keydown", boardroomKeys);
  }

  function resetAll() {
    stopTransport();
    state.running = false;
    state.run = null;
    els.start.disabled = false;
    els.trigger.classList.remove("on");
    els.trigger.textContent = "";
    els.panels.textContent = "";
    els.provenance.textContent = "";
    els.provenance.classList.remove("on");
    setStatus("idle", false);
  }

  function stopTransport() {
    if (state.source) { state.source.close(); state.source = null; }
    clearTimers();
  }

  // ---- Explore mode -------------------------------------------------------

  function startExplore() {
    if (state.running) return;
    resetAll();
    state.running = true;
    els.start.disabled = true;
    var scenario = currentScenario();
    setStatus("streaming · " + scenario, true);
    emit("mizoki:demo-started", { scenario: scenario, seed: currentSeed() });

    if (!window.EventSource) { fallbackRun(scenario); return; }

    var source = new EventSource(
      "/api/demo/nexus/stream?scenario=" + encodeURIComponent(scenario) +
      "&seed=" + currentSeed()
    );
    state.source = source;
    var gotFrame = false;

    ["trigger", "division_start", "division_event", "division_verdict", "provenance"].forEach(function (type) {
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
      if (!gotFrame && state.running) fallbackRun(scenario);
      else if (state.running) {
        setStatus("stream interrupted — press Reset to try again", false);
        state.running = false;
        els.start.disabled = false;
      }
    };
  }

  function fallbackRun(scenario) {
    setStatus("replaying · " + scenario + " (fallback)", true);
    fetchRun(scenario).then(function (run) {
      var delay = 0;
      framesFromRun(run).forEach(function (frame) {
        delay += reduceMotion ? 20 : frame[2];
        later(function () { handleFrame(frame[0], frame[1]); }, delay);
      });
    }).catch(function () {
      setStatus("demo backend unavailable", false);
      state.running = false;
      els.start.disabled = false;
    });
  }

  function fetchRun(scenario) {
    return fetch("/api/demo/nexus/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenario, seed: currentSeed() })
    }).then(function (r) {
      if (!r.ok) throw new Error("run failed: " + r.status);
      return r.json();
    });
  }

  function framesFromRun(run) {
    var frames = [["trigger", run.trigger, 800]];
    (run.divisions || []).forEach(function (seg) {
      frames.push(["division_start", {
        division: seg.division,
        nexus_trace_id: seg.nexus_trace_id,
        division_trace_id: seg.division_trace_id,
        headline: seg.headline
      }, 700]);
      (seg.events || []).forEach(function (event) {
        frames.push(["division_event", { division: seg.division, event: event }, 700]);
      });
      frames.push(["division_verdict", { division: seg.division, verdict: seg.verdict }, 900]);
    });
    frames.push(["provenance", run.provenance, 1100]);
    frames.push(["done", {
      nexus_trace_id: run.nexus_trace_id, scenario: run.scenario,
      seed: run.seed, tagline: run.tagline
    }, 0]);
    return frames;
  }

  var handlers = {
    trigger: function (data) {
      els.trigger.textContent = "";
      els.trigger.appendChild(el("div", "nx-trigger-eyebrow", "// TRIGGER · " + data.source));
      els.trigger.appendChild(el("h3", "", data.title));
      els.trigger.appendChild(el("p", "", data.detail));
      els.trigger.classList.add("on");
    },
    division_start: function (data) {
      var panel = el("section", "nx-panel");
      panel.id = "nx-panel-" + data.division;
      panel.style.setProperty("--nx-accent", ACCENTS[data.division] || "#3FDCF2");
      var head = el("div", "nx-panel-head");
      head.appendChild(el("span", "nx-division", data.division.toUpperCase()));
      head.appendChild(el("span", "nx-headline", data.headline));
      panel.appendChild(head);
      panel.appendChild(el("div", "nx-trace",
        "trace " + data.nexus_trace_id + " · division " + data.division_trace_id));
      var list = el("div", "nx-events");
      list.setAttribute("aria-live", "polite");
      list.id = "nx-events-" + data.division;
      panel.appendChild(list);
      els.panels.appendChild(panel);
      requestAnimationFrame(function () { panel.classList.add("on"); });
      markDot(data.division, "active");
    },
    division_event: function (data) {
      var list = $("nx-events-" + data.division);
      if (!list) return;
      var row = el("div", "nx-event", data.event);
      list.appendChild(row);
      requestAnimationFrame(function () { row.classList.add("on"); });
    },
    division_verdict: function (data) {
      var panel = $("nx-panel-" + data.division);
      if (!panel) return;
      var verdict = data.verdict || {};
      var status = String(verdict.status || "");
      var bad = status === "vetoed" || status === "one_variant_blocked";
      var box = el("div", "nx-verdict " + (bad ? "hot" : "cool"));
      box.setAttribute("role", "status");
      box.appendChild(el("span", "nx-verdict-status", status.replace(/_/g, " ")));
      box.appendChild(el("p", "", verdict.detail || ""));
      if (verdict.veto && verdict.veto.rollback_token) {
        box.appendChild(el("div", "nx-token",
          "rule " + verdict.veto.rule_id + " · rollback " + verdict.veto.rollback_token));
      }
      if (verdict.blocked) {
        box.appendChild(el("div", "nx-token",
          "blocked " + verdict.blocked.action_id + " (" +
          (verdict.blocked.blocked_by || []).join(", ") + ")"));
      }
      panel.appendChild(box);
      markDot(data.division, "done");
    },
    provenance: function (data) {
      renderProvenance(data, els.provenance);
      els.provenance.classList.add("on");
    },
    done: function (data) {
      setStatus("run complete · " + (data.tagline || "") + " · trace " +
        (data.nexus_trace_id || ""), true);
      state.running = false;
      els.start.disabled = false;
      emit("mizoki:demo-completed", data || {});
    }
  };

  function handleFrame(type, data) {
    if (handlers[type]) handlers[type](data);
  }

  function markDot(division, stateName) {
    var dot = document.querySelector('.nx-dot[data-division="' + division + '"]');
    if (dot) { dot.classList.add(stateName); }
  }

  function renderProvenance(provenance, mount) {
    mount.textContent = "";
    mount.appendChild(el("h3", "", "Unified provenance — every division hanging off one trace"));
    var svgNS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", "0 0 900 330");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label",
      "Provenance graph: the trigger opens one trace and all five division decisions hang off it");
    svg.setAttribute("class", "nx-prov-svg");
    mount.appendChild(svg);

    var nodes = provenance.nodes || [];
    var trigger = nodes.filter(function (n) { return n.kind === "trigger"; })[0];
    var trace = nodes.filter(function (n) { return n.kind === "trace"; })[0];
    var divisions = nodes.filter(function (n) { return n.kind === "division_decision"; });

    var positions = {};
    if (trigger) positions[trigger.node_id] = { x: 450, y: 40 };
    if (trace) positions[trace.node_id] = { x: 450, y: 130 };
    divisions.forEach(function (node, index) {
      positions[node.node_id] = {
        x: 90 + index * (720 / Math.max(1, divisions.length - 1)),
        y: 260
      };
    });

    (provenance.edges || []).forEach(function (edge) {
      var from = positions[edge.from];
      var to = positions[edge.to];
      if (!from || !to) return;
      var line = document.createElementNS(svgNS, "line");
      line.setAttribute("x1", from.x); line.setAttribute("y1", from.y + 18);
      line.setAttribute("x2", to.x); line.setAttribute("y2", to.y - 18);
      line.setAttribute("stroke", "rgba(63, 220, 242,0.4)");
      line.setAttribute("stroke-width", "1.6");
      svg.appendChild(line);
    });

    nodes.forEach(function (node) {
      var pos = positions[node.node_id];
      if (!pos) return;
      var group = document.createElementNS(svgNS, "g");
      var rect = document.createElementNS(svgNS, "rect");
      var width = node.kind === "division_decision" ? 150 : 240;
      rect.setAttribute("x", pos.x - width / 2); rect.setAttribute("y", pos.y - 18);
      rect.setAttribute("width", width); rect.setAttribute("height", "36");
      rect.setAttribute("rx", "9");
      rect.setAttribute("fill", "#0B1E26");
      rect.setAttribute("stroke", node.kind === "division_decision"
        ? (ACCENTS[node.node_id] || "#3FDCF2") : "#3FDCF2");
      rect.setAttribute("stroke-width", node.kind === "trace" ? "2" : "1.2");
      group.appendChild(rect);
      var label = document.createElementNS(svgNS, "text");
      label.setAttribute("x", pos.x); label.setAttribute("y", pos.y + 4);
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#F4F6F7");
      label.setAttribute("font-size", node.kind === "division_decision" ? "10" : "12");
      label.setAttribute("font-family", "JetBrains Mono, monospace");
      var maxChars = node.kind === "division_decision" ? 22 : 34;
      label.textContent = node.label.length > maxChars
        ? node.label.slice(0, maxChars - 1) + "…" : node.label;
      group.appendChild(label);
      svg.appendChild(group);
    });
  }

  // ---- Boardroom mode -----------------------------------------------------

  function enterBoardroom() {
    var scenario = currentScenario();
    setStatus("boardroom · loading " + scenario, true);
    fetchRun(scenario).then(function (run) {
      state.run = run;
      buildBoardroom(run);
      els.overlay.hidden = false;
      document.body.classList.add("nx-board-open");
      emit("mizoki:demo-started", { scenario: scenario, seed: currentSeed() });
      window.MizokiDemoExtras && window.MizokiDemoExtras.beacon &&
        window.MizokiDemoExtras.beacon("boardroom_played", "nexus", scenario);
      playBoardroom(0);
    }).catch(function () { setStatus("demo backend unavailable", false); });
  }

  function buildBoardroom(run) {
    els.overlay.textContent = "";
    var rail = el("div", "nxb-rail");
    (run.divisions || []).forEach(function (seg) {
      var dot = el("span", "nxb-dot");
      dot.dataset.division = seg.division;
      dot.style.background = ACCENTS[seg.division] || "#3FDCF2";
      dot.setAttribute("aria-label", seg.division);
      rail.appendChild(dot);
    });
    els.overlay.appendChild(rail);
    els.overlay.appendChild(el("div", "nxb-stage"));
    var help = el("div", "nxb-help", "Space advance · R restart · Esc exit");
    els.overlay.appendChild(help);

    // Slides: trigger, one per division, finale (tagline + provenance ref).
    state.board = {
      slides: buildSlides(run),
      index: -1,
      timer: null
    };
  }

  function buildSlides(run) {
    var slides = [{
      kind: "trigger",
      eyebrow: "// TRIGGER",
      title: run.trigger.title,
      lines: [run.trigger.detail],
      accent: "#3FDCF2",
      hold: 7000
    }];
    (run.divisions || []).forEach(function (seg) {
      slides.push({
        kind: "division",
        division: seg.division,
        eyebrow: "// " + seg.division.toUpperCase(),
        title: seg.headline,
        lines: seg.events.concat([verdictLine(seg.verdict)]),
        accent: ACCENTS[seg.division] || "#3FDCF2",
        hold: 13000
      });
    });
    slides.push({
      kind: "finale",
      eyebrow: "// " + run.nexus_trace_id,
      title: run.tagline,
      lines: [
        "Every division's decision hangs off one trace id.",
        "Same seed, same run — replay it on your own machine."
      ],
      accent: "#9D7BE8",
      hold: 8000
    });
    return slides;
  }

  function verdictLine(verdict) {
    var status = String((verdict || {}).status || "").replace(/_/g, " ");
    return "VERDICT: " + status + " — " + ((verdict || {}).detail || "");
  }

  function playBoardroom(index) {
    var board = state.board;
    if (!board) return;
    if (board.timer) clearTimeout(board.timer);
    if (index >= board.slides.length) { exitBoardroom(); return; }
    board.index = index;
    var slide = board.slides[index];
    var stage = els.overlay.querySelector(".nxb-stage");
    stage.textContent = "";
    stage.style.setProperty("--nx-accent", slide.accent);

    stage.appendChild(el("div", "nxb-eyebrow", slide.eyebrow));
    stage.appendChild(el("h2", "nxb-title", slide.title));
    var list = el("div", "nxb-lines");
    stage.appendChild(list);

    var lineDelay = reduceMotion ? 60 :
      Math.min(1400, Math.floor((slide.hold - 2000) / Math.max(1, slide.lines.length)));
    slide.lines.forEach(function (line, lineIndex) {
      var row = el("p", "nxb-line" + (line.indexOf("VERDICT:") === 0 ? " verdict" : ""), line);
      list.appendChild(row);
      setTimeout(function () { row.classList.add("on"); }, lineIndex * lineDelay);
    });

    // Mark progress rail.
    var dots = els.overlay.querySelectorAll(".nxb-dot");
    Array.prototype.forEach.call(dots, function (dot, dotIndex) {
      dot.classList.toggle("active", slide.kind === "division" && dotIndex === index - 1);
      dot.classList.toggle("done", index - 1 > dotIndex);
    });

    var hold = reduceMotion ? Math.min(slide.hold, 2500) : slide.hold;
    board.timer = setTimeout(function () { playBoardroom(index + 1); }, hold);
  }

  function exitBoardroom() {
    if (state.board && state.board.timer) clearTimeout(state.board.timer);
    state.board = null;
    els.overlay.hidden = true;
    document.body.classList.remove("nx-board-open");
    setStatus("boardroom closed — explore the panels below", false);
  }

  function boardroomKeys(evt) {
    if (!state.board || els.overlay.hidden) return;
    if (evt.key === " " || evt.code === "Space") {
      evt.preventDefault();
      playBoardroom(state.board.index + 1);
    } else if (evt.key === "r" || evt.key === "R") {
      evt.preventDefault();
      playBoardroom(0);
    } else if (evt.key === "Escape") {
      evt.preventDefault();
      exitBoardroom();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
