"""Boss Docent — voice-guided demo tour: wiring + claims discipline.

The docent is a salesman with a compliance officer: every sentence it can
speak lives in assets/js/boss-docent.js, so this suite lints the copy the
same way the site's claim-discipline policy governs written pages.
"""
from __future__ import annotations

import pathlib
import re
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCENT_JS = REPO_ROOT / "assets" / "js" / "boss-docent.js"

from app import create_app  # noqa: E402
from mizoki_runtime import create_runtime  # noqa: E402


class _AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        runtime = create_runtime(base_dir=REPO_ROOT, data_dir=pathlib.Path(self.temp_dir.name))
        self.app = create_app(runtime=runtime)
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()


class DocentWiringTestCase(_AppTestCase):
    def test_docent_asset_exists_and_is_served(self) -> None:
        self.assertTrue(DOCENT_JS.is_file())
        response = self.client.get("/assets/js/boss-docent.js")
        self.assertEqual(200, response.status_code)

    def test_signal_demo_loads_the_docent(self) -> None:
        body = self.client.get("/demo/signal").get_data(as_text=True)
        self.assertIn('src="/assets/js/boss-docent.js"', body)
        self.assertIn("MizokiBossDocent.init()", body)


class DocentClaimsDisciplineTestCase(unittest.TestCase):
    """The narration may only ever say what the written canon may say."""

    def setUp(self) -> None:
        self.source = DOCENT_JS.read_text(encoding="utf-8")
        # Lint what the docent can SAY: every JS string literal. Comments may
        # name a banned phrase in order to ban it; speakable copy may not.
        literals = re.findall(r'"((?:[^"\\\n]|\\.)*)"', self.source)
        literals += re.findall(r"'((?:[^'\\\n]|\\.)*)'", self.source)
        self.speakable = "\n".join(literals)

    def test_banned_claims_vocabulary_absent(self) -> None:
        banned = [
            r"mind[\s-]?reading",
            r"we (?:are )?listen",       # "we listen" / "we are listening"
            r"will buy",
            r"guarantee",                 # guaranteed / guarantees
            r"risk[\s-]?free",
            r"revolutionary",
            r"best[\s-]in[\s-]class",
            r"act now",
            r"limited[\s-]time",
            r"don'?t miss",
        ]
        for pattern in banned:
            self.assertIsNone(
                re.search(pattern, self.speakable, re.IGNORECASE),
                f"banned claims phrase matched in speakable copy: {pattern}",
            )

    def test_required_disclosures_present(self) -> None:
        for required in (
            "I speak — I never listen",          # output-only voice bright line
            "No microphone",
            "Illustrative scenario",             # figures honestly labeled
            "deterministic and seeded",          # replayability claim
        ):
            self.assertIn(required, self.source, required)

    def test_soft_sell_exactly_one_cta_destination(self) -> None:
        # Not pushy: the pilot CTA appears exactly once (the closing chip).
        self.assertEqual(1, self.source.count("/contact?source=demo-signal-docent"))
        # And the spoken close carries the no-pressure framing.
        self.assertIn("No pressure", self.source)

    def test_no_silent_unlock_utterance(self) -> None:
        """2026-07-31 regression (voice dead on desktop AND mobile): a silent
        'unlock' utterance was queued on the launch tap and cancelled one frame
        later by beginTour. A cancel() landing on a just-queued utterance
        wedges Chrome's synthesis engine and silences everything after it.
        The first REAL sentence is already inside the gesture, so no separate
        unlock may ever be reintroduced."""
        self.assertNotIn("unlock:", self.source)
        self.assertNotIn("u.volume = 0", self.source)
        self.assertNotIn('SpeechSynthesisUtterance(" ")', self.source)

    def test_utterances_are_audible_and_well_formed(self) -> None:
        self.assertIn('u.lang = "en-US"', self.source)      # engines pick a voice by lang
        self.assertIn("u.volume = 1.0", self.source)         # never silent
        self.assertIn("pickVoice", self.source)              # resolved fresh, never stale
        self.assertIn("onProblem", self.source)              # honest failure surfacing
        self.assertIn("voice unavailable — captions", self.source)

    def test_mobile_launcher_and_speech_robustness(self) -> None:
        """2026-07-31 regressions: the phone launcher sat below the fold and
        mobile speech engines cut narration off."""
        # Fixed launcher on phones — otherwise the voice is never discovered.
        self.assertIn("@media (max-width:900px)", self.source)
        self.assertIn(".bd-launch{position:fixed", self.source)
        # The fixed bar must reserve its own space, never cover the controls.
        self.assertIn("html.bd-open body{padding-bottom", self.source)
        # Chrome/Android needs a resume beat or long narration dies silently.
        # (iOS is unlocked by the first REAL sentence running inside the tap —
        # see test_no_silent_unlock_utterance for why a separate unlock is
        # forbidden.)
        self.assertIn("startHeartbeat", self.source)
        self.assertIn("speechSynthesis.resume()", self.source)

    def test_no_audio_capture_apis(self) -> None:
        # Output-only, structurally: no speech recognition, no microphone APIs.
        for forbidden in ("SpeechRecognition", "webkitSpeechRecognition", "getUserMedia", "MediaRecorder"):
            self.assertNotIn(forbidden, self.source, forbidden)


if __name__ == "__main__":
    unittest.main()
