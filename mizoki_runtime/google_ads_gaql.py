"""Google Ads API version + GAQL field-compatibility pre-flight validation.

The Google Ads API churns ~3 versions a year and sunsets old ones on a published
schedule; once a version is removed, every request against it hard-fails. The
other common hard failure is a GAQL query that selects/filters/sorts on a field
that is not valid for the targeted API version + resource combination. The
official guidance is to check field availability with ``GoogleAdsFieldService``
and the Query Validator *before* a complex query ever runs.

This module is the in-process, deterministic, dependency-free embodiment of that
advice — same discipline as the JourneyEvent connectors (Cell 27 et al.): no
network, no third-party deps, fully unit-testable. It models

* a **version deprecation schedule** (``GOOGLE_ADS_API_VERSIONS``) that resolves a
  version to ``supported`` / ``deprecated`` / ``sunset`` / ``unreleased`` /
  ``unknown`` relative to a reference date, so MCC traversal stops calling a
  version the day it disappears instead of discovering it at runtime;
* a **GoogleAdsFieldService-style field registry** keyed by resource, carrying
  ``selectable`` / ``filterable`` / ``sortable`` flags and version availability
  windows (``available_since`` / ``deprecated_in`` / ``removed_in``);
* a dependency-free **GAQL parser** that extracts the SELECT / FROM / WHERE /
  ORDER BY field references; and
* a **validator + cache** that pre-flights a query against a version, returning a
  structured ``errors`` / ``warnings`` / ``fields`` report. The cache keys on
  (normalized query, version, date) so a query template reused across thousands
  of accounts in an MCC sweep is validated once, not once per account.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .journey import canonical_compact_json, sha256_hex


GOOGLE_ADS_CELL_ID = "cell.31.google_ads_compatibility"

# Number of days before a version's sunset date that it is surfaced as
# ``deprecated`` (an upgrade-now warning) rather than ``supported``.
DEPRECATION_WARNING_WINDOW_DAYS = 120


# ---------------------------------------------------------------------------
# Version deprecation schedule
# ---------------------------------------------------------------------------
#
# Release/sunset dates track Google's published Ads API deprecation schedule
# (roughly three releases a year, each supported for ~14 months). Dates are
# approximate-but-representative; bump this table as Google publishes new
# versions. ``status`` is *computed* from these dates against a reference date,
# never hard-coded, so the schedule stays correct as time passes.
GOOGLE_ADS_API_VERSIONS: dict[str, dict[str, str]] = {
    "v16": {"release_date": "2024-02-07", "sunset_date": "2025-02-05"},
    "v17": {"release_date": "2024-06-05", "sunset_date": "2025-06-04"},
    "v18": {"release_date": "2024-10-02", "sunset_date": "2025-09-24"},
    "v19": {"release_date": "2025-02-04", "sunset_date": "2026-02-25"},
    "v20": {"release_date": "2025-06-03", "sunset_date": "2026-09-23"},
    "v21": {"release_date": "2025-10-07", "sunset_date": "2027-02-24"},
}


# ---------------------------------------------------------------------------
# Field registry (GoogleAdsFieldService-style metadata)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GaqlFieldMeta:
    """Metadata for one GAQL field, mirroring GoogleAdsFieldService."""

    name: str
    category: str  # ATTRIBUTE | SEGMENT | METRIC | RESOURCE
    data_type: str = "STRING"
    selectable: bool = True
    filterable: bool = True
    sortable: bool = True
    available_since: str | None = None  # first version the field exists in
    deprecated_in: str | None = None  # version where it is deprecated (warn)
    removed_in: str | None = None  # version where it is gone (error if >=)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "data_type": self.data_type,
            "selectable": self.selectable,
            "filterable": self.filterable,
            "sortable": self.sortable,
            "available_since": self.available_since,
            "deprecated_in": self.deprecated_in,
            "removed_in": self.removed_in,
        }


def _meta(name: str, category: str, **kwargs: Any) -> GaqlFieldMeta:
    return GaqlFieldMeta(name=name, category=category, **kwargs)


# Shared SEGMENT fields, queryable from (almost) every resource.
_SEGMENT_FIELDS: tuple[GaqlFieldMeta, ...] = (
    _meta("segments.date", "SEGMENT", data_type="DATE"),
    _meta("segments.hour", "SEGMENT", data_type="INT64"),
    _meta("segments.day_of_week", "SEGMENT", data_type="ENUM"),
    _meta("segments.device", "SEGMENT", data_type="ENUM"),
    _meta("segments.geo_target_country", "SEGMENT", sortable=False),
    _meta("segments.conversion_action", "SEGMENT", sortable=False),
)

# Shared METRIC fields. Metrics are selectable + sortable but not filterable in
# the WHERE clause for most reporting resources (Google rejects metric filters).
_METRIC_FIELDS: tuple[GaqlFieldMeta, ...] = (
    _meta("metrics.impressions", "METRIC", data_type="INT64", filterable=False),
    _meta("metrics.clicks", "METRIC", data_type="INT64", filterable=False),
    _meta("metrics.conversions", "METRIC", data_type="DOUBLE", filterable=False),
    _meta("metrics.conversions_value", "METRIC", data_type="DOUBLE", filterable=False),
    _meta("metrics.cost_micros", "METRIC", data_type="INT64", filterable=False),
    _meta("metrics.ctr", "METRIC", data_type="DOUBLE", filterable=False),
    _meta("metrics.average_cpc", "METRIC", data_type="DOUBLE", filterable=False),
    # Deprecated-then-removed example: the legacy average-position metric was
    # removed years ago; selecting it against any modern version is a hard error.
    _meta(
        "metrics.average_position",
        "METRIC",
        data_type="DOUBLE",
        filterable=False,
        deprecated_in="v16",
        removed_in="v16",
    ),
)

# Per-resource attribute + attributed-resource fields. Each tuple is the set of
# non-segment, non-metric fields selectable when that resource is the FROM target.
_RESOURCE_ATTRIBUTES: dict[str, tuple[GaqlFieldMeta, ...]] = {
    "campaign": (
        _meta("campaign.id", "ATTRIBUTE", data_type="INT64"),
        _meta("campaign.name", "ATTRIBUTE"),
        _meta("campaign.status", "ATTRIBUTE", data_type="ENUM"),
        _meta("campaign.advertising_channel_type", "ATTRIBUTE", data_type="ENUM"),
        _meta("campaign.bidding_strategy_type", "ATTRIBUTE", data_type="ENUM"),
        _meta("customer.id", "ATTRIBUTE", data_type="INT64"),
        _meta("customer.currency_code", "ATTRIBUTE"),
    ),
    "ad_group": (
        _meta("ad_group.id", "ATTRIBUTE", data_type="INT64"),
        _meta("ad_group.name", "ATTRIBUTE"),
        _meta("ad_group.status", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group.type", "ATTRIBUTE", data_type="ENUM"),
        _meta("campaign.id", "ATTRIBUTE", data_type="INT64"),
        _meta("campaign.name", "ATTRIBUTE"),
    ),
    "ad_group_ad": (
        _meta("ad_group_ad.ad.id", "ATTRIBUTE", data_type="INT64"),
        _meta("ad_group_ad.ad.name", "ATTRIBUTE"),
        _meta("ad_group_ad.status", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group_ad.ad.type", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group.id", "ATTRIBUTE", data_type="INT64"),
        _meta("campaign.id", "ATTRIBUTE", data_type="INT64"),
    ),
    "ad_group_criterion": (
        _meta("ad_group_criterion.criterion_id", "ATTRIBUTE", data_type="INT64"),
        _meta("ad_group_criterion.keyword.text", "ATTRIBUTE"),
        _meta("ad_group_criterion.keyword.match_type", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group_criterion.status", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group.id", "ATTRIBUTE", data_type="INT64"),
        _meta("campaign.id", "ATTRIBUTE", data_type="INT64"),
    ),
    "search_term_view": (
        _meta("search_term_view.search_term", "ATTRIBUTE"),
        _meta("search_term_view.status", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group.id", "ATTRIBUTE", data_type="INT64"),
        _meta("campaign.id", "ATTRIBUTE", data_type="INT64"),
    ),
    "keyword_view": (
        _meta("ad_group_criterion.keyword.text", "ATTRIBUTE"),
        _meta("ad_group_criterion.keyword.match_type", "ATTRIBUTE", data_type="ENUM"),
        _meta("ad_group.id", "ATTRIBUTE", data_type="INT64"),
        _meta("campaign.id", "ATTRIBUTE", data_type="INT64"),
    ),
    "customer": (
        _meta("customer.id", "ATTRIBUTE", data_type="INT64"),
        _meta("customer.descriptive_name", "ATTRIBUTE"),
        _meta("customer.currency_code", "ATTRIBUTE"),
        _meta("customer.time_zone", "ATTRIBUTE"),
    ),
}

GOOGLE_ADS_RESOURCES: tuple[str, ...] = tuple(sorted(_RESOURCE_ATTRIBUTES))


def _build_resource_field_index() -> dict[str, dict[str, GaqlFieldMeta]]:
    """resource -> {field_name -> meta} including shared segments + metrics."""
    index: dict[str, dict[str, GaqlFieldMeta]] = {}
    for resource, attributes in _RESOURCE_ATTRIBUTES.items():
        fields: dict[str, GaqlFieldMeta] = {}
        for meta in (*attributes, *_SEGMENT_FIELDS, *_METRIC_FIELDS):
            fields[meta.name] = meta
        index[resource] = fields
    return index


_RESOURCE_FIELD_INDEX: dict[str, dict[str, GaqlFieldMeta]] = _build_resource_field_index()


# ---------------------------------------------------------------------------
# Deterministic primitives
# ---------------------------------------------------------------------------

class GaqlSyntaxError(ValueError):
    """Raised when a string cannot be parsed as a GAQL query."""


def parse_version(value: Any) -> int | None:
    """Parse ``"v19"`` / ``"19"`` / ``19`` -> ``19``; ``None`` if unparseable."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        match = re.fullmatch(r"\s*[vV]?(\d+)\s*", value)
        if match:
            return int(match.group(1))
    return None


def normalize_version(value: Any) -> str | None:
    parsed = parse_version(value)
    return f"v{parsed}" if parsed is not None else None


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _today(as_of: Any = None) -> date:
    if isinstance(as_of, date):
        return as_of
    if isinstance(as_of, str) and as_of.strip():
        return _parse_date(as_of.strip())
    return datetime.now(timezone.utc).date()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Version schedule resolution
# ---------------------------------------------------------------------------

def latest_known_version() -> str:
    return max(GOOGLE_ADS_API_VERSIONS, key=lambda v: parse_version(v) or 0)


def version_status(api_version: Any, as_of: Any = None) -> dict[str, Any]:
    """Resolve a version to its lifecycle status relative to ``as_of``.

    status ∈ {supported, deprecated, sunset, unreleased, unknown}. ``usable`` is
    True only when the API will still accept requests against the version.
    """
    normalized = normalize_version(api_version)
    today = _today(as_of)
    latest = latest_known_version()
    if normalized is None or normalized not in GOOGLE_ADS_API_VERSIONS:
        return {
            "api_version": normalized or str(api_version),
            "status": "unknown",
            "usable": False,
            "as_of": today.isoformat(),
            "latest_version": latest,
            "message": (
                f"{api_version!r} is not a known Google Ads API version; "
                f"the latest known version is {latest}."
            ),
        }

    schedule = GOOGLE_ADS_API_VERSIONS[normalized]
    release = _parse_date(schedule["release_date"])
    sunset = _parse_date(schedule["sunset_date"])
    days_until_sunset = (sunset - today).days

    if today < release:
        status, usable = "unreleased", False
        message = f"{normalized} is not released until {release.isoformat()}."
    elif today >= sunset:
        status, usable = "sunset", False
        message = (
            f"{normalized} sunset on {sunset.isoformat()}; requests are rejected. "
            f"Upgrade to {latest}."
        )
    elif days_until_sunset <= DEPRECATION_WARNING_WINDOW_DAYS:
        status, usable = "deprecated", True
        message = (
            f"{normalized} sunsets in {days_until_sunset} day(s) "
            f"({sunset.isoformat()}); upgrade to {latest} now."
        )
    else:
        status, usable = "supported", True
        message = f"{normalized} is supported until {sunset.isoformat()}."

    return {
        "api_version": normalized,
        "status": status,
        "usable": usable,
        "release_date": release.isoformat(),
        "sunset_date": sunset.isoformat(),
        "days_until_sunset": days_until_sunset,
        "as_of": today.isoformat(),
        "latest_version": latest,
        "message": message,
    }


def version_schedule(as_of: Any = None) -> list[dict[str, Any]]:
    """Full schedule with each version's computed status, oldest first."""
    return [
        version_status(name, as_of=as_of)
        for name in sorted(GOOGLE_ADS_API_VERSIONS, key=lambda v: parse_version(v) or 0)
    ]


# ---------------------------------------------------------------------------
# Field metadata access
# ---------------------------------------------------------------------------

def resource_fields(resource: str) -> dict[str, GaqlFieldMeta]:
    return _RESOURCE_FIELD_INDEX.get(resource, {})


def field_metadata(resource: str | None = None) -> dict[str, Any]:
    """GoogleAdsFieldService-style dump for one resource or the whole catalog."""
    if resource is not None:
        fields = resource_fields(resource)
        return {
            "resource": resource,
            "known_resource": resource in _RESOURCE_FIELD_INDEX,
            "field_count": len(fields),
            "fields": [meta.to_dict() for meta in sorted(fields.values(), key=lambda m: m.name)],
        }
    return {
        "resources": list(GOOGLE_ADS_RESOURCES),
        "fields_by_resource": {
            name: [meta.to_dict() for meta in sorted(fields.values(), key=lambda m: m.name)]
            for name, fields in _RESOURCE_FIELD_INDEX.items()
        },
    }


# ---------------------------------------------------------------------------
# GAQL parser
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParsedGaql:
    raw: str
    normalized: str
    resource: str
    select_fields: tuple[str, ...]
    where_fields: tuple[str, ...]
    order_by_fields: tuple[str, ...]
    limit: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource": self.resource,
            "select_fields": list(self.select_fields),
            "where_fields": list(self.where_fields),
            "order_by_fields": list(self.order_by_fields),
            "limit": self.limit,
        }


_FIELD_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_CLAUSE_SPLIT = re.compile(
    r"\b(WHERE|ORDER\s+BY|LIMIT|PARAMETERS)\b", flags=re.IGNORECASE
)


def _leading_field(condition: str) -> str | None:
    match = _FIELD_TOKEN.match(condition.strip().lstrip("("))
    return match.group(0) if match else None


def parse_gaql(query: Any) -> ParsedGaql:
    """Parse a GAQL string into its field references. Raises GaqlSyntaxError."""
    if not isinstance(query, str) or not query.strip():
        raise GaqlSyntaxError("query must be a non-empty string")

    normalized = re.sub(r"\s+", " ", query.strip())
    head = re.match(
        r"^SELECT\s+(?P<select>.+?)\s+FROM\s+(?P<resource>[A-Za-z_][A-Za-z0-9_]*)"
        r"(?P<rest>\b.*)?$",
        normalized,
        flags=re.IGNORECASE,
    )
    if not head:
        raise GaqlSyntaxError("query must match 'SELECT <fields> FROM <resource>'")

    select_clause = head.group("select")
    resource = head.group("resource")
    rest = head.group("rest") or ""

    select_fields = tuple(
        token for token in (part.strip() for part in select_clause.split(",")) if token
    )
    if not select_fields:
        raise GaqlSyntaxError("SELECT clause has no fields")

    # Carve the trailing clauses (WHERE / ORDER BY / LIMIT / PARAMETERS) out of rest.
    parts = _CLAUSE_SPLIT.split(rest)
    clauses: dict[str, str] = {}
    idx = 1
    while idx < len(parts) - 1:
        keyword = re.sub(r"\s+", " ", parts[idx].strip().upper())
        body = parts[idx + 1].strip()
        clauses[keyword] = body
        idx += 2

    where_fields: tuple[str, ...] = ()
    if clauses.get("WHERE"):
        conditions = re.split(r"\b(?:AND|OR)\b", clauses["WHERE"], flags=re.IGNORECASE)
        seen: list[str] = []
        for condition in conditions:
            token = _leading_field(condition)
            if token and token not in seen:
                seen.append(token)
        where_fields = tuple(seen)

    order_by_fields: tuple[str, ...] = ()
    if clauses.get("ORDER BY"):
        items = clauses["ORDER BY"].split(",")
        seen_order: list[str] = []
        for item in items:
            token = _FIELD_TOKEN.match(item.strip())
            if token and token.group(0) not in seen_order:
                seen_order.append(token.group(0))
        order_by_fields = tuple(seen_order)

    limit: int | None = None
    if clauses.get("LIMIT"):
        limit_match = re.match(r"(\d+)", clauses["LIMIT"])
        if limit_match:
            limit = int(limit_match.group(1))

    return ParsedGaql(
        raw=query,
        normalized=normalized,
        resource=resource,
        select_fields=select_fields,
        where_fields=where_fields,
        order_by_fields=order_by_fields,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def _field_available_in(meta: GaqlFieldMeta, version_num: int) -> tuple[bool, str | None]:
    """Return (available, reason-if-not) for a field at a numeric version."""
    if meta.removed_in is not None:
        removed = parse_version(meta.removed_in)
        if removed is not None and version_num >= removed:
            return False, f"removed in {meta.removed_in}"
    if meta.available_since is not None:
        since = parse_version(meta.available_since)
        if since is not None and version_num < since:
            return False, f"not available until {meta.available_since}"
    return True, None


class GaqlValidator:
    """Pre-flight a GAQL query against an API version + field catalog."""

    def validate(self, query: Any, api_version: Any, as_of: Any = None) -> dict[str, Any]:
        status = version_status(api_version, as_of=as_of)
        resolved_version = status["api_version"]
        version_num = parse_version(resolved_version)
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        field_reports: list[dict[str, Any]] = []

        # --- API version gates -------------------------------------------------
        if status["status"] == "unknown":
            errors.append({"code": "unknown_api_version", "field": None, "message": status["message"]})
        elif status["status"] == "sunset":
            errors.append({"code": "api_version_sunset", "field": None, "message": status["message"]})
        elif status["status"] == "unreleased":
            errors.append({"code": "api_version_unreleased", "field": None, "message": status["message"]})
        elif status["status"] == "deprecated":
            warnings.append({"code": "api_version_deprecated", "field": None, "message": status["message"]})

        # --- Parse -------------------------------------------------------------
        try:
            parsed = parse_gaql(query)
        except GaqlSyntaxError as exc:
            errors.append({"code": "gaql_syntax_error", "field": None, "message": str(exc)})
            return self._report(query, None, resolved_version, status, errors, warnings, field_reports)

        resource = parsed.resource
        fields = resource_fields(resource)
        if resource not in _RESOURCE_FIELD_INDEX:
            errors.append({
                "code": "unknown_resource",
                "field": resource,
                "message": (
                    f"'{resource}' is not a known GAQL resource for {resolved_version}; "
                    f"known resources: {', '.join(GOOGLE_ADS_RESOURCES)}."
                ),
            })

        # When the version itself is unparseable we cannot do per-version field
        # availability checks; fall back to existence/clause checks only.
        check_availability = version_num is not None and resource in _RESOURCE_FIELD_INDEX

        for clause, field_names, flag, flag_label in (
            ("select", parsed.select_fields, "selectable", "selectable"),
            ("where", parsed.where_fields, "filterable", "filterable in WHERE"),
            ("order_by", parsed.order_by_fields, "sortable", "sortable in ORDER BY"),
        ):
            for name in field_names:
                report = {"field": name, "clause": clause, "status": "ok"}
                meta = fields.get(name)
                if resource not in _RESOURCE_FIELD_INDEX:
                    report["status"] = "skipped"
                    field_reports.append(report)
                    continue
                if meta is None:
                    report["status"] = "error"
                    errors.append({
                        "code": "unknown_field",
                        "field": name,
                        "message": f"'{name}' is not a valid field for resource '{resource}'.",
                    })
                    field_reports.append(report)
                    continue

                report["category"] = meta.category
                report["data_type"] = meta.data_type

                if check_availability:
                    available, reason = _field_available_in(meta, version_num)
                    if not available:
                        report["status"] = "error"
                        errors.append({
                            "code": "field_unavailable_in_version",
                            "field": name,
                            "message": f"'{name}' is {reason} (querying {resolved_version}).",
                        })
                        field_reports.append(report)
                        continue

                if not getattr(meta, flag):
                    report["status"] = "error"
                    errors.append({
                        "code": f"field_not_{flag}",
                        "field": name,
                        "message": f"'{name}' is not {flag_label}.",
                    })
                    field_reports.append(report)
                    continue

                # Deprecated-but-still-present field -> warning, not error.
                if check_availability and meta.deprecated_in is not None:
                    dep = parse_version(meta.deprecated_in)
                    if dep is not None and version_num >= dep:
                        report["status"] = "deprecated"
                        warnings.append({
                            "code": "field_deprecated",
                            "field": name,
                            "message": f"'{name}' is deprecated as of {meta.deprecated_in}.",
                        })

                field_reports.append(report)

        return self._report(query, parsed, resolved_version, status, errors, warnings, field_reports)

    @staticmethod
    def _report(
        query: Any,
        parsed: ParsedGaql | None,
        resolved_version: str,
        status: dict[str, Any],
        errors: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        field_reports: list[dict[str, Any]],
    ) -> dict[str, Any]:
        normalized = parsed.normalized if parsed is not None else (
            query if isinstance(query, str) else canonical_compact_json(query)
        )
        cache_key = sha256_hex(
            "|".join([normalized, resolved_version, status.get("as_of", "")])
        )
        return {
            "query": query if isinstance(query, str) else canonical_compact_json(query),
            "normalized_query": normalized,
            "api_version": resolved_version,
            "version_status": status,
            "resource": parsed.resource if parsed is not None else None,
            "parsed": parsed.to_dict() if parsed is not None else None,
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "fields": field_reports,
            "cache_key": cache_key,
            "checked_at": _now_iso(),
        }


# ---------------------------------------------------------------------------
# Validation cache
# ---------------------------------------------------------------------------

class GaqlValidationCache:
    """LRU-ish cache of validation reports keyed on (query, version, date).

    MCC traversal reuses a small set of query templates across thousands of
    accounts; this validates a (template, version, day) once and serves the rest
    from cache. The cache key folds in the ``as_of`` date so a verdict that
    flips when a version sunsets is not served stale across day boundaries.
    """

    def __init__(self, validator: GaqlValidator | None = None, maxsize: int = 512) -> None:
        self._validator = validator or GaqlValidator()
        self._maxsize = max(1, maxsize)
        self._store: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _key(query: Any, api_version: Any, as_of: Any) -> str:
        normalized = re.sub(r"\s+", " ", query.strip()) if isinstance(query, str) else canonical_compact_json(query)
        version = normalize_version(api_version) or str(api_version)
        day = _today(as_of).isoformat()
        return sha256_hex("|".join([normalized, version, day]))

    def validate(self, query: Any, api_version: Any, as_of: Any = None) -> dict[str, Any]:
        key = self._key(query, api_version, as_of)
        cached = self._store.get(key)
        if cached is not None:
            self.hits += 1
            self._order.remove(key)
            self._order.append(key)
            return {**cached, "cached": True}
        self.misses += 1
        report = self._validator.validate(query, api_version, as_of=as_of)
        self._store[key] = report
        self._order.append(key)
        if len(self._order) > self._maxsize:
            evicted = self._order.pop(0)
            self._store.pop(evicted, None)
        return {**report, "cached": False}

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "size": len(self._store),
            "maxsize": self._maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
        }

    def clear(self) -> None:
        self._store.clear()
        self._order.clear()
        self.hits = 0
        self.misses = 0


# ---------------------------------------------------------------------------
# Compatibility cell
# ---------------------------------------------------------------------------

class GoogleAdsCompatibilityCell:
    """SENSE-stage pre-flight: validate GAQL against the live version schedule.

    Wraps the validator + cache and persists recent validation traces to JSONL
    (same pattern as Cell 27) so an MCC sweep's compatibility checks are
    auditable. Deterministic and dependency-free: no Google Ads client, no
    network — the version schedule + field registry are the source of truth.
    """

    def __init__(self, trace_file: Path | None = None, default_version: str | None = None) -> None:
        self._trace_file = Path(trace_file) if trace_file is not None else None
        if self._trace_file is not None:
            self._trace_file.parent.mkdir(parents=True, exist_ok=True)
        self._validator = GaqlValidator()
        self.cache = GaqlValidationCache(self._validator)
        self.default_version = normalize_version(default_version) or latest_known_version()

    def _resolve_version(self, api_version: Any) -> Any:
        if api_version is None or (isinstance(api_version, str) and not api_version.strip()):
            return self.default_version
        return api_version

    def validate_query(self, query: Any, api_version: Any = None, as_of: Any = None) -> dict[str, Any]:
        report = self.cache.validate(query, self._resolve_version(api_version), as_of=as_of)
        self._persist(report)
        return report

    def validate_batch(self, queries: Any, api_version: Any = None, as_of: Any = None) -> dict[str, Any]:
        if not isinstance(queries, (list, tuple)) or not queries:
            raise ValueError("queries must be a non-empty array")
        resolved = self._resolve_version(api_version)
        results: list[dict[str, Any]] = []
        valid_count = 0
        for index, query in enumerate(queries):
            report = self.cache.validate(query, resolved, as_of=as_of)
            results.append({"index": index, **report})
            if report["valid"]:
                valid_count += 1
            self._persist(report)
        return {
            "api_version": normalize_version(resolved) or str(resolved),
            "received": len(queries),
            "valid": valid_count,
            "invalid": len(queries) - valid_count,
            "cache": self.cache.stats(),
            "results": results,
        }

    def version_status(self, api_version: Any = None, as_of: Any = None) -> dict[str, Any]:
        if api_version is None or (isinstance(api_version, str) and not api_version.strip()):
            return {
                "latest_version": latest_known_version(),
                "default_version": self.default_version,
                "schedule": version_schedule(as_of=as_of),
            }
        return version_status(api_version, as_of=as_of)

    def field_metadata(self, resource: str | None = None) -> dict[str, Any]:
        return field_metadata(resource)

    def _persist(self, report: dict[str, Any]) -> None:
        if self._trace_file is None:
            return
        trace = {
            "ts": time.time(),
            "checked_at": report.get("checked_at"),
            "api_version": report.get("api_version"),
            "resource": report.get("resource"),
            "valid": report.get("valid"),
            "error_count": len(report.get("errors", [])),
            "warning_count": len(report.get("warnings", [])),
            "version_status": report.get("version_status", {}).get("status"),
            "cache_key": report.get("cache_key"),
            "normalized_query": report.get("normalized_query"),
        }
        with self._trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace) + "\n")

    def _load_traces(self) -> list[dict[str, Any]]:
        if self._trace_file is None or not self._trace_file.exists():
            return []
        traces: list[dict[str, Any]] = []
        for line in self._trace_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return traces

    def recent_validations(self, limit: int = 10) -> list[dict[str, Any]]:
        bounded = max(1, min(int(limit), 100))
        traces = self._load_traces()[-bounded:]
        traces.reverse()
        return traces

    def discovery_block(self) -> dict[str, Any]:
        return {
            "cell": GOOGLE_ADS_CELL_ID,
            "description": (
                "Pre-flights GAQL queries against the Google Ads API version "
                "deprecation schedule and a GoogleAdsFieldService-style field "
                "registry so version sunsets and field/version mismatches are "
                "caught before a query runs across MCC accounts."
            ),
            "default_version": self.default_version,
            "latest_version": latest_known_version(),
            "supported_versions": [
                status["api_version"]
                for status in version_schedule()
                if status["usable"]
            ],
            "resources": list(GOOGLE_ADS_RESOURCES),
            "tools": [
                "google_ads.validate_gaql",
                "google_ads.validate_gaql_batch",
                "google_ads.version_status",
                "google_ads.field_metadata",
            ],
            "cache": self.cache.stats(),
        }
