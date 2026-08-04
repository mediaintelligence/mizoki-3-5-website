"""Truth-discipline gate + link-preview contract (Phase 3, 2026-08-03).

Two guarantees, permanently in the suite:

1. scripts/content_qa.py both FIRES on seeded violations (a gate that cannot
   fail is not a gate) and passes CLEAN on the real scoped surfaces — banned
   strings, preview framing, number labeling, §-sequence.
2. Every page of the Signal capability site renders a correct link preview:
   non-empty <title> and meta description, og:title/og:description/og:image
   present, and the og:image asset actually resolves on this site.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app import app  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "content_qa", BASE_DIR / "scripts" / "content_qa.py"
)
content_qa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(content_qa)

SIGNAL_PAGES = (
    "/signal",
    "/signal/thresholds",
    "/signal/budget",
    "/signal/creative",
    "/signal/audiences",
    "/signal/measurement",
)


class ContentQAGateTestCase(unittest.TestCase):
    def test_gate_fires_on_every_seeded_violation_class(self) -> None:
        findings = content_qa.check_file("signal.html", content_qa.SEEDED_BAD)
        for marker in ("mind-reading", "guaranteed", "deployed-intent",
                       "preview-framing", "number-label", "sec-sequence"):
            self.assertTrue(
                any(marker in f for f in findings),
                f"gate failed to catch seeded violation class: {marker}",
            )

    def test_gate_stays_quiet_on_the_clean_seed(self) -> None:
        self.assertEqual([], content_qa.check_file("signal.html", content_qa.SEEDED_CLEAN))

    def test_scoped_surfaces_hold_the_truth_discipline(self) -> None:
        findings = content_qa.run_scan(BASE_DIR)
        self.assertEqual([], findings, "\n".join(findings))


class LinkPreviewTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def _meta(self, body: str, prop: str) -> str:
        m = re.search(
            r'<meta[^>]+(?:property|name)="' + re.escape(prop) + r'"[^>]+content="([^"]*)"',
            body,
        ) or re.search(
            r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="' + re.escape(prop) + r'"',
            body,
        )
        return m.group(1) if m else ""

    def test_every_signal_page_renders_a_complete_link_preview(self) -> None:
        for path in SIGNAL_PAGES:
            body = self.client.get(path).get_data(as_text=True)
            title = re.search(r"<title>([^<]+)</title>", body)
            self.assertTrue(title and title.group(1).strip(), f"{path}: empty <title>")
            self.assertTrue(self._meta(body, "description").strip(), f"{path}: empty description")
            self.assertTrue(self._meta(body, "og:title").strip(), f"{path}: missing og:title")
            self.assertTrue(self._meta(body, "og:description").strip(), f"{path}: missing og:description")
            og_image = self._meta(body, "og:image")
            self.assertTrue(og_image, f"{path}: missing og:image")
            asset = urlparse(og_image).path
            self.assertEqual(
                200, self.client.get(asset).status_code,
                f"{path}: og:image does not resolve on this site: {asset}",
            )

    def test_sitemap_carries_lastmod_for_the_rollout_pages(self) -> None:
        sitemap = self.client.get("/sitemap.xml").get_data(as_text=True)
        for path in SIGNAL_PAGES:
            entry = re.search(
                r"<loc>https://mizoki3\.com" + re.escape(path) + r"</loc>\s*<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>",
                sitemap,
            )
            self.assertIsNotNone(entry, f"{path}: sitemap entry lacks lastmod")


if __name__ == "__main__":
    unittest.main()
