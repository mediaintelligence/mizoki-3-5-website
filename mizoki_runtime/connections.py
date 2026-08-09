"""Customer-facing API connection management for the admin backend.

Providers are the Virtuoso model vendors (mirrored from
``mizoki_runtime.virtuoso`` — Anthropic, Google/Gemini, OpenAI, xAI) plus the
platform's other outbound integrations (SendGrid, Meta Marketing, Google Ads).

Keys are applied to the *process environment* so every runtime layer that
resolves credentials lazily (the Virtuoso dispatcher, vendor adapters) picks
them up on the next call. Cloud Run instances are ephemeral: a key set here
lives until the instance recycles. Durable configuration belongs in Secret
Manager (docs/PRODUCTION_SECRETS_SETUP.md) — the admin page says so out loud.

Bright lines:
- A full key value is NEVER returned, logged, or persisted to disk by this
  module. Status output carries only a mask (last 4 characters).
- Verification calls send the key only to the provider's own API host.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

VERIFY_TIMEOUT_SECONDS = 8
MAX_KEY_LENGTH = 512

# In-process record of keys set at runtime (env var name -> ISO timestamp).
# Deliberately not written to disk: secrets on an ephemeral filesystem are a
# leak surface with no durability benefit.
_runtime_set_at: dict[str, str] = {}


@dataclass(frozen=True)
class ProviderSpec:
    """One connectable outbound API."""

    provider_id: str
    label: str
    env_var: str
    group: str  # "model-vendor" | "integration"
    verify_request: Callable[[str], urllib.request.Request] | None
    notes: str
    roles: tuple[str, ...] = field(default=())

    def describe(self) -> dict:
        return {
            "id": self.provider_id,
            "label": self.label,
            "env_var": self.env_var,
            "group": self.group,
            "verifiable": self.verify_request is not None,
            "notes": self.notes,
            "roles": list(self.roles),
        }


def _anthropic_request(key: str) -> urllib.request.Request:
    return urllib.request.Request(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
    )


def _gemini_request(key: str) -> urllib.request.Request:
    # GEMINI_API_KEY authenticates the Generative Language API; Vertex uses
    # OAuth/ADC and is out of scope for a pasted-key check.
    return urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": key},
    )


def _openai_request(key: str) -> urllib.request.Request:
    return urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {key}"},
    )


def _xai_request(key: str) -> urllib.request.Request:
    return urllib.request.Request(
        "https://api.x.ai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
    )


def _sendgrid_request(key: str) -> urllib.request.Request:
    return urllib.request.Request(
        "https://api.sendgrid.com/v3/scopes",
        headers={"Authorization": f"Bearer {key}"},
    )


def _meta_request(key: str) -> urllib.request.Request:
    # Token travels in the query string per Graph API convention; host is
    # Meta's own API, consistent with the send-only-to-provider bright line.
    return urllib.request.Request(
        f"https://graph.facebook.com/v21.0/me?access_token={key}"
    )


PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        "anthropic",
        "Anthropic (Claude)",
        "ANTHROPIC_API_KEY",
        "model-vendor",
        _anthropic_request,
        "Boss Agent, coding/architecture role, and the Virtuoso global fallback.",
        roles=("CODING_ARCH", "GLOBAL_FALLBACK"),
    ),
    ProviderSpec(
        "gemini",
        "Google (Gemini)",
        "GEMINI_API_KEY",
        "model-vendor",
        _gemini_request,
        "Extraction and causal cells (data/causal role).",
        roles=("DATA_CAUSAL",),
    ),
    ProviderSpec(
        "openai",
        "OpenAI (GPT)",
        "OPENAI_API_KEY",
        "model-vendor",
        _openai_request,
        "Creative direction and asset generation role.",
        roles=("CREATIVE_MM",),
    ),
    ProviderSpec(
        "xai",
        "xAI (Grok)",
        "XAI_API_KEY",
        "model-vendor",
        _xai_request,
        "Deploy, incident, and ops agents role.",
        roles=("DEVOPS_OPS",),
    ),
    ProviderSpec(
        "sendgrid",
        "SendGrid",
        "SENDGRID_API_KEY",
        "integration",
        _sendgrid_request,
        "Lifecycle email delivery and event webhooks.",
    ),
    ProviderSpec(
        "meta_ads",
        "Meta Marketing API",
        "META_ACCESS_TOKEN",
        "integration",
        _meta_request,
        "Paid social signal ingestion and campaign telemetry.",
    ),
    ProviderSpec(
        "google_ads",
        "Google Ads (developer token)",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "integration",
        None,  # a developer token can't be checked without OAuth + customer id
        "GAQL pre-flight and campaign telemetry. Verified only through a full "
        "OAuth flow, so this row is status-only.",
    ),
)

_BY_ID: dict[str, ProviderSpec] = {p.provider_id: p for p in PROVIDERS}


class UnknownProviderError(KeyError):
    """Raised for a provider id not in the registry."""


def get_provider(provider_id: str) -> ProviderSpec:
    try:
        return _BY_ID[provider_id]
    except KeyError as exc:
        raise UnknownProviderError(provider_id) from exc


def mask_key(value: str) -> str:
    """Show at most the last 4 characters, never more."""
    if not value:
        return ""
    if len(value) <= 8:
        return "•••• (set)"
    return f"••••{value[-4:]}"


def provider_status(provider: ProviderSpec, env: dict | None = None) -> dict:
    source_env = os.environ if env is None else env
    value = (source_env.get(provider.env_var) or "").strip()
    entry = provider.describe()
    entry.update(
        {
            "configured": bool(value),
            "masked": mask_key(value),
            "source": (
                "runtime"
                if provider.env_var in _runtime_set_at
                else ("environment" if value else "unset")
            ),
            "runtime_set_at": _runtime_set_at.get(provider.env_var),
        }
    )
    return entry


def connections_status(env: dict | None = None) -> list[dict]:
    return [provider_status(p, env=env) for p in PROVIDERS]


def set_key(provider_id: str, value: str) -> dict:
    """Apply a key to the process environment. Returns masked status only."""
    provider = get_provider(provider_id)
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("api_key must be a non-empty string")
    if len(cleaned) > MAX_KEY_LENGTH:
        raise ValueError(f"api_key exceeds {MAX_KEY_LENGTH} characters")
    if any(ch in cleaned for ch in "\r\n\t"):
        raise ValueError("api_key must not contain control characters")
    os.environ[provider.env_var] = cleaned
    _runtime_set_at[provider.env_var] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )
    return provider_status(provider)


def clear_key(provider_id: str) -> dict:
    provider = get_provider(provider_id)
    os.environ.pop(provider.env_var, None)
    _runtime_set_at.pop(provider.env_var, None)
    return provider_status(provider)


def verify_connection(provider_id: str, opener=None, env: dict | None = None) -> dict:
    """Live round-trip to the provider's own API. Never echoes the key."""
    provider = get_provider(provider_id)
    source_env = os.environ if env is None else env
    key = (source_env.get(provider.env_var) or "").strip()
    base = {"id": provider.provider_id, "env_var": provider.env_var}
    if provider.verify_request is None:
        return {**base, "ok": False, "detail": "not verifiable from a pasted key"}
    if not key:
        return {**base, "ok": False, "detail": f"{provider.env_var} is not set"}

    request = provider.verify_request(key)
    open_fn = opener if opener is not None else urllib.request.urlopen
    try:
        with open_fn(request, timeout=VERIFY_TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", 200)
        return {
            **base,
            "ok": 200 <= status < 300,
            "http_status": status,
            "detail": "credential accepted" if 200 <= status < 300 else "unexpected status",
        }
    except urllib.error.HTTPError as exc:
        detail = "credential rejected" if exc.code in (401, 403) else f"HTTP {exc.code}"
        return {**base, "ok": False, "http_status": exc.code, "detail": detail}
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        reason = getattr(exc, "reason", None) or exc
        return {**base, "ok": False, "detail": f"network error: {reason}"}


def status_json(env: dict | None = None) -> str:
    """Convenience for logging/diagnostics — masked, never raw."""
    return json.dumps(connections_status(env), indent=2)
