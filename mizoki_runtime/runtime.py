from __future__ import annotations

import html
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


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


def _strip_markup(raw_text: str) -> str:
    without_blocks = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_text)
    without_tags = re.sub(r"(?s)<[^>]+>", " ", without_blocks)
    collapsed = re.sub(r"\s+", " ", html.unescape(without_tags)).strip()
    return collapsed


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
            payload["default"] = self.default
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

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "tags": list(self.tags),
            "kind": "alias" if self.alias_target else "tool",
        }
        if self.alias_target:
            payload["alias_target"] = self.alias_target
            if self.default_arguments:
                payload["default_arguments"] = self.default_arguments
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
    "validation_arbitration": {
        "name": "Validation & Arbitration Layer",
        "type": "governance",
        "summary": "Planner, verifier, risk, and policy evaluation layer that challenges actions before they are approved.",
        "aliases": ("validation layer", "arbitration", "verifier"),
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
        "summary": "Sense, Reason, Plan, Validate, Decide, Act, Learn workflow for governed autonomous decisions.",
        "aliases": ("sensed reason plan validate decide act learn", "pipeline", "loop"),
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
    "validate": {
        "name": "Validate",
        "type": "stage",
        "summary": "Challenge plans against policies, graph constraints, and simulation outcomes.",
        "aliases": ("verify", "validation"),
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
    ("plan", "feeds", "validate"),
    ("validate", "feeds", "decide"),
    ("decide", "governed_by", "decision_control_plane"),
    ("decide", "feeds", "act"),
    ("act", "feeds", "learn"),
    ("learn", "updates", "knowledge_graph"),
    ("validate", "uses", "validation_arbitration"),
    ("validate", "uses", "counterfactual_simulation"),
    ("srpvdal", "contains", "sense"),
    ("srpvdal", "contains", "reason"),
    ("srpvdal", "contains", "plan"),
    ("srpvdal", "contains", "validate"),
    ("srpvdal", "contains", "decide"),
    ("srpvdal", "contains", "act"),
    ("srpvdal", "contains", "learn"),
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


class SkillStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._skills: list[LearnedSkill] = self._load()

    def _load(self) -> list[LearnedSkill]:
        if not self.file_path.exists():
            return []
        payload = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [LearnedSkill.from_dict(item) for item in payload]

    def _save(self) -> None:
        payload = [skill.to_dict() for skill in self._skills]
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def all(self) -> list[LearnedSkill]:
        return list(self._skills)

    def add(self, skill: LearnedSkill) -> LearnedSkill:
        if any(existing.name == skill.name for existing in self._skills):
            raise ValueError(f"skill already exists: {skill.name}")
        self._skills.append(skill)
        self._save()
        return skill

    def match(self, intent: str) -> list[LearnedSkill]:
        normalized_intent = intent.lower()
        matches = []
        for skill in self._skills:
            if any(trigger.lower() in normalized_intent for trigger in skill.trigger_phrases):
                matches.append(skill)
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

    def _validate_arguments(self, definition: ToolDefinition, arguments: dict[str, Any] | None) -> dict[str, Any]:
        arguments = dict(arguments or {})
        allowed_parameters = {parameter.name: parameter for parameter in definition.parameters}
        unexpected = sorted(key for key in arguments if key not in allowed_parameters)
        if unexpected:
            raise ValueError(f"unexpected parameters for {definition.name}: {', '.join(unexpected)}")

        validated: dict[str, Any] = {}
        for parameter in definition.parameters:
            if parameter.name in arguments:
                validated[parameter.name] = _coerce_value(parameter.type, arguments[parameter.name])
                continue
            if parameter.default is not None:
                validated[parameter.name] = parameter.default
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
        if name in self._definitions:
            raise ValueError(f"tool already registered: {name}")
        target_definition = self.get(target_tool)
        alias_definition = ToolDefinition(
            name=name,
            description=description,
            category=target_definition.category,
            parameters=target_definition.parameters,
            tags=tuple(tags or target_definition.tags),
            alias_target=target_tool,
            default_arguments=dict(default_arguments or {}),
        )
        self.register(alias_definition)
        if persist:
            aliases = []
            if self.alias_file.exists():
                aliases = json.loads(self.alias_file.read_text(encoding="utf-8"))
            aliases.append(
                {
                    "name": name,
                    "description": description,
                    "target_tool": target_tool,
                    "default_arguments": default_arguments or {},
                    "tags": tags or list(target_definition.tags),
                }
            )
            self.alias_file.write_text(json.dumps(aliases, indent=2), encoding="utf-8")
        return alias_definition.to_public_dict()

    def load_aliases(self) -> None:
        if not self.alias_file.exists():
            return
        aliases = json.loads(self.alias_file.read_text(encoding="utf-8"))
        for alias in aliases:
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
        trace_file: Path,
    ) -> None:
        self.registry = registry
        self.skill_store = skill_store
        self.corpus = corpus
        self.knowledge_graph = knowledge_graph
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
        }

    def learn_skill(
        self,
        name: str,
        description: str,
        trigger_phrases: list[str],
        preferred_tools: list[str] | None = None,
        examples: list[str] | None = None,
    ) -> dict[str, Any]:
        preferred_tools = preferred_tools or []
        for tool_name in preferred_tools:
            self.registry.get(tool_name)
        skill = LearnedSkill(
            name=name,
            description=description,
            trigger_phrases=tuple(trigger_phrases),
            preferred_tools=tuple(preferred_tools),
            examples=tuple(examples or []),
        )
        stored = self.skill_store.add(skill)
        return stored.to_dict()

    def recent_traces(self, limit: int = 5) -> list[dict[str, Any]]:
        if not self.trace_file.exists():
            return []
        lines = [line for line in self.trace_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        traces = [json.loads(line) for line in lines[-limit:]]
        traces.reverse()
        return traces

    def execute(self, intent: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if not intent.strip():
            raise ValueError("intent must not be empty")

        context = self._build_context(intent)
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
            "selection": selection.to_dict(),
            "execution": execution,
        }

    def _build_context(self, intent: str) -> dict[str, Any]:
        entity_matches = self.knowledge_graph.search_entities(intent)
        retrieval = self.corpus.search(intent, top_k=3)
        skill_matches = [skill.to_dict() for skill in self.skill_store.match(intent)]
        return {
            "matched_entities": entity_matches,
            "retrieval": retrieval,
            "matched_skills": skill_matches,
        }

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
            "validate": "validate",
            "verify": "validate",
            "decide": "decide",
            "act": "act",
            "learn": "learn",
        }

        if tool_name == "graphrag.query":
            arguments.setdefault("query", intent)
        elif tool_name == "kg.describe_entity":
            if "entity_id" not in arguments and context["matched_entities"]:
                arguments["entity_id"] = context["matched_entities"][0]["entity_id"]
        elif tool_name == "kg.list_neighbors":
            if "entity_id" not in arguments and context["matched_entities"]:
                arguments["entity_id"] = context["matched_entities"][0]["entity_id"]
        elif tool_name == "decision.explain_pipeline":
            lowered_intent = intent.lower()
            for keyword, stage in stage_map.items():
                if keyword in lowered_intent:
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
        lowered_intent = intent.lower()
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

        if definition.name.startswith("kg.") and context["matched_entities"]:
            score += 2.5
            reasons.append("knowledge graph entity matched")

        if definition.name == "decision.explain_pipeline" and any(word in lowered_intent for word in ("pipeline", "stage", "flow", "srpvdal", "dcp")):
            score += 3
            reasons.append("pipeline explanation intent detected")

        if definition.name == "tools.list" and any(word in lowered_intent for word in ("tool", "tools", "discover", "available")):
            score += 5
            reasons.append("tool discovery intent detected")

        if definition.name == "skills.list" and any(word in lowered_intent for word in ("skill", "skills")) and "learn" not in lowered_intent:
            score += 5
            reasons.append("skill discovery intent detected")

        if definition.name == "skills.learn" and any(word in lowered_intent for word in ("learn", "teach", "memorize", "new skill")):
            score += 6
            reasons.append("skill learning intent detected")

        if definition.name == "tools.register_alias" and any(word in lowered_intent for word in ("register tool", "new tool", "tool alias", "add tool")):
            score += 6
            reasons.append("tool registration intent detected")

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
            score -= 5
            reasons.append("missing required parameters")

        if definition.alias_target:
            score += 0.25

        return score, reasons

    def _select_tool(
        self,
        intent: str,
        provided_arguments: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[ToolSelection, list[dict[str, Any]]]:
        candidates: list[tuple[float, ToolDefinition, dict[str, Any], list[str]]] = []
        for tool in (self.registry.get(item["name"]) for item in self.registry.list_tools()):
            inferred_arguments, complete = self._infer_arguments(tool.name, provided_arguments, context, intent)
            score, reasons = self._score_tool(tool, intent, inferred_arguments, context, complete)
            candidates.append((score, tool, inferred_arguments, reasons))

        candidates.sort(key=lambda item: item[0], reverse=True)
        if not candidates or candidates[0][0] <= 0:
            fallback_arguments, _ = self._infer_arguments("graphrag.query", provided_arguments, context, intent)
            selection = ToolSelection(
                tool_name="graphrag.query",
                confidence=0.25,
                reasons=("fallback to GraphRAG retrieval",),
                arguments=fallback_arguments,
            )
            candidate_payload = []
            return selection, candidate_payload

        top_score, top_tool, top_arguments, top_reasons = candidates[0]
        second_score = candidates[1][0] if len(candidates) > 1 else 0.0
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
                "reasons": reasons,
            }
            for score, tool, _, reasons in candidates[:5]
        ]
        return selection, candidate_payload


class BossRuntime:
    def __init__(self, base_dir: Path | None = None, data_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or Path(__file__).resolve().parent.parent).resolve()
        self.data_dir = (data_dir or (self.base_dir / "data")).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.corpus = SiteCorpus(self.base_dir)
        self.knowledge_graph = KnowledgeGraph(self.corpus)
        self.skill_store = SkillStore(self.data_dir / "boss_skills.json")
        self.registry = ToolRegistry(self.data_dir / "tool_aliases.json")
        self._register_tools()
        self.registry.load_aliases()
        self.boss = BossAgent(
            registry=self.registry,
            skill_store=self.skill_store,
            corpus=self.corpus,
            knowledge_graph=self.knowledge_graph,
            trace_file=self.data_dir / "boss_decision_log.jsonl",
        )

    def _register_tools(self) -> None:
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

    def health_snapshot(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "tool_count": len(self.registry.list_tools()),
            "skill_count": len(self.skill_store.all()),
            "document_count": len(self.corpus.documents),
            "graph_entity_count": self.knowledge_graph.node_count,
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

    def execute(self, intent: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.boss.execute(intent, arguments)

    def recent_traces(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.boss.recent_traces(limit=limit)


def create_runtime(base_dir: Path | None = None, data_dir: Path | None = None) -> BossRuntime:
    return BossRuntime(base_dir=base_dir, data_dir=data_dir)
