"""MIZ OKI Media (/media) — route, asset, copy, and isolation contract.

The /media surface is an additive, fully isolated product page (2026-08-03):
one self-contained HTML document in media/ plus local video/poster/storyboard
assets, wired by exactly two routes in app.py. These tests pin that contract:

1. ROUTES — /media and /media/ both serve the page directly (200, no
   redirect hop), and the asset route streams the film as real video/mp4
   with Range support so it can never fall through to an HTML handler.
2. COPY — the approved positioning is present verbatim: product name,
   category descriptor, hero, Decision Graph chain, the knowledge-graph
   distinction, the SRPVDAL order, and the 90-day pilot framing.
3. CLAIMS DISCIPLINE — the page passes the house truth-discipline checker
   (scripts/content_qa.py check_file) even though it is not in that gate's
   CI scope: no affirmative "guaranteed"/"mind-reading", and every visible
   %/× number shares its section with an illustrative-style label.
4. ISOLATION — no existing surface links into /media, the page pulls no
   shared stylesheet and no external origin, and the classic routes
   (/  /marketing  /signal  /demo) still serve unchanged.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app import create_app  # noqa: E402
from mizoki_runtime import create_runtime  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "content_qa", BASE_DIR / "scripts" / "content_qa.py"
)
content_qa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(content_qa)

MEDIA_HTML = BASE_DIR / "media" / "index.html"
MEDIA_MP4 = BASE_DIR / "media" / "video" / "mizoki-signal-explainer.mp4"
MEDIA_POSTER = BASE_DIR / "media" / "assets" / "mizoki-signal-preview.png"
MEDIA_STORYBOARD = BASE_DIR / "media" / "assets" / "mizoki-signal-storyboard.png"


class MediaPageTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=BASE_DIR, data_dir=Path(cls.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        cls.client = app.test_client()
        cls.page = cls.client.get("/media").get_data(as_text=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    # ------------------------------------------------------------ routes --

    def test_media_serves_directly_with_and_without_trailing_slash(self) -> None:
        for path in ("/media", "/media/"):
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)
            self.assertEqual("text/html", response.mimetype, path)
            self.assertIn("MIZ OKI Media", response.get_data(as_text=True), path)
            response.close()

    def test_video_asset_served_as_mp4(self) -> None:
        response = self.client.get("/media/video/mizoki-signal-explainer.mp4")
        self.assertEqual(200, response.status_code)
        self.assertEqual("video/mp4", response.mimetype)
        body = response.get_data()
        self.assertGreater(len(body), 10_000)
        # A real MP4 container, not an HTML page that fell through a fallback.
        self.assertIn(b"ftyp", body[:32])
        self.assertNotIn(b"<!DOCTYPE", body[:200])
        response.close()

    def test_video_asset_supports_byte_range_requests(self) -> None:
        response = self.client.get(
            "/media/video/mizoki-signal-explainer.mp4",
            headers={"Range": "bytes=0-99"},
        )
        self.assertEqual(206, response.status_code)
        self.assertEqual(100, len(response.get_data()))
        self.assertTrue(response.headers.get("Content-Range", "").startswith("bytes 0-99/"))
        response.close()

    def test_image_assets_served_as_png(self) -> None:
        for path in (
            "/media/assets/mizoki-signal-preview.png",
            "/media/assets/mizoki-signal-storyboard.png",
        ):
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)
            self.assertEqual("image/png", response.mimetype, path)
            self.assertEqual(b"\x89PNG", response.get_data()[:4], path)
            response.close()

    def test_asset_route_refuses_traversal_and_unknown_files(self) -> None:
        for path in (
            "/media/%2e%2e/app.py",
            "/media/video/%2e%2e/%2e%2e/app.py",
            "/media/no-such-file.png",
            "/media/video/",
        ):
            response = self.client.get(path)
            self.assertEqual(404, response.status_code, path)
            response.close()

    def test_media_assets_exist_on_disk(self) -> None:
        for asset in (MEDIA_HTML, MEDIA_MP4, MEDIA_POSTER, MEDIA_STORYBOARD):
            self.assertTrue(asset.is_file(), asset.name)
            self.assertGreater(asset.stat().st_size, 0, asset.name)

    # -------------------------------------------------------------- copy --

    def test_approved_positioning_is_verbatim(self) -> None:
        for phrase in (
            "MIZ OKI Media",
            "Causal Growth Control · powered by the MIZ OKI Decision Graph",
            "Know why performance moved. Put the next dollar where it creates profit.",
            "MIZ OKI Media connects media, commerce, customer experience, inventory, "
            "product economics, and policy into one governed decision pathway.",
            "A conventional knowledge graph explains what is connected.",
            "A 90-Day Causal Growth Control Pilot",
            "Begin observe-only. Advance to human-approved actions only after "
            "evidence quality, economics, and policy boundaries are validated.",
            "focused commercial application powered by the broader MIZ OKI "
            "Operating Knowledge Intelligence platform",
            "Explore the 90-Day Pilot",
            "Watch the Explainer",
        ):
            self.assertIn(phrase, self.page, phrase)

    def test_decision_graph_chain_in_order(self) -> None:
        # The hero chain strip carries the seven stages as consecutive items.
        chain = re.search(
            r'<li class="c1">Signal</li><li class="c2">Entity</li>'
            r'<li class="c3">Cause</li><li class="c4">Objective</li>'
            r'<li class="c5">Policy</li><li class="c6">Action</li>'
            r'<li class="c7">Outcome</li>',
            self.page,
        )
        self.assertIsNotNone(chain, "hero Decision Graph chain missing or reordered")

    def test_srpvdal_order_is_exact_and_complete(self) -> None:
        self.assertIn(
            "SENSE → REASON → PLAN → VALIDATE → DECIDE → ACT → LEARN", self.page
        )
        # Each stage carries its own described step, in order.
        order = ["1 · SENSE", "2 · REASON", "3 · PLAN", "4 · VALIDATE",
                 "5 · DECIDE", "6 · ACT", "7 · LEARN"]
        idx = [self.page.find(step) for step in order]
        self.assertNotIn(-1, idx, "a SRPVDAL stage row is missing")
        self.assertEqual(idx, sorted(idx), "SRPVDAL stage rows out of order")

    def test_memory_layers_and_maturity_labels_present(self) -> None:
        for phrase in ("Evidence memory", "Operating context", "Decision memory",
                       "Outcome memory", "Pilot-ready", "Illustrative", "Roadmap",
                       "Illustrative scenario"):
            self.assertIn(phrase, self.page, phrase)

    def test_pilot_phases_present(self) -> None:
        for phrase in ("Days 1–30", "Days 31–60", "Days 61–90",
                       "Connect and observe", "Diagnose and recommend",
                       "Approve, act, and learn"):
            self.assertIn(phrase, self.page, phrase)

    def test_final_cta_uses_mailto_lead_path(self) -> None:
        # The in-repo contact form posts to a placeholder endpoint, so the
        # approved destination is the pilot mailto: link.
        self.assertIn(
            'href="mailto:contact@mizoki3.com?subject=MIZ%20OKI%20Media%20Pilot"',
            self.page,
        )
        self.assertIn("Discuss a MIZ OKI Media Pilot", self.page)

    # ------------------------------------------------------ video markup --

    def test_video_element_contract(self) -> None:
        video = re.search(r"<video\b[^>]*>", self.page)
        self.assertIsNotNone(video, "no <video> element")
        tag = video.group(0)
        self.assertIn("controls", tag)
        self.assertIn("playsinline", tag)
        self.assertIn('preload="metadata"', tag)
        self.assertIn('poster="/media/assets/mizoki-signal-preview.png"', tag)
        self.assertNotIn("autoplay", tag)
        self.assertIn(
            '<source src="/media/video/mizoki-signal-explainer.mp4?v=', self.page
        )
        self.assertIn('type="video/mp4"', self.page)

    # ------------------------------------------------- claims discipline --

    def test_page_passes_house_truth_discipline_checks(self) -> None:
        # Reuse the truth-discipline gate directly (the page is deliberately
        # outside that gate's CI scope, but must still satisfy its rules:
        # no affirmative guaranteed/mind-reading claims, and every visible
        # %/× number shares its section with an illustrative-style label).
        findings = content_qa.check_file("media/index.html", MEDIA_HTML.read_text(encoding="utf-8"))
        self.assertEqual([], findings)

    def test_no_absolute_performance_promises(self) -> None:
        text = re.sub(r"<[^>]+>", " ", self.page).lower()
        for banned in ("100% policy", "guaranteed roi", "guaranteed savings",
                       "fully autonomous execution", "soc 2 certified",
                       "hipaa certified", "patented"):
            self.assertNotIn(banned, text, banned)

    # ------------------------------------------------- metadata & a11y ---

    def test_page_metadata(self) -> None:
        self.assertIn("<title>MIZ OKI Media | Causal Growth Control</title>", self.page)
        self.assertIn('<link rel="canonical" href="https://mizoki3.com/media">', self.page)
        self.assertIn('property="og:title" content="MIZ OKI Media — Causal Growth Control"', self.page)
        self.assertIn('property="og:image" content="https://mizoki3.com/media/assets/mizoki-signal-preview.png"', self.page)
        self.assertIn('name="twitter:card" content="summary_large_image"', self.page)
        # Favicon set matches the existing site's canonical assets, unchanged.
        self.assertIn('href="/assets/img/favicon.svg"', self.page)
        self.assertIn('href="/assets/img/favicon.ico"', self.page)
        self.assertIn('href="/assets/img/apple-touch-icon.png"', self.page)

    def test_accessibility_basics(self) -> None:
        self.assertEqual(1, len(re.findall(r"<h1\b", self.page)), "exactly one h1")
        self.assertIn('lang="en"', self.page)
        self.assertIn("Skip to content", self.page)
        self.assertIn("prefers-reduced-motion", self.page)
        storyboard_img = re.search(r'<img[^>]*mizoki-signal-storyboard[^>]*>', self.page)
        self.assertIsNotNone(storyboard_img)
        self.assertIn('alt="Storyboard of the MIZ OKI Media explainer film', storyboard_img.group(0))
        self.assertIn('width="1600"', storyboard_img.group(0))
        self.assertIn('loading="lazy"', storyboard_img.group(0))

    # ---------------------------------------------------------- isolation --

    def test_page_is_self_contained(self) -> None:
        # No shared stylesheet, no external stylesheet/font/script origins.
        self.assertNotIn('rel="stylesheet"', self.page)
        self.assertNotIn("/assets/css/", self.page)
        self.assertNotIn("fonts.googleapis.com", self.page)
        self.assertNotIn("fonts.gstatic.com", self.page)
        self.assertNotIn('<script src=', self.page)
        # Every subresource the page loads is site-local (the only absolute
        # URLs are its own canonical/OG metadata and the footer home link).
        for attr, url in re.findall(r'(src|poster|href)="(https?://[^"]+)"', self.page):
            self.assertTrue(
                url.startswith("https://mizoki3.com"),
                f"external origin in {attr}: {url}",
            )

    def test_existing_surfaces_do_not_link_into_media(self) -> None:
        # Comparison stays one-way: /media links out, nothing links in.
        for path in ("/", "/marketing", "/signal", "/demo"):
            response = self.client.get(path)
            body = response.get_data(as_text=True)
            response.close()
            self.assertNotIn('href="/media"', body, path)
            self.assertNotIn('href="/media/', body, path)

    def test_existing_surfaces_still_serve(self) -> None:
        for path in ("/", "/marketing", "/signal", "/demo", "/pricing"):
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)
            response.close()
        # The unrelated legacy redirect beside the new routes is untouched.
        response = self.client.get("/media-buying")
        self.assertEqual(301, response.status_code)
        self.assertTrue(response.headers["Location"].endswith("/marketing"))
        response.close()


if __name__ == "__main__":
    unittest.main()
