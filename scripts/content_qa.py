#!/usr/bin/env python3
"""Truth-discipline content gate for the Signal rollout surfaces.

Runs in CI (deploy-homepage.yml, beside the design-canon guard) and in the
site test suite (tests/test_content_qa.py). Fails the build when any scoped
file violates the rollout's truth discipline:

  A. BANNED STRINGS — "mind-reading" and "guaranteed" as affirmative claims
     (negated uses such as "not mind-reading" / "never a guaranteed outcome"
     are the discipline itself and stay legal), plus any present-tense claim
     that intent prediction / ORACLE — or net-yield pricing/bidding — is
     deployed for customers. Claim-ledger bans (signal-net-yield rollout,
     per docs/marketing/mizoki-shopify-net-yield-positioning.md §2):
     "Quokka Swarm" anywhere; Airbnb's published KL-divergence figures
     (4.95 → 0.66 / 0.04) in a section that does not attribute them to
     Airbnb; 15-minute-cycle / sub-second claims in a section without a
     "design target" label.
  B. PREVIEW FRAMING — every section that mentions ORACLE / anticipatory or
     latent intent — or net yield / net contribution — must carry the
     "Preview · in development" framing string in that same section.
  C. NUMBER LABELING — every percentage or multiplier visible in a section
     must share that section with an honesty label: "illustrative" or
     "composite" for scenario numbers, "operating default" / "operating
     parameter" for real module parameters. Numbers inside <style>/<script>
     blocks and tag attributes are not customer-visible and are ignored.
  D. SECTION SEQUENCE — pages using the §-mark filing grammar must number
     their sec-marks strictly 1..N with no gaps or duplicates.

Scope is the explicit file list below (the surfaces this rollout created or
touched), not the whole site: pre-existing pages keep their own history.

Usage:
  python3 scripts/content_qa.py               # scan; exit 0 clean / 1 findings
  python3 scripts/content_qa.py --self-test   # prove the gate fires on seeded
                                              # violations and stays quiet on a
                                              # clean sample; exit 0 iff both
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[1]

# The rollout's surfaces. Paths are relative to the site root.
SCOPE_FILES = [
    "signal.html",
    "signal-thresholds.html",
    "signal-budget.html",
    "signal-creative.html",
    "signal-audiences.html",
    "signal-measurement.html",
    "demo.html",
    "demo-signal.html",
    "blog/doorman-problem.html",
    "executive-briefing/js/data.js",
    "shopify.html",
    # Customer-facing draft copy is scoped even before it is published anywhere.
    "docs/marketing/shopify-app-listing-copy.md",
    # docs/marketing/signal-story-bank.md is deliberately NOT scoped: it is the
    # rulebook these checks implement, so it must quote banned phrases to define
    # them ("no present-tense deployment claims until ORACLE is live") and is
    # not a served customer surface. The served surfaces it governs are all in
    # scope above.
]

# Pages that use the §-mark filing grammar (check D).
SEC_MARK_PAGES = [
    "signal.html",
    "signal-thresholds.html",
    "signal-budget.html",
    "signal-creative.html",
    "signal-audiences.html",
    "signal-measurement.html",
    "shopify.html",
]

# --- check A: banned strings -------------------------------------------------

# "mind-reading" is only legal when explicitly negated ("not mind-reading").
MIND_READING = re.compile(r"(?<!not )(?<!never )(?<!no )mind[\s-]?reading", re.I)
# "guaranteed" is only legal when explicitly negated ("never a guaranteed
# outcome" is story-bank rule 5 verbatim).
GUARANTEED = re.compile(r"(?<!never a )(?<!not )(?<!no )(?<!nothing )guaranteed", re.I)
# Present-tense claims that intent prediction is customer-deployed. The intent
# platform runs in shadow, gated, labeled "built, pre-benchmark" — marketing
# copy may not promote it to a live product.
DEPLOYED_INTENT = [
    re.compile(r"intent (?:\w+ ){0,2}is (?:live|deployed|running|in production|shipping)", re.I),
    re.compile(r"ORACLE is (?:live|deployed|running|in production|shipping)", re.I),
    re.compile(r"(?:now|already) predict(?:s|ing) (?:\w+ )?intent", re.I),
    re.compile(r"intent (?:prediction|inference|scoring) (?:is )?(?:deployed|live|in production)", re.I),
]

# Present-tense claims that net-yield pricing/bidding/writeback is customer-
# deployed. The capability is scaffolded behind NET_YIELD_WRITEBACK=false and
# stays "Preview · in development" until a real pilot writes verified numbers.
DEPLOYED_NET_YIELD = [
    re.compile(r"net[\s-]?(?:yield|contribution)(?: \w+){0,2} is "
               r"(?:live|deployed|running|in production|shipping)", re.I),
    re.compile(r"(?:now|already) bid(?:s|ding)? on net[\s-]?contribution", re.I),
]

# Claim-ledger bans (positioning doc §2). "Quokka Swarm" is an unvalidated
# novelty term — banned outright on customer surfaces. The KL-divergence trio
# is Airbnb's published research: legal only in a section that names Airbnb.
# 15-minute cycles / sub-second latency are design targets, never observed
# performance — the section must say "design target".
QUOKKA = re.compile(r"quokka\s+swarm", re.I)
AIRBNB_KL_HEADLINE = re.compile(r"\b4\.95\b")
KL_CONTEXT = re.compile(r"KL[\s-]?divergence", re.I)
KL_SECONDARY = re.compile(r"\b0\.66\b|\b0\.04\b")
AIRBNB_ATTRIBUTION = re.compile(r"airbnb", re.I)
OBSERVED_PERF = re.compile(r"15[\s-]?minute|sub[\s-]?second", re.I)
DESIGN_TARGET_LABEL = re.compile(r"design\s+target", re.I)

# --- check B: preview framing ------------------------------------------------

INTENT_TRIGGER = re.compile(
    r"\bORACLE\b|anticipatory[\s-]intent|latent[\s-]intent"
    r"|intent[\s-](?:preview|inference|prediction|scoring|stages?)\b",
    re.I,
)
PREVIEW_FRAMING = re.compile(r"preview\s*(?:[·—–-]|&#183;|&middot;)\s*in development", re.I)

# Net-yield / net-contribution copy carries the same framing obligation as
# intent copy until the pilot flips the label (positioning doc claim ledger).
NET_YIELD_TRIGGER = re.compile(r"net[\s-]?yield|net[\s-]?contribution", re.I)

# --- check C: number labeling ------------------------------------------------

# A multiplier must not be followed by another digit: "2.4×" is a multiplier,
# the "5×" inside a "5×5 risk matrix" is a grid dimension.
NUMBER = re.compile(r"\d+(?:\.\d+)?\s?(?:%|×(?!\d))")
NUMBER_LABEL = re.compile(r"illustrative|composite|operating default|operating parameter", re.I)

SEC_MARK = re.compile(r"§\s*(\d+)")


def _strip_invisible_html(html: str) -> str:
    """Reduce HTML to customer-visible text: drop style/script/comments/tags."""
    text = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def _sections(rel_path: str, raw: str) -> list[tuple[str, str]]:
    """Split a scoped file into (section_name, visible_text) chunks.

    HTML splits on <section> boundaries, Markdown on headings, and the
    briefing data.js on its top-level domain blocks — so "same section"
    matches how a reader actually encounters the copy.
    """
    if rel_path.endswith(".js"):
        marks = [(m.start(), m.group(1)) for m in re.finditer(r'id:\s*"(\w+)"', raw)]
        # keep only top-level domain ids (they repeat inside signals arrays;
        # the first occurrence of each unique id opens that domain's block)
        seen: dict[str, int] = {}
        for pos, name in marks:
            seen.setdefault(name, pos)
        bounds = sorted((pos, name) for name, pos in seen.items()
                        if re.search(r'\n  \w+: \{\s*\n\s*id: "' + name + '"', raw))
        if not bounds:
            return [("file", raw)]
        chunks: list[tuple[str, str]] = [("prelude", raw[: bounds[0][0]])]
        for i, (pos, name) in enumerate(bounds):
            end = bounds[i + 1][0] if i + 1 < len(bounds) else len(raw)
            chunks.append((f"domain:{name}", raw[pos:end]))
        return chunks
    if rel_path.endswith(".md"):
        parts = re.split(r"(?m)^(#{1,3} .+)$", raw)
        chunks = [("intro", parts[0])]
        for i in range(1, len(parts), 2):
            title = parts[i].strip("# ").strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            # The heading is customer-visible text of the section it opens, so
            # labels/framing carried in the heading count for that section.
            chunks.append((title, f"{title}\n{body}"))
        return chunks
    # HTML: chunk on <section boundaries; the head/nav before the first
    # section is its own chunk.
    pieces = re.split(r"(?=<section\b)", raw, flags=re.I)
    chunks = []
    for idx, piece in enumerate(pieces):
        m = re.search(r'id="([^"]+)"', piece[:200])
        name = m.group(1) if m else ("head" if idx == 0 else f"section-{idx}")
        chunks.append((name, _strip_invisible_html(piece)))
    return chunks


def check_file(rel_path: str, raw: str) -> list[str]:
    findings: list[str] = []
    visible_whole = _strip_invisible_html(raw) if rel_path.endswith(".html") else raw

    # A — banned strings on visible text
    for pattern, label in ((MIND_READING, 'affirmative "mind-reading"'),
                           (GUARANTEED, 'affirmative "guaranteed"')):
        for m in pattern.finditer(visible_whole):
            ctx = visible_whole[max(0, m.start() - 40): m.end() + 40].strip()
            findings.append(f"{rel_path} :: banned-string :: {label}: …{' '.join(ctx.split())}…")
    for patterns, label in ((DEPLOYED_INTENT, "deployed-intent"),
                            (DEPLOYED_NET_YIELD, "deployed-net-yield")):
        for pattern in patterns:
            for m in pattern.finditer(visible_whole):
                ctx = visible_whole[max(0, m.start() - 40): m.end() + 40].strip()
                findings.append(
                    f"{rel_path} :: banned-string :: present-tense {label} claim: "
                    f"…{' '.join(ctx.split())}…"
                )
    for m in QUOKKA.finditer(visible_whole):
        ctx = visible_whole[max(0, m.start() - 40): m.end() + 40].strip()
        findings.append(
            f"{rel_path} :: banned-string :: \"Quokka Swarm\" (unvalidated novelty term): "
            f"…{' '.join(ctx.split())}…"
        )

    # B + C — per section
    for name, text in _sections(rel_path, raw):
        if INTENT_TRIGGER.search(text) and not PREVIEW_FRAMING.search(text):
            findings.append(
                f"{rel_path} :: preview-framing :: section '{name}' mentions intent/ORACLE "
                f"without 'Preview · in development' framing"
            )
        if NET_YIELD_TRIGGER.search(text) and not PREVIEW_FRAMING.search(text):
            findings.append(
                f"{rel_path} :: preview-framing :: section '{name}' mentions net yield / "
                f"net contribution without 'Preview · in development' framing"
            )
        if (AIRBNB_KL_HEADLINE.search(text)
                or (KL_CONTEXT.search(text) and KL_SECONDARY.search(text))):
            if not AIRBNB_ATTRIBUTION.search(text):
                findings.append(
                    f"{rel_path} :: claim-ledger :: section '{name}' quotes the KL-divergence "
                    f"figures without attributing them to Airbnb's published research"
                )
        if OBSERVED_PERF.search(text) and not DESIGN_TARGET_LABEL.search(text):
            findings.append(
                f"{rel_path} :: claim-ledger :: section '{name}' states 15-minute / "
                f"sub-second performance without a 'design target' label"
            )
        numbers = NUMBER.findall(text)
        if numbers and not NUMBER_LABEL.search(text):
            findings.append(
                f"{rel_path} :: number-label :: section '{name}' shows {sorted(set(numbers))} "
                f"without an illustrative/composite/operating-default label"
            )

    # D — §-mark sequence. The class attribute is multi-valued on the real
    # pages (class="mark sec-mark"), so match sec-mark anywhere in it — and
    # refuse to pass vacuously: a sec-mark page where the extractor finds
    # nothing is a broken extractor or a broken page, never a pass.
    if rel_path in SEC_MARK_PAGES:
        marks = [int(n) for n in SEC_MARK.findall(
            " ".join(re.findall(r'class="[^"]*\bsec-mark\b[^"]*"[^>]*>([^<]*)<', raw))
        )]
        if not marks:
            findings.append(f"{rel_path} :: sec-sequence :: no §-marks extracted from a sec-mark page")
        elif marks != list(range(1, len(marks) + 1)):
            findings.append(f"{rel_path} :: sec-sequence :: §-marks not strictly 1..N: {marks}")
    return findings


def run_scan(root: Path = SITE_ROOT) -> list[str]:
    findings: list[str] = []
    for rel in SCOPE_FILES:
        path = root / rel
        if not path.exists():
            findings.append(f"{rel} :: missing :: scoped file not found")
            continue
        findings.extend(check_file(rel, path.read_text(encoding="utf-8")))
    return findings


# --- self-test ---------------------------------------------------------------

SEEDED_BAD = """<html><head><title>seed</title></head><body>
<section id="s1"><p class="mark sec-mark">§01</p>
<p>Our platform is pure mind-reading with guaranteed results.</p></section>
<section id="s2"><p class="mark sec-mark">§03</p>
<p>ORACLE is live and already predicting intent for every visitor.</p></section>
<section id="s3"><p>Customers see a 37% lift and 2.4× return.</p></section>
<section id="s4"><p>Net-yield bidding is live: our Quokka Swarm inspector
already bids on net-contribution for every store.</p></section>
<section id="s5"><p>KL divergence fell from 4.95 to 0.66 in our tests,
refreshed on 15-minute cycles.</p></section>
</body></html>"""

SEEDED_CLEAN = """<html><head><title>seed</title></head><body>
<section id="s1"><p class="mark sec-mark">§01</p>
<p>Anticipatory intent — not mind-reading. Preview · in development.</p>
<p>Never a guaranteed outcome.</p></section>
<section id="s2"><p class="mark sec-mark">§02</p>
<p>A composite scenario: 37% of spend was non-incremental (illustrative).</p>
<p>The 10% daily cap is an operating default.</p></section>
<section id="s3"><p>Net contribution pricing — Preview · in development —
runs on a 15-minute cycle as a design target, not observed performance.
Airbnb's published research reported KL divergence of 4.95 falling to 0.66;
those are Airbnb's figures, never quoted as ours.</p></section>
</body></html>"""


def run_self_test() -> bool:
    bad = check_file("signal.html", SEEDED_BAD)  # named so check D applies
    expected = {
        "banned mind-reading": any("mind-reading" in f for f in bad),
        "banned guaranteed": any("guaranteed" in f for f in bad),
        "deployed-intent claim": any("deployed-intent" in f for f in bad),
        "deployed-net-yield claim": any("deployed-net-yield" in f for f in bad),
        "banned quokka-swarm": any("Quokka Swarm" in f for f in bad),
        "unattributed KL figures": any("KL-divergence" in f for f in bad),
        "unlabeled observed-perf": any("design target" in f for f in bad),
        "net-yield preview framing": any(
            "preview-framing" in f and "net" in f for f in bad),
        "preview framing": any("preview-framing" in f for f in bad),
        "number label": any("number-label" in f for f in bad),
        "sec sequence": any("sec-sequence" in f for f in bad),
    }
    clean = check_file("signal.html", SEEDED_CLEAN)
    ok = all(expected.values()) and not clean
    for name, fired in expected.items():
        print(f"  self-test seeded violation [{name}]: {'CAUGHT' if fired else 'MISSED'}")
    print(f"  self-test clean sample: {len(clean)} finding(s) (expected 0)")
    for f in clean:
        print(f"    unexpected: {f}")
    print(f"SELF-TEST {'PASS — the gate fires' if ok else 'FAIL — the gate is broken'}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="verify the gate catches seeded violations")
    parser.add_argument("--root", default=str(SITE_ROOT),
                        help="site root (default: the folder above scripts/)")
    args = parser.parse_args()
    if args.self_test:
        return 0 if run_self_test() else 1
    findings = run_scan(Path(args.root))
    if findings:
        print(f"CONTENT QA: {len(findings)} finding(s)")
        for f in findings:
            print(f"  {f}")
        return 1
    print(f"CONTENT QA OK — {len(SCOPE_FILES)} scoped files clean "
          f"(banned strings, preview framing, number labels, §-sequence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
