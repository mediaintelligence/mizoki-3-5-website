"""Cookieless demo telemetry — append-only JSONL, no IP, no user agent.

The demo measures itself with the runtime it demonstrates: the Flask
endpoint appends rows here and the ``demo.telemetry.summary`` MCP tool
reads them back. Stored fields are exactly ``{ts, event, demo, scenario}``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = ["TELEMETRY_EVENTS", "record_event", "summarize"]

TELEMETRY_EVENTS = frozenset({
    "demo_started",
    "demo_completed",
    "share_copied",
    "export_downloaded",
    "boardroom_played",
    "lead_click",
})

_MAX_FIELD_LENGTH = 64


def record_event(path: Path, event: str, demo: str, scenario: str) -> dict[str, Any]:
    """Validate and append one telemetry row. Raises ValueError on junk."""
    if event not in TELEMETRY_EVENTS:
        known = ", ".join(sorted(TELEMETRY_EVENTS))
        raise ValueError(f"unknown event: {event!r} (expected one of: {known})")
    for name, value in (("demo", demo), ("scenario", scenario)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"field '{name}' must be a non-empty string")
        if len(value) > _MAX_FIELD_LENGTH:
            raise ValueError(f"field '{name}' must be at most {_MAX_FIELD_LENGTH} characters")
    row = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "demo": demo.strip(),
        "scenario": scenario.strip(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def summarize(path: Path) -> dict[str, Any]:
    """Event counts by demo and scenario (malformed rows are skipped)."""
    total = 0
    by_event: dict[str, int] = {}
    by_demo: dict[str, dict[str, int]] = {}
    by_scenario: dict[str, dict[str, int]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event = row.get("event")
                demo = row.get("demo")
                scenario = row.get("scenario")
                if event not in TELEMETRY_EVENTS or not demo or not scenario:
                    continue
                total += 1
                by_event[event] = by_event.get(event, 0) + 1
                by_demo.setdefault(demo, {})
                by_demo[demo][event] = by_demo[demo].get(event, 0) + 1
                key = f"{demo}:{scenario}"
                by_scenario.setdefault(key, {})
                by_scenario[key][event] = by_scenario[key].get(event, 0) + 1
    return {
        "total_events": total,
        "by_event": by_event,
        "by_demo": by_demo,
        "by_demo_scenario": by_scenario,
    }
