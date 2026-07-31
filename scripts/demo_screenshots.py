#!/usr/bin/env python3
"""Visual QA gate for the demo surface (dev-only; §7 of the v4 build doc).

Boots the Flask app on a test port, then uses the environment's Playwright
(with its bundled Chromium — do NOT add playwright to requirements.txt) to
capture:

- /demo (hub)
- all six demo pages, mid-run (click Start, await the finale/decision card)
- Boardroom mode on /demo/nexus
- /walkthrough.html

at 390 / 768 / 1440 px widths, into scripts/screenshots/.

Review every image before committing; attach the 1440 px set to the PR.
D1 shipped because this step didn't exist — it is now a merge gate.

Usage:
    python3 scripts/demo_screenshots.py [--out scripts/screenshots]
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

PORT = int(os.environ.get("MIZOKI_SCREENSHOT_PORT", "8765"))
BASE_URL = f"http://127.0.0.1:{PORT}"
WIDTHS = (390, 768, 1440)

# (slug, path, ready_selector, start_selector, finale_selector)
PAGES = [
    ("hub", "/demo", ".demo-cards", None, None),
    ("signal", "/demo/signal", "#startBtn", "#startBtn", "#decisionCard.on"),
    ("counsel", "/demo/counsel", "#scenarioGrid .scn-card", "#scenarioGrid .scn-card", "#synthPanel.on"),
    ("estate", "/demo/estate", "#startBtn", "#startBtn", "#finaleCard.on"),
    ("capital", "/demo/capital", "#startBtn", "#startBtn", "#decisionCard.on"),
    ("risk", "/demo/risk", "#startBtn", "#startBtn", "#finaleCard.on"),
    ("nexus", "/demo/nexus", "#startBtn", "#startBtn", "#provenancePanel.on"),
    ("walkthrough", "/walkthrough.html", "h1", None, None),
]


def boot_app() -> None:
    from app import create_app

    app = create_app()
    # Keep runs snappy for screenshots: SSE unpaced (finales appear fast).
    app.config.update(TESTING=True)

    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    import urllib.request

    for _ in range(60):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1):
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("app did not boot on the test port")


def capture(out_dir: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    shots: list[Path] = []
    executable = os.environ.get("MIZOKI_CHROMIUM_PATH")

    with sync_playwright() as p:
        launch_kwargs = {}
        if executable:
            launch_kwargs["executable_path"] = executable
        browser = p.chromium.launch(**launch_kwargs)
        for width in WIDTHS:
            context = browser.new_context(
                viewport={"width": width, "height": 900},
                reduced_motion="reduce",
            )
            page = context.new_page()
            for slug, path, ready, start, finale in PAGES:
                page.goto(BASE_URL + path, wait_until="networkidle")
                page.wait_for_selector(ready, timeout=15000)
                if start:
                    page.wait_for_timeout(500)
                    page.click(start)
                    if finale:
                        page.wait_for_selector(finale, timeout=60000)
                        page.wait_for_timeout(600)
                target = out_dir / f"{slug}-{width}.png"
                page.screenshot(path=str(target), full_page=True)
                shots.append(target)
                print(f"  captured {target}")
                # Boardroom mode — nexus only, once per width.
                if slug == "nexus":
                    page.click("#boardroomBtn")
                    page.wait_for_selector(".nxb-stage .nxb-title", timeout=20000)
                    page.wait_for_timeout(1200)
                    target = out_dir / f"nexus-boardroom-{width}.png"
                    page.screenshot(path=str(target))
                    shots.append(target)
                    print(f"  captured {target}")
                    page.keyboard.press("Escape")
            context.close()
        browser.close()
    return shots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(BASE_DIR / "scripts" / "screenshots"))
    args = parser.parse_args()

    print(f"booting app on {BASE_URL} …")
    boot_app()
    print("capturing screenshots …")
    shots = capture(Path(args.out))
    print(f"\n{len(shots)} screenshots in {args.out} — review every image "
          "(overflow, clipped widgets, unstyled states, projector type) before commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
