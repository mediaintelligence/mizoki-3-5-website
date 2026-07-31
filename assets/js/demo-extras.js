/* MIZ OKI demo extras — shared showcase widgets for every demo page.
 *
 * Provides: shareable deterministic replays (?scenario=&seed= autorun +
 * "Copy shareable run"), the Trace Narrator "Why?" toggle, the MCP proof
 * terminal, the signed audit export download, cookieless telemetry
 * beacons, and the Governance Challenge drawer (Signal + Capital).
 *
 * Vanilla JS only. All user-adjacent text is rendered via textContent.
 */
(function () {
  "use strict";

  var CANONICAL = "https://mizoki3.com";
  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function $(id) { return document.getElementById(id); }

  function beacon(event, demo, scenario) {
    var payload = JSON.stringify({
      event: event,
      demo: demo,
      scenario: scenario || "unknown"
    });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(
          "/api/demo/telemetry",
          new Blob([payload], { type: "application/json" })
        );
        return;
      }
    } catch (err) { /* telemetry must never break the demo */ }
    try {
      fetch("/api/demo/telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true
      });
    } catch (err) { /* ignore */ }
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function init(config) {
    var demo = config.demo;

    function getScenario() {
      if (config.getScenario) return config.getScenario();
      var select = $(config.scenarioSelect || "scenario");
      return (select && select.value) || config.defaultScenario || "";
    }

    function getSeed() {
      if (config.getSeed) return config.getSeed();
      var input = $(config.seedInput || "seedInput");
      var value = input ? parseInt(input.value, 10) : NaN;
      return isNaN(value) ? 42 : value;
    }

    function shareUrl() {
      return CANONICAL + "/demo/" + demo +
        "?scenario=" + encodeURIComponent(getScenario()) +
        "&seed=" + encodeURIComponent(getSeed());
    }

    function mcpArguments() {
      if (config.mcpArgs) return config.mcpArgs(getScenario(), getSeed());
      return { scenario: getScenario(), seed: getSeed() };
    }

    // ---- telemetry wiring -------------------------------------------------

    document.addEventListener("mizoki:demo-started", function (evt) {
      beacon("demo_started", demo, (evt.detail || {}).scenario || getScenario());
    });
    document.addEventListener("mizoki:demo-completed", function (evt) {
      beacon("demo_completed", demo, (evt.detail || {}).scenario || getScenario());
    });
    document.addEventListener("click", function (evt) {
      var target = evt.target && evt.target.closest &&
        evt.target.closest("[data-telemetry]");
      if (target) beacon(target.dataset.telemetry, demo, getScenario());
    });

    // ---- toolbar ----------------------------------------------------------

    var mount = $(config.extrasMount || "demoExtras");
    if (mount) buildToolbar(mount);

    function buildToolbar(container) {
      container.classList.add("dx-toolbar");

      var row = el("div", "dx-row");
      var shareBtn = el("button", "dx-btn", "⎘ Copy shareable run");
      shareBtn.type = "button";
      shareBtn.setAttribute("aria-label", "Copy a shareable link to this exact run");
      var whyBtn = el("button", "dx-btn", "Why? →");
      whyBtn.type = "button";
      whyBtn.setAttribute("aria-expanded", "false");
      var exportBtn = el("button", "dx-btn", "⬇ Download decision trace");
      exportBtn.type = "button";
      var mcpBtn = el("button", "dx-btn", "&gt;_ MCP terminal");
      mcpBtn.textContent = ">_ MCP terminal";
      mcpBtn.type = "button";
      mcpBtn.setAttribute("aria-expanded", "false");
      var status = el("span", "dx-status", "");
      status.setAttribute("role", "status");
      row.appendChild(shareBtn);
      row.appendChild(whyBtn);
      row.appendChild(exportBtn);
      row.appendChild(mcpBtn);
      row.appendChild(status);
      container.appendChild(row);

      var whyPanel = el("div", "dx-panel dx-why");
      whyPanel.hidden = true;
      whyPanel.setAttribute("aria-live", "polite");
      container.appendChild(whyPanel);

      var terminal = buildTerminal();
      terminal.root.hidden = true;
      container.appendChild(terminal.root);

      function flash(text) {
        status.textContent = text;
        setTimeout(function () {
          if (status.textContent === text) status.textContent = "";
        }, 4000);
      }

      shareBtn.addEventListener("click", function () {
        var url = shareUrl();
        var done = function () {
          beacon("share_copied", demo, getScenario());
          flash("link copied — same seed, same run, anywhere");
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(done, function () { flash(url); });
        } else {
          flash(url);
        }
      });

      whyBtn.addEventListener("click", function () {
        if (!whyPanel.hidden) {
          whyPanel.hidden = true;
          whyBtn.setAttribute("aria-expanded", "false");
          return;
        }
        whyPanel.hidden = false;
        whyBtn.setAttribute("aria-expanded", "true");
        whyPanel.textContent = "Narrating this trace…";
        fetch("/api/demo/" + demo + "/narrate?scenario=" +
              encodeURIComponent(getScenario()) + "&seed=" + getSeed())
          .then(function (r) { return r.json(); })
          .then(function (body) {
            whyPanel.textContent = "";
            whyPanel.appendChild(el("p", "dx-narration", body.narration ||
              body.error || "narration unavailable"));
            if (body.trace_id) {
              whyPanel.appendChild(el("div", "dx-trace-ref", "trace " + body.trace_id +
                " · deterministic template narration — no LLM, same seed = same words"));
            }
          })
          .catch(function () { whyPanel.textContent = "narrator unavailable"; });
      });

      exportBtn.addEventListener("click", function () {
        fetch("/api/demo/" + demo + "/export?scenario=" +
              encodeURIComponent(getScenario()) + "&seed=" + getSeed())
          .then(function (r) { return r.json(); })
          .then(function (body) {
            var trace = body.trace || {};
            var traceId = trace.trace_id || trace.nexus_trace_id || demo;
            var blob = new Blob([JSON.stringify(body, null, 2)],
              { type: "application/json" });
            var link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = "mizoki-trace-" + traceId + ".json";
            document.body.appendChild(link);
            link.click();
            link.remove();
            beacon("export_downloaded", demo, getScenario());
            flash("signed trace saved — sha256 digest inside");
          })
          .catch(function () { flash("export unavailable"); });
      });

      mcpBtn.addEventListener("click", function () {
        var open = terminal.root.hidden;
        terminal.root.hidden = !open;
        mcpBtn.setAttribute("aria-expanded", String(open));
        if (open) terminal.refresh();
      });
    }

    function buildTerminal() {
      var root = el("div", "dx-panel dx-terminal");
      root.appendChild(el("div", "dx-term-caption",
        "Everything you just clicked is a tool your agents can call."));
      var pre = el("pre", "dx-term-cmd");
      pre.tabIndex = 0;
      root.appendChild(pre);
      var row = el("div", "dx-row");
      var copyBtn = el("button", "dx-btn", "Copy curl");
      copyBtn.type = "button";
      var runBtn = el("button", "dx-btn dx-btn-accent", "▶ Run via MCP");
      runBtn.type = "button";
      row.appendChild(copyBtn);
      row.appendChild(runBtn);
      root.appendChild(row);
      var out = el("pre", "dx-term-out");
      out.hidden = true;
      out.setAttribute("aria-live", "polite");
      root.appendChild(out);

      function command() {
        var body = JSON.stringify({ name: config.mcpName, arguments: mcpArguments() });
        return "curl -s -X POST " + CANONICAL + "/api/mcp/call \\\n" +
          "  -H 'Content-Type: application/json' \\\n" +
          "  -d '" + body.replace(/'/g, "'\\''") + "'";
      }

      function refresh() { pre.textContent = command(); }

      copyBtn.addEventListener("click", function () {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(command());
          copyBtn.textContent = "Copied ✓";
          setTimeout(function () { copyBtn.textContent = "Copy curl"; }, 2500);
        }
      });

      runBtn.addEventListener("click", function () {
        out.hidden = false;
        out.textContent = "calling " + config.mcpName + " …";
        fetch("/api/mcp/call", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: config.mcpName, arguments: mcpArguments() })
        })
          .then(function (r) { return r.json(); })
          .then(function (envelope) {
            out.textContent = JSON.stringify(envelope, null, 2).slice(0, 12000);
          })
          .catch(function () { out.textContent = "MCP call failed"; });
      });

      return { root: root, refresh: refresh };
    }

    // ---- governance challenge drawer (§5.2) ------------------------------

    if (config.governance) buildGovernanceDrawer();

    function buildGovernanceDrawer() {
      var mountNode = $(config.governanceMount || "govDrawer");
      if (!mountNode) return;

      var toggle = el("button", "dx-btn dx-gov-toggle",
        "⚖ Governance Challenge — move the floors yourself");
      toggle.type = "button";
      toggle.setAttribute("aria-expanded", "false");
      mountNode.appendChild(toggle);

      var drawer = el("div", "dx-panel dx-gov");
      drawer.hidden = true;
      mountNode.appendChild(drawer);

      var sliders = {};
      var defaults = {
        uplift: { label: "Uplift floor", min: 0, max: 20, step: 0.5, value: 5, unit: "%" },
        confidence: { label: "Confidence floor", min: 0.5, max: 0.95, step: 0.01, value: 0.7, unit: "" },
        sample: { label: "Sample floor", min: 5, max: 50, step: 1, value: 15, unit: "" },
        budget: { label: "Budget swing cap", min: 5, max: 40, step: 1, value: 20, unit: "%" },
        bid: { label: "Bid swing cap", min: 5, max: 50, step: 1, value: 30, unit: "%" }
      };
      var results = el("div", "dx-gov-results");
      results.setAttribute("aria-live", "polite");
      var lesson = el("div", "dx-gov-lesson");
      lesson.hidden = true;
      var data = null;
      var baselineBlocked = {};

      Object.keys(defaults).forEach(function (key) {
        var spec = defaults[key];
        var wrap = el("label", "dx-gov-slider");
        var caption = el("span", "dx-gov-label",
          spec.label + ": " + spec.value + spec.unit);
        var input = document.createElement("input");
        input.type = "range";
        input.min = spec.min;
        input.max = spec.max;
        input.step = spec.step;
        input.value = spec.value;
        input.setAttribute("aria-label", spec.label);
        input.addEventListener("input", function () {
          caption.textContent = spec.label + ": " + input.value + spec.unit;
          evaluate();
        });
        wrap.appendChild(caption);
        wrap.appendChild(input);
        drawer.appendChild(wrap);
        sliders[key] = input;
      });
      drawer.appendChild(results);
      drawer.appendChild(lesson);

      toggle.addEventListener("click", function () {
        var open = drawer.hidden;
        drawer.hidden = !open;
        toggle.setAttribute("aria-expanded", String(open));
        if (open && !data) load();
        else if (open) evaluate();
      });

      function load() {
        results.textContent = "Fetching the run you just watched…";
        fetch(config.runEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario: getScenario(), seed: getSeed() })
        })
          .then(function (r) { return r.json(); })
          .then(function (run) {
            data = extract(run);
            baselineBlocked = {};
            evaluate(true);
          })
          .catch(function () { results.textContent = "run unavailable"; });
      }

      function extract(run) {
        var signals = [];
        var actions = [];
        (run.stages || []).forEach(function (stage) {
          if (stage.stage === "reason") {
            (stage.items || []).forEach(function (item) {
              if (item.signal) signals.push(item.signal);
            });
          }
          if (stage.stage === "plan") {
            (stage.items || []).forEach(function (item) { actions.push(item); });
          }
        });
        return { signals: signals, actions: actions };
      }

      function evaluate(isBaseline) {
        if (!data) return;
        var floors = {
          uplift: parseFloat(sliders.uplift.value) / 100,
          confidence: parseFloat(sliders.confidence.value),
          sample: parseInt(sliders.sample.value, 10),
          budget: parseFloat(sliders.budget.value),
          bid: parseFloat(sliders.bid.value)
        };
        results.textContent = "";
        var loosenedApproval = false;

        data.signals.forEach(function (signal) {
          var score = Math.max(0, signal.uplift) * signal.confidence *
            Math.log(1 + signal.sample_size);
          var pass = signal.uplift >= floors.uplift &&
            signal.confidence >= floors.confidence &&
            signal.sample_size >= floors.sample;
          results.appendChild(line(
            (pass ? "✓ " : "✕ ") + signal.entity_id +
            " · score " + (Math.round(score * 100) / 100) +
            " (uplift " + Math.round(signal.uplift * 100) + "%, conf " +
            signal.confidence + ", n=" + signal.sample_size + ")",
            pass
          ));
        });

        data.actions.forEach(function (action) {
          var magnitude = Math.abs(action.magnitude_pct || 0);
          var failures = [];
          var budgetAction = action.type === "budget_increase" ||
            action.type === "budget_decrease" || action.type === "capital_shift" ||
            action.type === "working_capital_draw";
          if (budgetAction && magnitude > floors.budget) failures.push("budget cap");
          if (action.type === "bid_adjust" && magnitude > floors.bid) failures.push("bid cap");
          if ((action.confidence || 0) < floors.confidence) failures.push("confidence floor");
          if ((action.supporting_conversions || 0) < floors.sample) failures.push("sample floor");
          if (action.headroom_after_pct != null && action.headroom_after_pct < 15) {
            failures.push("covenant_headroom (fixed 15%)");
          }
          var pass = failures.length === 0;
          if (isBaseline && !pass) baselineBlocked[action.action_id] = true;
          if (!isBaseline && pass && baselineBlocked[action.action_id]) {
            loosenedApproval = true;
          }
          results.appendChild(line(
            (pass ? "✓ " : "✕ ") + action.action_id + " · " + action.type +
            " " + (action.magnitude_pct > 0 ? "+" : "") + action.magnitude_pct +
            "% → " + action.entity_id +
            (pass ? "" : " — blocked by " + failures.join(", ")),
            pass
          ));
        });

        lesson.hidden = !loosenedApproval;
        if (loosenedApproval) {
          lesson.textContent =
            "You just approved a decision the governor would have blocked — " +
            "that's why the floor exists.";
        }
      }

      function line(text, pass) {
        return el("div", "dx-gov-line " + (pass ? "ok" : "bad"), text);
      }
    }

    // ---- shared-replay autorun (§5.1) ------------------------------------

    var body = document.body;
    var sharedScenario = body.getAttribute("data-scenario");
    var sharedSeed = body.getAttribute("data-seed");
    if (sharedSeed) {
      var seedField = $(config.seedInput || "seedInput");
      if (seedField) seedField.value = sharedSeed;
    }
    if (sharedScenario) {
      var kick = function () {
        if (config.autorun) {
          return config.autorun(sharedScenario, parseInt(sharedSeed || "42", 10)) !== false;
        }
        var select = $(config.scenarioSelect || "scenario");
        var start = $(config.startButton || "startBtn");
        if (select && start &&
            Array.prototype.some.call(select.options, function (option) {
              return option.value === sharedScenario;
            })) {
          select.value = sharedScenario;
          start.click();
          return true;
        }
        return false;
      };
      // The scenario picker may still be loading — retry briefly.
      var attempts = 0;
      var timer = setInterval(function () {
        attempts += 1;
        if (kick() || attempts > 20) clearInterval(timer);
      }, reduceMotion ? 100 : 250);
    }

    return { beacon: beacon, shareUrl: shareUrl };
  }

  window.MizokiDemoExtras = { init: init, beacon: beacon };
})();
