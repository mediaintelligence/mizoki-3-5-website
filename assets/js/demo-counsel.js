/* Counsel Room demo — Mixture-of-Legal-Experts front end.
 *
 * One POST to /api/demo/counsel/query returns the full synthesis; this file
 * orchestrates the staggered reveal client-side. Vanilla JS only.
 *
 * Security note: any user-supplied free text is only ever rendered via
 * textContent — never innerHTML — so echoed queries cannot inject markup.
 */
(function () {
  "use strict";

  var EXPERT_ORDER = ["ct_law", "trust_law", "estate_law", "tax_law"];
  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var STAGGER = reduceMotion ? 40 : 600;

  var els = {};
  var state = { selectedScenario: null, timers: [], busy: false };

  function $(id) { return document.getElementById(id); }

  function init() {
    els.grid = $("scenarioGrid");
    els.freeText = $("freeText");
    els.ask = $("askBtn");
    els.status = $("crStatus");
    els.router = $("routerGrid");
    els.irac = $("iracGrid");
    els.conflict = $("conflictBanner");
    els.synth = $("synthPanel");
    els.warning = $("upWarning");

    renderRouterSkeleton();
    loadScenarios();
    els.ask.addEventListener("click", submit);
    els.freeText.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); submit(); }
    });
    els.freeText.addEventListener("input", function () {
      state.selectedScenario = null;
      highlightSelection();
    });
  }

  function loadScenarios() {
    fetch("/api/demo/counsel/scenarios")
      .then(function (r) { return r.json(); })
      .then(function (body) {
        els.grid.textContent = "";
        (body.scenarios || []).forEach(function (s) {
          var card = document.createElement("button");
          card.type = "button";
          card.className = "scn-card";
          card.dataset.id = s.id;
          var h = document.createElement("h3");
          h.textContent = s.title;
          card.appendChild(h);
          var p = document.createElement("p");
          p.textContent = s.description;
          card.appendChild(p);
          card.addEventListener("click", function () {
            state.selectedScenario = s.id;
            els.freeText.value = "";
            highlightSelection();
            submit();
          });
          els.grid.appendChild(card);
        });
      })
      .catch(function () { setStatus("could not load scenarios"); });
  }

  function highlightSelection() {
    Array.prototype.forEach.call(els.grid.children, function (card) {
      card.classList.toggle("sel", card.dataset.id === state.selectedScenario);
    });
  }

  function setStatus(text) { els.status.textContent = text; }

  function clearTimers() {
    state.timers.forEach(clearTimeout);
    state.timers = [];
  }

  function later(fn, delay) { state.timers.push(setTimeout(fn, delay)); }

  function submit() {
    if (state.busy) return;
    var query = (els.freeText.value || "").trim();
    var body = {};
    if (state.selectedScenario && !query) {
      body.scenario_id = state.selectedScenario;
    } else if (query) {
      if (query.length > 500) { setStatus("query too long (max 500 chars)"); return; }
      body.query = query;
    } else {
      setStatus("pick a scenario or describe your situation");
      return;
    }

    clearTimers();
    resetPanels();
    state.busy = true;
    els.ask.disabled = true;
    setStatus("routing to experts…");
    try {
      document.dispatchEvent(new CustomEvent("mizoki:demo-started", {
        detail: { scenario: body.scenario_id || "free_text" }
      }));
    } catch (err) { /* telemetry only */ }

    fetch("/api/demo/counsel/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
      .then(function (r) {
        return r.json().then(function (data) {
          if (!r.ok) throw new Error(data.error || ("request failed: " + r.status));
          return data;
        });
      })
      .then(render)
      .catch(function (err) {
        setStatus(String(err.message || err));
        state.busy = false;
        els.ask.disabled = false;
      });
  }

  function resetPanels() {
    renderRouterSkeleton();
    els.irac.textContent = "";
    els.conflict.textContent = "";
    els.conflict.classList.remove("on", "slid");
    els.synth.textContent = "";
    els.synth.classList.remove("on");
  }

  function renderRouterSkeleton() {
    els.router.textContent = "";
    EXPERT_ORDER.forEach(function (expert) {
      var tile = document.createElement("div");
      tile.className = "expert-tile";
      tile.id = "tile-" + expert;
      var h = document.createElement("h4");
      h.textContent = labelFor(expert);
      tile.appendChild(h);
      var score = document.createElement("div");
      score.className = "score-num";
      score.textContent = "—";
      tile.appendChild(score);
      var track = document.createElement("div");
      track.className = "track";
      var fill = document.createElement("div");
      fill.className = "fill";
      track.appendChild(fill);
      tile.appendChild(track);
      var why = document.createElement("p");
      why.className = "why";
      why.textContent = "Awaiting routing…";
      tile.appendChild(why);
      els.router.appendChild(tile);
    });
  }

  function labelFor(expert) {
    return {
      ct_law: "Connecticut Law",
      trust_law: "Trust Law",
      estate_law: "Estate Law",
      tax_law: "Tax Law"
    }[expert] || expert;
  }

  function render(response) {
    // Scenario echo — textContent only (XSS-safe for free text).
    var scenarioLine = "scenario: " + response.scenario.id;
    if (response.query) scenarioLine += " · routed from your text";
    setStatus(scenarioLine);

    if (response.unauthorized_practice_warning) {
      els.warning.textContent = response.unauthorized_practice_warning;
    }

    // 1. Router tiles with animated relevance bars.
    (response.routing || []).forEach(function (entry, index) {
      later(function () { paintTile(entry); }, index * (reduceMotion ? 20 : 220));
    });

    // 2. Expert IRAC cards, staggered ~600ms apart, collapsible.
    var analyses = response.expert_analyses || [];
    analyses.forEach(function (analysis, index) {
      later(function () {
        var card = buildIracCard(analysis, index === 0);
        els.irac.appendChild(card);
        requestAnimationFrame(function () { card.classList.add("on"); });
      }, 900 + index * STAGGER);
    });

    var afterExperts = 900 + analyses.length * STAGGER + 300;

    // 3. Conflict banner — only when conflicts exist, sliding in last.
    var conflicts = response.conflicts || [];
    if (conflicts.length) {
      later(function () {
        renderConflicts(conflicts);
      }, afterExperts);
    }

    // 4. Synthesis + numbered compliance checklist.
    later(function () {
      renderSynthesis(response);
      state.busy = false;
      els.ask.disabled = false;
      setStatus("consultation complete — flagged for attorney review");
      try {
        document.dispatchEvent(new CustomEvent("mizoki:demo-completed", {
          detail: { scenario: response.scenario.id }
        }));
      } catch (err) { /* telemetry only */ }
    }, afterExperts + (conflicts.length ? (reduceMotion ? 60 : 500) : 0));
  }

  function paintTile(entry) {
    var tile = $("tile-" + entry.expert);
    if (!tile) return;
    tile.classList.remove("dimmed", "consulted");
    tile.classList.add(entry.consulted ? "consulted" : "dimmed");
    tile.querySelector(".score-num").textContent =
      entry.relevance.toFixed(2) + (entry.consulted ? "" : " · not consulted");
    tile.querySelector(".why").textContent = entry.rationale;
    var fill = tile.querySelector(".fill");
    requestAnimationFrame(function () {
      fill.style.width = Math.round(entry.relevance * 100) + "%";
    });
  }

  function buildIracCard(analysis, startOpen) {
    var card = document.createElement("article");
    card.className = "irac-card" + (startOpen ? " openb" : "");

    var head = document.createElement("button");
    head.type = "button";
    head.className = "irac-head";
    var title = document.createElement("span");
    title.textContent = labelFor(analysis.expert) + " — IRAC analysis";
    head.appendChild(title);
    var conf = document.createElement("span");
    conf.className = "conf";
    conf.textContent = "confidence " + analysis.confidence.toFixed(2);
    head.appendChild(conf);
    var chev = document.createElement("span");
    chev.className = "chev";
    chev.textContent = "▾";
    head.appendChild(chev);
    head.addEventListener("click", function () { card.classList.toggle("openb"); });
    card.appendChild(head);

    var body = document.createElement("div");
    body.className = "irac-body";
    ["issue", "rule", "application", "conclusion"].forEach(function (key) {
      var el = document.createElement("div");
      el.className = "irac-el";
      var k = document.createElement("span");
      k.className = "k";
      k.textContent = key;
      el.appendChild(k);
      var p = document.createElement("p");
      p.textContent = analysis.irac[key];
      el.appendChild(p);
      body.appendChild(el);
    });

    var authWrap = document.createElement("div");
    authWrap.className = "irac-el";
    var ak = document.createElement("span");
    ak.className = "k";
    ak.textContent = "authorities";
    authWrap.appendChild(ak);
    var chips = document.createElement("div");
    chips.className = "auth-chips";
    (analysis.authorities || []).forEach(function (auth) {
      var chip = document.createElement("span");
      chip.className = "auth-chip";
      chip.textContent = auth.citation + " ";
      var note = document.createElement("span");
      note.className = "note";
      note.textContent = "· " + auth.note;
      chip.appendChild(note);
      chips.appendChild(chip);
    });
    authWrap.appendChild(chips);
    body.appendChild(authWrap);
    card.appendChild(body);
    return card;
  }

  function renderConflicts(conflicts) {
    els.conflict.textContent = "";
    var h = document.createElement("h3");
    h.textContent = "⚠ Cross-domain conflict detected";
    els.conflict.appendChild(h);
    conflicts.forEach(function (conflict) {
      var sum = document.createElement("p");
      sum.className = "c-sum";
      var sev = document.createElement("span");
      sev.className = "sev";
      sev.textContent = conflict.severity;
      sum.appendChild(sev);
      sum.appendChild(document.createTextNode(conflict.summary));
      els.conflict.appendChild(sum);
      var rec = document.createElement("p");
      rec.className = "c-rec";
      rec.textContent = "Recommendation: " + conflict.recommendation +
        "  [" + (conflict.domains || []).join(" × ") + "]";
      els.conflict.appendChild(rec);
    });
    els.conflict.classList.add("on");
    requestAnimationFrame(function () {
      els.conflict.classList.add("slid");
    });
  }

  function renderSynthesis(response) {
    els.synth.textContent = "";
    var h = document.createElement("h3");
    h.textContent = "Synthesized counsel";
    els.synth.appendChild(h);

    ["issue", "rule", "application", "conclusion"].forEach(function (key) {
      var el = document.createElement("div");
      el.className = "synth-el";
      var k = document.createElement("span");
      k.className = "k";
      k.textContent = key;
      el.appendChild(k);
      var p = document.createElement("p");
      p.textContent = response.synthesis[key];
      el.appendChild(p);
      els.synth.appendChild(el);
    });

    var listTitle = document.createElement("div");
    listTitle.className = "synth-el";
    var lk = document.createElement("span");
    lk.className = "k";
    lk.textContent = "compliance checklist";
    listTitle.appendChild(lk);
    els.synth.appendChild(listTitle);

    var list = document.createElement("ol");
    list.className = "checklist";
    list.style.listStyle = "none";
    (response.compliance_checklist || []).forEach(function (item) {
      var li = document.createElement("li");
      li.className = "check-item";
      var n = document.createElement("span");
      n.className = "n";
      li.appendChild(n);
      var s = document.createElement("span");
      s.className = "s";
      s.textContent = item.step;
      li.appendChild(s);
      var badge = document.createElement("span");
      badge.className = "deadline-badge";
      badge.textContent = item.deadline;
      li.appendChild(badge);
      list.appendChild(li);
    });
    els.synth.appendChild(list);
    els.synth.classList.add("on");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
