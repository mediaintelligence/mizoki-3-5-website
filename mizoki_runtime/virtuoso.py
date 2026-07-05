"""Virtuoso model plane — role-based flagship registry consolidated with the Boss Agent.

This is the in-repo counterpart of the ``virtuoso_models`` package that WIRING.md
drops into MIZOKICloudRun: one source of truth for which frontier model serves each
role, a hard guard against retired model strings, and a cross-vendor global-fallback
contract. The Boss Agent stops carrying vendor model ids of its own and resolves
everything through ``get_model(Role.X)`` — the same lookup the SRPVDAL cells use —
so the registry and every provenance stamp agree on which flagship produced a row.

Kept in the house style: deterministic, dependency-free, unit-testable. No vendor
SDK is imported here; ``virtuoso_call`` dispatches through injectable per-vendor
adapters, so the failover semantics (served_by / primary_error / opt-out) are fully
exercised in-process with no network and no keys.

Reconciliation notes vs. WIRING.md (intentional, documented):
- The DATA_CAUSAL slot defaults to ``gemini-3.5-pro`` because this repo already
  pinned that model for the JourneyEvent extractor (founder pin, 2026-06) and it is
  what production stamps into provenance. The ``VIRTUOSO_GEMINI_35_PRO_GA`` flag is
  still accepted for env parity with MIZOKICloudRun cells; it resolves to the same
  string here.
- The seven-phase SRPVDAL loop is authoritative in this repo (WIRING §9 encodes the
  same); roles (which flagship runs) and phases (pipeline position) are orthogonal.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping


class Role(str, Enum):
    """Which flagship serves a class of work — not where it sits in the loop."""

    DATA_CAUSAL = "data_causal"  # SENSE/REASON/DECIDE extraction + causal cells
    CODING_ARCH = "coding_arch"  # Boss Agent / codegen / architecture
    CREATIVE_MM = "creative_mm"  # creative & asset generation (multimodal)
    DEVOPS_OPS = "devops_ops"  # deploy / incident / ops agents


# The seven-phase SRPVDAL loop is authoritative (matches the JourneyEvent
# provenance spec; two phases more than the platform skill's five-phase SRDAL).
SRPVDAL_PHASES = ("sense", "reason", "plan", "validate", "decide", "act", "learn")

# Cross-vendor failover target for every role. Deliberately crosses the in-family
# lock — availability beats the lock for the backup path only (Boss directive
# 2026-06-26). CODING_ARCH legitimately shares this string; its failover is a
# no-op re-raise.
GLOBAL_FALLBACK = "claude-opus-4-8"
GLOBAL_FALLBACK_VENDOR = "anthropic"

# Retired / superseded model strings (WIRING §2). A config or env override that
# resolves to any of these is a misconfiguration, rejected at startup.
FORBIDDEN_LEGACY_PATTERNS = (
    r"gemini-2\.0-flash",
    r"gemini-3-pro-preview",
    r"grok-4-1",
    r"grok-4-fast",
    r"grok-4-0709",
    r"grok-code-fast",
    r"claude-opus-4-6",
    r"claude-opus-4-7",
    r"gpt-5\.2",
    r"imagen-4\.0",
    r"image-preview",
)
_LEGACY_RE = re.compile("|".join(f"({pattern})" for pattern in FORBIDDEN_LEGACY_PATTERNS))

ENV_OVERRIDE_PREFIX = "VIRTUOSO_MODEL_"
GEMINI_GA_FLAG = "VIRTUOSO_GEMINI_35_PRO_GA"
IMAGE_OVERRIDE_ENV = "VIRTUOSO_IMAGE_GOOGLE_FLAGSHIP"


@dataclass(frozen=True)
class ModelSpec:
    role: Role
    model: str
    vendor: str
    sdk: str
    api_key_env: str
    srpvdal_stages: tuple[str, ...]
    rationale: str
    provisional: bool = False
    source: str = "registry"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "model": self.model,
            "vendor": self.vendor,
            "sdk": self.sdk,
            "api_key_env": self.api_key_env,
            "srpvdal_stages": list(self.srpvdal_stages),
            "rationale": self.rationale,
            "provisional": self.provisional,
            "source": self.source,
            "global_fallback": GLOBAL_FALLBACK,
        }


_PRIMARIES: dict[Role, ModelSpec] = {
    Role.DATA_CAUSAL: ModelSpec(
        role=Role.DATA_CAUSAL,
        model="gemini-3.5-pro",
        vendor="google",
        sdk="google-genai",
        api_key_env="GEMINI_API_KEY",
        srpvdal_stages=("sense", "reason", "decide"),
        rationale=(
            "Extraction + causal cells (incl. Cell 26/27 X-/DR-Learner framing prompts). "
            "GA pin already applied in this repo (JourneyEvent extractor, 2026-06)."
        ),
    ),
    Role.CODING_ARCH: ModelSpec(
        role=Role.CODING_ARCH,
        model="claude-opus-4-8",
        vendor="anthropic",
        sdk="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        srpvdal_stages=("plan", "act"),
        rationale=(
            "Boss Agent / codegen / architecture. Legitimately shares the global-fallback "
            "string; its failover is a no-op re-raise."
        ),
    ),
    Role.CREATIVE_MM: ModelSpec(
        role=Role.CREATIVE_MM,
        model="gpt-5.5",
        vendor="openai",
        sdk="openai",
        api_key_env="OPENAI_API_KEY",
        srpvdal_stages=("act",),
        rationale=(
            "Creative & asset generation; image work delegates to "
            "IMAGE_MODELS['google_flagship']."
        ),
        provisional=True,
    ),
    Role.DEVOPS_OPS: ModelSpec(
        role=Role.DEVOPS_OPS,
        model="grok-5",
        vendor="xai",
        sdk="openai-compatible",
        api_key_env="XAI_API_KEY",
        srpvdal_stages=("act", "learn"),
        rationale=(
            "Deploy / incident / ops agents. Watch the api.x.ai -> SpaceXAI endpoint "
            "migration (12+ mo)."
        ),
        provisional=True,
    ),
}


def find_legacy_strings(text: str) -> list[str]:
    """Return every retired model string present in ``text`` (deduped, in order)."""
    seen: list[str] = []
    for match in _LEGACY_RE.finditer(text or ""):
        value = match.group(0)
        if value not in seen:
            seen.append(value)
    return seen


def assert_no_legacy_strings(text: str, source: str = "config") -> None:
    """Startup guard: refuse to boot if a retired string sneaks back in."""
    violations = find_legacy_strings(text)
    if violations:
        raise ValueError(
            f"retired model string(s) {violations} found in {source}; "
            "replace with a get_model(Role.X).model lookup"
        )


def image_model(key: str = "google_flagship", env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Image generation delegates (CREATIVE_MM). Provisional pending vendor GA cards."""
    source = os.environ if env is None else env
    if key != "google_flagship":
        raise ValueError(f"unknown image model key: {key!r}")
    override = (source.get(IMAGE_OVERRIDE_ENV) or "").strip()
    if override:
        assert_no_legacy_strings(override, source=IMAGE_OVERRIDE_ENV)
    return {
        "key": key,
        "model": override or "imagen-5",
        "vendor": "google",
        "provisional": not override,
    }


def get_model(role: Role, env: Mapping[str, str] | None = None) -> ModelSpec:
    """Resolve the flagship serving ``role``: env override first, else the registry.

    Overrides (``VIRTUOSO_MODEL_<ROLE>``) are rejected if they resolve to a retired
    string, so a legacy id can never be reintroduced through configuration.
    """
    source = os.environ if env is None else env
    spec = _PRIMARIES[role]
    override = (source.get(f"{ENV_OVERRIDE_PREFIX}{role.name}") or "").strip()
    if override:
        assert_no_legacy_strings(override, source=f"{ENV_OVERRIDE_PREFIX}{role.name}")
        return replace(spec, model=override, provisional=False, source="env")
    if role is Role.DATA_CAUSAL and (source.get(GEMINI_GA_FLAG) or "").strip() == "1":
        # Env parity with MIZOKICloudRun cells; this repo's default is already the
        # GA string, so the flag confirms rather than flips.
        return replace(spec, model="gemini-3.5-pro", source="ga-flag")
    return spec


def assert_fallback_not_primary(role: Role, env: Mapping[str, str] | None = None) -> ModelSpec:
    """A non-Anthropic role whose primary resolves to the fallback string is a
    misconfiguration — the failover path would mask itself. Runs on every call."""
    resolved = get_model(role, env)
    if resolved.model == GLOBAL_FALLBACK and role is not Role.CODING_ARCH:
        raise ValueError(
            f"role {role.value} primary resolves to the global fallback "
            f"({GLOBAL_FALLBACK}); fix the {ENV_OVERRIDE_PREFIX}{role.name} override"
        )
    return resolved


def validate_registry(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Boot-time guard over every role: legacy strings and fallback-as-primary
    both raise, so a misconfigured cell refuses to start."""
    roles = {}
    for role in Role:
        roles[role.value] = assert_fallback_not_primary(role, env).to_dict()
    return {"roles": roles, "global_fallback": GLOBAL_FALLBACK, "ok": True}


# Adapter contract: (model, messages) -> {"text": str, "reasoning_summary": str|None}.
VendorAdapter = Callable[[str, list[dict[str, Any]]], dict[str, Any]]


@dataclass
class VirtuosoResponse:
    role: Role
    model: str
    text: str
    served_by: str  # "primary" | "global_fallback"
    primary_error: str | None = None
    reasoning_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "model": self.model,
            "text": self.text,
            "served_by": self.served_by,
            "primary_error": self.primary_error,
            "reasoning_summary": self.reasoning_summary,
        }


def virtuoso_call(
    role: Role,
    messages: list[dict[str, Any]],
    *,
    fallback: bool = True,
    adapters: dict[str, VendorAdapter] | None = None,
    env: Mapping[str, str] | None = None,
) -> VirtuosoResponse:
    """Dispatch a call to the role's flagship with cross-vendor failover.

    Failover fires only AFTER a primary failure, never first-choice. Responses
    carry ``served_by`` and ``primary_error`` so a degraded path is never silent.
    ``fallback=False`` re-raises the primary error instead of masking it. Because
    of the global fallback, the Anthropic adapter/key must be available in every
    cell — even ones whose primary is Gemini/GPT/Grok — or the failover path will
    itself fail (raised with both errors attached).
    """
    resolved = assert_fallback_not_primary(role, env)
    vendor_adapters = adapters or {}

    def invoke(vendor: str, model: str, api_key_env: str) -> dict[str, Any]:
        adapter = vendor_adapters.get(vendor)
        if adapter is None:
            raise RuntimeError(
                f"no {vendor} adapter configured for model {model} "
                f"(set {api_key_env} and wire the vendor adapter)"
            )
        output = adapter(model, messages)
        if not isinstance(output, dict):
            raise RuntimeError(f"{vendor} adapter returned {type(output).__name__}, expected dict")
        return output

    try:
        output = invoke(resolved.vendor, resolved.model, resolved.api_key_env)
        return VirtuosoResponse(
            role=role,
            model=resolved.model,
            text=str(output.get("text") or ""),
            served_by="primary",
            reasoning_summary=output.get("reasoning_summary"),
        )
    except Exception as primary_exc:
        if not fallback:
            raise
        if resolved.model == GLOBAL_FALLBACK and resolved.vendor == GLOBAL_FALLBACK_VENDOR:
            raise  # CODING_ARCH: failover to itself is a no-op re-raise
        try:
            output = invoke(GLOBAL_FALLBACK_VENDOR, GLOBAL_FALLBACK, "ANTHROPIC_API_KEY")
        except Exception as fallback_exc:
            raise RuntimeError(
                f"primary {resolved.model} failed ({primary_exc}); "
                f"global fallback {GLOBAL_FALLBACK} also failed ({fallback_exc})"
            ) from primary_exc
        return VirtuosoResponse(
            role=role,
            model=GLOBAL_FALLBACK,
            text=str(output.get("text") or ""),
            served_by="global_fallback",
            primary_error=str(primary_exc),
            reasoning_summary=output.get("reasoning_summary"),
        )


def reasoning_trace_row(response: VirtuosoResponse, ts: float | None = None) -> dict[str, Any]:
    """MII distillation hook (WIRING §6): every reasoning_summary is the signal.
    Claude is richest, then GPT, then Grok; Gemini summaries are None (signatures
    are encrypted), so Gemini rows never reach the trace store."""
    return {
        "role": response.role.value,
        "model": response.model,
        "summary": response.reasoning_summary,
        "served_by": response.served_by,
        "ts": time.time() if ts is None else ts,
    }


class VirtuosoModelPlane:
    """Runtime cell wrapping the registry for the Boss Agent: boot-time config
    guard, role resolution, legacy scanning, governed dispatch, and a persistent
    JSONL MII reasoning-trace store (same ephemeral-disk caveat as the v1 store)."""

    def __init__(self, trace_file: Path, env: Mapping[str, str] | None = None) -> None:
        self.trace_file = trace_file
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        self._env = env
        # Startup guard — a misconfigured registry refuses to boot.
        validate_registry(env)

    def _resolve_role(self, role_name: Any) -> Role:
        if isinstance(role_name, Role):
            return role_name
        if not isinstance(role_name, str) or not role_name.strip():
            raise ValueError("role must be a non-empty string")
        normalized = role_name.strip().lower()
        for role in Role:
            if normalized in (role.value, role.name.lower()):
                return role
        raise ValueError(
            f"unknown virtuoso role: {role_name!r}; expected one of "
            f"{[role.value for role in Role]}"
        )

    def resolve(self, role_name: Any) -> dict[str, Any]:
        return get_model(self._resolve_role(role_name), self._env).to_dict()

    def registry_snapshot(self) -> dict[str, Any]:
        snapshot = validate_registry(self._env)
        snapshot["image_models"] = {"google_flagship": image_model(env=self._env)}
        snapshot["srpvdal_phases"] = list(SRPVDAL_PHASES)
        snapshot["phase_note"] = (
            "seven-phase SRPVDAL is authoritative; roles (which flagship runs) and "
            "phases (pipeline position) are orthogonal"
        )
        snapshot["forbidden_legacy_patterns"] = list(FORBIDDEN_LEGACY_PATTERNS)
        snapshot["mii_trace_count"] = self.trace_count()
        return snapshot

    def scan_text(self, text: Any, source: str = "inline") -> dict[str, Any]:
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        violations = find_legacy_strings(text)
        return {"source": source, "violations": violations, "clean": not violations}

    def call(
        self,
        role_name: Any,
        messages: list[dict[str, Any]],
        *,
        fallback: bool = True,
        adapters: dict[str, VendorAdapter] | None = None,
    ) -> dict[str, Any]:
        response = virtuoso_call(
            self._resolve_role(role_name),
            messages,
            fallback=fallback,
            adapters=adapters,
            env=self._env,
        )
        if response.reasoning_summary:
            self._append_trace(reasoning_trace_row(response))
        return response.to_dict()

    def _append_trace(self, row: dict[str, Any]) -> None:
        with self.trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def _load_traces(self) -> list[dict[str, Any]]:
        if not self.trace_file.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.trace_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn write must not break trace inspection
            if isinstance(parsed, dict):
                rows.append(parsed)
        return rows

    def recent_traces(self, limit: int = 10) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        rows = self._load_traces()[-limit:]
        rows.reverse()
        return rows

    def trace_count(self) -> int:
        return len(self._load_traces())

    def discovery_block(self) -> dict[str, Any]:
        return {
            **self.registry_snapshot(),
            "tools": [
                "virtuoso.registry",
                "virtuoso.resolve_model",
                "virtuoso.scan_legacy",
                "virtuoso.reasoning_traces",
            ],
            "description": (
                "Virtuoso model plane: one role-based registry of frontier models with a "
                "legacy-string boot guard and a cross-vendor global fallback "
                f"({GLOBAL_FALLBACK}); every provenance stamp resolves through get_model()."
            ),
        }
