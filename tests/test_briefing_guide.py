"""Decision Concierge (Executive Briefing guide agent) — behavior + claims lint."""
from __future__ import annotations

import pathlib
import re
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDE_JS = REPO_ROOT / "executive-briefing" / "js" / "guide.js"

from app import create_app  # noqa: E402
from mizoki_runtime import briefing_guide, create_runtime  # noqa: E402


class _AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = pathlib.Path(self.temp_dir.name)
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=self.data_dir)
        self.app = create_app(runtime=runtime)
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()


class GuideWiringTestCase(_AppTestCase):
    def test_briefing_page_loads_the_guide(self) -> None:
        body = self.client.get("/executive-briefing/").get_data(as_text=True)
        self.assertIn('src="js/guide.js"', body)

    def test_guide_asset_served(self) -> None:
        self.assertTrue(GUIDE_JS.is_file())
        response = self.client.get("/executive-briefing/js/guide.js")
        self.assertEqual(200, response.status_code)

    def test_guide_tools_registered_under_boss(self) -> None:
        body = self.client.get("/api/mcp/tools").get_data(as_text=True)
        self.assertIn("guide.answer", body)
        self.assertIn("guide.memory_summary", body)


class GuideEndpointsTestCase(_AppTestCase):
    def test_event_roundtrip_and_summary(self) -> None:
        for event, payload in (
            ("guide_opened", {"mode": "guided"}),
            ("stage_changed", {"stage": "exposure"}),
            ("suggestion_accepted", {"suggestion": "x"}),
            ("decision_confirmed", {"intent": "pilot"}),
        ):
            response = self.client.post(
                "/api/briefing/guide/event",
                json={"session": "gs_test", "event": event, "stage": "exposure",
                      "domain": "signal", "role": "cfo", "payload": payload},
            )
            self.assertEqual(200, response.status_code, event)
        summary = self.client.get("/api/briefing/guide/summary").get_json()
        self.assertEqual(1, summary["sessions"])
        self.assertEqual(4, summary["events_total"])
        self.assertEqual(1.0, summary["suggestion_acceptance"])
        self.assertIn("decision_confirmed:pilot", summary["decision_intents"])

    def test_unknown_event_rejected(self) -> None:
        response = self.client.post(
            "/api/briefing/guide/event",
            json={"session": "gs_test", "event": "rm_rf_everything"},
        )
        self.assertEqual(400, response.status_code)

    def test_ask_matches_bi_objection_and_logs_it(self) -> None:
        response = self.client.post(
            "/api/briefing/guide/ask",
            json={"session": "gs_test", "question": "We already have BI dashboards in Looker — why this?",
                  "stage": "exposure", "domain": "signal", "role": "cfo"},
        )
        self.assertEqual(200, response.status_code)
        answer = response.get_json()
        self.assertEqual("objection", answer["kind"])
        self.assertEqual("existing_bi", answer["topic"])
        self.assertIn("Keep your BI", answer["answer"])
        summary = self.client.get("/api/briefing/guide/summary").get_json()
        self.assertEqual({"existing_bi": 1}, summary["objections_ranked"])

    def test_security_answer_makes_no_certification_claims(self) -> None:
        answer = self.client.post(
            "/api/briefing/guide/ask",
            json={"session": "gs_test", "question": "How do you handle security and compliance?"},
        ).get_json()
        self.assertEqual("security", answer["topic"])
        for banned in ("SOC", "ISO 27001", "certified", "guarantee"):
            self.assertNotIn(banned.lower(), answer["answer"].lower(), banned)

    def test_unknown_question_gets_honest_fallback(self) -> None:
        answer = self.client.post(
            "/api/briefing/guide/ask",
            json={"session": "gs_test", "question": "zzz qqq xxyzzy?"},
        ).get_json()
        self.assertEqual("unknown", answer["kind"])
        self.assertIn("human follow-up", answer["answer"])


class GuideBankTestCase(unittest.TestCase):
    def test_every_cached_objection_resolves(self) -> None:
        probes = {
            "integration_risk": "how hard is the integration with our systems",
            "existing_bi": "we already have dashboards and a reporting team",
            "security": "is our data secure, what about privacy",
            "not_now": "maybe next quarter, timing is bad",
            "budget_owner": "who is the budget sponsor for procurement",
            "pricing": "how much does the subscription cost",
        }
        for expected, question in probes.items():
            kind, topic, _entry = briefing_guide.classify_question(question)
            self.assertEqual(("objection", expected), (kind, topic), question)

    def test_record_event_rejects_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                briefing_guide.record_event(pathlib.Path(tmp) / "g.jsonl", "s", "bogus_event")


class GuideClaimsDisciplineTestCase(unittest.TestCase):
    """The concierge may only say what written canon may say — both layers."""

    def setUp(self) -> None:
        js = GUIDE_JS.read_text(encoding="utf-8")
        literals = re.findall(r'"((?:[^"\\\n]|\\.)*)"', js)
        literals += re.findall(r"'((?:[^'\\\n]|\\.)*)'", js)
        py_answers = [f["answer"] for f in briefing_guide.PRODUCT_FACTS]
        py_answers += [o["answer"] for o in briefing_guide.OBJECTIONS]
        py_answers.append(briefing_guide.UNKNOWN_ANSWER)
        self.speakable = "\n".join(literals + py_answers)

    def test_banned_vocabulary_absent(self) -> None:
        banned = [
            r"guarantee", r"soc\s?2", r"iso\s?27001", r"will buy", r"act now",
            r"limited[\s-]?time", r"risk[\s-]?free", r"revolutionary",
            r"best[\s-]in[\s-]class", r"don'?t miss", r"mind[\s-]?reading",
            r"\$\s?\d",  # the concierge never invents dollar figures
        ]
        for pattern in banned:
            self.assertIsNone(
                re.search(pattern, self.speakable, re.IGNORECASE),
                f"banned phrase in concierge copy: {pattern}",
            )

    def test_required_stance_present(self) -> None:
        self.assertIn("I'll suggest; you commit", self.speakable)
        self.assertIn("how fast you start", self.speakable)

    def test_guide_never_clicks_briefing_controls(self) -> None:
        # Suggest + highlight only: the executive commits every action.
        source = GUIDE_JS.read_text(encoding="utf-8")
        self.assertNotIn(".click(", source)


if __name__ == "__main__":
    unittest.main()
