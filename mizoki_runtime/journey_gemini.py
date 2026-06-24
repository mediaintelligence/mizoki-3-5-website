"""Optional Gemini strict-schema extraction connector for JourneyEvents.

Turns an unstructured/raw signal into a canonical JourneyEvent by calling Gemini
with a pinned model + API revision and the served ``journey-event.json`` as a
strict ``response_format`` json_schema, then threading the model provenance
(``model_version``/``request_id``/``prompt_hash``/``response_schema_hash``)
through ``JourneyEventNormalizer.assemble_from_extraction`` so the result is
audit-identical in shape to the rule-based connectors.

Kept dependency-free and testable:
- the HTTP call uses the **standard library** (``urllib.request``) — no new pip
  deps — and only fires when a ``GEMINI_API_KEY`` is configured;
- a ``transport`` callable can be injected to exercise the full parse ->
  provenance -> canonicalize path deterministically, with no network.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Callable

from .journey import JourneyEventNormalizer, sha256_hex


# Pinned defaults — override via env so a deployment can bump the model/revision
# without a code change (and the pin is recorded in provenance per row).
DEFAULT_GEMINI_MODEL = "gemini-2.0-pro-exp-02-05"
DEFAULT_GEMINI_API_REVISION = "2026-06-01"
DEFAULT_VERTEX_LOCATION = "us-central1"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


Transport = Callable[[str, dict[str, str], bytes], dict[str, Any]]


class GeminiJourneyExtractor:
    def __init__(
        self,
        normalizer: JourneyEventNormalizer,
        *,
        model: str | None = None,
        api_revision: str | None = None,
        api_key: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.normalizer = normalizer
        self.model = model or os.environ.get("MIZOKI_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        self.api_revision = api_revision or os.environ.get("MIZOKI_GEMINI_API_REVISION") or DEFAULT_GEMINI_API_REVISION
        self.api_key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY")
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key) or self._transport is not None

    def build_request_body(self, prompt_text: str) -> dict[str, Any]:
        return {
            "model_version": self.model,
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.9,
                "responseMimeType": "application/json",
            },
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "JourneyEvent", "schema": self.normalizer.schema.schema},
                "strict": True,
            },
            "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
        }

    def _call(self, prompt_text: str) -> dict[str, Any]:
        body = json.dumps(self.build_request_body(prompt_text)).encode("utf-8")
        url = GEMINI_ENDPOINT.format(model=self.model, key=self.api_key or "")
        headers = {"Content-Type": "application/json", "X-Api-Revision": self.api_revision}
        if self._transport is not None:
            return self._transport(url, headers, body)
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set; cannot call Gemini")
        import urllib.request  # lazy: only when actually calling out

        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request) as response:  # noqa: S310 - pinned Google endpoint
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or [{}]
        content = (candidates[0] or {}).get("content") or {}
        parts = content.get("parts") or [{}]
        return parts[0].get("text") or "{}"

    def _model_provenance(self, data: dict[str, Any], prompt_text: str) -> dict[str, Any]:
        usage = data.get("usageMetadata") or {}
        return {
            "model_version": data.get("modelVersion") or self.model,
            "request_id": data.get("responseId") or data.get("requestId") or usage.get("requestId"),
            "prompt_hash": sha256_hex(prompt_text),
            "raw_uri": data.get("modelUri"),
        }

    def extract(self, prompt_text: str, *, event_source: str = "other") -> dict[str, Any]:
        data = self._call(prompt_text)
        extracted = json.loads(self._extract_text(data))
        provenance = self._model_provenance(data, prompt_text)
        result = self.normalizer.assemble_from_extraction(
            extracted,
            event_source=event_source,
            prompt=prompt_text,
            model_version=provenance["model_version"],
            request_id=provenance["request_id"],
            raw_response=json.dumps(extracted, sort_keys=True),
        )
        result["model_provenance"] = provenance
        return result


def gemini_extractor_metadata(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Discovery metadata for the optional Gemini extractor (no client built)."""
    source = os.environ if env is None else env
    return {
        "provider": "google-gemini",
        "model": source.get("MIZOKI_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
        "api_revision": source.get("MIZOKI_GEMINI_API_REVISION") or DEFAULT_GEMINI_API_REVISION,
        "strict_response_format": True,
        "configured": bool((source.get("GEMINI_API_KEY") or "").strip()),
    }


def _resolve_vertex_project(env: dict[str, str]) -> str:
    for key in ("MIZOKI_GEMINI_PROJECT", "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT_ID", "GCP_PROJECT"):
        value = (env.get(key) or "").strip()
        if value:
            return value
    return ""


def to_vertex_response_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Project a JSON Schema onto the subset Vertex controlled-generation accepts.

    Vertex's ``response_schema`` is an OpenAPI-style subset: it has no ``$schema``/
    ``$id``/``additionalProperties`` and expresses nullability via ``nullable`` rather
    than a ``["T","null"]`` type union. This rewrites those so the served
    ``journey-event.json`` can drive Vertex strict generation; the in-process
    validator remains the authoritative gate regardless.
    """
    if not isinstance(schema, dict):
        return schema
    result: dict[str, Any] = {}
    for key, value in schema.items():
        if key in ("$schema", "$id", "additionalProperties"):
            continue
        if key == "type" and isinstance(value, list):
            non_null = [item for item in value if item != "null"]
            result["type"] = non_null[0] if non_null else "string"
            if "null" in value:
                result["nullable"] = True
            continue
        if key == "properties" and isinstance(value, dict):
            result["properties"] = {name: to_vertex_response_schema(sub) for name, sub in value.items()}
            continue
        if key == "items":
            result["items"] = to_vertex_response_schema(value)
            continue
        result[key] = value
    return result


class VertexGeminiJourneyExtractor:
    """Gemini extraction via Vertex AI using Application Default Credentials.

    On Cloud Run this authenticates with the attached service account (which needs
    ``roles/aiplatform.user``) — no API key. Uses the ``google-genai`` SDK, imported
    lazily so importing this module never requires the dependency, and accepts an
    injected ``client`` so the parse -> provenance -> canonicalize path is unit-tested
    with no SDK and no network.
    """

    def __init__(
        self,
        normalizer: JourneyEventNormalizer,
        *,
        model: str | None = None,
        project: str | None = None,
        location: str | None = None,
        client: Any = None,
    ) -> None:
        self.normalizer = normalizer
        self.model = model or os.environ.get("MIZOKI_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        self.project = project if project is not None else _resolve_vertex_project(os.environ)
        self.location = location or os.environ.get("MIZOKI_GEMINI_LOCATION") or DEFAULT_VERTEX_LOCATION
        self._client = client

    @property
    def configured(self) -> bool:
        return self._client is not None or bool(self.project)

    def _resolve_client(self) -> Any:
        if self._client is None:
            if not self.project:
                raise RuntimeError("Vertex project is not configured (set MIZOKI_GEMINI_PROJECT or GOOGLE_CLOUD_PROJECT)")
            from google import genai  # lazy: optional dependency (google-genai)

            self._client = genai.Client(vertexai=True, project=self.project, location=self.location)
        return self._client

    def build_config(self) -> dict[str, Any]:
        # google-genai accepts a plain dict for `config`; keep it dict-only so the
        # injected-client test path needs no SDK import.
        return {
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 40,
            "response_mime_type": "application/json",
            "response_schema": to_vertex_response_schema(deepcopy(self.normalizer.schema.schema)),
        }

    def extract(self, prompt_text: str, *, event_source: str = "other") -> dict[str, Any]:
        client = self._resolve_client()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt_text,
            config=self.build_config(),
        )
        extracted = json.loads(getattr(response, "text", None) or "{}")
        provenance = {
            "model_version": getattr(response, "model_version", None) or self.model,
            "request_id": getattr(response, "response_id", None),
            "prompt_hash": sha256_hex(prompt_text),
            "raw_uri": f"vertex://{self.project}/{self.location}/{self.model}",
        }
        result = self.normalizer.assemble_from_extraction(
            extracted,
            event_source=event_source,
            prompt=prompt_text,
            model_version=provenance["model_version"],
            request_id=provenance["request_id"],
            raw_response=json.dumps(extracted, sort_keys=True),
        )
        result["model_provenance"] = provenance
        return result


def vertex_extractor_metadata(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Discovery metadata for the Vertex (google-genai) extractor (no client built)."""
    source = os.environ if env is None else env
    project = _resolve_vertex_project(source)
    return {
        "provider": "google-vertex-ai",
        "auth": "application-default-credentials",
        "model": source.get("MIZOKI_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
        "location": source.get("MIZOKI_GEMINI_LOCATION") or DEFAULT_VERTEX_LOCATION,
        "strict_response_format": True,
        "configured": bool(project),
    }
