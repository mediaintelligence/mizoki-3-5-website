#!/usr/bin/env python3
"""MIZOKI3 design-canon guard.

The site's look and feel is governed by canon.lock.json — a sha256 manifest
of every core surface (homepage, shared theme, demo hub + six desks,
walkthrough, Executive Briefing module, pricing). The live site must match
the canon byte-for-byte on these files.

Usage:
    python3 scripts/check_design_canon.py            # verify (CI/deploy gate)
    python3 scripts/check_design_canon.py --update   # re-pin after an
                                                     # explicitly human-approved
                                                     # change (commit the diff)

Exit codes: 0 = canon holds, 1 = drift detected / file missing.

Governance: canon changes ship ONLY with specific human approval. The deploy
workflow (deploy-homepage.yml) is manual-dispatch-only and runs this check
before building; re-pinning via --update is part of an approved change, never
a way around it.

Stdlib only. Run from the site root ("# MIZ OKI 3.5/") or pass --root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

LOCK_NAME = "canon.lock.json"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None, help="site root (default: script's parent dir)")
    ap.add_argument("--update", action="store_true",
                    help="re-pin hashes for an approved change")
    args = ap.parse_args()

    root = pathlib.Path(args.root) if args.root else pathlib.Path(__file__).resolve().parent.parent
    lock_path = root / LOCK_NAME
    if not lock_path.is_file():
        print(f"CANON ERROR: {lock_path} not found", file=sys.stderr)
        return 1

    lock = json.loads(lock_path.read_text())
    files: dict[str, str] = lock["files"]

    drift: list[str] = []
    missing: list[str] = []
    current: dict[str, str] = {}
    for rel, pinned in files.items():
        p = root / rel
        if not p.is_file():
            missing.append(rel)
            continue
        digest = sha256(p)
        current[rel] = digest
        if digest != pinned:
            drift.append(rel)

    if args.update:
        lock["files"] = {rel: current.get(rel, files[rel]) for rel in files}
        lock_path.write_text(json.dumps(lock, indent=2) + "\n")
        print(f"CANON RE-PINNED: {len(drift)} file(s) updated, "
              f"{len(missing)} missing kept as-was. Commit {LOCK_NAME} with the "
              f"approved change.")
        for rel in drift:
            print(f"  repinned: {rel}")
        return 0

    if missing:
        for rel in missing:
            print(f"CANON MISSING: {rel}", file=sys.stderr)
    if drift:
        for rel in drift:
            print(f"CANON DRIFT: {rel}", file=sys.stderr)
    if missing or drift:
        print(f"\nCANON CHECK FAILED — {len(drift)} drifted, {len(missing)} missing.",
              file=sys.stderr)
        print("If this change carries specific human approval, re-pin with: "
              "python3 scripts/check_design_canon.py --update", file=sys.stderr)
        return 1

    print(f"CANON OK — {len(files)} core surfaces match {lock.get('version', '?')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
