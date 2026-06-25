"""Stateful identity-cluster resolver — cross-event identity stitching.

Upgrades the CanonicalEventEnvelope's ``identity.identity_cluster`` from null to a
resolved, deterministic cross-event cluster id by connecting events that share any
**strong** identifier (``user_id`` / ``email`` / ``phone_sha256`` / ``device_ifa``).
Weak signals (``ip``) are deliberately **not** stitched on — shared NAT/office IPs
would over-merge distinct people.

Mechanism: connected components via union-find with *union-by-min-root*, so a
cluster's id is a stable function of the lexicographically smallest strong token in
the component. The id changes only when two previously-separate clusters genuinely
merge (a deterministic, explainable event we surface as ``newly_merged``).

Deterministic and dependency-free; persists a JSON snapshot so clusters survive
across events and restarts. Same ephemeral-disk caveat as ``JourneyEventStore``: on
Cloud Run this holds per instance/revision — back it with a shared store for durable
cross-instance clusters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .journey import sha256_hex


# Only strong identifiers stitch events together. `ip` is intentionally excluded.
STRONG_IDENTITY_KEYS = ("user_id", "email", "phone_sha256", "device_ifa")


def _tokens(actor: Any) -> list[str]:
    if not isinstance(actor, dict):
        return []
    return [f"{key}:{actor[key]}" for key in STRONG_IDENTITY_KEYS if actor.get(key)]


class IdentityClusterResolver:
    """Persistent union-find over strong identity tokens."""

    def __init__(self, store_path: Any = None) -> None:
        self.store_path = Path(store_path) if store_path else None
        self.parent: dict[str, str] = {}
        self.size: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        if self.store_path and self.store_path.is_file():
            try:
                data = json.loads(self.store_path.read_text())
                self.parent = dict(data.get("parent", {}))
                self.size = {key: int(value) for key, value in data.get("size", {}).items()}
            except (ValueError, OSError):
                self.parent, self.size = {}, {}

    def _save(self) -> None:
        if not self.store_path:
            return
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
        tmp.write_text(json.dumps({"parent": self.parent, "size": self.size}))
        tmp.replace(self.store_path)

    def _find(self, token: str) -> str:
        root = token
        while self.parent.get(root, root) != root:
            root = self.parent[root]
        cursor = token
        while cursor != root:  # path compression
            nxt = self.parent.get(cursor, cursor)
            self.parent[cursor] = root
            cursor = nxt
        return root

    def _add(self, token: str) -> None:
        if token not in self.parent:
            self.parent[token] = token
            self.size[token] = 1

    def _attach(self, child_root: str, anchor: str) -> None:
        if child_root == anchor:
            return
        self.parent[child_root] = anchor
        self.size[anchor] = self.size.get(anchor, 1) + self.size.get(child_root, 1)
        self.size.pop(child_root, None)

    def resolve(self, actor: Any, *, persist: bool = True) -> dict[str, Any]:
        tokens = _tokens(actor)
        if not tokens:
            return {
                "identity_cluster": None,
                "cluster_root": None,
                "cluster_size": 0,
                "linked_keys": [],
                "anonymous": True,
                "newly_merged": False,
            }
        # Roots of tokens already seen in prior events. The anchor is an *established*
        # root when one exists, so a brand-new identifier joining a known cluster
        # adopts that cluster's id rather than relabeling it. Only an event bridging
        # >1 previously-separate known clusters relabels (deterministic min root).
        prior_roots = {self._find(token) for token in tokens if token in self.parent}
        for token in tokens:
            self._add(token)
        anchor = min(prior_roots) if prior_roots else min(tokens)
        for token in tokens:
            self._attach(self._find(token), anchor)
        if persist:
            self._save()
        return {
            "identity_cluster": f"Cluster:{sha256_hex(anchor)[:16]}",
            "cluster_root": anchor,
            "cluster_size": self.size.get(anchor, len(tokens)),
            "linked_keys": tokens,
            "anonymous": False,
            "newly_merged": len(prior_roots) > 1,
        }

    def stats(self) -> dict[str, Any]:
        roots = {self._find(token) for token in self.parent}
        return {
            "tokens": len(self.parent),
            "clusters": len(roots),
            "largest_cluster": max(self.size.values(), default=0),
        }


class IdentityResolutionCell:
    """SENSE-stage enrichment cell that resolves cross-event identity clusters."""

    def __init__(self, store_path: Any = None) -> None:
        self.resolver = IdentityClusterResolver(store_path)

    def resolve_actor(self, actor: Any) -> dict[str, Any]:
        return self.resolver.resolve(actor)

    def resolve_event(self, journey_event: Any) -> dict[str, Any]:
        actor = journey_event.get("actor", {}) if isinstance(journey_event, dict) else {}
        return self.resolver.resolve(actor)

    def stats(self) -> dict[str, Any]:
        return self.resolver.stats()

    def discovery_block(self) -> dict[str, Any]:
        return {
            "cell": "cell.sense.identity_resolver",
            "method": "union-find connected components (union-by-min-root)",
            "stitch_keys": list(STRONG_IDENTITY_KEYS),
            "excluded_keys": ["ip"],
            "deterministic": True,
            **self.stats(),
        }
