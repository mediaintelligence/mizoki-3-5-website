"""Virtuoso model plane — role-based flagship registry consolidated with the Boss Agent.

This is the in-repo counterpart of the ``virtuoso_models`` package that lives in
MIZOKICloudRun (``src/shared/virtuoso_models``): one source of truth for which
frontier model serves each role, a hard guard against retired model strings, and a
cross-vendor global-fallback contract. The Boss Agent stops carrying vendor model
ids of its own and resolves everything through ``get_model(Role.X)`` — the same
lookup the SRPVDAL cells use — so the registry and every provenance stamp agree on
which flagship produced a row.

Registry data is synced from the canonical package (model_registry.py as of
2026-07-04):
  DATA_CAUSAL   -> Google    gemini-3.5-flash   (GA flip 2026-07-04; base gemini-3.1-pro-preview)
  CODING_ARCH   -> Anthropic claude-opus-4-8
  CREATIVE_MM   -> OpenAI    gpt-5.5
  DEVOPS_OPS    -> xAI       grok-4.3
  GLOBAL BACKUP -> Anthropic claude-opus-4-8    (all roles, cross-vendor)

Kept in the house style: deterministic, dependency-free, unit-testable. No vendor
SDK is imported here; ``virtuoso_call`` dispatches through injectable per-vendor
adapters, so the failover semantics (served_by / primary_error / opt-out) are fully
exercised in-process with no network and no keys. ``get_model`` additionally
accepts an injectable env mapping (the canonical package reads ``os.getenv``
directly) so resolution is testable without patching the process environment.

The seven-phase SRPVDAL loop is authoritative in this repo (the canonical WIRING §9
encodes the same); roles (which flagship runs) and phases (pipeline position) are
orthogonal.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, replace
from enum import Enum
from os import environ
from pathlib import Path
from typing import Any, Callable, Mapping


class Role(str, Enum):
    """Which flagship serves a class of work — not where it sits in the loop."""

    DATA_CAUSAL = "data_causal"  # data science, strategy, causal inference (SENSE/REASON/DECIDE cells)
    CODING_ARCH = "coding_arch"  # coding & software architecture (Boss Agent, codegen)
    CREATIVE_MM = "creative_mm"  # creative direction, multimodal generation
    DEVOPS_OPS = "devops_ops"  # devops, deploy, operations


# The seven-phase SRPVDAL loop is authoritative (matches the JourneyEvent
# provenance spec; two phases more than the platform skill's five-phase SRDAL).
SRPVDAL_PHASES = ("sense", "reason", "plan", "validate", "decide", "act", "learn")

# Cross-vendor failover target for every role. Deliberately crosses the in-family
# lock — availability beats the lock for the backup path only (Boss directive
# 2026-06-26). CODING_ARCH legitimately shares this string; its failover is a
# no-op re-raise.
GLOBAL_FALLBACK = "claude-opus-4-8"
GLOBAL_FALLBACK_VENDOR = "anthropic"

# Gemini 3.5 Flash auto-flip — GA confirmed on Vertex 2026-07-04, flag flipped True
# in the canonical registry. Boss directive 2026-07-04: DATA_CAUSAL's flip target is
# the FLASH tier (not 3.5 Pro) — an explicit cost/latency choice that overrides
# "capability over cost" for this one role. Env VIRTUOSO_GEMINI_35_FLASH_GA=1 also
# forces it on; clearing the constant reverts to the gemini-3.1-pro-preview base.
GEMINI_35_FLASH_IS_GA = True
GEMINI_35_FLASH_STRING = "gemini-3.5-flash"
GEMINI_GA_FLAG = "VIRTUOSO_GEMINI_35_FLASH_GA"

ENV_OVERRIDE_PREFIX = "VIRTUOSO_MODEL_"


@dataclass(frozen=True)
class ModelSpec:
    role: Role
    model: str  # exact API model string (the PRIMARY)
    vendor: str
    endpoint: str
    api_key_env: str
    effort_param: str
    effort_default: str
    exposes_reasoning_summary: bool  # usable for MII distillation capture
    srpvdal_stages: tuple[str, ...]
    notes: str
    forbidden_legacy: tuple[str, ...] = ()
    # In-family upgrade target announced but gated on a GA flag. Cross-vendor is
    # NOT allowed here — this is the in-family successor only.
    pending_upgrade: str | None = None
    source: str = "registry"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "model": self.model,
            "vendor": self.vendor,
            "endpoint": self.endpoint,
            "api_key_env": self.api_key_env,
            "effort_param": self.effort_param,
            "effort_default": self.effort_default,
            "exposes_reasoning_summary": self.exposes_reasoning_summary,
            "srpvdal_stages": list(self.srpvdal_stages),
            "notes": self.notes,
            "pending_upgrade": self.pending_upgrade,
            "source": self.source,
            "global_fallback": GLOBAL_FALLBACK,
        }


REGISTRY: dict[Role, ModelSpec] = {
    Role.DATA_CAUSAL: ModelSpec(
        role=Role.DATA_CAUSAL,
        model="gemini-3.1-pro-preview",
        vendor="google",
        endpoint="https://aiplatform.googleapis.com",  # Vertex AI; location=global
        api_key_env="GEMINI_API_KEY",
        effort_param="thinking_level",
        effort_default="high",
        exposes_reasoning_summary=False,  # thought signatures are ENCRYPTED — not distillable
        srpvdal_stages=("sense", "reason", "decide"),
        notes=(
            "Extraction + causal cells (incl. Cell 26/27 X-/DR-Learner framing prompts). "
            "Resolves to gemini-3.5-flash while the GA flag is on (Boss directive "
            "2026-07-04: Flash tier, an explicit cost/latency choice). "
            "Global fallback: claude-opus-4-8 (cross-vendor)."
        ),
        forbidden_legacy=(
            "gemini-2.0-flash",  # SHUTDOWN 2026-06-01
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite-001",
            "gemini-3-pro-preview",  # shut down 2026-03-09, silently aliased
            "gemini-2.5-flash",  # cost-tier: barred by capability-over-cost rule
            "gemini-2.5-flash-lite",
        ),
        pending_upgrade=GEMINI_35_FLASH_STRING,
    ),
    Role.CODING_ARCH: ModelSpec(
        role=Role.CODING_ARCH,
        model="claude-opus-4-8",
        vendor="anthropic",
        endpoint="https://api.anthropic.com",
        api_key_env="ANTHROPIC_API_KEY",
        effort_param="effort",
        effort_default="xhigh",
        exposes_reasoning_summary=True,  # richest MII signal
        srpvdal_stages=("plan", "act"),
        notes=(
            "Boss Agent / codegen / architecture. This is also the GLOBAL FALLBACK "
            "model; on this role the primary and fallback are the same, so failover "
            "is a no-op re-raise."
        ),
        forbidden_legacy=(
            "claude-opus-4-6-20260201",
            "claude-opus-4-6",
            "claude-opus-4-7",
        ),
    ),
    Role.CREATIVE_MM: ModelSpec(
        role=Role.CREATIVE_MM,
        model="gpt-5.5",
        vendor="openai",
        endpoint="https://api.openai.com",
        api_key_env="OPENAI_API_KEY",
        effort_param="reasoning.effort",
        effort_default="high",
        exposes_reasoning_summary=True,
        srpvdal_stages=("act",),
        notes=(
            "Creative direction & asset generation; image work delegates to "
            "IMAGE_MODELS. Global fallback: claude-opus-4-8 (cross-vendor)."
        ),
        forbidden_legacy=(
            "gpt-5.2-chat-latest",  # deprecated 2026-05-08
            "gpt-5.3-chat-latest",
            "gpt-5.2",
            "chatgpt-5.2",
        ),
    ),
    Role.DEVOPS_OPS: ModelSpec(
        role=Role.DEVOPS_OPS,
        model="grok-4.3",
        vendor="xai",
        endpoint="https://api.x.ai",
        api_key_env="XAI_API_KEY",
        effort_param="reasoning_effort",
        effort_default="high",  # incident/deploy reasoning: never default-low
        exposes_reasoning_summary=True,
        srpvdal_stages=("act", "learn"),
        notes=(
            "Deploy / incident / ops agents. Retired 4.1/4-fast slugs silently "
            "redirect here at LOW effort — pin the string AND the effort. "
            "Global fallback: claude-opus-4-8 (cross-vendor)."
        ),
        forbidden_legacy=(
            "grok-4-1-fast-reasoning",  # retired 2026-05-15, silent redirect
            "grok-4-1-fast-non-reasoning",
            "grok-4-fast-reasoning",
            "grok-4-fast-non-reasoning",
            "grok-4-0709",
            "grok-code-fast-1",
            "grok-3",
        ),
    ),
}

# Image-generation strings (Creative role delegates to these; Imagen shut down
# 2026-06-24, the *-preview strings shut down 2026-06-25):
IMAGE_MODELS = {
    "google_flagship": "gemini-3-pro-image",  # Nano Banana Pro (GA string)
    "google_fast": "gemini-3.1-flash-image",  # Nano Banana 2 (GA string)
}
FORBIDDEN_IMAGE_LEGACY = (
    "imagen-4.0-generate-001",
    "imagen-4.0-ultra-generate-001",
    "imagen-4.0-fast-generate-001",
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
)


def all_forbidden_strings() -> tuple[str, ...]:
    return FORBIDDEN_IMAGE_LEGACY + tuple(
        legacy for spec in REGISTRY.values() for legacy in spec.forbidden_legacy
    )


def find_legacy_strings(text: str) -> list[str]:
    """Return every retired model string present in ``text`` (deduped)."""
    return [legacy for legacy in dict.fromkeys(all_forbidden_strings()) if legacy in (text or "")]


def assert_no_legacy_strings(text: str | None = None, source: str = "config") -> None:
    """Startup guard: refuse to boot if a retired string sneaks back in.

    With ``text`` given, scans that config blob. With no args, self-audits the
    live registry — every string it would actually serve (resolved primaries +
    image models) must itself be clean.
    """
    if text is None:
        resolved = [get_model(role).model for role in Role] + list(IMAGE_MODELS.values())
        text = " ".join(resolved)
        source = "registry:self-audit"
    violations = find_legacy_strings(text)
    if violations:
        raise ValueError(
            f"retired model string(s) {violations} found in {source}; "
            "these are shut down or silently redirected — replace with a "
            "get_model(Role.X).model lookup"
        )


def _gemini_35_flash_is_ga(env: Mapping[str, str]) -> bool:
    return GEMINI_35_FLASH_IS_GA or env.get(GEMINI_GA_FLAG) == "1"


def get_model(role: Role, env: Mapping[str, str] | None = None) -> ModelSpec:
    """Resolve the active PRIMARY for a role: env override > GA auto-flip > base.

    Overrides (``VIRTUOSO_MODEL_<ROLE>``) are rejected if they contain a retired
    string, so a legacy id can never be reintroduced through configuration.
    Stateless: returns a resolved copy; the REGISTRY entry is never mutated, so
    flips/overrides revert cleanly when their condition goes away.
    """
    source = environ if env is None else env
    spec = REGISTRY[role]
    override = (source.get(f"{ENV_OVERRIDE_PREFIX}{role.name}") or "").strip()
    if override:
        assert_no_legacy_strings(override, source=f"{ENV_OVERRIDE_PREFIX}{role.name}")
        return replace(spec, model=override, source="env")
    if spec.pending_upgrade and role is Role.DATA_CAUSAL and _gemini_35_flash_is_ga(source):
        return replace(spec, model=spec.pending_upgrade, source="ga-flip")
    return spec


def assert_fallback_not_primary(role: Role, env: Mapping[str, str] | None = None) -> ModelSpec:
    """A non-Anthropic role whose primary resolves to the fallback string is a
    misconfiguration — it would mask an outage as 'normal'. Runs on every call."""
    resolved = get_model(role, env)
    if resolved.vendor != GLOBAL_FALLBACK_VENDOR and resolved.model == GLOBAL_FALLBACK:
        raise ValueError(
            f"role {role.value} primary resolved to the global fallback "
            f"({GLOBAL_FALLBACK}) but its vendor is '{resolved.vendor}'; a fallback "
            f"must never silently become the primary — fix the "
            f"{ENV_OVERRIDE_PREFIX}{role.name} override"
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
        snapshot["image_models"] = dict(IMAGE_MODELS)
        snapshot["srpvdal_phases"] = list(SRPVDAL_PHASES)
        snapshot["phase_note"] = (
            "seven-phase SRPVDAL is authoritative; roles (which flagship runs) and "
            "phases (pipeline position) are orthogonal"
        )
        snapshot["forbidden_legacy_strings"] = list(dict.fromkeys(all_forbidden_strings()))
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
