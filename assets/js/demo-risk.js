/* Risk Sentinel demo — enterprise events on a 5×5 severity×likelihood
 * matrix, lighting cell by cell, with exactly two escalations: one
 * auto-mitigated (green) and one vetoed (red, with rule id, evidence
 * chain, and rollback token).
 *
 * One POST to /api/demo/risk/run; the page paces the reveal locally.
 * Vanilla JS only; textContent everywhere; honors prefers-reduced-motion.
 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var STEP = reduceMotion ? 30 : 380;

  var els = {};
  var state = { timers: [], busy: false };

  function $(id) { return document.getElementById(id); }

  function emit(name, detail) {
    try {
      document.dispatchEvent(new CustomEvent(name, { detail: detail || {} }));
    } catch (err) { /* telemetry only */ }
  }

  function later(fn, delay) { state.timers.push(setTimeout(fn, delay)); }
  function clearTimers() { state.timers.forEach(clearTimeout); state.timers = []; }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function currentSeed() {
    var input = $("seedInput");
    var value = input ? parseInt(input.value, 10) : NaN;
    return isNaN(value) ? 42 : value;
  }

  function setStatus(text, live) {
    els.status.textContent = "";
    els.status.appendChild(el("span", live ? "live" : "", text));
  }

  function init() {
    els.scenario = $("scenario");
    els.start = $("startBtn");
    els.reset = $("resetBtn");
    els.status = $("status");
    els.matrix = $("riskMatrix");
    els.feed = $("eventFeed");
    els.escalations = $("escalations");
    els.finale = $("finaleCard");
    els.finaleHead = $("finaleHead");
    els.finaleSummary = $("finaleSummary");
    els.finaleNumbers = $("finaleNumbers");

    buildMatrix();

    fetch("/api/demo/risk/scenarios")
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

    els.start.addEventListener("click", startRun);
    els.reset.addEventListener("click", resetAll);
  }

  function buildMatrix() {
    els.matrix.textContent = "";
    // Severity 5 at the top row, likelihood 1..5 left to right.
    for (var sev = 5; sev >= 1; sev -= 1) {
      for (var lik = 1; lik <= 5; lik += 1) {
        var cell = el("div", "rm-cell heat-" + (sev + lik));
        cell.id = "cell-s" + sev + "l" + lik;
        cell.setAttribute("role", "img");
        cell.setAttribute("aria-label",
          "severity " + sev + ", likelihood " + lik + ": 0 events");
        cell.dataset.count = "0";
        var count = el("span", "rm-count", "");
        cell.appendChild(count);
        els.matrix.appendChild(cell);
      }
    }
  }

  function resetAll() {
    clearTimers();
    state.busy = false;
    els.start.disabled = false;
    buildMatrix();
    els.feed.textContent = "";
    els.escalations.textContent = "";
    els.finale.classList.remove("on");
    setStatus("idle", false);
  }

  function startRun() {
    if (state.busy) return;
    resetAll();
    state.busy = true;
    els.start.disabled = true;
    var scenario = els.scenario.value || "quarterly_close";
    setStatus("sensing · " + scenario, true);
    emit("mizoki:demo-started", { scenario: scenario, seed: currentSeed() });

    fetch("/api/demo/risk/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: scenario, seed: currentSeed() })
    })
      .then(function (r) {
        if (!r.ok) throw new Error("run failed: " + r.status);
        return r.json();
      })
      .then(render)
      .catch(function () {
        setStatus("demo backend unavailable", false);
        state.busy = false;
        els.start.disabled = false;
      });
  }

  function render(run) {
    (run.events || []).forEach(function (event, index) {
      later(function () { landEvent(event); }, index * STEP);
    });

    var afterEvents = (run.events || []).length * STEP + 300;
    (run.escalations || []).forEach(function (esc, index) {
      later(function () { renderEscalation(esc); }, afterEvents + index * (STEP * 2));
    });

    later(function () {
      els.finaleHead.textContent = run.finale.headline;
      els.finaleSummary.textContent = run.finale.summary + "  [trace " + run.trace_id + "]";
      els.finaleNumbers.textContent = "";
      (run.finale.key_numbers || []).forEach(function (kn) {
        var cell = el("div", "cell");
        cell.appendChild(el("div", "num", kn.value));
        cell.appendChild(el("div", "cap", kn.label));
        els.finaleNumbers.appendChild(cell);
      });
      els.finale.classList.add("on");
      setStatus("run complete — reproducible with seed " + currentSeed(), true);
      state.busy = false;
      els.start.disabled = false;
      emit("mizoki:demo-completed", { scenario: run.scenario });
    }, afterEvents + (run.escalations || []).length * (STEP * 2) + 400);
  }

  function landEvent(event) {
    var cell = $("cell-" + event.cell_id);
    if (cell) {
      var count = parseInt(cell.dataset.count || "0", 10) + 1;
      cell.dataset.count = String(count);
      cell.classList.add("lit");
      if (event.escalation === "auto_mitigated") cell.classList.add("auto");
      if (event.escalation === "vetoed") cell.classList.add("veto");
      cell.querySelector(".rm-count").textContent = String(count);
      cell.setAttribute("aria-label",
        "severity " + event.severity + ", likelihood " + event.likelihood +
        ": " + count + " events");
    }
    var row = el("div", "feed-row" +
      (event.escalation === "vetoed" ? " veto" :
        event.escalation === "auto_mitigated" ? " auto" : ""));
    row.appendChild(el("span", "feed-id", event.event_id));
    row.appendChild(el("span", "feed-cat", event.category_label));
    row.appendChild(el("span", "feed-ent", event.entity_id));
    row.appendChild(el("span", "feed-cell", "s" + event.severity + "·l" + event.likelihood));
    els.feed.appendChild(row);
    els.feed.scrollTop = els.feed.scrollHeight;
    requestAnimationFrame(function () { row.classList.add("on"); });
  }

  function renderEscalation(esc) {
    var vetoed = esc.kind === "vetoed";
    var card = el("article", "esc-card " + (vetoed ? "veto" : "auto"));
    card.setAttribute("role", vetoed ? "alert" : "status");

    var head = el("div", "esc-head");
    head.appendChild(el("span", "esc-kind", vetoed ? "VETOED" : "AUTO-MITIGATED"));
    head.appendChild(el("span", "esc-rule", "rule " + esc.rule_id));
    card.appendChild(head);
    card.appendChild(el("div", "esc-entity", esc.entity_id + " · " + esc.event_id));
    card.appendChild(el("p", "esc-detail", esc.detail));
    if (esc.mitigation) card.appendChild(el("p", "esc-mitigation", "✓ " + esc.mitigation));

    var chain = el("div", "esc-chain");
    chain.appendChild(el("div", "esc-chain-title", "evidence chain"));
    (esc.evidence_chain || []).forEach(function (step, index) {
      chain.appendChild(el("div", "esc-chain-step", (index + 1) + ". " + step));
    });
    card.appendChild(chain);

    if (esc.rollback_token) {
      card.appendChild(el("div", "esc-token",
        "rollback token " + esc.rollback_token + " — minted before anything could execute"));
    }
    els.escalations.appendChild(card);
    requestAnimationFrame(function () { card.classList.add("on"); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
