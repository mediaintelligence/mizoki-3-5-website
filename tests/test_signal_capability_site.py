"""Contract tests for the Signal capability site (2026-08-02).

/signal is the hub of a multi-page media-buying surface. Each capability
page must: serve on both its clean URL and .html path, stay self-contained
(inline styles, root-absolute links), keep §-marks strictly sequential,
and hold the truth discipline — operating defaults framed as defaults,
intent content preview-framed, no banned claim vocabulary.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app import app  # noqa: E402

CAPABILITY_SLUGS = ("thresholds", "budget", "creative", "audiences", "measurement")


class _AppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.config["TESTING"] = True
        cls.client = app.test_client()


class CapabilityRoutesTestCase(_AppTestCase):
    def test_clean_and_html_routes_serve_the_same_page(self) -> None:
        for slug in CAPABILITY_SLUGS:
            clean = self.client.get(f"/signal/{slug}")
            html = self.client.get(f"/signal-{slug}.html")
            self.assertEqual(200, clean.status_code, slug)
            self.assertEqual(200, html.status_code, slug)
            self.assertEqual(clean.get_data(), html.get_data(), slug)

    def test_pages_are_self_contained_with_root_absolute_links(self) -> None:
        for slug in CAPABILITY_SLUGS:
            body = self.client.get(f"/signal/{slug}").get_data(as_text=True)
            self.assertIn("<style>", body, slug)
            self.assertNotIn('rel="stylesheet"', body, slug)
            for href in re.findall(r'href="([^"]+)"', body):
                if href.startswith(("http", "mailto:", "#")):
                    continue
                self.assertTrue(href.startswith("/"), f"{slug}: non-root link {href}")

    def test_sitemap_lists_the_capability_pages(self) -> None:
        sitemap = self.client.get("/sitemap.xml").get_data(as_text=True)
        for slug in CAPABILITY_SLUGS:
            self.assertIn(f"https://mizoki3.com/signal/{slug}", sitemap, slug)

    def test_hub_links_every_capability_page(self) -> None:
        hub = self.client.get("/signal").get_data(as_text=True)
        self.assertIn('id="capabilities"', hub)
        for slug in CAPABILITY_SLUGS:
            self.assertIn(f'href="/signal/{slug}"', hub, slug)


class SectionMarkSequenceTestCase(_AppTestCase):
    def test_sec_marks_strictly_sequential_on_every_signal_page(self) -> None:
        for path in ["/signal"] + [f"/signal/{s}" for s in CAPABILITY_SLUGS]:
            body = self.client.get(path).get_data(as_text=True)
            nums = [int(n) for n in re.findall(r'class="mark sec-mark">§(\d+)', body)]
            self.assertEqual(list(range(1, len(nums) + 1)), nums, path)
            self.assertGreaterEqual(len(nums), 3, path)


class TruthDisciplineTestCase(_AppTestCase):
    BARE_MIND_READING = re.compile(r"(?<!not )(?<!never )(?<!no )mind.reading", re.I)

    def test_banned_vocabulary_absent(self) -> None:
        for path in ["/signal"] + [f"/signal/{s}" for s in CAPABILITY_SLUGS]:
            body = self.client.get(path).get_data(as_text=True)
            self.assertNotIn("guaranteed", body.lower(), path)
            self.assertIsNone(self.BARE_MIND_READING.search(body), path)

    def test_intent_content_carries_preview_framing(self) -> None:
        # Intent/ORACLE appears on the hub (§06) and the audiences page (§04):
        # both must carry the preview tag and the in-development statement.
        for path in ("/signal", "/signal/audiences"):
            body = self.client.get(path).get_data(as_text=True)
            self.assertIn("Preview · in development", body, path)
            self.assertIn("in development", body, path)
        audiences = self.client.get("/signal/audiences").get_data(as_text=True)
        self.assertIn("no microphone or audio signals", audiences)

    def test_operating_defaults_framed_as_defaults_not_outcomes(self) -> None:
        for slug in CAPABILITY_SLUGS:
            body = self.client.get(f"/signal/{slug}").get_data(as_text=True)
            self.assertIn("operating default", body, slug)

    def test_hub_ledger_stays_illustrative(self) -> None:
        hub = self.client.get("/signal").get_data(as_text=True)
        self.assertIn("Illustrative", hub)
        self.assertIn('aria-label="Illustrative split', hub)


if __name__ == "__main__":
    unittest.main()
