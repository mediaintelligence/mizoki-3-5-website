/* Media Buying page engine — three pieces, one file:
 *   1. the 7-stage accordion (+ stage rail sync)
 *   2. the Interactive Scenario Simulator (deterministic model, replayable)
 *   3. the 90-second storyboard player (+ transcript seeking)
 *
 * The simulator is an ILLUSTRATIVE model of the decision loop: every number is
 * a pure function of the visible controls, so the same inputs always replay the
 * same run. No live account data, no network calls, no randomness — the replay
 * id is a hash of the inputs, not a timestamp. The live desks (/demo) are the
 * production runtime; this widget exists so a media buyer can feel the loop
 * react before opening them.
 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function $(id) { return document.getElementById(id); }
  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
  function money(n) {
    return "$" + Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ================= 1 · Accordion ================= */

  function initAccordion() {
    var acc = $("stageAcc");
    if (!acc) return;
    var items = Array.prototype.slice.call(acc.querySelectorAll(".mb-acc-item"));
    var pips = Array.prototype.slice.call(document.querySelectorAll("#stageRail .stage-pip"));

    function openStage(idx) {
      items.forEach(function (item, i) {
        var head = item.querySelector(".mb-acc-head");
        var on = i === idx;
        item.classList.toggle("open", on);
        head.setAttribute("aria-expanded", on ? "true" : "false");
      });
      pips.forEach(function (pip, i) { pip.classList.toggle("lit", i === idx); });
    }

    items.forEach(function (item, i) {
      item.querySelector(".mb-acc-head").addEventListener("click", function () {
        openStage(item.classList.contains("open") ? -1 : i);
      });
    });
    pips.forEach(function (pip, i) {
      pip.addEventListener("click", function () { openStage(i); });
    });
  }

  /* ================= 2 · Scenario Simulator ================= */

  // Model constants — shared arithmetic the terminal echoes verbatim, so the
  // narration can never disagree with the math.
  var ROAS_FLOOR = 2.2;      // × — safety toggle 1
  var MAX_SHIFT = 5000;      // $ — safety toggle 2
  var BASE_ROAS = 3.4;       // healthy blended ROAS in the illustrative account
  var CPA = 34;              // blended $ cost per conversion
  var SKU_SHARE = 0.18;      // share of conversions on the hero SKU
  var COVER_DAYS = 7;        // healthy days of inventory cover
  var PIXEL_DROP = 0.35;     // fraction of conversion fires lost in scenario 3
  var VERIFIED_ROAS = 3.1;   // server-side truth in scenario 3

  function readState() {
    var scen = document.querySelector('input[name="simScenario"]:checked');
    return {
      scenario: scen ? scen.value : "latency",
      latency: parseFloat($("simLatency").value),
      inventory: parseInt($("simInventory").value, 10),
      budget: parseInt($("simBudget").value, 10),
      floorOn: $("simFloor").checked,
      capOn: $("simCap").checked
    };
  }

  // Deterministic replay id — a tiny FNV-ish hash of the input tuple.
  function replayId(s) {
    var key = [s.scenario, s.latency.toFixed(1), s.inventory, s.budget,
               s.floorOn ? 1 : 0, s.capOn ? 1 : 0].join("|");
    var h = 2166136261;
    for (var i = 0; i < key.length; i++) {
      h ^= key.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    return "MB-" + ("000000" + h.toString(16)).slice(-6).toUpperCase();
  }

  function chain(nodes) {
    var out = '<span class="causal-chain">';
    nodes.forEach(function (n, i) {
      if (i) out += '<span class="causal-arrow">─▶</span>';
      out += '<span class="causal-node">' + esc(n) + "</span>";
    });
    return out + "</span>";
  }

  /* --- scenario models: pure functions of state → run description --- */

  function modelLatency(s) {
    var lcp = s.latency;
    var cvrLoss = clamp(0.07 * ((lcp - 1.0) / 0.5), 0, 0.85); // 7% CVR per +0.5s over 1.0s
    var effRoas = BASE_ROAS * (1 - cvrLoss);
    var wasted = s.budget * cvrLoss;
    var recovery = 0.4;   // reroute recovers 40% of the loss — the rest needs the infra fix,
                          // so past ~5.2s the floor vetoes continued spend (reachable on the slider)
    var projRoas = BASE_ROAS * (1 - cvrLoss * (1 - recovery));
    var rawShift = Math.round(s.budget * 0.35);
    var clamped = s.capOn && rawShift > MAX_SHIFT;
    var shift = clamped ? MAX_SHIFT : rawShift;
    var floorBreached = s.floorOn && projRoas < ROAS_FLOOR;

    return {
      sense: [
        "p75 LCP /landing/summer …… <b>" + lcp.toFixed(1) + "s</b>  (baseline 1.0s)",
        'deploy web-frontend@8c41f …… 14:02 UTC  <span class="dim">← latency step change</span>',
        "paid sessions in-flight …… " + money(s.budget) + "/day still serving to the slow page",
        "modeled CVR impact …… −" + Math.round(cvrLoss * 100) + "% (0.07 × (" + lcp.toFixed(1) + "−1.0)/0.5)"
      ],
      reasonChain: ["deploy 14:02", "LCP " + lcp.toFixed(1) + "s", "CVR −" + Math.round(cvrLoss * 100) + "%", "eff. ROAS " + effRoas.toFixed(2) + "×"],
      reasonLines: [
        "named cause: <b>site-speed regression</b>, not creative fatigue — creative CTR is flat while post-click conversion fell",
        "confidence " + (0.62 + clamp(cvrLoss, 0, 0.3)).toFixed(2) + " · evidence spans web stack + ads + analytics"
      ],
      actions: [
        { t: "Reroute paid traffic to the fast LP variant", d: "recovers ~" + Math.round(recovery * 100) + "% of the modeled CVR loss" },
        { t: "Shift " + money(shift) + "/day to unaffected campaigns", d: clamped ? "requested " + money(rawShift) + " — clamped at the " + money(MAX_SHIFT) + " auto-shift cap" : "inside the " + money(MAX_SHIFT) + " auto-shift cap" },
        { t: "Open infra ticket with the evidence chain attached", d: "deploy hash, latency series, CVR series" }
      ],
      checks: [
        { name: "budget caps", pass: true, detail: "shift " + money(shift) + " ≤ campaign caps" },
        { name: "brand rules", pass: true, detail: "no creative or placement changes proposed" },
        { name: "max auto-shift " + money(MAX_SHIFT), pass: !clamped ? true : "warn", detail: clamped ? "clamped " + money(rawShift) + " → " + money(MAX_SHIFT) : "within cap", enabled: s.capOn },
        { name: "ROAS floor " + ROAS_FLOOR.toFixed(1) + "×", pass: !floorBreached, detail: "projected " + projRoas.toFixed(2) + "× after reroute" + (s.floorOn ? "" : " (floor disabled)"), enabled: s.floorOn }
      ],
      veto: floorBreached,
      vetoWhy: "Projected ROAS " + projRoas.toFixed(2) + "× is below the " + ROAS_FLOOR.toFixed(1) + "× floor even after the reroute — at " + lcp.toFixed(1) + "s the page cannot pay for its own traffic.",
      vetoHold: "Hold: pause prospecting on the affected LP until the infra fix lands. Continuing spend requires a human override.",
      elevated: clamped,
      wasted: wasted,
      wastedLabel: "modeled spend loss stopped, per day",
      roas: projRoas,
      roasLabel: "projected ROAS after reroute",
      learnNote: "outcome + deploy-latency pattern recorded — next latency step change is diagnosed on sight"
    };
  }

  function modelStock(s) {
    var conv = s.budget / CPA;
    var heroConv = Math.max(1, Math.round(conv * SKU_SHARE));
    var cover = s.inventory / heroConv;
    var healthy = cover >= COVER_DAYS;
    var oos = s.inventory === 0;
    var urgency = clamp((COVER_DAYS - cover) / COVER_DAYS, 0, 1);
    var rawShift = Math.round(s.budget * SKU_SHARE * urgency);
    var clamped = s.capOn && rawShift > MAX_SHIFT;
    var shift = clamped ? MAX_SHIFT : rawShift;
    var wasted = s.budget * SKU_SHARE * urgency;
    var dilutedRoas = BASE_ROAS * (1 - 0.15 * urgency);

    return {
      sense: [
        "hero-SKU inventory …… <b>" + s.inventory + " units</b>",
        "modeled sell-through …… " + heroConv + " units/day at " + money(s.budget) + "/day (" + money(CPA) + " CPA · " + Math.round(SKU_SHARE * 100) + "% SKU share)",
        "days of cover …… <b>" + (oos ? "0.0" : cover.toFixed(1)) + " days</b>  (healthy ≥ " + COVER_DAYS + ")",
        "hero-SKU campaigns …… still spending " + money(s.budget * SKU_SHARE) + "/day"
      ],
      reasonChain: oos
        ? ["inventory 0", "ads still live", "spend buys nothing", "refund + CS load"]
        : ["cover " + cover.toFixed(1) + "d", "sell-through " + heroConv + "/day", "ads outpace stock", "stock-out in " + cover.toFixed(1) + "d"],
      reasonLines: [
        healthy
          ? "named state: <b>inventory is healthy</b> — demand and stock are in balance at this budget"
          : "named cause: <b>ad spend is outrunning inventory</b> — commerce data, not ad data, is the constraint",
        "confidence " + (healthy ? "0.93" : (0.72 + 0.2 * urgency).toFixed(2)) + " · evidence spans inventory + ads + pacing"
      ],
      actions: healthy ? [
        { t: "No change — hold current allocation", d: "cover " + cover.toFixed(1) + " days ≥ " + COVER_DAYS + "-day threshold; keep monitoring" }
      ] : oos ? [
        { t: "Pause hero-SKU campaigns now", d: "spend on an unavailable product converts to refunds and support load" },
        { t: "Shift " + money(shift) + "/day to in-stock SKUs", d: clamped ? "requested " + money(rawShift) + " — clamped at the " + money(MAX_SHIFT) + " cap" : "inside the " + money(MAX_SHIFT) + " cap" },
        { t: "Arm auto-relaunch on restock signal", d: "campaigns resume when inventory crosses the cover threshold" }
      ] : [
        { t: "Taper hero-SKU budgets −" + Math.round(urgency * 100) + "%", d: "sized to " + cover.toFixed(1) + " days of cover vs the " + COVER_DAYS + "-day floor" },
        { t: "Shift " + money(shift) + "/day to in-stock SKUs", d: clamped ? "requested " + money(rawShift) + " — clamped at the " + money(MAX_SHIFT) + " cap" : "inside the " + money(MAX_SHIFT) + " cap" },
        { t: "Notify inventory owner with the pacing math", d: "restock before cover hits zero keeps the campaigns live" }
      ],
      checks: [
        { name: "budget caps", pass: true, detail: healthy ? "no movement proposed" : "reallocation stays inside account budget" },
        { name: "brand rules", pass: true, detail: "no creative changes proposed" },
        { name: "max auto-shift " + money(MAX_SHIFT), pass: !clamped ? true : "warn", detail: clamped ? "clamped " + money(rawShift) + " → " + money(MAX_SHIFT) : "shift " + money(shift) + " within cap", enabled: s.capOn },
        { name: "ROAS floor " + ROAS_FLOOR.toFixed(1) + "×", pass: true, detail: "projected blended " + BASE_ROAS.toFixed(1) + "× (spend follows stock)" + (s.floorOn ? "" : " (floor disabled)"), enabled: s.floorOn }
      ],
      veto: false,
      elevated: clamped,
      holdRun: healthy,
      wasted: wasted,
      wastedLabel: "spend redirected from dead inventory, per day",
      roas: healthy ? BASE_ROAS : dilutedRoas + (BASE_ROAS - dilutedRoas) * 0.9,
      roasLabel: healthy ? "blended ROAS held" : "blended ROAS protected vs " + dilutedRoas.toFixed(2) + "× drift",
      learnNote: "sell-through vs cover pattern recorded — restock cadence feeds the next pacing plan"
    };
  }

  function modelPixel(s) {
    var reported = VERIFIED_ROAS * (1 - PIXEL_DROP);
    var naiveCut = 0.4;
    var prevented = s.budget * naiveCut;
    var belowFloor = reported < ROAS_FLOOR;

    return {
      sense: [
        "pixel conversion fires …… <b>−" + Math.round(PIXEL_DROP * 100) + "%</b> day-over-day",
        "order stream (commerce) …… flat (−1%, within noise)",
        "platform-reported ROAS …… <b>" + reported.toFixed(2) + "×</b>" + (belowFloor && s.floorOn ? "  ← under the " + ROAS_FLOOR.toFixed(1) + "× floor" : ""),
        "server-side verified ROAS …… <b>" + VERIFIED_ROAS.toFixed(2) + "×</b>  (orders ÷ spend)"
      ],
      reasonChain: ["pixel fires −" + Math.round(PIXEL_DROP * 100) + "%", "orders flat", "divergence 34pts", "measurement break, not demand"],
      reasonLines: [
        "named cause: <b>client-side attribution drift</b> — the pixel broke, demand did not",
        "the dangerous path: an automation trusting the pixel would cut " + Math.round(naiveCut * 100) + "% of spend against a healthy account"
      ],
      actions: [
        { t: "Quarantine the drifted pixel metric", d: "flagged evidence-invalid; excluded from bidding and floors" },
        { t: "Switch bidding to server-side events", d: "decisions run on the verified order stream" },
        { t: "Hold budgets steady — shift $0", d: "the correct move is refusing the panic cut" },
        { t: "Alert the analytics owner", d: "divergence series + the browser-update timeline attached" }
      ],
      checks: [
        { name: "budget caps", pass: true, detail: "no spend movement proposed" },
        { name: "brand rules", pass: true, detail: "no creative changes proposed" },
        { name: "max auto-shift " + money(MAX_SHIFT), pass: true, detail: "shift $0 — trivially within cap", enabled: s.capOn },
        { name: "ROAS floor " + ROAS_FLOOR.toFixed(1) + "×", pass: true, detail: s.floorOn ? "evaluated on VERIFIED " + VERIFIED_ROAS.toFixed(2) + "× — the quarantined " + reported.toFixed(2) + "× is not evidence" : "floor disabled — same plan on the evidence", enabled: s.floorOn }
      ],
      veto: false,
      elevated: false,
      wasted: prevented,
      wastedLabel: "panic budget cuts refused, per day",
      roas: VERIFIED_ROAS,
      roasLabel: "verified ROAS defended",
      learnNote: "pixel-vs-orders divergence signature recorded — the next drift is quarantined before any bid moves"
    };
  }

  var MODELS = { latency: modelLatency, stock: modelStock, pixel: modelPixel };

  /* --- rendering --- */

  var PHASES = ["Sense", "Reason", "Plan", "Validate", "Decide", "Act", "Learn"];
  var runEpoch = 0;
  var timers = [];

  function later(fn, ms) {
    if (reduceMotion) { fn(); return; }
    timers.push(window.setTimeout(fn, ms));
  }
  function clearTimers() {
    timers.forEach(function (t) { window.clearTimeout(t); });
    timers = [];
  }

  function phase(name) { return $("ph" + name); }
  function body(name) { return $("body" + name); }
  function setPhase(name, state, stat) {
    var el = phase(name);
    el.classList.remove("live", "done", "veto");
    if (state) el.classList.add(state);
    el.querySelector(".pstat").textContent = stat || "—";
  }

  function renderRun(s) {
    runEpoch += 1;
    var epoch = runEpoch;
    clearTimers();

    var run = MODELS[s.scenario](s);
    var rid = replayId(s);
    $("simReplayId").textContent = "replay " + rid;
    $("simDot").classList.toggle("hold", !!run.veto);
    $("simStatus").textContent = run.veto
      ? "Execution Monitor · guardrail hold"
      : "Execution Monitor · armed · recalculating live";

    // Phases 1–5 render immediately (the "recalculates as sliders move" spec);
    // a short stagger lights them up when motion is allowed.
    body("Sense").innerHTML = run.sense.map(function (l) { return '<span class="ln">' + l + "</span>"; }).join("");
    body("Reason").innerHTML = chain(run.reasonChain) +
      run.reasonLines.map(function (l) { return '<span class="ln">' + l + "</span>"; }).join("");
    body("Plan").innerHTML = run.actions.map(function (a, i) {
      return '<span class="ln"><b>' + (i + 1) + " · " + esc(a.t) + "</b></span>" +
             '<span class="ln"><span class="dim">    ' + esc(a.d) + "</span></span>";
    }).join("");
    body("Validate").innerHTML = run.checks.map(function (c) {
      var mark = c.pass === true ? '<span class="ok">✓</span>'
               : c.pass === "warn" ? '<span class="warn">◆</span>'
               : '<span class="bad">✕</span>';
      var name = c.enabled === false ? c.name + " (off)" : c.name;
      return '<span class="ln">' + mark + " " + esc(name) + ' — <span class="dim">' + esc(c.detail) + "</span></span>";
    }).join("");

    var decideHtml;
    if (run.veto) {
      decideHtml =
        '<div class="veto-plate"><b>VETOED — nothing executed · human override required</b><br />' +
        esc(run.vetoWhy) + "<br />" + esc(run.vetoHold) + "</div>" +
        '<span class="ln"><span class="dim">The veto is not an opinion — it is arithmetic against the policy you set on the left.</span></span>';
    } else if (run.holdRun) {
      decideHtml =
        '<span class="ln"><span class="ok">✓</span> Decision: <b>hold — no action required</b></span>' +
        '<span class="ln"><span class="dim">Doing nothing is a governed decision too; it is recorded like any other.</span></span>' +
        '<button class="sim-approve" id="simApprove">Log the hold</button>';
    } else {
      decideHtml =
        '<span class="ln">risk tier: <b>' + (run.elevated ? "elevated — routed for approval (Slack / Teams in production)" : "low — inside Level-2 autonomy grants; auto-approvable") + "</b></span>" +
        '<span class="ln"><span class="dim">In this simulator you hold the pen either way — commit the strategy to see dispatch.</span></span>' +
        '<button class="sim-approve" id="simApprove">▶ Approve Strategy</button>';
    }
    body("Decide").innerHTML = decideHtml;

    body("Act").innerHTML = "";
    body("Learn").innerHTML = "";

    // Wire the outcome synchronously — a click must never land on a dead
    // button, and a veto's lesson must be readable the moment it renders.
    // The stagger below is chrome only.
    if (run.veto) {
      renderLearn(run, s, rid, true);
    } else {
      var btn = $("simApprove");
      if (btn) {
        var epochAtRender = epoch;
        btn.addEventListener("click", function () { approve(run, s, rid, epochAtRender); });
      }
    }

    // Stagger the phase states.
    PHASES.forEach(function (name) { setPhase(name, null, "—"); });
    var stagger = reduceMotion ? 0 : 160;
    ["Sense", "Reason", "Plan", "Validate"].forEach(function (name, i) {
      later(function () {
        if (epoch !== runEpoch) return;
        setPhase(name, "done", "✓ " + (name === "Validate" && run.veto ? "checks ran" : "complete"));
      }, stagger * (i + 1));
    });
    later(function () {
      if (epoch !== runEpoch) return;
      if (run.veto) {
        setPhase("Validate", "veto", "✕ floor breached");
        setPhase("Decide", "veto", "VETOED");
        setPhase("Act", null, "no dispatch");
        setPhase("Learn", "done", "recorded");
      } else {
        setPhase("Decide", "live", "awaiting you");
      }
    }, stagger * 5);
  }

  function approve(run, s, rid, epoch) {
    if (epoch !== runEpoch) return;
    var btn = $("simApprove");
    if (btn) { btn.disabled = true; btn.textContent = run.holdRun ? "Hold logged" : "Strategy approved"; }
    setPhase("Decide", "done", "✓ committed");
    setPhase("Act", "live", "dispatching…");

    var lines = run.holdRun ? [
      'decision log …… <span class="ok">200</span> hold recorded — no platform calls issued'
    ] : [
      'POST googleads: customers/&hellip;/campaignBudgets:mutate …… <span class="ok">200 OK</span> <span class="dim">(simulated)</span>',
      'POST graph.facebook: /act_&hellip;/adsets budget+status …… <span class="ok">200 OK</span> <span class="dim">(simulated)</span>',
      'POST slack: #media-desk decision card + evidence chain …… <span class="ok">200 OK</span> <span class="dim">(simulated)</span>',
      'dispatch ledger …… every call bound to decision ' + rid
    ];

    var actBody = body("Act");
    var step = reduceMotion ? 0 : 260;
    lines.forEach(function (l, i) {
      later(function () {
        if (epoch !== runEpoch) return;
        actBody.innerHTML += '<span class="ln">' + l + "</span>";
      }, step * (i + 1));
    });
    later(function () {
      if (epoch !== runEpoch) return;
      setPhase("Act", "done", "✓ dispatched");
      renderLearn(run, s, rid, false);
      later(function () {
        if (epoch !== runEpoch) return;
        setPhase("Learn", "done", "recorded");
      }, reduceMotion ? 0 : 500);
    }, step * (lines.length + 1));
  }

  function renderLearn(run, s, rid, isVeto) {
    var learnBody = body("Learn");
    learnBody.innerHTML =
      '<div class="tick-grid">' +
      '<div class="tick-cell"><div class="tv" id="tickWasted">$0</div><span class="tk">Wasted Spend Prevented · ' + esc(run.wastedLabel) + "</span></div>" +
      '<div class="tick-cell roas"><div class="tv" id="tickRoas">0.00×</div><span class="tk">ROAS Preserved · ' + esc(run.roasLabel) + "</span></div>" +
      "</div>" +
      '<span class="ln"><span class="dim">' +
      (isVeto ? "The veto is recorded too — the desk remembers why it held. " : "") +
      esc(run.learnNote) + " · Compounding ROI Memory · replay " + rid + "</span></span>";

    // Count-up ticker (eased, deterministic endpoints).
    var wastedEl = $("tickWasted");
    var roasEl = $("tickRoas");
    var target = Math.max(0, run.wasted);
    var roasTarget = run.roas;
    if (reduceMotion) {
      wastedEl.textContent = money(target);
      roasEl.textContent = roasTarget.toFixed(2) + "×";
      return;
    }
    var t0 = null;
    var DUR = 900;
    function tick(ts) {
      if (t0 === null) t0 = ts;
      var p = clamp((ts - t0) / DUR, 0, 1);
      var e = 1 - Math.pow(1 - p, 3);
      wastedEl.textContent = money(target * e);
      roasEl.textContent = (roasTarget * e).toFixed(2) + "×";
      if (p < 1) window.requestAnimationFrame(tick);
    }
    window.requestAnimationFrame(tick);
  }

  /* --- controls wiring --- */

  function initSimulator() {
    if (!$("simTerminal")) return;

    var scenLabels = Array.prototype.slice.call(
      document.querySelectorAll("#simScenarios .sim-scen label"));

    function refreshControlChrome(s) {
      scenLabels.forEach(function (label) {
        var input = label.querySelector("input");
        label.classList.toggle("on", input.checked);
      });
      $("tgFloor").classList.toggle("on", s.floorOn);
      $("tgCap").classList.toggle("on", s.capOn);
      // Dim the sliders a scenario doesn't read — still draggable, honestly labeled.
      $("slLatency").classList.toggle("dim", s.scenario !== "latency");
      $("slInventory").classList.toggle("dim", s.scenario !== "stock");
      $("simLatencyVal").textContent = s.latency.toFixed(1) + "s";
      $("simInventoryVal").textContent = s.inventory.toLocaleString("en-US") + " units";
      $("simBudgetVal").textContent = money(s.budget);
    }

    function onChange() {
      var s = readState();
      refreshControlChrome(s);
      renderRun(s);
    }

    ["simLatency", "simInventory", "simBudget"].forEach(function (id) {
      $(id).addEventListener("input", onChange);
    });
    ["simFloor", "simCap"].forEach(function (id) {
      $(id).addEventListener("change", onChange);
    });
    Array.prototype.slice.call(
      document.querySelectorAll('input[name="simScenario"]')
    ).forEach(function (radio) {
      radio.addEventListener("change", onChange);
    });

    onChange(); // first paint — the monitor is never empty
  }

  /* ================= 3 · Storyboard player ================= */

  var SCENES = [
    {
      t: 0, end: 15, title: "The Media Buyer's Dilemma",
      copy: "It's 7 a.m. and CPA is up forty percent. Was it creative fatigue? A slow landing page? A tracking break? Your dashboards show you twelve symptoms — and no cause. So you guess, and the spend keeps burning while you do."
    },
    {
      t: 15, end: 35, title: "What Are Real Signals?",
      copy: "MIZ OKI reads your stack differently. Every ad click, page load, inventory count, and margin figure arrives as Structured Signal Evidence — one format, full provenance, cross-checked against its source system. Not more data. Better evidence."
    },
    {
      t: 35, end: 55, title: "Causal Reasoning in Action",
      copy: "The Cross-Stack Root Cause Engine correlates across the systems your tools treat as silos: the 2 p.m. deploy slowed your landing page, conversion fell, CPA rose. A named cause with a confidence figure attached — in minutes, not at Monday's retro."
    },
    {
      t: 55, end: 75, title: "Governed Action & 1-Click Approvals",
      copy: "Then it acts — inside your rules. Budget caps, brand rules, and margin floors are checked before anything moves. Low-risk fixes execute hands-free; bigger calls route to Slack for one-click approval. And when a move fails the safety check, it is vetoed. Nothing executes."
    },
    {
      t: 75, end: 90, title: "Compounding Memory Ledger",
      copy: "Every outcome is recorded to Compounding ROI Memory — permanently. The next decision starts smarter than the last one finished. That's not another dashboard. That's a control plane for ad growth."
    }
  ];
  var VID_LEN = 90;

  function fmtTime(sec) {
    var m = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return m + ":" + (s < 10 ? "0" : "") + s;
  }

  function initVideo() {
    var plate = $("vidPlate");
    if (!plate) return;

    var playBtn = $("vidPlay");
    var bar = $("vidBar");
    var timeEl = $("vidTime");
    var kicker = $("vidSceneKicker");
    var title = $("vidSceneTitle");
    var copy = $("vidSceneCopy");
    var chips = Array.prototype.slice.call(document.querySelectorAll("#vidChips .vid-chip"));

    var pos = 0;
    var playing = false;
    var timer = null;
    var TICK = 250;

    function sceneAt(sec) {
      for (var i = SCENES.length - 1; i >= 0; i--) {
        if (sec >= SCENES[i].t) return i;
      }
      return 0;
    }

    function paint() {
      var i = sceneAt(pos);
      var sc = SCENES[i];
      kicker.textContent = "Scene " + (i + 1) + " of " + SCENES.length + " · " + fmtTime(sc.t);
      if (title.textContent !== sc.title) {
        title.textContent = sc.title;
        copy.textContent = sc.copy;
      }
      bar.style.width = ((pos / VID_LEN) * 100).toFixed(2) + "%";
      timeEl.textContent = fmtTime(pos) + " / " + fmtTime(VID_LEN);
      chips.forEach(function (chip, ci) { chip.classList.toggle("lit", ci === i); });
    }

    function stop() {
      playing = false;
      playBtn.textContent = "▶ PLAY";
      if (timer) { window.clearInterval(timer); timer = null; }
    }

    function play() {
      if (pos >= VID_LEN) pos = 0;
      playing = true;
      playBtn.textContent = "❚❚ PAUSE";
      var step = reduceMotion ? 5 : TICK / 1000;
      var interval = reduceMotion ? 1000 : TICK;
      timer = window.setInterval(function () {
        pos = Math.min(VID_LEN, pos + step);
        paint();
        if (pos >= VID_LEN) { stop(); playBtn.textContent = "↻ REPLAY"; }
      }, interval);
    }

    playBtn.addEventListener("click", function () { playing ? stop() : play(); });

    function seek(sec) {
      pos = clamp(sec, 0, VID_LEN);
      paint();
      if (!playing) { play(); }
    }
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () { seek(parseInt(chip.getAttribute("data-t"), 10)); });
    });
    Array.prototype.slice.call(
      document.querySelectorAll("#vidTranscript .vt-row > button")
    ).forEach(function (btn) {
      btn.addEventListener("click", function () {
        seek(parseInt(btn.getAttribute("data-t"), 10));
        plate.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
      });
    });

    var transToggle = $("vidTransToggle");
    var transcript = $("vidTranscript");
    transToggle.addEventListener("click", function () {
      var open = transcript.classList.toggle("open");
      transToggle.setAttribute("aria-expanded", open ? "true" : "false");
      transToggle.textContent = open ? "Full transcript ▴" : "Full transcript ▾";
    });

    // Hero CTA "Watch 90-Sec Platform Walkthrough" lands on #video — begin at
    // scene 1 paused; autoplaying on scroll would be presumptuous.
    paint();
  }

  /* ================= boot ================= */

  function boot() {
    initAccordion();
    initSimulator();
    initVideo();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
