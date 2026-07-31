"""Executive Briefing integration coverage.

The module lives at executive-briefing/ and is served at the canonical
/executive-briefing/ path (trailing slash — its asset links are relative).
Confirmed decisions hand off to the site's real lead path (/contact) with
?source=executive-briefing, intent + domain as query params, and the fuller
payload in sessionStorage under one module-specific key.
"""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from mizoki_runtime import create_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]


class ExecutiveBriefingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=Path(self.temp_dir.name))
        app = create_app(runtime=runtime)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # ---- canonical route ------------------------------------------------

    def test_canonical_path_serves_module_shell(self) -> None:
        response = self.client.get("/executive-briefing/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.mimetype, "text/html")
        body = response.get_data(as_text=True)
        self.assertIn('id="mizoki-briefing"', body)
        self.assertIn("js/data.js", body)
        self.assertIn("js/app.js", body)

    def test_bare_path_redirects_to_canonical(self) -> None:
        # Relative css/ + js/ links break at the bare path, so it must never
        # serve the page directly — only redirect to the trailing-slash form.
        response = self.client.get("/executive-briefing")
        self.assertIn(response.status_code, (301, 308))
        self.assertTrue(response.headers["Location"].endswith("/executive-briefing/"))

    def test_assets_serve_with_correct_mime_types(self) -> None:
        css = self.client.get("/executive-briefing/css/briefing.css")
        self.assertEqual(css.status_code, 200)
        self.assertEqual(css.mimetype, "text/css")
        for path in ("/executive-briefing/js/data.js", "/executive-briefing/js/app.js"):
            js = self.client.get(path)
            self.assertEqual(js.status_code, 200, path)
            self.assertIn(js.mimetype, ("text/javascript", "application/javascript"), path)

    def test_asset_route_refuses_traversal_and_unknown_extensions(self) -> None:
        for path in (
            "/executive-briefing/..%2fapp.py",
            "/executive-briefing/js/..%2f..%2fapp.py",
            "/executive-briefing/nope.txt",
            "/executive-briefing/missing.css",
        ):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    # ---- decision handoff wiring ---------------------------------------

    def test_shell_config_routes_decisions_to_contact(self) -> None:
        body = self.client.get("/executive-briefing/").get_data(as_text=True)
        self.assertIn('contactUrl: "/contact"', body)
        self.assertIn("mizoki.executiveBriefing.decision", body)
        for intent in ("pilot", "board", "deep-dive"):
            self.assertIn(intent, body)

    def test_contact_page_carries_source_and_prefill_script(self) -> None:
        response = self.client.get("/contact?source=executive-briefing&intent=pilot")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        # Server-side sanitized source lands in the hidden field…
        self.assertIn('value="executive-briefing"', body)
        # …and the client-side prefill reads the module-specific storage key.
        self.assertIn("mizoki.executiveBriefing.decision", body)

    # ---- CTAs and two-track positioning --------------------------------

    def test_cta_pages_link_canonical_path(self) -> None:
        for path in ("/", "/pricing", "/demo", "/walkthrough", "/demo-opener.html"):
            body = self.client.get(path, follow_redirects=True).get_data(as_text=True)
            self.assertIn('href="/executive-briefing/"', body, path)

    def test_legacy_demo_pages_still_serve(self) -> None:
        for path in ("/demo", "/walkthrough", "/walkthrough.html", "/demo-opener.html"):
            self.assertEqual(
                self.client.get(path, follow_redirects=True).status_code, 200, path
            )

    def test_sitemap_lists_briefing(self) -> None:
        body = self.client.get("/sitemap.xml").get_data(as_text=True)
        self.assertIn("/executive-briefing/", body)


if __name__ == "__main__":
    unittest.main()
