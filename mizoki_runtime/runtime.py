from __future__ import annotations

import html
import json
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .envelope import CanonicalEnvelopeBuilder
from .google_ads_gaql import GOOGLE_ADS_CELL_ID, GoogleAdsCompatibilityCell
from .identity import IdentityResolutionCell
from .journey import JourneyIngestCell
from .journey_gemini import active_extractor_metadata
from .journey_sinks import build_journey_sinks_from_env
from .virtuoso import VirtuosoModelPlane


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "the",
    "this",
    "to",
    "what",
    "with",
}

SUPPORTED_PARAMETER_TYPES = {"string", "integer", "number", "boolean", "array", "object"}


def _normalize_tokens(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return [token for token in tokens if token not in STOP_WORDS]


def _contains_phrase(value: str, phrase: str) -> bool:
    words = re.findall(r"[a-z0-9]+", phrase.lower())
    if not words:
        return False
    pattern = r"\b" + r"[\W_]+".join(re.escape(word) for word in words) + r"\b"
    return bool(re.search(pattern, value.lower()))


def _contains_any_phrase(value: str, phrases: tuple[str, ...] | list[str]) -> bool:
    return any(_contains_phrase(value, phrase) for phrase in phrases)


def _strip_markup(raw_text: str) -> str:
    without_blocks = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_text)
    without_tags = re.sub(r"(?s)<[^>]+>", " ", without_blocks)
    collapsed = re.sub(r"\s+", " ", html.unescape(without_tags)).strip()
    return collapsed


def _load_json_list(file_path: Path, label: str) -> list[Any]:
    if not file_path.exists():
        return []
    raw_payload = file_path.read_text(encoding="utf-8").strip()
    if not raw_payload:
        return []
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} file is not valid JSON: {file_path}") from exc
    if not isinstance(payload, list):
        raise RuntimeError(f"{label} file must contain a JSON array: {file_path}")
    return payload


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty")
    return cleaned


def _require_bounded_integer(
    value: Any,
    field_name: str,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{field_name} must be at most {maximum}")
    return value


def _clean_string_list(values: Any, field_name: str, minimum: int = 0) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be an array of strings")

    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must contain only strings")
        normalized = value.strip()
        if not normalized:
            continue
        dedupe_key = normalized.casefold()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        cleaned.append(normalized)

    if len(cleaned) < minimum:
        raise ValueError(f"{field_name} must contain at least {minimum} non-empty string(s)")
    return cleaned


def _extract_quoted_phrases(value: str) -> list[str]:
    matches = re.findall(r'"([^"]+)"|\'([^\']+)\'', value)
    return [first or second for first, second in matches if (first or second).strip()]


def _titleize_phrase(value: str, suffix: str = "") -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        return suffix or "Generated"
    title = " ".join(word.capitalize() for word in words[:6])
    if suffix and not title.endswith(suffix):
        return f"{title} {suffix}".strip()
    return title


def _coerce_value(expected_type: str, value: Any) -> Any:
    if expected_type == "string":
        if isinstance(value, str):
            return value
        return str(value)
    if expected_type == "integer":
        if isinstance(value, bool):
            raise ValueError("boolean cannot be coerced to integer")
        return int(value)
    if expected_type == "number":
        if isinstance(value, bool):
            raise ValueError("boolean cannot be coerced to number")
        return float(value)
    if expected_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
        raise ValueError(f"cannot coerce {value!r} to boolean")
    if expected_type == "array":
        if isinstance(value, list):
            return value
        raise ValueError(f"expected array, received {type(value).__name__}")
    if expected_type == "object":
        if isinstance(value, dict):
            return value
        raise ValueError(f"expected object, received {type(value).__name__}")
    raise ValueError(f"unsupported parameter type: {expected_type}")


@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None

    def __post_init__(self) -> None:
        if self.type not in SUPPORTED_PARAMETER_TYPES:
            raise ValueError(f"unsupported parameter type: {self.type}")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            payload["default"] = deepcopy(self.default)
        return payload

    def to_json_schema(self) -> dict[str, Any]:
        payload = {
            "type": self.type,
            "description": self.description,
        }
        if self.default is not None:
            payload["default"] = deepcopy(self.default)
        return payload


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: str
    parameters: tuple[ToolParameter, ...] = ()
    tags: tuple[str, ...] = ()
    handler: Callable[[dict[str, Any]], dict[str, Any]] | None = field(default=None, repr=False)
    alias_target: str | None = None
    default_arguments: dict[str, Any] = field(default_factory=dict)

    def argument_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {parameter.name: parameter.to_json_schema() for parameter in self.parameters},
            "additionalProperties": False,
        }
        required = [parameter.name for parameter in self.parameters if parameter.required]
        if required:
            schema["required"] = required
        return schema

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "argument_schema": self.argument_schema(),
            "tags": list(self.tags),
            "kind": "alias" if self.alias_target else "tool",
        }
        if self.alias_target:
            payload["alias_target"] = self.alias_target
            if self.default_arguments:
                payload["default_arguments"] = deepcopy(self.default_arguments)
        return payload


@dataclass(frozen=True)
class SiteDocument:
    document_id: str
    path: str
    title: str
    summary: str
    topics: tuple[str, ...]
    entities: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class LearnedSkill:
    name: str
    description: str
    trigger_phrases: tuple[str, ...]
    preferred_tools: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger_phrases": list(self.trigger_phrases),
            "preferred_tools": list(self.preferred_tools),
            "examples": list(self.examples),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearnedSkill":
        return cls(
            name=payload["name"],
            description=payload["description"],
            trigger_phrases=tuple(payload.get("trigger_phrases", [])),
            preferred_tools=tuple(payload.get("preferred_tools", [])),
            examples=tuple(payload.get("examples", [])),
            created_at=float(payload.get("created_at", time.time())),
        )


@dataclass(frozen=True)
class ToolSelection:
    tool_name: str
    confidence: float
    reasons: tuple[str, ...]
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "arguments": self.arguments,
        }


DOCUMENT_SPECS = (
    {
        "document_id": "home",
        "path": "index.html",
        "title": "Homepage",
        "summary": "Overview of the SRPVDAL loop, decision control plane, and governed autonomy.",
        "topics": ("decision intelligence", "boss agent", "knowledge graph", "decision control plane"),
        "entities": ("boss_agent", "srpvdal", "decision_control_plane", "knowledge_graph"),
    },
    {
        "document_id": "how_it_works",
        "path": "how-it-works.html",
        "title": "How It Works",
        "summary": "Deep dive on the seven-stage pipeline, GraphRAG, validation, and learning.",
        "topics": ("pipeline", "graphrag", "validation", "learning"),
        "entities": (
            "srpvdal",
            "graphrag",
            "knowledge_graph",
            "decision_control_plane",
            "validation_arbitration",
            "counterfactual_simulation",
        ),
    },
    {
        "document_id": "platform",
        "path": "platform.html",
        "title": "Platform Architecture",
        "summary": "Architecture page describing the graph, reasoning, orchestration, and learning layers.",
        "topics": ("platform", "architecture", "graph", "orchestration"),
        "entities": (
            "boss_agent",
            "mcp_server",
            "graphrag",
            "knowledge_graph",
            "decision_control_plane",
            "skills_memory",
        ),
    },
    {
        "document_id": "security",
        "path": "security.html",
        "title": "Security",
        "summary": "Security and governance posture with auditability and policy controls.",
        "topics": ("security", "governance", "auditability"),
        "entities": ("decision_control_plane", "validation_arbitration", "skills_memory"),
    },
    {
        "document_id": "resources",
        "path": "resources.html",
        "title": "Resources",
        "summary": "Resource hub covering the SRPVDAL pipeline, GraphRAG, and knowledge graph materials.",
        "topics": ("resources", "knowledge graph", "graphrag", "pipeline"),
        "entities": ("srpvdal", "graphrag", "knowledge_graph", "decision_control_plane"),
    },
    {
        "document_id": "investor",
        "path": "investor.html",
        "title": "Investor Overview",
        "summary": "Investor framing for the platform, including GraphRAG, governance, and the DCP.",
        "topics": ("investor", "governance", "graphrag"),
        "entities": ("boss_agent", "graphrag", "decision_control_plane"),
    },
    {
        "document_id": "blog_dcp",
        "path": "blog/decision-control-plane.html",
        "title": "Decision Control Plane Article",
        "summary": "Article explaining why agents need centralized decision authorization.",
        "topics": ("decision control plane", "agents", "governance"),
        "entities": ("boss_agent", "decision_control_plane", "validation_arbitration"),
    },
    {
        "document_id": "blog_relu",
        "path": "blog/relu-lens-meta-algorithm.html",
        "title": "ReLU Lens Article",
        "summary": "Article connecting causal learning, thresholds, and knowledge graph memory in media systems.",
        "topics": ("causal learning", "media optimization", "knowledge graph"),
        "entities": ("knowledge_graph", "learn", "reason"),
    },
    {
        "document_id": "readme",
        "path": "README.md",
        "title": "Repository README",
        "summary": "Repository-level deployment and platform notes.",
        "topics": ("deployment", "boss agent", "mcp"),
        "entities": ("boss_agent", "mcp_server", "srpvdal"),
    },
    {
        "document_id": "claude",
        "path": "CLAUDE.md",
        "title": "Assistant Context",
        "summary": "Assistant-oriented overview of the platform and repository structure.",
        "topics": ("assistant", "boss agent", "mcp"),
        "entities": ("boss_agent", "mcp_server", "srpvdal", "graphrag"),
    },
)


GRAPH_NODES = {
    "boss_agent": {
        "name": "Boss Agent",
        "type": "agent",
        "summary": "Primary orchestrator that discovers tools, learns reusable skills, and routes work through the SRPVDAL loop.",
        "aliases": ("boss", "orchestrator", "control plane orchestrator"),
    },
    "mcp_server": {
        "name": "MCP Server",
        "type": "service",
        "summary": "Model Context Protocol compatible tool surface exposing registered tools with schemas and validated execution.",
        "aliases": ("mcp", "tool server", "tool registry"),
    },
    "tool_registry": {
        "name": "Tool Registry",
        "type": "service",
        "summary": "Validated catalog of tools, parameters, aliases, and categories used by the Boss Agent.",
        "aliases": ("registry", "tools"),
    },
    "skills_memory": {
        "name": "Skills Memory",
        "type": "memory",
        "summary": "Persistent store of learned skills, trigger phrases, and preferred tools for future routing decisions.",
        "aliases": ("skills", "skill memory", "learned skills"),
    },
    "graphrag": {
        "name": "GraphRAG",
        "type": "retrieval",
        "summary": "Graph-aware retrieval layer that grounds answers in site documents and related graph entities.",
        "aliases": ("graph rag", "causal graphrag", "retrieval"),
    },
    "knowledge_graph": {
        "name": "Knowledge Graph",
        "type": "graph",
        "summary": "Shared memory and relationship model connecting platform concepts, documents, and decision traces.",
        "aliases": ("kg", "graph", "tco kg"),
    },
    "decision_control_plane": {
        "name": "Decision Control Plane",
        "type": "governance",
        "summary": "Central authority that authorizes, rejects, defers, or escalates proposed actions before execution.",
        "aliases": ("dcp", "control plane", "decision plane"),
    },
    "verification_arbitration": {
        "name": "Verification & Arbitration Layer",
        "type": "governance",
        "summary": "Planner, verifier, risk, and policy evaluation layer that challenges actions before they are approved.",
        "aliases": ("verification layer", "arbitration", "verifier"),
    },
    "counterfactual_simulation": {
        "name": "Counterfactual Simulation Engine",
        "type": "simulation",
        "summary": "Simulation layer used to compare proposed actions, alternatives, and no-action baselines.",
        "aliases": ("simulation", "counterfactual", "what if"),
    },
    "srpvdal": {
        "name": "SRPVDAL Loop",
        "type": "pipeline",
        "summary": "Sense, Reason, Plan, Verify, Decide, Act, Learn workflow for governed autonomous decisions.",
        "aliases": ("sensed reason plan verify decide act learn", "pipeline", "loop"),
    },
    "sense": {
        "name": "Sense",
        "type": "stage",
        "summary": "Collect signals, events, and context before graph enrichment.",
        "aliases": ("observe", "ingest"),
    },
    "reason": {
        "name": "Reason",
        "type": "stage",
        "summary": "Traverse graph relationships and evidence to identify drivers and explanations.",
        "aliases": ("analyze", "reasoning"),
    },
    "plan": {
        "name": "Plan",
        "type": "stage",
        "summary": "Generate candidate actions and execution options grounded in the graph.",
        "aliases": ("planning", "options"),
    },
    "verify": {
        "name": "Verify",
        "type": "stage",
        "summary": "Challenge plans against policies, graph constraints, and simulation outcomes.",
        "aliases": ("verify", "verification"),
    },
    "decide": {
        "name": "Decide",
        "type": "stage",
        "summary": "Select the governed action or escalation path through the DCP.",
        "aliases": ("decision", "authorize"),
    },
    "act": {
        "name": "Act",
        "type": "stage",
        "summary": "Execute the chosen action or route it to the correct human or system.",
        "aliases": ("execute", "action"),
    },
    "learn": {
        "name": "Learn",
        "type": "stage",
        "summary": "Persist outcomes, traces, and skill refinements so the next decision improves.",
        "aliases": ("feedback", "learning"),
    },
    "journey_event": {
        "name": "JourneyEvent Schema",
        "type": "schema",
        "summary": "Canonical event shape that normalizes Meta, Google Ads, SendGrid, and OpenRTB signals into one record so every connector enters SRPVDAL deterministically and idempotently at the SENSE stage.",
        "aliases": ("journey event", "canonical event", "event schema", "journeyevent"),
    },
    "journey_ingest": {
        "name": "Journey Ingest Cell",
        "type": "cell",
        "summary": "SENSE-stage connector layer that maps native Meta/Google Ads/SendGrid/OpenRTB payloads to the JourneyEvent schema, validates them against the schema gate, and upserts them idempotently on a stable event_id with full provenance.",
        "aliases": ("journey ingest", "event normalizer", "connector layer", "sense connectors"),
    },
    "virtuoso_model_plane": {
        "name": "Virtuoso Model Plane",
        "type": "registry",
        "summary": "Role-based flagship-model registry consolidated with the Boss Agent: every cell resolves its model through get_model(Role.X), retired model strings are rejected at boot, and every role fails over to one cross-vendor global fallback with served_by/primary_error surfaced so a degraded path is never silent.",
        "aliases": ("virtuoso", "model registry", "model plane", "flagship registry", "virtuoso models"),
    },
}


GRAPH_EDGES = (
    ("boss_agent", "uses", "mcp_server"),
    ("boss_agent", "discovers", "tool_registry"),
    ("boss_agent", "learns_from", "skills_memory"),
    ("boss_agent", "queries", "knowledge_graph"),
    ("boss_agent", "enriches_with", "graphrag"),
    ("boss_agent", "operates_within", "decision_control_plane"),
    ("mcp_server", "exposes", "tool_registry"),
    ("mcp_server", "supports", "boss_agent"),
    ("tool_registry", "contains", "graphrag"),
    ("tool_registry", "contains", "knowledge_graph"),
    ("skills_memory", "improves", "boss_agent"),
    ("graphrag", "grounded_in", "knowledge_graph"),
    ("knowledge_graph", "supports", "reason"),
    ("reason", "feeds", "plan"),
    ("plan", "feeds", "verify"),
    ("verify", "feeds", "decide"),
    ("decide", "governed_by", "decision_control_plane"),
    ("decide", "feeds", "act"),
    ("act", "feeds", "learn"),
    ("learn", "updates", "knowledge_graph"),
    ("verify", "uses", "verification_arbitration"),
    ("verify", "uses", "counterfactual_simulation"),
    ("srpvdal", "contains", "sense"),
    ("srpvdal", "contains", "reason"),
    ("srpvdal", "contains", "plan"),
    ("srpvdal", "contains", "verify"),
    ("srpvdal", "contains", "decide"),
    ("srpvdal", "contains", "act"),
    ("srpvdal", "contains", "learn"),
    ("journey_ingest", "normalizes_to", "journey_event"),
    ("journey_ingest", "feeds", "sense"),
    ("journey_ingest", "validated_by", "verification_arbitration"),
    ("journey_event", "feeds", "sense"),
    ("boss_agent", "resolves_models_through", "virtuoso_model_plane"),
    ("virtuoso_model_plane", "serves", "srpvdal"),
    ("journey_ingest", "stamps_provenance_from", "virtuoso_model_plane"),
    ("virtuoso_model_plane", "governed_by", "decision_control_plane"),
)

GRAPH_NATIVE_STAGE_ORDER = ("sense", "reason", "plan", "verify", "decide", "act", "learn")

GRAPH_NATIVE_STAGE_KEYWORDS = {
    "sense": ("sense", "observe", "ingest", "signal", "context"),
    "reason": ("reason", "analyze", "diagnose", "why", "causal"),
    "plan": ("plan", "strategy", "option", "roadmap"),
    "verify": ("verify", "check", "guardrail", "policy"),
    "decide": ("decide", "decision", "authorize", "approve"),
    "act": ("act", "execute", "ship", "launch", "deploy"),
    "learn": ("learn", "feedback", "improve", "memory"),
}

GRAPH_NATIVE_SUBAGENTS = (
    {
        "subagent_id": "subagent.sense_graph",
        "stage": "sense",
        "name": "Sense Graph Cell",
        "responsibility": "Collect GraphRAG evidence, identify matching entities, and build the initial graph state.",
        "preferred_tools": ("gndi.inspect_context", "graphrag.query", "kg.describe_entity"),
        "triggers": ("sense", "context", "evidence", "signals", "graphrag"),
    },
    {
        "subagent_id": "subagent.reason_causal",
        "stage": "reason",
        "name": "Reason Causal Cell",
        "responsibility": "Traverse graph relationships and surface plausible drivers, dependencies, and explanations.",
        "preferred_tools": ("gndi.run_decision_loop", "kg.list_neighbors", "decision.explain_pipeline"),
        "triggers": ("reason", "causal", "why", "dependency", "explain"),
    },
    {
        "subagent_id": "subagent.plan_orchestrator",
        "stage": "plan",
        "name": "Plan Orchestrator Cell",
        "responsibility": "Turn evidence into graph-constrained candidate actions and tool chains.",
        "preferred_tools": ("gndi.run_decision_loop", "graphrag.query", "tools.list"),
        "triggers": ("plan", "strategy", "orchestrate", "next step", "tool chain"),
    },
    {
        "subagent_id": "subagent.verify_guard",
        "stage": "verify",
        "name": "Verify Guard Cell",
        "responsibility": "Stress-test plans against guardrails, evidence sufficiency, and counterfactual checks.",
        "preferred_tools": ("gndi.simulate_action", "gndi.run_decision_loop", "decision.recent_traces"),
        "triggers": ("verify", "simulate", "counterfactual", "risk", "policy"),
    },
    {
        "subagent_id": "subagent.decide_control_plane",
        "stage": "decide",
        "name": "Decision Control Plane Cell",
        "responsibility": "Select approve, defer, or escalate paths from the verified graph state.",
        "preferred_tools": ("gndi.run_decision_loop", "decision.explain_pipeline"),
        "triggers": ("decide", "authorize", "approve", "governance", "control plane"),
    },
    {
        "subagent_id": "subagent.learn_memory",
        "stage": "learn",
        "name": "Learn Memory Cell",
        "responsibility": "Distill traces into reusable knowledge, follow-up skills, and audit-ready memory.",
        "preferred_tools": ("gndi.recent_loops", "skills.learn", "decision.recent_traces"),
        "triggers": ("learn", "memory", "feedback", "trace", "improve"),
    },
)


class SiteCorpus:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.documents = self._load_documents()

    def _load_documents(self) -> list[SiteDocument]:
        documents: list[SiteDocument] = []
        for spec in DOCUMENT_SPECS:
            path = self.base_dir / spec["path"]
            if not path.exists():
                continue
            raw_text = path.read_text(encoding="utf-8")
            text = _strip_markup(raw_text if path.suffix == ".html" else raw_text)
            documents.append(
                SiteDocument(
                    document_id=spec["document_id"],
                    path=spec["path"],
                    title=spec["title"],
                    summary=spec["summary"],
                    topics=tuple(spec["topics"]),
                    entities=tuple(spec["entities"]),
                    text=text,
                )
            )
        return documents

    def search(self, query: str, top_k: int = 3) -> dict[str, Any]:
        tokens = _normalize_tokens(query)
        matches: list[dict[str, Any]] = []
        for document in self.documents:
            title_tokens = set(_normalize_tokens(document.title))
            summary_tokens = set(_normalize_tokens(document.summary))
            topic_tokens = set(_normalize_tokens(" ".join(document.topics)))
            entity_tokens = set(_normalize_tokens(" ".join(document.entities)))
            body_tokens = _normalize_tokens(document.text[:8000])
            body_counter = {token: body_tokens.count(token) for token in set(body_tokens)}

            score = 0.0
            for token in tokens:
                if token in title_tokens:
                    score += 5
                if token in summary_tokens:
                    score += 4
                if token in topic_tokens or token in entity_tokens:
                    score += 3
                score += min(body_counter.get(token, 0), 4) * 0.5

            if score <= 0:
                continue

            snippet = document.summary
            for token in tokens:
                location = document.text.lower().find(token.lower())
                if location >= 0:
                    snippet = document.text[max(location - 80, 0): location + 180].strip()
                    break

            matches.append(
                {
                    "document_id": document.document_id,
                    "title": document.title,
                    "path": document.path,
                    "score": round(score, 2),
                    "summary": document.summary,
                    "snippet": snippet,
                    "entities": list(document.entities),
                }
            )

        matches.sort(key=lambda match: match["score"], reverse=True)
        return {
            "query": query,
            "matches": matches[:top_k],
        }


class KnowledgeGraph:
    def __init__(self, corpus: SiteCorpus) -> None:
        self._corpus = corpus
        self._nodes = GRAPH_NODES
        self._edges = GRAPH_EDGES

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def search_entities(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        tokens = _normalize_tokens(query)
        if not tokens:
            return []

        matches: list[dict[str, Any]] = []
        for entity_id, node in self._nodes.items():
            haystack = " ".join((node["name"], node["summary"], " ".join(node.get("aliases", ()))))
            entity_tokens = set(_normalize_tokens(haystack))
            score = 0.0
            for token in tokens:
                if token in entity_tokens:
                    score += 3
                if token == entity_id.replace("_", ""):
                    score += 2
            if score <= 0:
                continue
            matches.append(
                {
                    "entity_id": entity_id,
                    "name": node["name"],
                    "type": node["type"],
                    "summary": node["summary"],
                    "score": round(score, 2),
                }
            )

        matches.sort(key=lambda match: match["score"], reverse=True)
        return matches[:limit]

    def describe_entity(self, entity_id: str, include_neighbors: bool = False) -> dict[str, Any]:
        if entity_id not in self._nodes:
            raise ValueError(f"unknown entity: {entity_id}")
        node = self._nodes[entity_id]
        related_documents = [
            {
                "document_id": document.document_id,
                "title": document.title,
                "path": document.path,
            }
            for document in self._corpus.documents
            if entity_id in document.entities
        ]
        response = {
            "entity_id": entity_id,
            "name": node["name"],
            "type": node["type"],
            "summary": node["summary"],
            "aliases": list(node.get("aliases", ())),
            "related_documents": related_documents,
        }
        if include_neighbors:
            response["neighbors"] = self.list_neighbors(entity_id)["neighbors"]
        return response

    def list_neighbors(self, entity_id: str, relationship_type: str | None = None) -> dict[str, Any]:
        if entity_id not in self._nodes:
            raise ValueError(f"unknown entity: {entity_id}")

        neighbors: list[dict[str, Any]] = []
        for source, edge_type, target in self._edges:
            if relationship_type and relationship_type != edge_type:
                continue
            if source == entity_id:
                neighbors.append(
                    {
                        "relationship": edge_type,
                        "direction": "outbound",
                        "entity_id": target,
                        "name": self._nodes[target]["name"],
                    }
                )
            if target == entity_id:
                neighbors.append(
                    {
                        "relationship": edge_type,
                        "direction": "inbound",
                        "entity_id": source,
                        "name": self._nodes[source]["name"],
                    }
                )
        return {"entity_id": entity_id, "neighbors": neighbors}


class GraphNativeDecisionIntelligence:
    def __init__(self, corpus: SiteCorpus, knowledge_graph: KnowledgeGraph, trace_file: Path) -> None:
        self._corpus = corpus
        self._knowledge_graph = knowledge_graph
        self._trace_file = trace_file
        self._trace_file.parent.mkdir(parents=True, exist_ok=True)

    def list_subagents(self) -> list[dict[str, Any]]:
        return [deepcopy(subagent) for subagent in GRAPH_NATIVE_SUBAGENTS]

    def recent_loops(self, limit: int = 5) -> list[dict[str, Any]]:
        bounded_limit = _require_bounded_integer(limit, "limit", minimum=1, maximum=100)
        traces = self._load_traces()
        traces = traces[-bounded_limit:]
        traces.reverse()
        return traces

    def latest_loop(self) -> dict[str, Any] | None:
        loops = self._load_traces()
        return loops[-1] if loops else None

    def get_loop(self, trace_id: str) -> dict[str, Any]:
        cleaned_trace_id = _require_non_empty_string(trace_id, "trace_id")
        for trace in reversed(self._load_traces()):
            if trace.get("trace_id") == cleaned_trace_id:
                return trace
        raise ValueError(f"unknown trace_id: {cleaned_trace_id}")

    def build_context(self, intent: str, top_k: int = 3, constraints: list[str] | None = None) -> dict[str, Any]:
        cleaned_intent = _require_non_empty_string(intent, "intent")
        bounded_top_k = _require_bounded_integer(top_k, "top_k", minimum=1, maximum=10)
        cleaned_constraints = _clean_string_list(constraints or [], "constraints")
        stage_focus = self._detect_stage_focus(cleaned_intent)
        retrieval = self._corpus.search(cleaned_intent, top_k=bounded_top_k)
        matched_entities = self._knowledge_graph.search_entities(cleaned_intent, limit=5)

        graph_brief: list[dict[str, Any]] = []
        for entity in matched_entities[:3]:
            description = self._knowledge_graph.describe_entity(entity["entity_id"], include_neighbors=True)
            description["neighbors"] = description.get("neighbors", [])[:4]
            graph_brief.append(description)

        recommended_subagents = self._recommend_subagents(
            cleaned_intent,
            stage_focus,
            matched_entities,
            retrieval["matches"],
        )
        governance = self._build_governance_signals(
            cleaned_intent,
            cleaned_constraints,
            matched_entities,
            retrieval["matches"],
        )
        stage_path = [
            {
                "stage": stage,
                "entity_id": stage,
                "description": GRAPH_NODES[stage]["summary"],
            }
            for stage in GRAPH_NATIVE_STAGE_ORDER
        ]

        return {
            "intent": cleaned_intent,
            "constraints": cleaned_constraints,
            "stage_focus": stage_focus or "full_loop",
            "matched_entities": matched_entities,
            "retrieval": retrieval,
            "graph_brief": graph_brief,
            "recommended_subagents": recommended_subagents,
            "governance": governance,
            "stage_path": stage_path,
        }

    def simulate_action(
        self,
        intent: str,
        proposed_action: str = "",
        constraints: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        context = self.build_context(intent, top_k=top_k, constraints=constraints)
        candidates = self._build_candidate_actions(intent, "", proposed_action, context)
        proposed = self._simulate_candidate(candidates[0], context)
        baseline = self._simulate_candidate(candidates[1], context)
        delta = round(proposed["predicted_value"] - baseline["predicted_value"], 2)
        return {
            "context": context,
            "proposed": proposed,
            "baseline": baseline,
            "counterfactual_delta": delta,
            "recommendation": "proceed" if delta > 0 and not proposed["needs_review"] else "review",
        }

    def run_decision_loop(
        self,
        intent: str,
        goal: str = "",
        proposed_action: str = "",
        constraints: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        context = self.build_context(intent, top_k=top_k, constraints=constraints)
        candidates = self._build_candidate_actions(intent, goal, proposed_action, context)
        simulations = [self._simulate_candidate(candidate, context) for candidate in candidates]
        best_simulation = max(simulations, key=lambda item: (item["predicted_value"] - item["risk_score"], item["confidence"]))

        verify_metrics = {
            "policy_checks": context["governance"]["policy_checks"],
            "requires_review": any(simulation["needs_review"] for simulation in simulations),
            "approved_candidates": [
                simulation["candidate_id"] for simulation in simulations if not simulation["needs_review"]
            ],
            "blocked_candidates": [
                simulation["candidate_id"] for simulation in simulations if simulation["needs_review"]
            ],
        }
        if best_simulation["needs_review"]:
            decision_status = "needs_review"
        elif best_simulation["predicted_value"] >= 2.5:
            decision_status = "approved"
        else:
            decision_status = "deferred"

        act = {
            "status": decision_status,
            "chosen_candidate_id": best_simulation["candidate_id"],
            "recommended_tool_chain": best_simulation["tool_chain"],
            "assigned_subagents": [item["subagent_id"] for item in context["recommended_subagents"][:3]],
        }
        learn = {
            "trace_summary": self._build_trace_summary(intent, best_simulation, context),
            "recommended_skill_seed": self._build_skill_seed(intent, best_simulation, context),
            "knowledge_graph_updates": [
                f"link intent '{intent[:80]}' to stage '{context['stage_focus']}'",
                f"store decision status '{decision_status}' with {len(context['matched_entities'])} matched entities",
            ],
        }

        trace = {
            "trace_id": f"gndi-{int(time.time() * 1000)}",
            "timestamp": time.time(),
            "intent": intent,
            "goal": goal,
            "proposed_action": proposed_action,
            "context": context,
            "sense": {
                "retrieval_matches": len(context["retrieval"]["matches"]),
                "graph_entities": len(context["matched_entities"]),
            },
            "reason": {
                "stage_focus": context["stage_focus"],
                "graph_brief": context["graph_brief"],
            },
            "plan": {
                "candidates": candidates,
            },
            "verify": verify_metrics,
            "decide": {
                "status": decision_status,
                "best_candidate": best_simulation,
            },
            "act": act,
            "learn": learn,
        }
        with self._trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace) + "\n")
        self._export_trace_to_telemetry(trace)
        return trace

    def _export_trace_to_telemetry(self, trace: dict[str, Any]) -> None:
        import threading
        def _bg_export():
            try:
                from google.cloud import firestore
                db = firestore.Client()
                doc_id = trace.get("trace_id", f"trace-{int(time.time() * 1000)}")
                db.collection("decision_traces").document(doc_id).set(trace)
            except Exception:
                pass
            
            try:
                from google.cloud import bigquery
                bq = bigquery.Client()
                table_id = "mizoki_telemetry.decision_traces"
                bq.insert_rows_json(table_id, [trace])
            except Exception:
                pass

        threading.Thread(target=_bg_export, daemon=True).start()

    def _detect_stage_focus(self, intent: str) -> str:
        if _contains_any_phrase(intent, ("decision loop", "full loop", "srpvdal loop")):
            return ""
        for stage, keywords in GRAPH_NATIVE_STAGE_KEYWORDS.items():
            if _contains_any_phrase(intent, keywords):
                return stage
        return ""

    def _recommend_subagents(
        self,
        intent: str,
        stage_focus: str,
        matched_entities: list[dict[str, Any]],
        retrieval_matches: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        lowered_intent = intent.lower()
        recommendations: list[dict[str, Any]] = []
        for subagent in GRAPH_NATIVE_SUBAGENTS:
            score = 0.0
            reasons: list[str] = []
            if stage_focus and subagent["stage"] == stage_focus:
                score += 4
                reasons.append("matches detected SRPVDAL stage")
            searchable = " ".join(
                (
                    subagent["name"],
                    subagent["responsibility"],
                    " ".join(subagent["triggers"]),
                )
            ).lower()
            keyword_matches = sum(1 for token in _normalize_tokens(intent) if token in searchable)
            if keyword_matches:
                score += keyword_matches * 1.5
                reasons.append(f"matched {keyword_matches} subagent keywords")
            if matched_entities and subagent["stage"] in {"reason", "plan", "verify", "decide"}:
                score += 1
                reasons.append("graph entities available")
            if retrieval_matches and subagent["stage"] in {"sense", "reason", "plan"}:
                score += 1
                reasons.append("retrieval evidence available")
            if any(tool_name.split(".", 1)[0] == "gndi" for tool_name in subagent["preferred_tools"]) and "graph" in lowered_intent:
                score += 1
                reasons.append("graph-native request detected")
            recommendations.append(
                {
                    **deepcopy(subagent),
                    "score": round(score, 2),
                    "reasons": reasons,
                }
            )

        recommendations.sort(key=lambda item: item["score"], reverse=True)
        return recommendations[:4]

    def _build_governance_signals(
        self,
        intent: str,
        constraints: list[str],
        matched_entities: list[dict[str, Any]],
        retrieval_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        live_action_requested = self._intent_implies_live_action(intent)
        evidence_count = len(retrieval_matches)
        entity_count = len(matched_entities)
        policy_checks = [
            {
                "name": "evidence_sufficiency",
                "status": "pass" if evidence_count > 0 else "warn",
                "detail": f"{evidence_count} retrieval match(es) available.",
            },
            {
                "name": "graph_grounding",
                "status": "pass" if entity_count > 0 else "warn",
                "detail": f"{entity_count} graph entity match(es) available.",
            },
        ]
        if live_action_requested:
            policy_checks.append(
                {
                    "name": "live_action_review",
                    "status": "warn" if evidence_count == 0 else "pass",
                    "detail": "Live-action language detected in the request.",
                }
            )
        for constraint in constraints:
            policy_checks.append(
                {
                    "name": f"constraint:{constraint.lower().replace(' ', '_')}",
                    "status": "pass",
                    "detail": f"Constraint '{constraint}' propagated into verification.",
                }
            )
        return {
            "live_action_requested": live_action_requested,
            "requires_review": live_action_requested and evidence_count == 0,
            "policy_checks": policy_checks,
        }

    def _build_candidate_actions(
        self,
        intent: str,
        goal: str,
        proposed_action: str,
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        stage_focus = context["stage_focus"]
        supporting_entities = [entity["entity_id"] for entity in context["matched_entities"][:3]]
        primary_summary = proposed_action.strip() or f"Run a graph-grounded {stage_focus.replace('_', ' ')} pass for the request."
        candidates = [
            {
                "candidate_id": "candidate.graph_grounded_execution",
                "mode": "execute",
                "summary": primary_summary,
                "goal": goal.strip() or intent,
                "supporting_entities": supporting_entities,
                "tool_chain": self._build_tool_chain(stage_focus, supporting_entities),
            },
            {
                "candidate_id": "candidate.observe_and_refine",
                "mode": "observe",
                "summary": "Collect more GraphRAG evidence and refine the graph context before acting.",
                "goal": "Increase grounding and reduce ambiguity.",
                "supporting_entities": supporting_entities,
                "tool_chain": ["gndi.inspect_context", "graphrag.query", "kg.describe_entity"],
            },
            {
                "candidate_id": "candidate.escalate_control_plane",
                "mode": "escalate",
                "summary": "Escalate the request through the decision control plane with an audit-ready trace.",
                "goal": "Require explicit approval before action.",
                "supporting_entities": supporting_entities,
                "tool_chain": ["gndi.run_decision_loop", "decision.explain_pipeline", "decision.recent_traces"],
            },
        ]
        return candidates

    def _build_tool_chain(self, stage_focus: str, supporting_entities: list[str]) -> list[str]:
        tool_chain = ["gndi.inspect_context", "graphrag.query"]
        if supporting_entities:
            tool_chain.append("kg.describe_entity")
        if stage_focus in {"reason", "verify", "decide", "full_loop"}:
            tool_chain.append("decision.explain_pipeline")
        if stage_focus in {"verify", "decide", "act"}:
            tool_chain.append("gndi.simulate_action")
        return tool_chain

    def _simulate_candidate(self, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        evidence_count = len(context["retrieval"]["matches"])
        entity_count = len(context["matched_entities"])
        constraint_count = len(context["constraints"])
        mode = candidate["mode"]

        predicted_value = 1.0 + (evidence_count * 0.85) + (entity_count * 0.45)
        if mode == "execute":
            predicted_value += 1.1
        elif mode == "observe":
            predicted_value += 0.35
        else:
            predicted_value += 0.55

        risk_score = constraint_count * 0.45
        if mode == "execute" and context["governance"]["live_action_requested"]:
            risk_score += 1.1
        if evidence_count == 0 and mode != "observe":
            risk_score += 0.9
        if mode == "escalate":
            risk_score += 0.15

        confidence = max(0.2, min(0.96, 0.4 + (evidence_count * 0.08) + (entity_count * 0.04) - (risk_score * 0.07)))
        needs_review = context["governance"]["requires_review"] or risk_score >= 1.6
        return {
            "candidate_id": candidate["candidate_id"],
            "mode": mode,
            "summary": candidate["summary"],
            "tool_chain": list(candidate["tool_chain"]),
            "predicted_value": round(predicted_value, 2),
            "risk_score": round(risk_score, 2),
            "confidence": round(confidence, 2),
            "needs_review": needs_review,
            "counterfactual_note": "Compared against the observe-and-refine baseline inside the graph-native loop.",
        }

    def _build_trace_summary(
        self,
        intent: str,
        best_simulation: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        return (
            f"Intent '{intent[:72]}' routed through {context['stage_focus']} with "
            f"{len(context['matched_entities'])} entity match(es), "
            f"{len(context['retrieval']['matches'])} retrieval match(es), and "
            f"decision status '{best_simulation['mode']}'."
        )

    def _build_skill_seed(
        self,
        intent: str,
        best_simulation: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        focus_phrase = self._detect_stage_focus(intent) or context["stage_focus"]
        return {
            "name": _titleize_phrase(f"{focus_phrase} graph workflow", suffix="Skill"),
            "description": "Suggested skill derived from a graph-native decision loop trace.",
            "trigger_phrases": [focus_phrase, intent[:80]],
            "preferred_tools": list(best_simulation["tool_chain"][:3]),
        }

    def _intent_implies_live_action(self, intent: str) -> bool:
        return _contains_any_phrase(intent, ("deploy", "publish", "launch", "push", "change", "modify", "execute"))

    def _load_traces(self) -> list[dict[str, Any]]:
        if not self._trace_file.exists():
            return []
        traces: list[dict[str, Any]] = []
        for line in self._trace_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                traces.append(payload)
        return traces


class SkillStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._skills: list[LearnedSkill] = self._load()

    def _load(self) -> list[LearnedSkill]:
        payload = _load_json_list(self.file_path, "skill store")
        return [LearnedSkill.from_dict(item) for item in payload if isinstance(item, dict)]

    def _save(self) -> None:
        payload = [skill.to_dict() for skill in self._skills]
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def all(self) -> list[LearnedSkill]:
        return list(self._skills)

    def add(self, skill: LearnedSkill) -> LearnedSkill:
        if any(existing.name.casefold() == skill.name.casefold() for existing in self._skills):
            raise ValueError(f"skill already exists: {skill.name}")
        self._skills.append(skill)
        self._save()
        return skill

    def match(self, intent: str) -> list[LearnedSkill]:
        normalized_intent = intent.lower()
        intent_tokens = set(_normalize_tokens(intent))
        matches = []
        for skill in self._skills:
            for trigger in skill.trigger_phrases:
                normalized_trigger = trigger.strip().lower()
                trigger_tokens = set(_normalize_tokens(trigger))
                if normalized_trigger and normalized_trigger in normalized_intent:
                    matches.append(skill)
                    break
                if trigger_tokens and trigger_tokens.issubset(intent_tokens):
                    matches.append(skill)
                    break
        return matches


class ToolRegistry:
    def __init__(self, alias_file: Path) -> None:
        self.alias_file = alias_file
        self.alias_file.parent.mkdir(parents=True, exist_ok=True)
        self._definitions: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"tool already registered: {definition.name}")
        if not definition.handler and not definition.alias_target:
            raise ValueError(f"tool {definition.name} must define a handler or alias target")
        self._definitions[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        if name not in self._definitions:
            raise ValueError(f"unknown tool: {name}")
        return self._definitions[name]

    def list_tools(self) -> list[dict[str, Any]]:
        return [definition.to_public_dict() for definition in sorted(self._definitions.values(), key=lambda item: item.name)]

    def _validate_partial_arguments(self, definition: ToolDefinition, arguments: dict[str, Any] | None) -> dict[str, Any]:
        arguments = dict(arguments or {})
        allowed_parameters = {parameter.name: parameter for parameter in definition.parameters}
        unexpected = sorted(key for key in arguments if key not in allowed_parameters)
        if unexpected:
            raise ValueError(f"unexpected parameters for {definition.name}: {', '.join(unexpected)}")

        validated: dict[str, Any] = {}
        for name, value in arguments.items():
            validated[name] = _coerce_value(allowed_parameters[name].type, value)
        return validated

    def _validate_arguments(self, definition: ToolDefinition, arguments: dict[str, Any] | None) -> dict[str, Any]:
        validated = self._validate_partial_arguments(definition, arguments)
        for parameter in definition.parameters:
            if parameter.name in validated:
                continue
            if parameter.default is not None:
                validated[parameter.name] = deepcopy(parameter.default)
                continue
            if parameter.required:
                raise ValueError(f"missing required parameter: {parameter.name}")
        return validated

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        definition = self.get(name)
        if definition.alias_target:
            merged_arguments = dict(definition.default_arguments)
            merged_arguments.update(arguments or {})
            target_definition = self.get(definition.alias_target)
            validated_arguments = self._validate_arguments(target_definition, merged_arguments)
            result = target_definition.handler(validated_arguments)  # type: ignore[misc]
            return {
                "tool": name,
                "resolved_tool": target_definition.name,
                "arguments": validated_arguments,
                "result": result,
            }

        validated_arguments = self._validate_arguments(definition, arguments)
        result = definition.handler(validated_arguments)  # type: ignore[misc]
        return {
            "tool": definition.name,
            "resolved_tool": definition.name,
            "arguments": validated_arguments,
            "result": result,
        }

    def register_alias(
        self,
        name: str,
        description: str,
        target_tool: str,
        default_arguments: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        name = _require_non_empty_string(name, "name")
        description = _require_non_empty_string(description, "description")
        tags = _clean_string_list(tags or [], "tags")
        if name in self._definitions:
            raise ValueError(f"tool already registered: {name}")
        target_definition = self.get(target_tool)
        validated_defaults = self._validate_partial_arguments(target_definition, default_arguments)
        alias_definition = ToolDefinition(
            name=name,
            description=description,
            category=target_definition.category,
            parameters=target_definition.parameters,
            tags=tuple(tags or target_definition.tags),
            alias_target=target_tool,
            default_arguments=validated_defaults,
        )
        self.register(alias_definition)
        if persist:
            aliases = _load_json_list(self.alias_file, "tool alias store")
            aliases.append(
                {
                    "name": name,
                    "description": description,
                    "target_tool": target_tool,
                    "default_arguments": validated_defaults,
                    "tags": tags or list(target_definition.tags),
                }
            )
            self.alias_file.write_text(json.dumps(aliases, indent=2), encoding="utf-8")
        return alias_definition.to_public_dict()

    def load_aliases(self) -> None:
        aliases = _load_json_list(self.alias_file, "tool alias store")
        for alias in aliases:
            if not isinstance(alias, dict):
                continue
            if not {"name", "description", "target_tool"}.issubset(alias):
                continue
            if alias["name"] in self._definitions:
                continue
            self.register_alias(
                name=alias["name"],
                description=alias["description"],
                target_tool=alias["target_tool"],
                default_arguments=alias.get("default_arguments", {}),
                tags=alias.get("tags", []),
                persist=False,
            )


class BossAgent:
    def __init__(
        self,
        registry: ToolRegistry,
        skill_store: SkillStore,
        corpus: SiteCorpus,
        knowledge_graph: KnowledgeGraph,
        graph_decision: GraphNativeDecisionIntelligence,
        google_ads: GoogleAdsCompatibilityCell,
        journey: JourneyIngestCell,
        envelope_builder: CanonicalEnvelopeBuilder,
        identity_resolver: IdentityResolutionCell,
        virtuoso: VirtuosoModelPlane,
        trace_file: Path,
    ) -> None:
        self.registry = registry
        self.skill_store = skill_store
        self.corpus = corpus
        self.knowledge_graph = knowledge_graph
        self.graph_decision = graph_decision
        self.google_ads = google_ads
        self.journey = journey
        self.envelope_builder = envelope_builder
        self.identity_resolver = identity_resolver
        self.virtuoso = virtuoso
        self.trace_file = trace_file
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)

    def discover(self) -> dict[str, Any]:
        return {
            "tools": self.registry.list_tools(),
            "skills": [skill.to_dict() for skill in self.skill_store.all()],
            "graph": {
                "entity_count": self.knowledge_graph.node_count,
                "document_count": len(self.corpus.documents),
            },
            "graph_native": {
                "subagents": self.graph_decision.list_subagents(),
                "recent_loops": self.graph_decision.recent_loops(limit=3),
            },
            "google_ads": self.google_ads.discovery_block(),
            "journey": {
                **self.journey.discovery_block(),
                "llm_extractor": active_extractor_metadata(),
                "envelope": self.envelope_builder.discovery_block(),
                "identity_resolution": self.identity_resolver.discovery_block(),
                "description": "Canonical JourneyEvent connector layer: normalizes Meta, Google Ads, SendGrid, and OpenRTB signals into one schema at SENSE with deterministic, idempotent upserts.",
            },
            "virtuoso": self.virtuoso.discovery_block(),
            "capabilities": {
                "skill_learning_tools": ["skills.learn", "skills.learn_from_loop"],
                "tool_learning_tools": ["tools.register_alias"],
                "routing_behaviors": [
                    "graph-native context grounding",
                    "counterfactual simulation selection",
                    "skill-aware tool ranking",
                ],
            },
        }

    def learn_skill(
        self,
        name: str,
        description: str,
        trigger_phrases: list[str],
        preferred_tools: list[str] | None = None,
        examples: list[str] | None = None,
    ) -> dict[str, Any]:
        name = _require_non_empty_string(name, "name")
        description = _require_non_empty_string(description, "description")
        trigger_phrases = _clean_string_list(trigger_phrases, "trigger_phrases", minimum=1)
        preferred_tools = _clean_string_list(preferred_tools or [], "preferred_tools")
        examples = _clean_string_list(examples or [], "examples")
        for tool_name in preferred_tools:
            self.registry.get(tool_name)
        skill = LearnedSkill(
            name=name,
            description=description,
            trigger_phrases=tuple(trigger_phrases),
            preferred_tools=tuple(preferred_tools),
            examples=tuple(examples),
        )
        stored = self.skill_store.add(skill)
        return stored.to_dict()

    def recent_traces(self, limit: int = 5) -> list[dict[str, Any]]:
        bounded_limit = _require_bounded_integer(limit, "limit", minimum=1, maximum=100)
        traces = self._load_traces()
        traces = traces[-bounded_limit:]
        traces.reverse()
        return traces

    def learn_skill_from_loop(
        self,
        trace_id: str = "",
        name: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        loop = self.graph_decision.get_loop(trace_id) if trace_id.strip() else self.graph_decision.latest_loop()
        if loop is None:
            raise ValueError("no graph-native loop traces available")
        seed = loop.get("learn", {}).get("recommended_skill_seed", {})
        trigger_phrases = seed.get("trigger_phrases", [])
        preferred_tools = seed.get("preferred_tools", [])
        skill_name = name.strip() or seed.get("name", "")
        skill_description = description.strip() or seed.get("description", "")
        if not skill_name or not skill_description or not trigger_phrases:
            raise ValueError("selected loop trace does not contain a usable skill seed")
        return self.learn_skill(
            name=skill_name,
            description=skill_description,
            trigger_phrases=trigger_phrases,
            preferred_tools=preferred_tools,
            examples=[loop.get("intent", "")],
        )

    def execute(self, intent: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if not intent.strip():
            raise ValueError("intent must not be empty")

        context = self._build_context(intent, arguments or {})
        selection, candidates = self._select_tool(intent, arguments or {}, context)
        execution = self.registry.call(selection.tool_name, selection.arguments)
        trace = {
            "timestamp": time.time(),
            "intent": intent,
            "context": context,
            "candidates": candidates,
            "selection": selection.to_dict(),
            "execution": {
                "tool": execution["tool"],
                "resolved_tool": execution["resolved_tool"],
                "arguments": execution["arguments"],
            },
        }
        with self.trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace) + "\n")
        return {
            "context": context,
            "candidates": candidates,
            "selection": selection.to_dict(),
            "execution": execution,
        }

    def _build_context(self, intent: str, provided_arguments: dict[str, Any]) -> dict[str, Any]:
        constraints = provided_arguments.get("constraints", [])
        top_k = provided_arguments.get("top_k", 3)
        if not isinstance(top_k, int):
            top_k = 3
        if not isinstance(constraints, list):
            constraints = []
        context = self.graph_decision.build_context(intent, top_k=top_k, constraints=constraints)
        context["matched_skills"] = [skill.to_dict() for skill in self.skill_store.match(intent)]
        return context

    def _extract_focus_phrase(self, intent: str) -> str:
        for pattern in (
            r"\bfor\s+(.+?)(?:[.?!]|$)",
            r"\babout\s+(.+?)(?:[.?!]|$)",
            r"\bwhen\s+(.+?)(?:[.?!]|$)",
        ):
            match = re.search(pattern, intent, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" .?!")
                if candidate:
                    return candidate
        if _extract_quoted_phrases(intent):
            return _extract_quoted_phrases(intent)[0]
        return ""

    def _infer_preferred_tool(self, intent: str, context: dict[str, Any]) -> str | None:
        if _contains_any_phrase(intent, ("counterfactual", "simulate", "what if", "tradeoff")):
            return "gndi.simulate_action"
        if _contains_any_phrase(intent, ("subagent", "subagents", "specialist", "cell")):
            return "gndi.list_subagents"
        if (
            _contains_any_phrase(intent, ("graph native", "graph-native", "decision loop", "run the loop"))
            or (_contains_phrase(intent, "run") and any(_contains_phrase(intent, stage) for stage in GRAPH_NATIVE_STAGE_ORDER))
        ):
            return "gndi.run_decision_loop"
        if _contains_any_phrase(intent, ("graph context", "grounding", "context graph", "graph state")):
            return "gndi.inspect_context"
        if _contains_any_phrase(intent, ("pipeline", "stage", "decision control plane", "dcp", "govern", "authorize")):
            return "decision.explain_pipeline"
        if _contains_any_phrase(intent, ("neighbor", "relationship", "relates")):
            return "kg.list_neighbors"
        if context["matched_entities"]:
            return "kg.describe_entity"
        if context["retrieval"]["matches"]:
            return "graphrag.query"
        return None

    def _is_skill_learning_intent(self, intent: str) -> bool:
        return _contains_any_phrase(
            intent,
            ("learn", "teach", "memorize", "new skill", "save as skill"),
        )

    def _is_loop_skill_learning_intent(self, intent: str) -> bool:
        return _contains_any_phrase(intent, ("learn from loop", "learn from trace", "save loop as skill", "promote loop to skill"))

    def _is_tool_registration_intent(self, intent: str) -> bool:
        return _contains_any_phrase(intent, ("register tool", "new tool", "tool alias", "add tool", "register alias"))

    def _infer_skill_learning_arguments(
        self,
        provided_arguments: dict[str, Any],
        context: dict[str, Any],
        intent: str,
    ) -> dict[str, Any]:
        arguments = dict(provided_arguments)
        focus_phrase = self._extract_focus_phrase(intent)
        quoted_phrases = _extract_quoted_phrases(intent)

        if "name" not in arguments:
            explicit_name_match = re.search(r"\b(?:named|called)\s+['\"]?([A-Za-z0-9][A-Za-z0-9 _.-]{1,80})", intent, flags=re.IGNORECASE)
            if explicit_name_match:
                arguments["name"] = explicit_name_match.group(1).strip(" .?!'\"")
            elif focus_phrase:
                arguments["name"] = _titleize_phrase(focus_phrase, suffix="Skill")
            elif context["matched_entities"]:
                arguments["name"] = f"{context['matched_entities'][0]['name']} Skill"

        if "description" not in arguments and (focus_phrase or context["matched_entities"]):
            focus_label = focus_phrase or context["matched_entities"][0]["name"]
            arguments["description"] = f"Auto-learned skill for {focus_label}."

        if "trigger_phrases" not in arguments:
            triggers: list[str] = []
            if focus_phrase:
                triggers.append(focus_phrase)
            for phrase in quoted_phrases:
                triggers.append(phrase)
            for entity in context["matched_entities"][:2]:
                triggers.append(entity["name"].lower())
            if triggers:
                arguments["trigger_phrases"] = _clean_string_list(triggers, "trigger_phrases", minimum=1)

        if "preferred_tools" not in arguments:
            preferred_tool = self._infer_preferred_tool(intent, context)
            if preferred_tool:
                arguments["preferred_tools"] = [preferred_tool]

        arguments.setdefault("examples", [intent.strip()])
        return arguments

    def _infer_alias_arguments(
        self,
        provided_arguments: dict[str, Any],
        intent: str,
    ) -> dict[str, Any]:
        arguments = dict(provided_arguments)
        lowered_intent = intent.lower()

        if "target_tool" not in arguments:
            for tool in self.registry.list_tools():
                if _contains_phrase(intent, tool["name"]):
                    arguments["target_tool"] = tool["name"]
                    break
            else:
                if _contains_any_phrase(intent, ("graphrag", "retrieval")):
                    arguments["target_tool"] = "graphrag.query"
                elif _contains_any_phrase(intent, ("neighbor", "relationship")):
                    arguments["target_tool"] = "kg.list_neighbors"
                elif _contains_any_phrase(intent, ("entity", "knowledge graph", "kg")):
                    arguments["target_tool"] = "kg.describe_entity"
                elif _contains_any_phrase(intent, ("pipeline", "dcp")):
                    arguments["target_tool"] = "decision.explain_pipeline"

        if "name" not in arguments:
            explicit_name_match = re.search(r"\b(?:named|called|as)\s+['\"]?([A-Za-z0-9][A-Za-z0-9_.-]{1,80})", intent, flags=re.IGNORECASE)
            if explicit_name_match:
                arguments["name"] = explicit_name_match.group(1).strip(" .?!'\"")

        if "description" not in arguments and arguments.get("target_tool"):
            arguments["description"] = f"Alias for {arguments['target_tool']} inferred from natural-language registration."

        if "default_arguments" not in arguments:
            inferred_defaults: dict[str, Any] = {}
            top_k_match = re.search(r"\btop[_ ]?k\s+(\d+)\b", lowered_intent)
            if top_k_match and arguments.get("target_tool") == "graphrag.query":
                inferred_defaults["top_k"] = int(top_k_match.group(1))
            if inferred_defaults:
                arguments["default_arguments"] = inferred_defaults

        if "tags" not in arguments and arguments.get("target_tool"):
            target_tags = self.registry.get(arguments["target_tool"]).tags
            arguments["tags"] = list(target_tags[:3])

        return arguments

    def _infer_arguments(
        self,
        tool_name: str,
        provided_arguments: dict[str, Any],
        context: dict[str, Any],
        intent: str,
    ) -> tuple[dict[str, Any], bool]:
        arguments = dict(provided_arguments)

        stage_map = {
            "sense": "sense",
            "reason": "reason",
            "plan": "plan",
            "validate": "verify",
            "verify": "verify",
            "decide": "decide",
            "act": "act",
            "learn": "learn",
        }

        if tool_name == "graphrag.query":
            arguments.setdefault("query", intent)
        elif tool_name == "gndi.inspect_context":
            arguments.setdefault("intent", intent)
        elif tool_name == "gndi.simulate_action":
            arguments.setdefault("intent", intent)
            arguments.setdefault("proposed_action", self._extract_focus_phrase(intent) or "Graph-grounded recommendation")
        elif tool_name == "gndi.run_decision_loop":
            arguments.setdefault("intent", intent)
            arguments.setdefault("goal", self._extract_focus_phrase(intent) or intent)
        elif tool_name == "kg.describe_entity":
            if "entity_id" not in arguments and context["matched_entities"]:
                arguments["entity_id"] = context["matched_entities"][0]["entity_id"]
        elif tool_name == "kg.list_neighbors":
            if "entity_id" not in arguments and context["matched_entities"]:
                arguments["entity_id"] = context["matched_entities"][0]["entity_id"]
        elif tool_name == "skills.learn" and self._is_skill_learning_intent(intent) and not self._is_loop_skill_learning_intent(intent):
            arguments = self._infer_skill_learning_arguments(arguments, context, intent)
        elif tool_name == "skills.learn_from_loop" and self._is_loop_skill_learning_intent(intent):
            latest_loop = self.graph_decision.latest_loop()
            if latest_loop is not None:
                arguments.setdefault("trace_id", latest_loop["trace_id"])
        elif tool_name == "tools.register_alias" and self._is_tool_registration_intent(intent):
            arguments = self._infer_alias_arguments(arguments, intent)
        elif tool_name == "decision.explain_pipeline":
            for keyword, stage in stage_map.items():
                if _contains_phrase(intent, keyword):
                    arguments.setdefault("stage", stage)
                    break
            arguments.setdefault("focus", intent)

        definition = self.registry.get(tool_name)
        available = set(arguments)
        available.update(
            parameter.name
            for parameter in definition.parameters
            if parameter.default is not None
        )
        complete = all((not parameter.required) or (parameter.name in available) for parameter in definition.parameters)
        return arguments, complete

    def _score_tool(
        self,
        definition: ToolDefinition,
        intent: str,
        inferred_arguments: dict[str, Any],
        context: dict[str, Any],
        complete: bool,
    ) -> tuple[float, list[str]]:
        tokens = set(_normalize_tokens(intent))
        searchable = " ".join((definition.name, definition.description, " ".join(definition.tags))).lower()
        reasons: list[str] = []
        score = 0.0

        direct_keyword_matches = sum(1 for token in tokens if token in searchable)
        if direct_keyword_matches:
            score += direct_keyword_matches * 1.5
            reasons.append(f"matched {direct_keyword_matches} tool keywords")

        if definition.name == "graphrag.query" and context["retrieval"]["matches"]:
            score += 2.5
            reasons.append("retrieval candidates available")

        if definition.name.startswith("gndi.") and context.get("recommended_subagents"):
            score += 1.5
            reasons.append("graph-native subagents available")

        if definition.name == "gndi.inspect_context" and _contains_any_phrase(
            intent, ("graph context", "grounding", "graph-native", "graph state")
        ):
            score += 5
            reasons.append("graph context intent detected")

        if definition.name == "gndi.simulate_action" and _contains_any_phrase(
            intent, ("simulate", "counterfactual", "what if", "tradeoff")
        ):
            score += 6
            reasons.append("counterfactual intent detected")

        if definition.name == "gndi.run_decision_loop" and (
            _contains_any_phrase(intent, ("graph native", "graph-native", "decision loop", "run the loop"))
            or (_contains_phrase(intent, "run") and any(_contains_phrase(intent, stage) for stage in GRAPH_NATIVE_STAGE_ORDER))
        ):
            score += 6
            reasons.append("graph-native decision loop intent detected")
        if definition.name == "gndi.run_decision_loop" and self._is_loop_skill_learning_intent(intent) and self.graph_decision.latest_loop() is None:
            score += 4
            reasons.append("no prior loop trace available; generate one first")

        if definition.name == "gndi.list_subagents" and _contains_any_phrase(
            intent, ("subagent", "subagents", "specialist", "cell")
        ):
            score += 6
            reasons.append("subagent discovery intent detected")

        if definition.name == "gndi.recent_loops" and _contains_any_phrase(
            intent, ("recent loops", "decision loops", "graph traces", "graph loop")
        ):
            score += 5
            reasons.append("graph-native trace intent detected")

        if definition.name.startswith("kg.") and context["matched_entities"]:
            score += 2.5
            reasons.append("knowledge graph entity matched")

        if definition.name == "decision.explain_pipeline" and _contains_any_phrase(
            intent, ("pipeline", "stage", "flow", "srpvdal", "dcp", "decision control plane", "explain")
        ):
            score += 3
            reasons.append("pipeline explanation intent detected")

        if definition.name == "tools.list" and _contains_any_phrase(intent, ("tool", "tools", "discover", "available")):
            score += 5
            reasons.append("tool discovery intent detected")

        if definition.name == "skills.list" and _contains_any_phrase(intent, ("skill", "skills")) and not self._is_skill_learning_intent(intent):
            score += 5
            reasons.append("skill discovery intent detected")

        if definition.name == "skills.learn" and self._is_skill_learning_intent(intent) and not self._is_loop_skill_learning_intent(intent):
            score += 6
            reasons.append("skill learning intent detected")

        if definition.name == "skills.learn_from_loop" and self._is_loop_skill_learning_intent(intent):
            if inferred_arguments.get("trace_id") or self.graph_decision.latest_loop() is not None:
                score += 7
                reasons.append("loop-to-skill learning intent detected")
            else:
                score -= 6
                reasons.append("no graph-native loop trace available")

        if definition.name == "tools.register_alias" and self._is_tool_registration_intent(intent):
            score += 6
            reasons.append("tool registration intent detected")

        if definition.name == "decision.recent_traces" and _contains_any_phrase(intent, ("trace", "audit", "history")):
            score += 4
            reasons.append("audit intent detected")

        for skill in context["matched_skills"]:
            if definition.name in skill["preferred_tools"]:
                score += 4
                reasons.append(f"preferred by skill '{skill['name']}'")

        required_argument_hits = 0
        for parameter in definition.parameters:
            if parameter.required and parameter.name in inferred_arguments:
                required_argument_hits += 1
        if required_argument_hits:
            score += required_argument_hits * 2
            reasons.append("required parameters available")

        if not complete:
            score -= 8
            reasons.append("missing required parameters")

        if definition.alias_target:
            score += 0.25

        return score, reasons

    def _load_traces(self) -> list[dict[str, Any]]:
        if not self.trace_file.exists():
            return []
        traces: list[dict[str, Any]] = []
        for line in self.trace_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                traces.append(payload)
        return traces

    def _select_tool(
        self,
        intent: str,
        provided_arguments: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[ToolSelection, list[dict[str, Any]]]:
        candidates: list[tuple[float, bool, ToolDefinition, dict[str, Any], list[str]]] = []
        for tool in (self.registry.get(item["name"]) for item in self.registry.list_tools()):
            inferred_arguments, complete = self._infer_arguments(tool.name, provided_arguments, context, intent)
            score, reasons = self._score_tool(tool, intent, inferred_arguments, context, complete)
            candidates.append((score, complete, tool, inferred_arguments, reasons))

        candidates.sort(key=lambda item: (item[1], item[0]), reverse=True)
        viable_candidates = [candidate for candidate in candidates if candidate[1] and candidate[0] > 0]
        if not viable_candidates:
            fallback_arguments, _ = self._infer_arguments("graphrag.query", provided_arguments, context, intent)
            selection = ToolSelection(
                tool_name="graphrag.query",
                confidence=0.25,
                reasons=("fallback to GraphRAG retrieval",),
                arguments=fallback_arguments,
            )
            candidate_payload = []
            return selection, candidate_payload

        top_score, _, top_tool, top_arguments, top_reasons = viable_candidates[0]
        second_score = viable_candidates[1][0] if len(viable_candidates) > 1 else 0.0
        confidence = round(min(0.99, 0.45 + max(top_score - second_score, 0) * 0.08 + max(top_score, 0) * 0.02), 2)
        selection = ToolSelection(
            tool_name=top_tool.name,
            confidence=confidence,
            reasons=tuple(top_reasons),
            arguments=top_arguments,
        )
        candidate_payload = [
            {
                "tool_name": tool.name,
                "score": round(score, 2),
                "complete": complete,
                "reasons": reasons,
            }
            for score, complete, tool, _, reasons in candidates[:5]
        ]
        return selection, candidate_payload


class BossRuntime:
    def __init__(self, base_dir: Path | None = None, data_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or Path(__file__).resolve().parent.parent).resolve()
        self.data_dir = (data_dir or (self.base_dir / "data")).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.corpus = SiteCorpus(self.base_dir)
        self.knowledge_graph = KnowledgeGraph(self.corpus)
        self.graph_decision = GraphNativeDecisionIntelligence(
            self.corpus,
            self.knowledge_graph,
            self.data_dir / "graph_native_loops.jsonl",
        )
        self.google_ads = GoogleAdsCompatibilityCell(self.data_dir / "google_ads_validations.jsonl")
        self.journey = JourneyIngestCell(
            self.base_dir / "schemas" / "journey-event.json",
            self.data_dir / "journey_events.jsonl",
            external_sinks=build_journey_sinks_from_env(),
        )
        self.envelope_builder = CanonicalEnvelopeBuilder(
            self.base_dir / "schemas" / "canonical-event-envelope.json",
            self.journey.schema,
        )
        self.identity_resolver = IdentityResolutionCell(self.data_dir / "identity_clusters.json")
        # Boot-time model-registry guard: a retired model string or a
        # fallback-as-primary override refuses to start the runtime.
        self.virtuoso = VirtuosoModelPlane(self.data_dir / "mii_reasoning_traces.jsonl")
        self.skill_store = SkillStore(self.data_dir / "boss_skills.json")
        self.registry = ToolRegistry(self.data_dir / "tool_aliases.json")
        self._register_tools()
        self.registry.load_aliases()
        self.boss = BossAgent(
            registry=self.registry,
            skill_store=self.skill_store,
            corpus=self.corpus,
            knowledge_graph=self.knowledge_graph,
            graph_decision=self.graph_decision,
            google_ads=self.google_ads,
            journey=self.journey,
            envelope_builder=self.envelope_builder,
            identity_resolver=self.identity_resolver,
            virtuoso=self.virtuoso,
            trace_file=self.data_dir / "boss_decision_log.jsonl",
        )

    def _register_tools(self) -> None:
        self.registry.register(
            ToolDefinition(
                name="gndi.inspect_context",
                description="Build graph-native context for an intent using GraphRAG retrieval, KG grounding, and subagent recommendations.",
                category="graph_native",
                parameters=(
                    ToolParameter("intent", "string", "Natural language intent to ground in the graph.", required=True),
                    ToolParameter("top_k", "integer", "Maximum number of retrieval matches to include.", default=3),
                    ToolParameter("constraints", "array", "Optional validation constraints to propagate through the loop.", default=[]),
                ),
                tags=("graph-native", "context", "graphrag", "knowledge graph"),
                handler=self._handle_graph_context,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="gndi.simulate_action",
                description="Run a counterfactual-style simulation for a proposed action using graph-native evidence and governance checks.",
                category="graph_native",
                parameters=(
                    ToolParameter("intent", "string", "Natural language intent to evaluate.", required=True),
                    ToolParameter("proposed_action", "string", "Optional action to compare against the observe baseline.", default=""),
                    ToolParameter("constraints", "array", "Optional validation constraints.", default=[]),
                    ToolParameter("top_k", "integer", "Maximum number of retrieval matches to include.", default=3),
                ),
                tags=("graph-native", "counterfactual", "simulate", "validation"),
                handler=self._handle_graph_simulation,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="guide.answer",
                description="Decision Concierge Q&A: answer an executive-briefing question strictly from the allowlisted product-fact and objection bank (no generative claims).",
                category="briefing_guide",
                parameters=(
                    ToolParameter("question", "string", "The visitor's question, verbatim.", required=True),
                    ToolParameter("domain", "string", "Active briefing domain id.", default=""),
                    ToolParameter("role", "string", "Active executive role id.", default=""),
                ),
                tags=("briefing", "guide", "concierge", "objection", "sales"),
                handler=self._handle_guide_answer,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="guide.memory_summary",
                description="Aggregate Decision Concierge interaction memory: sessions, top objections, question topics, drop-off stage, suggestion acceptance, and decision intents.",
                category="briefing_guide",
                parameters=(),
                tags=("briefing", "guide", "memory", "telemetry", "objections"),
                handler=self._handle_guide_memory_summary,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="gndi.run_decision_loop",
                description="Execute the full graph-native SRPVDAL loop and return an audit-ready decision trace.",
                category="graph_native",
                parameters=(
                    ToolParameter("intent", "string", "Natural language intent to route through the decision loop.", required=True),
                    ToolParameter("goal", "string", "Optional desired outcome for the loop.", default=""),
                    ToolParameter("proposed_action", "string", "Optional proposed action for the plan and validation stages.", default=""),
                    ToolParameter("constraints", "array", "Optional validation constraints.", default=[]),
                    ToolParameter("top_k", "integer", "Maximum number of retrieval matches to include.", default=3),
                ),
                tags=("graph-native", "srpvdal", "decision loop", "governance"),
                handler=self._handle_graph_loop,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="gndi.list_subagents",
                description="List graph-native subagents and the tools they prefer for each SRPVDAL stage.",
                category="graph_native",
                parameters=(),
                tags=("graph-native", "subagents", "orchestration"),
                handler=lambda _: {"subagents": self.graph_decision.list_subagents()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="gndi.recent_loops",
                description="Return recent graph-native decision loop traces.",
                category="graph_native",
                parameters=(ToolParameter("limit", "integer", "Maximum number of traces to return.", default=5),),
                tags=("graph-native", "traces", "audit"),
                handler=lambda payload: {"traces": self.graph_decision.recent_loops(limit=payload["limit"])},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="google_ads.validate_gaql",
                description="Pre-flight a GAQL query against a Google Ads API version: checks the version's deprecation status and validates every SELECT/WHERE/ORDER BY field against the GoogleAdsFieldService-style registry for that resource, so version sunsets and field/version mismatches are caught before the query runs.",
                category="google_ads",
                parameters=(
                    ToolParameter("query", "string", "The GAQL query to validate.", required=True),
                    ToolParameter("api_version", "string", "Target API version (e.g. 'v20' or '20'). Defaults to the latest known version.", default=""),
                    ToolParameter("as_of", "string", "Optional ISO date (YYYY-MM-DD) to evaluate version status against. Defaults to today.", default=""),
                ),
                tags=("google_ads", "gaql", "validation", "deprecation", "field-service"),
                handler=lambda payload: self.validate_gaql(
                    payload["query"], api_version=payload["api_version"], as_of=payload["as_of"]
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="google_ads.validate_gaql_batch",
                description="Validate a batch of GAQL query templates against one API version in a single call — the MCC-traversal pre-flight. Results are served from a (query, version, day) cache so a template reused across many accounts is validated once.",
                category="google_ads",
                parameters=(
                    ToolParameter("queries", "array", "Array of GAQL query strings to validate.", required=True),
                    ToolParameter("api_version", "string", "Target API version (e.g. 'v20'). Defaults to the latest known version.", default=""),
                    ToolParameter("as_of", "string", "Optional ISO date (YYYY-MM-DD) to evaluate version status against. Defaults to today.", default=""),
                ),
                tags=("google_ads", "gaql", "validation", "batch", "mcc", "cache"),
                handler=lambda payload: self.validate_gaql_batch(
                    payload["queries"], api_version=payload["api_version"], as_of=payload["as_of"]
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="google_ads.version_status",
                description="Resolve a Google Ads API version to its lifecycle status (supported/deprecated/sunset/unreleased/unknown) relative to a date, or return the full deprecation schedule when no version is given.",
                category="google_ads",
                parameters=(
                    ToolParameter("api_version", "string", "API version to resolve (e.g. 'v19'). Omit for the full schedule.", default=""),
                    ToolParameter("as_of", "string", "Optional ISO date (YYYY-MM-DD) to evaluate against. Defaults to today.", default=""),
                ),
                tags=("google_ads", "version", "deprecation", "schedule"),
                handler=lambda payload: self.google_ads_version_status(
                    api_version=payload["api_version"], as_of=payload["as_of"]
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="google_ads.field_metadata",
                description="Return GoogleAdsFieldService-style field metadata (selectable/filterable/sortable + version availability) for a resource, or the whole catalog when no resource is given.",
                category="google_ads",
                parameters=(
                    ToolParameter("resource", "string", "Resource name (e.g. 'campaign'). Omit for the full catalog.", default=""),
                ),
                tags=("google_ads", "field-service", "metadata", "schema"),
                handler=lambda payload: self.google_ads_field_metadata(resource=payload["resource"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="journey.normalize_event",
                description="Normalize a single native connector payload (meta, google_ads, sendgrid, openrtb, other) into the canonical JourneyEvent schema and validate it, without persisting.",
                category="journey",
                parameters=(
                    ToolParameter("source", "string", "Connector source: meta, google_ads, sendgrid, openrtb, or other.", required=True),
                    ToolParameter("payload", "object", "Native source payload to normalize.", required=True),
                ),
                tags=("journey", "schema", "normalize", "sense", "connector"),
                handler=lambda payload: self.journey.normalize_event(payload["source"], payload["payload"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="journey.ingest_events",
                description="SENSE stage: normalize a batch of native connector records into JourneyEvents, validate them against the schema gate, and upsert idempotently on a stable event_id.",
                category="journey",
                parameters=(
                    ToolParameter("source", "string", "Connector source: meta, google_ads, sendgrid, openrtb, or other.", required=True),
                    ToolParameter("events", "array", "Array of native source records for the connector.", required=True),
                    ToolParameter("replay", "boolean", "Mark the batch as a replay in provenance (idempotency unchanged).", default=False),
                ),
                tags=("journey", "schema", "ingest", "sense", "idempotent"),
                handler=lambda payload: self.journey.ingest(
                    payload["source"],
                    payload["events"],
                    replay=payload["replay"],
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="journey.recent_events",
                description="Return the most recent canonical JourneyEvents from the idempotent event store.",
                category="journey",
                parameters=(ToolParameter("limit", "integer", "Maximum number of events to return.", default=10),),
                tags=("journey", "events", "store", "audit"),
                handler=lambda payload: {"events": self.journey.recent_events(limit=payload["limit"])},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="journey.build_envelope",
                description="Normalize a native connector payload into a v1 JourneyEvent and wrap it in a CanonicalEventEnvelope (v2): classification, identity, KG refs, relationships, time intelligence, security, data quality, observability, SRPVDAL state, and reasoning scaffolds.",
                category="journey",
                parameters=(
                    ToolParameter("source", "string", "Connector source: meta, google_ads, sendgrid, openrtb, or other.", required=True),
                    ToolParameter("payload", "object", "Native source payload to normalize and wrap.", required=True),
                ),
                tags=("journey", "envelope", "canonical", "reasoning", "v2"),
                handler=lambda payload: self.build_journey_envelope(payload["source"], payload["payload"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="identity.resolve",
                description="Resolve a cross-event identity cluster for an actor by stitching on strong identifiers (user_id/email/phone_sha256/device_ifa). Returns a deterministic, persistent cluster id; weak signals like ip are not stitched.",
                category="identity",
                parameters=(
                    ToolParameter("actor", "object", "Canonical JourneyEvent actor (user_id/email/phone_sha256/device_ifa/ip).", required=True),
                ),
                tags=("identity", "resolution", "cluster", "sense"),
                handler=lambda payload: self.resolve_identity(payload["actor"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="identity.cluster_stats",
                description="Report identity-cluster store statistics: known tokens, resolved clusters, and largest cluster size.",
                category="identity",
                parameters=(),
                tags=("identity", "resolution", "stats"),
                handler=lambda payload: self.identity_cluster_stats(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="virtuoso.registry",
                description="Report the Virtuoso model-plane registry: every role's resolved flagship (env overrides applied), the cross-vendor global fallback, image delegates, forbidden legacy patterns, and the SRPVDAL phase note.",
                category="virtuoso",
                parameters=(),
                tags=("virtuoso", "models", "registry", "fallback", "discover"),
                handler=lambda _: self.virtuoso_registry(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="virtuoso.resolve_model",
                description="Resolve the flagship model serving a Virtuoso role (data_causal, coding_arch, creative_mm, devops_ops) — the get_model(Role.X) lookup that replaces hardcoded model strings.",
                category="virtuoso",
                parameters=(
                    ToolParameter("role", "string", "Virtuoso role: data_causal, coding_arch, creative_mm, or devops_ops.", required=True),
                ),
                tags=("virtuoso", "models", "resolve", "role"),
                handler=lambda payload: self.resolve_virtuoso_model(payload["role"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="virtuoso.scan_legacy",
                description="Scan a config/code snippet for retired model strings (the WIRING purge list). Returns the violations so a legacy id is caught before it reaches a deploy.",
                category="virtuoso",
                parameters=(
                    ToolParameter("text", "string", "Text to scan for retired model strings.", required=True),
                    ToolParameter("source", "string", "Label for where the text came from.", default="inline"),
                ),
                tags=("virtuoso", "legacy", "guard", "scan", "purge"),
                handler=lambda payload: self.scan_legacy_model_strings(payload["text"], payload["source"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="virtuoso.reasoning_traces",
                description="Return recent MII reasoning-distillation trace rows persisted from virtuoso_call responses that carried a reasoning_summary.",
                category="virtuoso",
                parameters=(ToolParameter("limit", "integer", "Maximum number of trace rows to return.", default=10),),
                tags=("virtuoso", "mii", "reasoning", "traces", "distillation"),
                handler=lambda payload: {"traces": self.recent_reasoning_traces(payload["limit"])},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="tools.list",
                description="List all registered MCP tools with schemas and categories.",
                category="system",
                parameters=(),
                tags=("tools", "registry", "mcp", "discover"),
                handler=lambda _: {"tools": self.registry.list_tools()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="tools.register_alias",
                description="Register a new declarative tool alias that wraps an existing tool with preset arguments.",
                category="system",
                parameters=(
                    ToolParameter("name", "string", "Unique alias tool name.", required=True),
                    ToolParameter("description", "string", "Human-readable alias description.", required=True),
                    ToolParameter("target_tool", "string", "Existing tool to wrap.", required=True),
                    ToolParameter("default_arguments", "object", "Default arguments merged into the target tool call.", default={}),
                    ToolParameter("tags", "array", "Search tags used during tool discovery.", default=[]),
                ),
                tags=("tools", "register", "alias", "mcp"),
                handler=lambda payload: {
                    "tool": self.registry.register_alias(
                        name=payload["name"],
                        description=payload["description"],
                        target_tool=payload["target_tool"],
                        default_arguments=payload["default_arguments"],
                        tags=payload["tags"],
                    )
                },
            )
        )
        self.registry.register(
            ToolDefinition(
                name="skills.list",
                description="List all learned Boss agent skills.",
                category="system",
                parameters=(),
                tags=("skills", "discover", "memory"),
                handler=lambda _: {"skills": [skill.to_dict() for skill in self.skill_store.all()]},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="skills.learn",
                description="Persist a new reusable skill with trigger phrases and preferred tools.",
                category="system",
                parameters=(
                    ToolParameter("name", "string", "Unique skill name.", required=True),
                    ToolParameter("description", "string", "What the skill means and when to use it.", required=True),
                    ToolParameter("trigger_phrases", "array", "Phrases that should activate the skill.", required=True),
                    ToolParameter("preferred_tools", "array", "Tool names the Boss agent should favor when this skill matches.", default=[]),
                    ToolParameter("examples", "array", "Optional example prompts for the skill.", default=[]),
                ),
                tags=("skills", "learn", "memory"),
                handler=lambda payload: {
                    "skill": self.boss.learn_skill(
                        name=payload["name"],
                        description=payload["description"],
                        trigger_phrases=payload["trigger_phrases"],
                        preferred_tools=payload["preferred_tools"],
                        examples=payload["examples"],
                    )
                },
            )
        )
        self.registry.register(
            ToolDefinition(
                name="skills.learn_from_loop",
                description="Turn a graph-native decision loop trace into a reusable skill using the trace's recommended skill seed.",
                category="system",
                parameters=(
                    ToolParameter("trace_id", "string", "Optional graph-native trace identifier. Defaults to the latest loop when omitted.", default=""),
                    ToolParameter("name", "string", "Optional override for the learned skill name.", default=""),
                    ToolParameter("description", "string", "Optional override for the learned skill description.", default=""),
                ),
                tags=("skills", "learn", "graph-native", "trace"),
                handler=lambda payload: {
                    "skill": self.boss.learn_skill_from_loop(
                        trace_id=payload["trace_id"],
                        name=payload["name"],
                        description=payload["description"],
                    )
                },
            )
        )
        self.registry.register(
            ToolDefinition(
                name="kg.describe_entity",
                description="Describe a graph entity and optionally include graph neighbors.",
                category="graph",
                parameters=(
                    ToolParameter("entity_id", "string", "Entity identifier.", required=True),
                    ToolParameter("include_neighbors", "boolean", "Include inbound and outbound graph neighbors.", default=False),
                ),
                tags=("knowledge graph", "entity", "describe", "graph"),
                handler=lambda payload: self.knowledge_graph.describe_entity(
                    payload["entity_id"],
                    include_neighbors=payload["include_neighbors"],
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="kg.list_neighbors",
                description="List inbound and outbound relationships for a graph entity.",
                category="graph",
                parameters=(
                    ToolParameter("entity_id", "string", "Entity identifier.", required=True),
                    ToolParameter("relationship_type", "string", "Optional relationship type filter.", default=""),
                ),
                tags=("knowledge graph", "neighbors", "graph"),
                handler=lambda payload: self.knowledge_graph.list_neighbors(
                    payload["entity_id"],
                    relationship_type=payload["relationship_type"] or None,
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="graphrag.query",
                description="Run graph-aware retrieval across site documents and related entities.",
                category="retrieval",
                parameters=(
                    ToolParameter("query", "string", "Natural language query.", required=True),
                    ToolParameter("top_k", "integer", "Maximum number of matches to return.", default=3),
                ),
                tags=("graphrag", "retrieval", "query", "knowledge graph"),
                handler=lambda payload: {
                    **self.corpus.search(payload["query"], top_k=payload["top_k"]),
                    "related_entities": self.knowledge_graph.search_entities(payload["query"]),
                },
            )
        )
        self.registry.register(
            ToolDefinition(
                name="decision.explain_pipeline",
                description="Explain how a pipeline stage maps to the knowledge graph, GraphRAG, and decision control plane.",
                category="decision",
                parameters=(
                    ToolParameter("stage", "string", "Optional SRPVDAL stage to focus on.", default=""),
                    ToolParameter("focus", "string", "Additional query or topic context.", default=""),
                ),
                tags=("pipeline", "srpvdal", "decision", "dcp"),
                handler=self._handle_pipeline_explanation,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="decision.recent_traces",
                description="Return recent Boss agent decision traces.",
                category="decision",
                parameters=(ToolParameter("limit", "integer", "Maximum number of traces to return.", default=5),),
                tags=("decision", "traces", "audit"),
                handler=lambda payload: {"traces": self.boss.recent_traces(limit=payload["limit"])},
            )
        )
        self._register_demo_tools()

    def _register_demo_tools(self) -> None:
        """Register the Signal Factory + Counsel Room virtual-demo tools.

        These power the public /demo pages and are also callable through
        POST /api/mcp/call and the /admin tool runner, exactly like every
        other registered tool.
        """
        from . import (
            demo_capital,
            demo_counsel,
            demo_estate,
            demo_narrator,
            demo_nexus,
            demo_risk,
            demo_signal,
            demo_telemetry,
        )

        signal_pipeline = demo_signal.SignalFactoryPipeline()
        counsel_synthesizer = demo_counsel.LegalSynthesizer()
        estate_engine = demo_estate.EstateRoomEngine()
        capital_pipeline = demo_capital.CapitalDeskPipeline()
        risk_engine = demo_risk.RiskSentinelEngine()
        nexus_engine = demo_nexus.NexusRunEngine()
        telemetry_path = self.data_dir / "demo_telemetry.jsonl"

        self.registry.register(
            ToolDefinition(
                name="demo.signal.run",
                description=(
                    "Run the Signal Factory demo: manufacture raw marketing signals into a governed "
                    "autonomous decision through the 7-stage SRPVDAL pipeline with a visible ReLU gate "
                    "and guardrails. Deterministic for a given scenario and seed."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "scenario",
                        "string",
                        "Scenario id: ecommerce_roas, leadgen_cpa, or email_reengagement.",
                        required=True,
                    ),
                    ToolParameter("seed", "integer", "Deterministic seed for the synthetic pipeline run.", default=demo_signal.DEFAULT_SEED),
                ),
                tags=("demo", "signal", "signal factory", "srpvdal", "relu gate", "pipeline", "run the signal demo"),
                handler=lambda payload: signal_pipeline.run(payload["scenario"], seed=payload["seed"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.signal.list_scenarios",
                description="List the seeded Signal Factory demo scenarios with names and signal mixes.",
                category="demo",
                parameters=(),
                tags=("demo", "signal", "signal factory", "scenarios", "list"),
                handler=lambda _: {"scenarios": demo_signal.list_scenarios()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.counsel.query",
                description=(
                    "Run the Counsel Room demo: route a legal scenario or free-text question through the "
                    "Mixture-of-Legal-Experts (Connecticut / Trust / Estate / Tax), collect IRAC analyses, "
                    "surface cross-domain conflicts, and return a synthesized answer with a compliance "
                    "checklist. Every response is flagged for attorney review."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "scenario_id",
                        "string",
                        "Scripted scenario id: trust_modification_gst, ct_probate_opening, or crummey_annual_gift.",
                        default="",
                    ),
                    ToolParameter(
                        "query",
                        "string",
                        "Free-text legal question (max 500 chars) — routed to the best scenario by keyword overlap.",
                        default="",
                    ),
                ),
                tags=("demo", "counsel", "legal", "mixture of experts", "irac", "run the counsel demo"),
                handler=lambda payload: counsel_synthesizer.synthesize(
                    scenario_id=payload["scenario_id"] or None,
                    free_text=payload["query"] or None,
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.counsel.list_scenarios",
                description="List the scripted Counsel Room demo scenarios with titles and descriptions.",
                category="demo",
                parameters=(),
                tags=("demo", "counsel", "legal", "scenarios", "list"),
                handler=lambda _: {"scenarios": demo_counsel.list_scenarios()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.estate.run",
                description=(
                    "Run the Estate Room demo: the five Connecticut statutory clocks, the "
                    "three-generation GST dynasty graph, or the IRC § 1014 basis step-up table. "
                    "Deterministic for a given scenario and seed; every response is flagged for "
                    "attorney review."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "scenario",
                        "string",
                        "Scenario id: ct_estate_settlement, gst_dynasty_review, or basis_step_up.",
                        required=True,
                    ),
                    ToolParameter("seed", "integer", "Deterministic seed for the run.", default=demo_signal.DEFAULT_SEED),
                ),
                tags=("demo", "estate", "probate", "statutory clocks", "gst", "basis step-up", "run the estate demo"),
                handler=lambda payload: estate_engine.run(payload["scenario"], seed=payload["seed"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.estate.list_scenarios",
                description="List the seeded Estate Room demo scenarios with names and signature widgets.",
                category="demo",
                parameters=(),
                tags=("demo", "estate", "scenarios", "list"),
                handler=lambda _: {"scenarios": demo_estate.list_scenarios()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.capital.run",
                description=(
                    "Run the Capital Desk demo: financial events become governed capital moves "
                    "through the shared ReLU gate and guardrails plus the capital-specific "
                    "covenant_headroom rule (blocks any move modeling headroom below 15%). "
                    "Deterministic for a given scenario and seed."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "scenario",
                        "string",
                        "Scenario id: growth_reallocation, debt_paydown_vs_buyback, or working_capital_stress.",
                        required=True,
                    ),
                    ToolParameter("seed", "integer", "Deterministic seed for the run.", default=demo_signal.DEFAULT_SEED),
                ),
                tags=("demo", "capital", "covenant headroom", "srpvdal", "relu gate", "run the capital demo"),
                handler=lambda payload: capital_pipeline.run(payload["scenario"], seed=payload["seed"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.capital.list_scenarios",
                description="List the seeded Capital Desk demo scenarios with names and signal mixes.",
                category="demo",
                parameters=(),
                tags=("demo", "capital", "scenarios", "list"),
                handler=lambda _: {"scenarios": demo_capital.list_scenarios()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.risk.run",
                description=(
                    "Run the Risk Sentinel demo: 12–16 enterprise events land on a 5×5 "
                    "severity×likelihood matrix with exactly two escalations — one auto-mitigated "
                    "and one vetoed with a rule id, evidence chain, and rollback token. "
                    "Deterministic for a given scenario and seed."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "scenario",
                        "string",
                        "Scenario id: quarterly_close, vendor_breach_drill, or campaign_compliance.",
                        required=True,
                    ),
                    ToolParameter("seed", "integer", "Deterministic seed for the run.", default=demo_signal.DEFAULT_SEED),
                ),
                tags=("demo", "risk", "risk matrix", "veto", "escalation", "run the risk demo"),
                handler=lambda payload: risk_engine.run(payload["scenario"], seed=payload["seed"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.risk.list_scenarios",
                description="List the seeded Risk Sentinel demo scenarios with names and event counts.",
                category="demo",
                parameters=(),
                tags=("demo", "risk", "scenarios", "list"),
                handler=lambda _: {"scenarios": demo_risk.list_scenarios()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.nexus.run",
                description=(
                    "Run the flagship Nexus demo: one trigger chains Signal, Capital, Risk, "
                    "Counsel, and Estate deterministically under a single nexus_trace_id — one "
                    "Capital covenant block, one Risk veto, a flagged Counsel clause, and an "
                    "Estate governance ledger entry, all on one provenance graph."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "scenario",
                        "string",
                        "Scenario id: cpm_shock (default) or contract_breach_cascade.",
                        default="cpm_shock",
                    ),
                    ToolParameter("seed", "integer", "Deterministic seed for the run.", default=demo_signal.DEFAULT_SEED),
                ),
                tags=("demo", "nexus", "flagship", "five divisions", "shared trace", "run the nexus demo"),
                handler=lambda payload: nexus_engine.run(payload["scenario"], seed=payload["seed"]),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.nexus.list_scenarios",
                description="List the Nexus Run scenarios with their division ordering.",
                category="demo",
                parameters=(),
                tags=("demo", "nexus", "scenarios", "list"),
                handler=lambda _: {"scenarios": demo_nexus.list_scenarios()},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.narrate",
                description=(
                    "Trace Narrator: deterministic plain-English narration of any demo run — "
                    "4–6 sentences citing entity names, uplift/confidence/sample numbers, which "
                    "rule blocked what, and the expected-value ranking. No LLM: same seed, same "
                    "words."
                ),
                category="demo",
                parameters=(
                    ToolParameter(
                        "demo",
                        "string",
                        "Demo id: signal, capital, counsel, estate, risk, or nexus.",
                        required=True,
                    ),
                    ToolParameter("scenario", "string", "Scenario id for that demo.", required=True),
                    ToolParameter("seed", "integer", "Deterministic seed for the narrated run.", default=demo_signal.DEFAULT_SEED),
                ),
                tags=("demo", "narrator", "why", "explain", "explainability", "narrate the run"),
                handler=lambda payload: demo_narrator.narrate(
                    payload["demo"], payload["scenario"], seed=payload["seed"]
                ),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="demo.telemetry.summary",
                description=(
                    "Summarize the cookieless demo telemetry: event counts by demo and scenario "
                    "(demo_started, demo_completed, share_copied, export_downloaded, "
                    "boardroom_played, lead_click). No IPs, no user agents — ever."
                ),
                category="demo",
                parameters=(),
                tags=("demo", "telemetry", "analytics", "summary", "measurement"),
                handler=lambda _: demo_telemetry.summarize(telemetry_path),
            )
        )

    def _handle_pipeline_explanation(self, payload: dict[str, Any]) -> dict[str, Any]:
        stage = payload["stage"].strip().lower()
        focus = payload["focus"].strip()
        entity_id = stage if stage in GRAPH_NODES else "srpvdal"
        explanation = self.knowledge_graph.describe_entity(entity_id, include_neighbors=True)
        retrieval_query = focus or stage or "SRPVDAL pipeline"
        retrieval = self.corpus.search(retrieval_query, top_k=3)
        return {
            "stage": stage or "srpvdal",
            "focus": focus,
            "graph_context": explanation,
            "retrieval": retrieval,
        }

    def _handle_guide_answer(self, payload: dict[str, Any]) -> dict[str, Any]:
        from . import briefing_guide

        return briefing_guide.answer_question(
            str(payload.get("question", "")),
            domain=str(payload.get("domain", "")),
            role=str(payload.get("role", "")),
        )

    def _handle_guide_memory_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        from . import briefing_guide

        return briefing_guide.summarize(self.data_dir / "guide_interactions.jsonl")

    def _handle_graph_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.graph_decision.build_context(
            payload["intent"],
            top_k=payload["top_k"],
            constraints=payload["constraints"],
        )

    def _handle_graph_simulation(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.graph_decision.simulate_action(
            payload["intent"],
            proposed_action=payload["proposed_action"],
            constraints=payload["constraints"],
            top_k=payload["top_k"],
        )

    def _handle_graph_loop(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.graph_decision.run_decision_loop(
            payload["intent"],
            goal=payload["goal"],
            proposed_action=payload["proposed_action"],
            constraints=payload["constraints"],
            top_k=payload["top_k"],
        )

    def health_snapshot(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "tool_count": len(self.registry.list_tools()),
            "skill_count": len(self.skill_store.all()),
            "document_count": len(self.corpus.documents),
            "graph_entity_count": self.knowledge_graph.node_count,
            "graph_native_loop_count": len(self.graph_decision.recent_loops(limit=100)),
            "graph_native_subagent_count": len(self.graph_decision.list_subagents()),
            "gaql_validation_count": len(self.google_ads.recent_validations(limit=100)),
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return self.registry.list_tools()

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.registry.call(name, arguments)

    def discover(self) -> dict[str, Any]:
        return self.boss.discover()

    def learn_skill(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.boss.learn_skill(
            name=payload["name"],
            description=payload["description"],
            trigger_phrases=payload["trigger_phrases"],
            preferred_tools=payload.get("preferred_tools", []),
            examples=payload.get("examples", []),
        )

    def learn_skill_from_loop(self, trace_id: str = "", name: str = "", description: str = "") -> dict[str, Any]:
        return self.boss.learn_skill_from_loop(trace_id=trace_id, name=name, description=description)

    def execute(self, intent: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.boss.execute(intent, arguments)

    def recent_traces(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.boss.recent_traces(limit=limit)

    def graph_context(self, intent: str, top_k: int = 3, constraints: list[str] | None = None) -> dict[str, Any]:
        return self.graph_decision.build_context(intent, top_k=top_k, constraints=constraints)

    def simulate_graph_action(
        self,
        intent: str,
        proposed_action: str = "",
        constraints: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        return self.graph_decision.simulate_action(
            intent,
            proposed_action=proposed_action,
            constraints=constraints,
            top_k=top_k,
        )

    def run_decision_loop(
        self,
        intent: str,
        goal: str = "",
        proposed_action: str = "",
        constraints: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        return self.graph_decision.run_decision_loop(
            intent,
            goal=goal,
            proposed_action=proposed_action,
            constraints=constraints,
            top_k=top_k,
        )

    def list_subagents(self) -> list[dict[str, Any]]:
        return self.graph_decision.list_subagents()

    def recent_graph_loops(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.graph_decision.recent_loops(limit=limit)

    def validate_gaql(self, query: Any, api_version: Any = None, as_of: Any = None) -> dict[str, Any]:
        return self.google_ads.validate_query(query, api_version=api_version, as_of=as_of)

    def validate_gaql_batch(self, queries: Any, api_version: Any = None, as_of: Any = None) -> dict[str, Any]:
        return self.google_ads.validate_batch(queries, api_version=api_version, as_of=as_of)

    def google_ads_version_status(self, api_version: Any = None, as_of: Any = None) -> dict[str, Any]:
        return self.google_ads.version_status(api_version=api_version, as_of=as_of)

    def google_ads_field_metadata(self, resource: Any = None) -> dict[str, Any]:
        cleaned = resource.strip() if isinstance(resource, str) and resource.strip() else None
        return self.google_ads.field_metadata(cleaned)

    def recent_gaql_validations(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.google_ads.recent_validations(limit=limit)

    def normalize_journey_event(self, source: str, payload: Any) -> dict[str, Any]:
        return self.journey.normalize_event(source, payload)

    def ingest_journey_events(
        self,
        source: str,
        events: Any,
        replay: bool = False,
    ) -> dict[str, Any]:
        return self.journey.ingest(source, events, replay=replay)

    def recent_journey_events(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.journey.recent_events(limit=limit)

    def build_journey_envelope(
        self,
        source: str,
        payload: Any,
        *,
        business_context: dict[str, Any] | None = None,
        reasoning_context: dict[str, Any] | None = None,
        causal: dict[str, Any] | None = None,
        intelligence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = self.journey.normalize_event(source, payload)
        result = self.envelope_builder.build_and_validate(
            normalized["event"],
            business_context=business_context,
            reasoning_context=reasoning_context,
            causal=causal,
            intelligence=intelligence,
        )
        # Stateful cross-event identity stitching: upgrade identity_cluster from the
        # builder's deterministic null to a resolved cluster id, then re-validate.
        resolution = self.identity_resolver.resolve_actor(normalized["event"].get("actor", {}))
        result["envelope"]["identity"]["identity_cluster"] = resolution["identity_cluster"]
        errors = self.envelope_builder.schema.validate(result["envelope"])
        result["valid"] = not errors
        result["errors"] = errors
        result["identity_resolution"] = resolution
        result["canonical_valid"] = normalized["valid"]
        result["canonical_errors"] = normalized["errors"]
        return result

    def resolve_identity(self, actor: Any) -> dict[str, Any]:
        return self.identity_resolver.resolve_actor(actor)

    def identity_cluster_stats(self) -> dict[str, Any]:
        return self.identity_resolver.stats()

    def virtuoso_registry(self) -> dict[str, Any]:
        return self.virtuoso.registry_snapshot()

    def resolve_virtuoso_model(self, role: Any) -> dict[str, Any]:
        return self.virtuoso.resolve(role)

    def scan_legacy_model_strings(self, text: Any, source: str = "inline") -> dict[str, Any]:
        return self.virtuoso.scan_text(text, source=source)

    def recent_reasoning_traces(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.virtuoso.recent_traces(limit=limit)


def create_runtime(base_dir: Path | None = None, data_dir: Path | None = None) -> BossRuntime:
    return BossRuntime(base_dir=base_dir, data_dir=data_dir)
