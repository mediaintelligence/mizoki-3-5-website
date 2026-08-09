"""Coverage for the admin API-connections surface.

Bright lines under test:
- every endpoint (and the page) is admin-session-gated, independent of
  MIZOKI_REQUIRE_AUTH_FOR_APIS;
- a full key value never appears in any response body;
- verification round-trips are provider-scoped and injectable (no network).
"""

from __future__ import annotations

import io
import json
import os
import unittest
import urllib.error

from app import create_app
from mizoki_runtime import connections


TEST_USERS = {"ops@example.com": "correct-horse"}


class ConnectionsModuleTestCase(unittest.TestCase):
    PROVIDER = "anthropic"
    ENV_VAR = "ANTHROPIC_API_KEY"

    def setUp(self) -> None:
        self._saved = os.environ.get(self.ENV_VAR)
        os.environ.pop(self.ENV_VAR, None)
        connections._runtime_set_at.pop(self.ENV_VAR, None)

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop(self.ENV_VAR, None)
        else:
            os.environ[self.ENV_VAR] = self._saved
        connections._runtime_set_at.pop(self.ENV_VAR, None)

    def test_registry_ids_and_env_vars_are_unique(self) -> None:
        ids = [p.provider_id for p in connections.PROVIDERS]
        envs = [p.env_var for p in connections.PROVIDERS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(envs), len(set(envs)))

    def test_registry_covers_all_virtuoso_vendor_key_envs(self) -> None:
        from mizoki_runtime import virtuoso

        wanted = {spec.api_key_env for spec in virtuoso.REGISTRY.values()}
        have = {p.env_var for p in connections.PROVIDERS}
        self.assertTrue(
            wanted.issubset(have),
            f"connections registry missing virtuoso key envs: {wanted - have}",
        )

    def test_mask_reveals_at_most_last_four(self) -> None:
        secret = "sk-ant-abcdefghijklmnop1234"
        masked = connections.mask_key(secret)
        self.assertNotIn(secret[:-4], masked)
        self.assertTrue(masked.endswith("1234"))
        self.assertEqual(connections.mask_key("short"), "•••• (set)")
        self.assertEqual(connections.mask_key(""), "")

    def test_set_key_applies_to_environ_and_masks(self) -> None:
        entry = connections.set_key(self.PROVIDER, "  sk-ant-secretsecret9876  ")
        self.assertEqual(os.environ[self.ENV_VAR], "sk-ant-secretsecret9876")
        self.assertEqual(entry["source"], "runtime")
        self.assertTrue(entry["configured"])
        self.assertNotIn("secretsecret", json.dumps(entry))

    def test_set_key_rejects_empty_control_chars_and_oversize(self) -> None:
        for bad in ("", "   ", "line\nbreak", "tab\tchar", "x" * 600):
            with self.assertRaises(ValueError):
                connections.set_key(self.PROVIDER, bad)

    def test_unknown_provider_raises(self) -> None:
        with self.assertRaises(connections.UnknownProviderError):
            connections.set_key("nope", "value")

    def test_clear_key_removes_env(self) -> None:
        connections.set_key(self.PROVIDER, "sk-ant-secretsecret9876")
        entry = connections.clear_key(self.PROVIDER)
        self.assertNotIn(self.ENV_VAR, os.environ)
        self.assertFalse(entry["configured"])
        self.assertEqual(entry["source"], "unset")

    def test_verify_unset_key_short_circuits(self) -> None:
        result = connections.verify_connection(self.PROVIDER)
        self.assertFalse(result["ok"])
        self.assertIn("not set", result["detail"])

    def test_verify_success_and_rejection_and_network_error(self) -> None:
        connections.set_key(self.PROVIDER, "sk-ant-secretsecret9876")

        class FakeResponse(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def ok_opener(request, timeout=None):
            # The key must go only to the provider's own host.
            self.assertIn("api.anthropic.com", request.full_url)
            self.assertEqual(
                request.get_header("X-api-key"), "sk-ant-secretsecret9876"
            )
            return FakeResponse(b"{}")

        result = connections.verify_connection(self.PROVIDER, opener=ok_opener)
        self.assertTrue(result["ok"])
        self.assertNotIn("secretsecret", json.dumps(result))

        def rejected_opener(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url, 401, "unauthorized", hdrs=None, fp=None
            )

        result = connections.verify_connection(self.PROVIDER, opener=rejected_opener)
        self.assertFalse(result["ok"])
        self.assertEqual(result["http_status"], 401)
        self.assertEqual(result["detail"], "credential rejected")

        def broken_opener(request, timeout=None):
            raise urllib.error.URLError("dns failure")

        result = connections.verify_connection(self.PROVIDER, opener=broken_opener)
        self.assertFalse(result["ok"])
        self.assertIn("network error", result["detail"])

    def test_google_ads_is_status_only(self) -> None:
        result = connections.verify_connection("google_ads")
        self.assertFalse(result["ok"])
        self.assertIn("not verifiable", result["detail"])


class ConnectionsApiTestCase(unittest.TestCase):
    ENV_VAR = "ANTHROPIC_API_KEY"

    def setUp(self) -> None:
        self._saved_users = os.environ.get("MIZOKI_DEMO_USERS_JSON")
        os.environ["MIZOKI_DEMO_USERS_JSON"] = json.dumps(TEST_USERS)
        self._saved_key = os.environ.get(self.ENV_VAR)
        os.environ.pop(self.ENV_VAR, None)
        connections._runtime_set_at.pop(self.ENV_VAR, None)
        self.app = create_app()
        self.app.config["TESTING"] = True

    def tearDown(self) -> None:
        if self._saved_users is None:
            os.environ.pop("MIZOKI_DEMO_USERS_JSON", None)
        else:
            os.environ["MIZOKI_DEMO_USERS_JSON"] = self._saved_users
        if self._saved_key is None:
            os.environ.pop(self.ENV_VAR, None)
        else:
            os.environ[self.ENV_VAR] = self._saved_key
        connections._runtime_set_at.pop(self.ENV_VAR, None)

    def _login(self, client) -> None:
        response = client.post(
            "/admin/login",
            data={"email": "ops@example.com", "password": "correct-horse"},
        )
        self.assertEqual(response.status_code, 302)

    def test_page_redirects_unauthenticated(self) -> None:
        client = self.app.test_client()
        response = client.get("/admin/connections")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])

    def test_api_endpoints_require_session(self) -> None:
        client = self.app.test_client()
        self.assertEqual(client.get("/api/admin/connections").status_code, 401)
        self.assertEqual(
            client.post(
                "/api/admin/connections/anthropic", json={"api_key": "x" * 20}
            ).status_code,
            401,
        )
        self.assertEqual(
            client.post("/api/admin/connections/anthropic/verify").status_code, 401
        )
        self.assertEqual(
            client.delete("/api/admin/connections/anthropic").status_code, 401
        )
        # And the key must NOT have been applied by the rejected call.
        self.assertNotIn(self.ENV_VAR, os.environ)

    def test_page_renders_for_admin(self) -> None:
        client = self.app.test_client()
        self._login(client)
        response = client.get("/admin/connections")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("API Connections", body)
        self.assertIn("Secret Manager", body)  # durability note is mandatory

    def test_status_update_and_clear_flow(self) -> None:
        client = self.app.test_client()
        self._login(client)

        listing = client.get("/api/admin/connections").get_json()
        by_id = {c["id"]: c for c in listing["connections"]}
        self.assertIn("anthropic", by_id)
        self.assertFalse(by_id["anthropic"]["configured"])

        secret = "sk-ant-verysecretvalue4321"
        response = client.post(
            "/api/admin/connections/anthropic", json={"api_key": secret}
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn(secret, body)
        self.assertIn("4321", body)
        self.assertEqual(os.environ[self.ENV_VAR], secret)

        listing = client.get("/api/admin/connections").get_json()
        self.assertNotIn(secret, json.dumps(listing))

        response = client.delete("/api/admin/connections/anthropic")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.ENV_VAR, os.environ)

    def test_update_validation_errors(self) -> None:
        client = self.app.test_client()
        self._login(client)
        self.assertEqual(
            client.post(
                "/api/admin/connections/anthropic", json={"api_key": "  "}
            ).status_code,
            400,
        )
        self.assertEqual(
            client.post(
                "/api/admin/connections/unknown-provider", json={"api_key": "x" * 20}
            ).status_code,
            404,
        )

    def test_dashboard_links_to_connections(self) -> None:
        client = self.app.test_client()
        self._login(client)
        response = client.get("/admin")
        self.assertIn("/admin/connections", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
