import tempfile
import unittest
from pathlib import Path

from mizoki_runtime.google_ads_gaql import (
    GaqlSyntaxError,
    GaqlValidationCache,
    GaqlValidator,
    GoogleAdsCompatibilityCell,
    field_metadata,
    latest_known_version,
    normalize_version,
    parse_gaql,
    parse_version,
    version_schedule,
    version_status,
)


# A fixed reference date so version-lifecycle assertions are deterministic.
# Against the shipped schedule on this date: v19 is sunset, v20 is deprecated
# (sunsets within the warning window), v21 is supported.
AS_OF = "2026-06-30"


class VersionScheduleTest(unittest.TestCase):
    def test_parse_and_normalize_version(self) -> None:
        self.assertEqual(19, parse_version("v19"))
        self.assertEqual(19, parse_version("19"))
        self.assertEqual(19, parse_version(19))
        self.assertIsNone(parse_version("vNineteen"))
        self.assertIsNone(parse_version(True))
        self.assertEqual("v20", normalize_version("20"))
        self.assertIsNone(normalize_version("nope"))

    def test_sunset_version_is_unusable(self) -> None:
        status = version_status("v19", as_of=AS_OF)
        self.assertEqual("sunset", status["status"])
        self.assertFalse(status["usable"])
        self.assertEqual(latest_known_version(), status["latest_version"])

    def test_deprecated_version_is_usable_with_warning(self) -> None:
        status = version_status("v20", as_of=AS_OF)
        self.assertEqual("deprecated", status["status"])
        self.assertTrue(status["usable"])
        self.assertGreater(status["days_until_sunset"], 0)

    def test_supported_version(self) -> None:
        status = version_status("v21", as_of=AS_OF)
        self.assertEqual("supported", status["status"])
        self.assertTrue(status["usable"])

    def test_unknown_version(self) -> None:
        status = version_status("v99", as_of=AS_OF)
        self.assertEqual("unknown", status["status"])
        self.assertFalse(status["usable"])

    def test_unreleased_version(self) -> None:
        # v21 releases 2025-10-07; before that it is unreleased.
        status = version_status("v21", as_of="2025-01-01")
        self.assertEqual("unreleased", status["status"])
        self.assertFalse(status["usable"])

    def test_schedule_is_ordered_and_complete(self) -> None:
        schedule = version_schedule(as_of=AS_OF)
        versions = [entry["api_version"] for entry in schedule]
        self.assertEqual(versions, sorted(versions, key=lambda v: parse_version(v)))
        self.assertIn("v21", versions)


class GaqlParserTest(unittest.TestCase):
    def test_parses_all_clauses(self) -> None:
        parsed = parse_gaql(
            "SELECT campaign.id, metrics.clicks FROM campaign "
            "WHERE segments.date DURING LAST_30_DAYS AND campaign.status = 'ENABLED' "
            "ORDER BY metrics.clicks DESC LIMIT 50"
        )
        self.assertEqual("campaign", parsed.resource)
        self.assertEqual(("campaign.id", "metrics.clicks"), parsed.select_fields)
        self.assertEqual(("segments.date", "campaign.status"), parsed.where_fields)
        self.assertEqual(("metrics.clicks",), parsed.order_by_fields)
        self.assertEqual(50, parsed.limit)

    def test_case_insensitive_keywords(self) -> None:
        parsed = parse_gaql("select campaign.id from campaign where campaign.id = 1")
        self.assertEqual("campaign", parsed.resource)
        self.assertEqual(("campaign.id",), parsed.where_fields)

    def test_rejects_non_query(self) -> None:
        with self.assertRaises(GaqlSyntaxError):
            parse_gaql("this is not gaql")
        with self.assertRaises(GaqlSyntaxError):
            parse_gaql("")


class GaqlValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = GaqlValidator()

    def test_valid_query_passes(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id, campaign.name, metrics.clicks FROM campaign "
            "WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.clicks DESC",
            "v21",
            as_of=AS_OF,
        )
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual([], report["errors"])
        self.assertEqual("campaign", report["resource"])

    def test_sunset_version_fails_even_for_valid_fields(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id FROM campaign", "v19", as_of=AS_OF
        )
        self.assertFalse(report["valid"])
        self.assertTrue(any(e["code"] == "api_version_sunset" for e in report["errors"]))

    def test_deprecated_version_warns_but_is_valid(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id FROM campaign", "v20", as_of=AS_OF
        )
        self.assertTrue(report["valid"])
        self.assertTrue(any(w["code"] == "api_version_deprecated" for w in report["warnings"]))

    def test_unknown_field_is_an_error(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id, campaign.bogus_field FROM campaign", "v21", as_of=AS_OF
        )
        self.assertFalse(report["valid"])
        codes = {e["code"] for e in report["errors"]}
        self.assertIn("unknown_field", codes)

    def test_unknown_resource_is_an_error(self) -> None:
        report = self.validator.validate(
            "SELECT foo.bar FROM not_a_resource", "v21", as_of=AS_OF
        )
        self.assertFalse(report["valid"])
        self.assertTrue(any(e["code"] == "unknown_resource" for e in report["errors"]))

    def test_metric_in_where_is_not_filterable(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id FROM campaign WHERE metrics.clicks > 100", "v21", as_of=AS_OF
        )
        self.assertFalse(report["valid"])
        self.assertTrue(any(e["code"] == "field_not_filterable" for e in report["errors"]))

    def test_non_sortable_field_in_order_by(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id, segments.geo_target_country FROM campaign "
            "ORDER BY segments.geo_target_country",
            "v21",
            as_of=AS_OF,
        )
        self.assertFalse(report["valid"])
        self.assertTrue(any(e["code"] == "field_not_sortable" for e in report["errors"]))

    def test_removed_field_unavailable_in_modern_version(self) -> None:
        report = self.validator.validate(
            "SELECT campaign.id, metrics.average_position FROM campaign", "v21", as_of=AS_OF
        )
        self.assertFalse(report["valid"])
        self.assertTrue(
            any(e["code"] == "field_unavailable_in_version" for e in report["errors"])
        )

    def test_syntax_error_is_reported(self) -> None:
        report = self.validator.validate("DELETE FROM campaign", "v21", as_of=AS_OF)
        self.assertFalse(report["valid"])
        self.assertTrue(any(e["code"] == "gaql_syntax_error" for e in report["errors"]))


class GaqlCacheTest(unittest.TestCase):
    def test_cache_serves_repeat_validations(self) -> None:
        cache = GaqlValidationCache()
        query = "SELECT campaign.id FROM campaign"
        first = cache.validate(query, "v21", as_of=AS_OF)
        second = cache.validate(query, "v21", as_of=AS_OF)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        stats = cache.stats()
        self.assertEqual(1, stats["hits"])
        self.assertEqual(1, stats["misses"])

    def test_cache_key_includes_date_so_verdicts_are_not_stale(self) -> None:
        cache = GaqlValidationCache()
        query = "SELECT campaign.id FROM campaign"
        # Same query + version but a different evaluation date is a cache miss,
        # because a version can sunset between days.
        cache.validate(query, "v20", as_of="2026-06-30")
        report = cache.validate(query, "v20", as_of="2027-01-01")
        self.assertFalse(report["cached"])
        self.assertEqual(2, cache.stats()["misses"])

    def test_whitespace_normalized_queries_share_a_cache_entry(self) -> None:
        cache = GaqlValidationCache()
        cache.validate("SELECT campaign.id FROM campaign", "v21", as_of=AS_OF)
        report = cache.validate("SELECT   campaign.id   FROM   campaign", "v21", as_of=AS_OF)
        self.assertTrue(report["cached"])


class FieldMetadataTest(unittest.TestCase):
    def test_per_resource_metadata(self) -> None:
        meta = field_metadata("campaign")
        self.assertTrue(meta["known_resource"])
        names = {f["name"] for f in meta["fields"]}
        self.assertIn("campaign.id", names)
        self.assertIn("metrics.clicks", names)
        self.assertIn("segments.date", names)

    def test_full_catalog(self) -> None:
        meta = field_metadata()
        self.assertIn("campaign", meta["resources"])
        self.assertIn("fields_by_resource", meta)


class GoogleAdsCompatibilityCellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cell = GoogleAdsCompatibilityCell(
            Path(self.temp_dir.name) / "google_ads_validations.jsonl"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_validate_query_defaults_to_latest_version(self) -> None:
        report = self.cell.validate_query("SELECT campaign.id FROM campaign", as_of=AS_OF)
        self.assertEqual(latest_known_version(), report["api_version"])
        self.assertTrue(report["valid"])

    def test_validate_batch_summarizes_and_persists(self) -> None:
        queries = [
            "SELECT campaign.id FROM campaign",  # valid
            "SELECT campaign.bogus FROM campaign",  # invalid field
            "SELECT campaign.id FROM campaign WHERE metrics.clicks > 1",  # metric filter
        ]
        result = self.cell.validate_batch(queries, api_version="v21", as_of=AS_OF)
        self.assertEqual(3, result["received"])
        self.assertEqual(1, result["valid"])
        self.assertEqual(2, result["invalid"])
        # Persisted traces are readable back from the JSONL trace file.
        recent = self.cell.recent_validations(limit=10)
        self.assertEqual(3, len(recent))

    def test_batch_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            self.cell.validate_batch([], api_version="v21")

    def test_version_status_returns_schedule_without_argument(self) -> None:
        status = self.cell.version_status(as_of=AS_OF)
        self.assertIn("schedule", status)
        self.assertEqual(latest_known_version(), status["latest_version"])

    def test_discovery_block_lists_tools_and_supported_versions(self) -> None:
        block = self.cell.discovery_block()
        self.assertIn("google_ads.validate_gaql", block["tools"])
        self.assertIn("campaign", block["resources"])
        self.assertIn("cache", block)


if __name__ == "__main__":
    unittest.main()
