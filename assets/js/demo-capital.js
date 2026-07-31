/* Capital Desk demo — thin page entry that boots the shared pipeline
 * player (demo-pipeline.js) against /api/demo/capital.
 *
 * Keeps the prompt-required filename assets/js/demo-capital.js while
 * reusing the Signal-pattern SSE + POST-replay implementation.
 * Requires /assets/js/demo-pipeline.js to load first.
 */
(function () {
  "use strict";

  function boot() {
    if (!window.MizokiPipelineDemo || typeof window.MizokiPipelineDemo.init !== "function") {
      return;
    }
    window.MizokiPipelineDemo.init({
      demo: "capital",
      api: "/api/demo/capital",
      defaultScenario: "growth_reallocation",
      accent: "#D9A83C"
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
