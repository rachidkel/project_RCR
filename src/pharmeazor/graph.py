
"""Knowledge graph for Pharmeazor.

The graph represents DCI, therapeutic classes, aliases,
documented interactions and their documentary sources.
"""

from __future__ import annotations

import json
import unicodedata
from collections import Counter, deque
from pathlib import Path
from typing import Any

import networkx as nx


class KnowledgeGraph:
    """Build and query the Pharmeazor knowledge graph."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    @staticmethod
    def _normalize(value: str) -> str:
        """Return a canonical identifier without accents."""
        if not isinstance(value, str):
            return ""

        value = unicodedata.normalize("NFKD", value)
        value = "".join(
            char for char in value
            if not unicodedata.combining(char)
        )
        return " ".join(value.upper().strip().split())

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        **attributes: Any,
    ) -> None:
        entity_id = self._normalize(entity_id)

        if not entity_id:
            return

        if entity_id not in self.graph:
            self.graph.add_node(
                entity_id,
                type=entity_type,
                **attributes,
            )
        else:
            # Do not accidentally change an existing node's type.
            self.graph.nodes[entity_id].update(attributes)

    
    def add_relation(
        self,
        source: str,
        target: str,
        relation: str,
        **attributes: Any,
    ) -> None:
        source = self._normalize(source)
        target = self._normalize(target)

        if not source or not target:
            return

        # Avoid duplicate edges with the same relation and attributes.
        existing = self.graph.get_edge_data(
            source, target, default={}
        )

        for edge_data in existing.values():
            if (
                edge_data.get("relation") == relation
                and all(
                    edge_data.get(key) == value
                    for key, value in attributes.items()
                )
                and all(
                    key in attributes
                    for key in edge_data
                    if key != "relation"
                )
            ):
                return

        self.graph.add_edge(
            source,
            target,
            relation=relation,
            **attributes,
        )


    def add_dci(
        self,
        dci: str,
        classes: list[str] | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        dci = self._normalize(dci)

        if not dci:
            return

        self.add_entity(dci, "dci", label=dci)

        for therapeutic_class in classes or []:
            therapeutic_class = self._normalize(therapeutic_class)

            if not therapeutic_class:
                continue

            self.add_entity(
                therapeutic_class,
                "class",
                label=therapeutic_class,
            )
            self.add_relation(dci, therapeutic_class, "member_of")

        for alias in aliases or []:
            alias = self._normalize(alias)

            if not alias or alias == dci:
                continue

            self.add_entity(alias, "alias", label=alias)
            self.add_relation(alias, dci, "alias_of")

    def add_interaction(
        self,
        interaction_id: str,
        label: str,
        substances: list[str] | None = None,
        classes: list[str] | None = None,
        source: str | None = None,
        description: str = "",
        level: str = "",
    ) -> None:
        self.add_entity(
            interaction_id,
            "interaction",
            label=label,
            description=description,
            level=level,
        )

        for substance in substances or []:
            substance = self._normalize(substance)
            self.add_entity(substance, "dci", label=substance)
            self.add_relation(interaction_id, substance, "involves")

        for therapeutic_class in classes or []:
            therapeutic_class = self._normalize(therapeutic_class)
            self.add_entity(
                therapeutic_class,
                "class",
                label=therapeutic_class,
            )
            self.add_relation(
                interaction_id,
                therapeutic_class,
                "involves",
            )

        if source:
            self.add_entity(source, "source", label=source)
            self.add_relation(
                interaction_id,
                source,
                "documented_in",
            )

    def neighbors(self, entity: str) -> list[dict[str, Any]]:
        """Return incoming and outgoing neighbors."""
        entity = self._normalize(entity)

        if entity not in self.graph:
            return []

        results = []

        for _, target, data in self.graph.out_edges(
            entity, data=True
        ):
            results.append({
                "entity": target,
                "direction": "outgoing",
                **data,
            })

        for source, _, data in self.graph.in_edges(
            entity, data=True
        ):
            results.append({
                "entity": source,
                "direction": "incoming",
                **data,
            })

        return results

    def interactions_for(self, dci: str) -> list[dict[str, Any]]:
        """Find direct and class-level interactions for a DCI."""
        dci = self._normalize(dci)

        if dci not in self.graph:
            return []

        relevant_nodes = {dci}

        # Retrieve all therapeutic classes of this DCI.
        for _, target, data in self.graph.out_edges(
            dci, data=True
        ):
            if data.get("relation") == "member_of":
                relevant_nodes.add(target)

        results: dict[str, dict[str, Any]] = {}

        for node in relevant_nodes:
            for interaction, _, edge_data in self.graph.in_edges(
                node, data=True
            ):
                if (
                    self.graph.nodes[interaction].get("type")
                    != "interaction"
                    or edge_data.get("relation") != "involves"
                ):
                    continue

                if interaction not in results:
                    results[interaction] = {
                        "id": interaction,
                        **self.graph.nodes[interaction],
                        "matched_via": [],
                    }

                match = (
                    "direct"
                    if node == dci
                    else "therapeutic_class"
                )

                results[interaction]["matched_via"].append({
                    "entity": node,
                    "scope": match,
                })

        return [
            results[key]
            for key in sorted(results)
        ]

    def paths(
        self,
        src: str,
        dst: str,
        max_depth: int = 3,
    ) -> list[list[str]]:
        """Return directed paths up to max_depth."""
        src = self._normalize(src)
        dst = self._normalize(dst)

        if (
            src not in self.graph
            or dst not in self.graph
            or max_depth < 0
        ):
            return []

        results = []
        queue = deque([[src]])

        while queue:
            path = queue.popleft()

            if len(path) - 1 > max_depth:
                continue

            current = path[-1]

            if current == dst:
                results.append(path)
                continue

            for neighbor in self.graph.successors(current):
                if neighbor not in path:
                    queue.append(path + [neighbor])

        return results

    def explain_absence(
        self,
        source: str,
        target: str,
    ) -> dict[str, Any]:
        """Explain the absence of a direct relation."""
        source = self._normalize(source)
        target = self._normalize(target)

        direct_edges = []

        if source in self.graph and target in self.graph:
            direct_edges = list(
                self.graph.get_edge_data(
                    source, target, default={}
                ).values()
            )

        if direct_edges:
            return {
                "direct_relation_found": True,
                "message": "A direct relation exists in the graph.",
                "evidence": direct_edges,
            }

        return {
            "direct_relation_found": False,
            "message": (
                "No direct relation was found between these entities "
                "in the currently loaded documentary corpus. "
                "This does not establish the absence of medical risk."
            ),
            "source": source,
            "target": target,
        }

    def stats(self) -> dict[str, Any]:
        """Return graph construction statistics."""
        orphan_nodes = [
            node
            for node in self.graph.nodes
            if self.graph.degree(node) == 0
        ]

        total = self.graph.number_of_nodes()

        return {
            "nodes": total,
            "edges": self.graph.number_of_edges(),
            "orphans": len(orphan_nodes),
            "orphan_rate": (
                len(orphan_nodes) / total if total else 0
            ),
            "node_types": dict(Counter(
                data.get("type", "unknown")
                for _, data in self.graph.nodes(data=True)
            )),
        }

    def save(self, path: str | Path) -> None:
        """Save the graph in JSON format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = nx.node_link_data(self.graph, edges="edges")

        with path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeGraph":
        """Load a graph from JSON."""
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)

        instance = cls()
        instance.graph = nx.node_link_graph(
            data,
            directed=True,
            multigraph=True,
            edges="edges",
        )
        return instance
