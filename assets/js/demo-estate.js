/* Estate Room demo — statutory clocks, dynasty graph, basis step-up.
 *
 * One POST to /api/demo/estate/run returns the full run; this file paces
 * the reveal client-side. Vanilla JS only; textContent everywhere;
 * honors prefers-reduced-motion.
 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var STAGGER = reduceMotion ? 30 : 420;

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
    var span = el("span", live ? "live" : "", text);
    els.status.appendChild(span);
  }

  function init() {
    els.scenario = $("scenario");
    els.start = $("startBtn");
    els.reset = $("resetBtn");
    els.status = $("status");
    els.widget = $("estateWidget");
    els.widgetTitle = $("widgetTitle");
    els.finale = $("finaleCard");
    els.finaleHead = $("finaleHead");
    els.finaleSummary = $("finaleSummary");
    els.finaleNumbers = $("finaleNumbers");
    els.authorities = $("authorityChips");

    fetch("/api/demo/estate/scenarios")
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

  function resetAll() {
    clearTimers();
    state.busy = false;
    els.start.disabled = false;
    els.widget.textContent = "";
    els.widgetTitle.textContent = "—";
    els.finale.classList.remove("on");
    els.authorities.textContent = "";
    setStatus("idle", false);
  }

  function startRun() {
    if (state.busy) return;
    resetAll();
    state.busy = true;
    els.start.disabled = true;
    var scenario = els.scenario.value || "ct_estate_settlement";
    setStatus("running · " + scenario, true);
    emit("mizoki:demo-started", { scenario: scenario, seed: currentSeed() });

    fetch("/api/demo/estate/run", {
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
    if (run.widget === "statutory_timeline") renderTimeline(run);
    else if (run.widget === "dynasty_graph") renderGraph(run);
    else renderBasisTable(run);

    (run.authorities || []).forEach(function (auth) {
      var chip = el("span", "auth-chip", auth.citation + " ");
      chip.appendChild(el("span", "note", "· " + auth.note));
      els.authorities.appendChild(chip);
    });

    var revealDelay = 600 + ((run.timeline || run.assets ||
      (run.graph || {}).nodes || []).length + 1) * STAGGER;
    later(function () {
      els.finaleHead.textContent = run.finale.headline;
      els.finaleSummary.textContent = run.finale.summary +
        "  [trace " + run.trace_id + "]";
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
    }, revealDelay);
  }

  // ---- widget: statutory-clock timeline -----------------------------------

  function renderTimeline(run) {
    els.widgetTitle.textContent = "The five statutory clocks · " +
      run.estate.decedent + " · " + run.estate.domicile;
    var wrap = el("div", "est-timeline");
    wrap.setAttribute("role", "list");
    els.widget.appendChild(wrap);

    (run.timeline || []).forEach(function (clock, index) {
      later(function () {
        var item = el("div", "est-clock");
        item.setAttribute("role", "listitem");
        item.setAttribute("aria-label",
          clock.label + " — " + clock.badge +
          (clock.depends_on.length ? " (depends on " + clock.depends_on.join(", ") + ")" : ""));
        item.id = "clock-" + clock.clock_id;

        var rail = el("div", "est-clock-rail");
        rail.appendChild(el("span", "est-clock-dot"));
        if (index < run.timeline.length - 1) rail.appendChild(el("span", "est-clock-line"));
        item.appendChild(rail);

        var body = el("div", "est-clock-body");
        var head = el("div", "est-clock-head");
        head.appendChild(el("span", "est-clock-label", clock.label));
        head.appendChild(el("span", "deadline-badge", clock.badge));
        body.appendChild(head);
        body.appendChild(el("p", "est-clock-detail", clock.detail));
        if (clock.depends_on && clock.depends_on.length) {
          body.appendChild(el("div", "est-clock-dep",
            "↳ depends on " + clock.depends_on.join(", ")));
        }
        if (clock.authority) {
          var chip = el("span", "auth-chip", clock.authority.citation + " ");
          chip.appendChild(el("span", "note", "· " + clock.authority.note));
          body.appendChild(chip);
        }
        item.appendChild(body);
        wrap.appendChild(item);
        requestAnimationFrame(function () { item.classList.add("on"); });
      }, index * STAGGER);
    });
  }

  // ---- widget: three-generation dynasty graph -----------------------------

  function renderGraph(run) {
    els.widgetTitle.textContent = "Three generations · GST grandfather flag";
    var graph = run.graph || { nodes: [], edges: [] };
    var svgNS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", "0 0 760 420");
    svg.setAttribute("class", "est-graph");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label",
      "Family and trust graph across three generations with transfer-tax exposure per node");
    els.widget.appendChild(svg);

    var positions = {};
    var byGen = { 1: [], 2: [], 3: [] };
    graph.nodes.forEach(function (node) { (byGen[node.generation] || byGen[1]).push(node); });
    Object.keys(byGen).forEach(function (gen) {
      var row = byGen[gen];
      row.forEach(function (node, index) {
        positions[node.node_id] = {
          x: 380 + (index - (row.length - 1) / 2) * 250,
          y: 70 + (parseInt(gen, 10) - 1) * 140
        };
      });
    });

    graph.edges.forEach(function (edge) {
      var from = positions[edge.from];
      var to = positions[edge.to];
      if (!from || !to) return;
      var line = document.createElementNS(svgNS, "line");
      line.setAttribute("x1", from.x); line.setAttribute("y1", from.y + 26);
      line.setAttribute("x2", to.x); line.setAttribute("y2", to.y - 26);
      line.setAttribute("stroke", edge.relation === "remainder_beneficiary"
        ? "rgba(65, 214, 149,0.55)" : "rgba(255,255,255,0.22)");
      line.setAttribute("stroke-width", "1.6");
      if (edge.relation === "remainder_beneficiary") line.setAttribute("stroke-dasharray", "5 4");
      svg.appendChild(line);
    });

    graph.nodes.forEach(function (node, index) {
      later(function () {
        var pos = positions[node.node_id];
        var group = document.createElementNS(svgNS, "g");
        group.setAttribute("opacity", "0");

        var isTrust = node.kind === "trust";
        var rect = document.createElementNS(svgNS, "rect");
        rect.setAttribute("x", pos.x - 100); rect.setAttribute("y", pos.y - 26);
        rect.setAttribute("width", "200"); rect.setAttribute("height", "52");
        rect.setAttribute("rx", isTrust ? "10" : "26");
        rect.setAttribute("fill", "#0B1E26");
        rect.setAttribute("stroke", isTrust ? "#41D695" : "rgba(255,255,255,0.3)");
        rect.setAttribute("stroke-width", isTrust ? "2" : "1.2");
        group.appendChild(rect);

        var label = document.createElementNS(svgNS, "text");
        label.setAttribute("x", pos.x); label.setAttribute("y", pos.y - 4);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("fill", "#F4F6F7");
        label.setAttribute("font-size", "13");
        label.textContent = node.label;
        group.appendChild(label);

        var sub = document.createElementNS(svgNS, "text");
        sub.setAttribute("x", pos.x); sub.setAttribute("y", pos.y + 15);
        sub.setAttribute("text-anchor", "middle");
        sub.setAttribute("font-size", "10.5");
        sub.setAttribute("font-family", "JetBrains Mono, monospace");
        if (node.gst_grandfathered) {
          sub.setAttribute("fill", "#41D695");
          sub.textContent = "GST GRANDFATHERED ✓";
        } else {
          sub.setAttribute("fill", node.transfer_tax_exposure > 0 ? "#fca5a5" : "#5E6E75");
          sub.textContent = node.transfer_tax_exposure > 0
            ? "exposure $" + node.transfer_tax_exposure.toLocaleString()
            : "no current exposure";
        }
        group.appendChild(sub);
        svg.appendChild(group);
        requestAnimationFrame(function () { group.setAttribute("opacity", "1"); });
      }, index * STAGGER);
    });

    var flag = run.grandfather_flag || {};
    later(function () {
      var banner = el("div", "est-flag-banner");
      banner.setAttribute("role", "note");
      banner.appendChild(el("strong", "", "Grandfather flag: "));
      banner.appendChild(document.createTextNode(
        flag.at_risk_if + " Corpus at stake: $" +
        (flag.corpus_at_stake || 0).toLocaleString() +
        " at a " + Math.round((flag.gst_rate_if_lost || 0.4) * 100) + "% GST rate."));
      els.widget.appendChild(banner);
    }, graph.nodes.length * STAGGER + 200);
  }

  // ---- widget: basis step-up table ----------------------------------------

  function renderBasisTable(run) {
    els.widgetTitle.textContent = "IRC § 1014 basis step-up at date of death";
    var table = el("table", "est-basis-table");
    var caption = el("caption", "", "Pre/post-death basis per asset — deterministic seeded valuations");
    table.appendChild(caption);
    var thead = el("thead");
    var headRow = el("tr");
    ["Asset", "Acquired", "Cost basis", "DOD value", "Stepped basis", "Gain eliminated"].forEach(function (h) {
      var th = el("th", "", h);
      th.scope = "col";
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);
    var tbody = el("tbody");
    table.appendChild(tbody);
    els.widget.appendChild(table);

    (run.assets || []).forEach(function (asset, index) {
      later(function () {
        var row = el("tr", "est-basis-row");
        row.appendChild(el("td", "", asset.label));
        row.appendChild(el("td", "", asset.acquired));
        row.appendChild(el("td", "mono", "$" + asset.cost_basis.toLocaleString()));
        row.appendChild(el("td", "mono", "$" + asset.date_of_death_value.toLocaleString()));
        row.appendChild(el("td", "mono up", "$" + asset.stepped_basis.toLocaleString()));
        row.appendChild(el("td", "mono up", "$" + asset.unrealized_gain_eliminated.toLocaleString()));
        tbody.appendChild(row);
        requestAnimationFrame(function () { row.classList.add("on"); });
      }, index * STAGGER);
    });

    later(function () {
      var totals = run.totals || {};
      var foot = el("tfoot");
      var row = el("tr", "est-basis-total");
      var label = el("td", "", "Total unrealized gain eliminated");
      label.colSpan = 5;
      row.appendChild(label);
      row.appendChild(el("td", "mono up",
        "$" + (totals.unrealized_gain_eliminated || 0).toLocaleString()));
      foot.appendChild(row);
      table.appendChild(foot);
    }, (run.assets || []).length * STAGGER + 100);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
