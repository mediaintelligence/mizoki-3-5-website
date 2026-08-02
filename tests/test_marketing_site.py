"""Marketing parallel site (/marketing/*) — the master-prompt contracts.

The proposed media-buyer experience runs as a complete parallel site (landing
+ /marketing/simulator + /marketing/walkthrough) so the classic canon site and
the new direction can be compared live before anything is retired.

Locks in: the mandated hero copy, the vocabulary translation key (plain-English
terms everywhere; engineering terms appear exactly once, in the on-page
translation ledger), the 7-stage Decision Control System accordion, the
Interactive Scenario Simulator control surface (exact slider ranges and policy
values), the 90-second storyboard's five scenes, deterministic-engine rules
(no randomness), the /media-buying → /marketing redirect, and the site-wide
hygiene contracts (root-absolute assets, favicon trio, canonical/OG, claim
discipline, the parallel-preview compare strip).
"""

import re
import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE_FILE = REPO_ROOT / "marketing" / "index.html"
ENGINE_FILE = REPO_ROOT / "assets" / "js" / "media-sim.js"
CSS_FILE = REPO_ROOT / "assets" / "css" / "marketing.css"

MARKETING_PAGES = ("/marketing", "/marketing/simulator", "/marketing/walkthrough")


class _AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        self.app = create_app(runtime=runtime)
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def page(self, path: str = "/marketing") -> str:
        return self.client.get(path).get_data(as_text=True)


class RoutingTestCase(_AppTestCase):
    def test_all_marketing_pages_serve(self) -> None:
        for path in MARKETING_PAGES + ("/marketing/", "/marketing/simulator/",
                                       "/marketing/walkthrough/"):
            response = self.client.get(path, follow_redirects=True)
            self.assertEqual(200, response.status_code, path)

    def test_media_buying_redirects_permanently_into_the_site(self) -> None:
        for path in ("/media-buying", "/media-buying.html"):
            response = self.client.get(path)
            self.assertEqual(301, response.status_code, path)
            self.assertEqual("/marketing", response.headers["Location"], path)

    def test_sitemap_lists_the_site_not_the_redirect(self) -> None:
        body = self.client.get("/sitemap.xml").get_data(as_text=True)
        for path in MARKETING_PAGES:
            self.assertIn(f"https://mizoki3.com{path}</loc>", body, path)
        self.assertNotIn("/media-buying", body)

    def test_shared_assets_are_served(self) -> None:
        for asset in ("/assets/js/media-sim.js", "/assets/css/marketing.css"):
            self.assertEqual(200, self.client.get(asset).status_code, asset)


class ParallelPreviewTestCase(_AppTestCase):
    """The whole point: side-by-side comparison, nothing replaced."""

    def test_compare_strip_on_every_marketing_page(self) -> None:
        for path in MARKETING_PAGES:
            body = self.page(path)
            self.assertIn('class="compare-strip"', body, path)
            self.assertIn("nothing on the classic site is replaced", body, path)
            self.assertIn('<a href="/">View classic site →</a>', body, path)

    def test_marketing_nav_cross_links_all_pages(self) -> None:
        for path in MARKETING_PAGES:
            body = self.page(path)
            self.assertIn('href="/marketing/simulator"', body, path)
            self.assertIn('href="/marketing/walkthrough"', body, path)
            self.assertIn('href="/demo"', body, path)
            self.assertIn('class="brand">MIZOKI3</a>', body, path)

    def test_no_root_surface_is_modified(self) -> None:
        # The parallel site is additive: the canon-pinned homepage still
        # serves and never links into /marketing (comparison stays one-way).
        home = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("/marketing", home)


class HeroMandateTestCase(_AppTestCase):
    """Section 1 of the master prompt — copy is verbatim, not paraphrased."""

    def test_badge_headline_and_subheadline(self) -> None:
        body = self.page()
        self.assertIn("MIZ OKI 3.5 — Operating Knowledge Intelligence", body)
        self.assertIn("Stop Managing Dashboards. Start Governing Ad Growth.", body)
        self.assertIn(
            "The first autonomous AI control plane built for high-scale media "
            "buyers. MIZ OKI connects your ad platforms, web stack, analytics, "
            "and inventory to catch cross-stack signals, diagnose true CPA "
            "drivers, and execute margin-safe campaign actions automatically.",
            body,
        )

    def test_both_ctas_present_and_wired(self) -> None:
        body = self.page()
        self.assertIn("Launch Interactive Scenario Simulator", body)
        self.assertIn('href="#simulator"', body)
        self.assertIn("Watch 90-Sec Platform Walkthrough", body)
        self.assertIn('href="#video"', body)

    def test_social_proof_metrics_with_honesty_note(self) -> None:
        body = self.page()
        for marker in ("$100M+", "Ad Spend Analyzed", "Sub-100ms",
                       "Signal Latency", "100%", "Policy Compliance"):
            self.assertIn(marker, body, marker)
        # The strip is labeled for what it is — architecture facts and design
        # targets, never outcome promises (claims governance).
        self.assertIn("not outcome promises", body)

    def test_problem_vs_solution_matrix(self) -> None:
        body = self.page()
        self.assertIn("Symptom management", body)
        self.assertIn("Root-Cause Intelligence", body)


class VocabularyKeyTestCase(_AppTestCase):
    """The MANDATORY vocabulary translation key, enforced structurally."""

    TRANSLATIONS = {
        "Canonical Event Envelope": "Structured Signal Evidence",
        "Temporal-Causal Knowledge Base": "Cross-Stack Root Cause Engine",
        "Domain Intelligence Cell": "Channel Intelligence Modules",
        "SRPVDAL": "7-Stage Decision Control System",
        "Immutable Learning Ledger": "Compounding ROI Memory",
    }

    def test_translated_terms_are_the_working_vocabulary(self) -> None:
        body = self.page()
        for translated in self.TRANSLATIONS.values():
            self.assertGreaterEqual(
                body.count(translated), 1, f"missing translated term: {translated}"
            )
        # The flagship terms carry the page, not one-off mentions.
        self.assertGreaterEqual(body.count("Structured Signal Evidence"), 3)
        self.assertGreaterEqual(body.count("Compounding ROI Memory"), 3)

    def test_engineering_terms_confined_to_the_translation_ledger(self) -> None:
        body = self.page()
        for raw in self.TRANSLATIONS:
            self.assertEqual(
                1, body.count(raw),
                f"engineering term '{raw}' must appear exactly once — "
                "in the on-page translation ledger",
            )

    def test_sub_pages_carry_no_raw_jargon_at_all(self) -> None:
        for path in ("/marketing/simulator", "/marketing/walkthrough"):
            body = self.page(path)
            for raw in self.TRANSLATIONS:
                self.assertNotIn(raw, body, f"{raw} on {path}")

    def test_meta_tags_use_translated_vocabulary(self) -> None:
        body = self.page()
        head = body.split("</head>")[0]
        self.assertIn("Structured Signal Evidence", head)
        self.assertIn("Cross-Stack Root Cause Engine", head)
        for raw in ("Canonical Event Envelope", "SRPVDAL", "Immutable Learning Ledger"):
            self.assertNotIn(raw, head, f"raw jargon in meta tags: {raw}")


class ControlLoopTestCase(_AppTestCase):
    """The SRPVDAL interactive section — translated, all 7 stages."""

    STAGE_GISTS = (
        "24/7 Full-Stack Radar",
        "Root Cause AI",
        "Actionable Strategy",
        "Safety Brakes",
        "1-Click Approvals",
        "Hands-Free Execution",
        "Compounding ROI Memory",
    )

    def test_all_seven_stages_with_mandated_descriptors(self) -> None:
        body = self.page()
        for stage in ("Sense", "Reason", "Plan", "Validate", "Decide", "Act", "Learn"):
            self.assertIn(f'<span class="stage">{stage}</span>', body, stage)
        for gist in self.STAGE_GISTS:
            self.assertIn(gist, body, gist)
        self.assertIn("Google Ads, Meta, Shopify", body)
        self.assertIn("Slack or Teams", body)

    def test_accordion_is_interactive_markup(self) -> None:
        body = self.page()
        self.assertEqual(
            7, len(re.findall(r'class="mb-acc-head" aria-expanded=', body)),
            "every accordion button carries expansion state",
        )


class SimulatorContractTestCase(_AppTestCase):
    """The DemoWidget spec — on the landing AND the dedicated page."""

    SIM_PAGES = ("/marketing", "/marketing/simulator")

    def test_layout_columns_and_height_spec(self) -> None:
        css = CSS_FILE.read_text(encoding="utf-8")
        self.assertIn("height: 650px", css)
        for path in self.SIM_PAGES:
            body = self.page(path)
            self.assertIn("Interactive Controls", body, path)
            self.assertIn("Execution Monitor", body, path)
            self.assertIn('href="/assets/css/marketing.css', body, path)

    def test_three_scenarios(self) -> None:
        for path in self.SIM_PAGES:
            body = self.page(path)
            for scenario in ("Landing Page Latency Spike", "SKU Out-of-Stock",
                             "Pixel Attribution Drift"):
                self.assertIn(scenario, body, f"{scenario} on {path}")
            for value in ('value="latency"', 'value="stock"', 'value="pixel"'):
                self.assertIn(value, body, f"{value} on {path}")

    def test_slider_ranges_match_the_spec(self) -> None:
        for path in self.SIM_PAGES:
            body = self.page(path)
            self.assertIn('id="simLatency" min="0.5" max="6.0" step="0.1"', body, path)
            self.assertIn('id="simInventory" min="0" max="1000"', body, path)
            self.assertIn('id="simBudget" min="1000" max="20000"', body, path)

    def test_safety_policy_values(self) -> None:
        for path in self.SIM_PAGES:
            body = self.page(path)
            self.assertIn("2.2×", body, path)
            self.assertIn("$5,000", body, path)
            self.assertIn('id="simFloor"', body, path)
            self.assertIn('id="simCap"', body, path)

    def test_all_seven_phase_blocks_render(self) -> None:
        for path in self.SIM_PAGES:
            body = self.page(path)
            for phase in ("Sense", "Reason", "Plan", "Validate", "Decide", "Act", "Learn"):
                self.assertIn(f'id="ph{phase}"', body, f"{phase} on {path}")

    def test_simulator_is_honestly_labeled_with_noscript_fallback(self) -> None:
        for path in self.SIM_PAGES:
            body = self.page(path)
            self.assertIn("Illustrative scenario", body, path)
            self.assertIn("<noscript>", body, path)
            self.assertIn('href="/demo"', body, path)


class EngineDisciplineTestCase(unittest.TestCase):
    """The JS engine: deterministic, claims-clean, veto-honest."""

    def setUp(self) -> None:
        self.source = ENGINE_FILE.read_text(encoding="utf-8")
        literals = re.findall(r'"((?:[^"\\\n]|\\.)*)"', self.source)
        literals += re.findall(r"'((?:[^'\\\n]|\\.)*)'", self.source)
        self.strings = "\n".join(literals)

    def test_engine_exists_and_pages_load_it(self) -> None:
        self.assertTrue(ENGINE_FILE.is_file())
        for name in ("index.html", "simulator.html", "walkthrough.html"):
            page = (REPO_ROOT / "marketing" / name).read_text(encoding="utf-8")
            self.assertIn('src="/assets/js/media-sim.js', page, name)

    def test_deterministic_no_randomness_no_clock_ids(self) -> None:
        self.assertNotIn("Math.random", self.source)
        self.assertNotIn("Date.now", self.source)

    def test_policy_constants_match_the_page(self) -> None:
        self.assertIn("ROAS_FLOOR = 2.2", self.source)
        self.assertIn("MAX_SHIFT = 5000", self.source)

    def test_approve_gate_and_learn_tickers(self) -> None:
        self.assertIn("Approve Strategy", self.source)
        self.assertIn("Wasted Spend Prevented", self.source)
        self.assertIn("ROAS Preserved", self.source)

    def test_veto_is_a_first_class_outcome(self) -> None:
        self.assertIn("VETOED — nothing executed · human override required",
                      self.source)
        # A veto still teaches the system.
        self.assertIn("The veto is recorded too", self.source)

    def test_dispatch_is_marked_simulated(self) -> None:
        self.assertIn("(simulated)", self.strings + self.source)

    def test_banned_claims_vocabulary_absent(self) -> None:
        banned = [
            r"mind[\s-]?reading",
            r"we (?:are )?listen",
            r"will buy",
            r"guarantee",
            r"risk[\s-]?free",
            r"revolutionary",
            r"best[\s-]in[\s-]class",
            r"act now",
            r"limited[\s-]time",
            r"don'?t miss",
        ]
        surfaces = {"engine strings": self.strings}
        for name in ("index.html", "simulator.html", "walkthrough.html"):
            surfaces[name] = (REPO_ROOT / "marketing" / name).read_text(encoding="utf-8")
        for label, text in surfaces.items():
            for pattern in banned:
                self.assertIsNone(
                    re.search(pattern, text, re.IGNORECASE),
                    f"banned claims phrase in {label}: {pattern}",
                )


class StoryboardTestCase(_AppTestCase):
    """The 90-second walkthrough — on the landing AND the dedicated page."""

    VID_PAGES = ("/marketing", "/marketing/walkthrough")

    SCENES = (
        ("0:00", "The Media Buyer", "0"),
        ("0:15", "What Are Real Signals?", "15"),
        ("0:35", "Causal Reasoning in Action", "35"),
        ("0:55", "Governed Action", "55"),
        ("1:15", "Compounding Memory Ledger", "75"),
    )

    def test_five_scenes_with_timestamps_and_seek_targets(self) -> None:
        for path in self.VID_PAGES:
            body = self.page(path)
            for stamp, title, seek in self.SCENES:
                self.assertIn(stamp, body, f"{stamp} on {path}")
                self.assertIn(title, body, f"{title} on {path}")
                self.assertIn(f'data-t="{seek}"', body, f"{seek} on {path}")

    def test_transcript_drawer_present(self) -> None:
        for path in self.VID_PAGES:
            body = self.page(path)
            self.assertIn('id="vidTranscript"', body, path)
            self.assertIn('id="vidTransToggle"', body, path)
            self.assertEqual(5, body.count('class="vt-row"'), path)

    def test_player_chrome(self) -> None:
        for path in self.VID_PAGES:
            body = self.page(path)
            for el in ('id="vidPlay"', 'id="vidBar"', 'id="vidTime"', 'id="vidPlate"'):
                self.assertIn(el, body, f"{el} on {path}")


class HygieneTestCase(_AppTestCase):
    """Site-wide contracts every served surface must honor — all 3 pages."""

    def test_root_absolute_assets_only(self) -> None:
        for path in MARKETING_PAGES:
            body = self.page(path)
            self.assertIn('href="/assets/css/styles.css"', body, path)
            self.assertNotIn('href="assets/', body, path)
            self.assertNotIn('src="assets/', body, path)
            self.assertIsNone(re.search(r'href="[a-z][a-z0-9-]*\.html', body), path)

    def test_icon_set_canonical_and_og(self) -> None:
        canonical = {
            "/marketing": "https://mizoki3.com/marketing",
            "/marketing/simulator": "https://mizoki3.com/marketing/simulator",
            "/marketing/walkthrough": "https://mizoki3.com/marketing/walkthrough",
        }
        for path, url in canonical.items():
            body = self.page(path)
            self.assertIn('href="/assets/img/favicon.svg"', body, path)
            self.assertIn('href="/assets/img/favicon.ico"', body, path)
            self.assertIn('href="/assets/img/apple-touch-icon.png"', body, path)
            self.assertIn(f'<link rel="canonical" href="{url}" />', body, path)
            self.assertIn('property="og:title"', body, path)

    def test_nav_and_shared_scripts(self) -> None:
        for path in MARKETING_PAGES:
            body = self.page(path)
            self.assertIn('src="/assets/js/nav-mobile.js"', body, path)
            self.assertIn('class="nav-links"', body, path)

    def test_no_placeholder_links(self) -> None:
        for path in MARKETING_PAGES:
            self.assertNotIn('href="#"', self.page(path), path)

    def test_soft_sell_discipline_single_contact_cta(self) -> None:
        body = self.page()
        self.assertEqual(1, body.count("/contact?source=marketing"))
        self.assertIn("no pressure", body)
        self.assertIn('href="/demo"', body)
        self.assertIn('href="/executive-briefing/"', body)


if __name__ == "__main__":
    unittest.main()
