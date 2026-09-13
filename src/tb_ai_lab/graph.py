# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Deterministic, source-backed graph construction and traversal."""

from __future__ import annotations

from collections import deque
import json
import re
from urllib.parse import quote

from .contracts import Document, Evidence, Scope
from .storage import Index
from .text import terms


def graph_id(kind: str, label: str) -> str:
    return f"{kind}:{quote(' '.join(label.casefold().split()), safe='')}"


def relation_span(
    text: str, source_label: str, predicate: str, target_label: str
) -> tuple[int, int] | None:
    predicate_text = " ".join(
        part for part in re.split(r"[-_\s]+", predicate.casefold()) if part
    )
    required = (source_label.casefold(), predicate_text, target_label.casefold())
    for sentence in re.finditer(r"[^.!?\n]+[.!?]?", text):
        folded = sentence.group(0).casefold()
        if all(value and value in folded for value in required):
            leading = len(sentence.group(0)) - len(sentence.group(0).lstrip())
            trailing = len(sentence.group(0)) - len(sentence.group(0).rstrip())
            return sentence.start() + leading, sentence.end() - trailing
    return None


class Graph:
    def __init__(self, index: Index) -> None:
        self.index = index
        self.connection = index.connection
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS graph_nodes(
              id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              kind TEXT NOT NULL,
              label TEXT NOT NULL,
              source_document_id TEXT NOT NULL,
              PRIMARY KEY(id, tenant, collection_name, source_document_id)
            );
            CREATE TABLE IF NOT EXISTS graph_edges(
              id TEXT PRIMARY KEY,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              source_id TEXT NOT NULL,
              predicate TEXT NOT NULL,
              target_id TEXT NOT NULL,
              source_document_id TEXT NOT NULL,
              confidence REAL NOT NULL,
              provenance TEXT NOT NULL,
              source_start INTEGER NOT NULL,
              source_end INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS graph_edges_scope_source
              ON graph_edges(tenant, collection_name, source_id);
            CREATE INDEX IF NOT EXISTS graph_edges_scope_target
              ON graph_edges(tenant, collection_name, target_id);
            CREATE INDEX IF NOT EXISTS graph_nodes_source_document
              ON graph_nodes(source_document_id);
            CREATE INDEX IF NOT EXISTS graph_edges_source_document
              ON graph_edges(source_document_id);
            """
        )

    def add_document(self, document: Document) -> int:
        metadata = document.metadata
        entities = metadata.get("entities", {})
        relations = metadata.get("relations", [])
        if not isinstance(entities, dict) or not isinstance(relations, list):
            return 0
        document_node = graph_id("document", document.id)
        contributions: list[tuple[str, str, str, int, int]] = []
        with self.connection:
            self.connection.execute(
                """DELETE FROM graph_edges WHERE source_document_id = ?
                   AND tenant = ? AND collection_name = ?""",
                (document.id, document.tenant, document.collection),
            )
            self.connection.execute(
                """DELETE FROM graph_nodes WHERE source_document_id = ?
                   AND tenant = ? AND collection_name = ?""",
                (document.id, document.tenant, document.collection),
            )
            self._node(document_node, "document", document.title or document.id, document)
            for kind, labels in entities.items():
                if not isinstance(labels, list):
                    continue
                for label in labels[:20]:
                    if not isinstance(label, str) or label.casefold() not in document.text.casefold():
                        continue
                    target = graph_id(str(kind), label)
                    self._node(target, str(kind), label, document)
                    label_start = document.text.casefold().find(label.casefold())
                    contributions.append(
                        (
                            document_node,
                            "mentions",
                            target,
                            label_start,
                            label_start + len(label),
                        )
                    )
            for relation in relations[:100]:
                if not isinstance(relation, dict):
                    continue
                source_label = str(relation.get("source", ""))[:300]
                target_label = str(relation.get("target", ""))[:300]
                predicate = str(relation.get("predicate", "related-to"))[:100]
                if not source_label or not target_label:
                    continue
                span = relation_span(document.text, source_label, predicate, target_label)
                if span is None:
                    continue
                source = graph_id(str(relation.get("source_type", "entity")), source_label)
                target = graph_id(str(relation.get("target_type", "entity")), target_label)
                self._node(source, str(relation.get("source_type", "entity")), source_label, document)
                self._node(target, str(relation.get("target_type", "entity")), target_label, document)
                contributions.append((source, predicate, target, *span))
            for index, (source, predicate, target, source_start, source_end) in enumerate(contributions):
                edge_id = (
                    f"edge:{quote(document.tenant, safe='')}:"
                    f"{quote(document.collection, safe='')}:"
                    f"{quote(document.id, safe='')}:{index}:{quote(predicate, safe='')}"
                )
                self.connection.execute(
                    "INSERT INTO graph_edges VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        edge_id,
                        document.tenant,
                        document.collection,
                        source,
                        predicate,
                        target,
                        document.id,
                        1.0,
                        "deterministic-local",
                        source_start,
                        source_end,
                    ),
                )
        return len(contributions)

    def _node(self, node_id: str, kind: str, label: str, document: Document) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO graph_nodes VALUES(?, ?, ?, ?, ?, ?)",
            (node_id, document.tenant, document.collection, kind, label[:300], document.id),
        )

    def neighborhood(self, query: str, scope: Scope, depth: int = 2, limit: int = 24) -> dict[str, object]:
        depth = max(1, min(depth, 4))
        query_terms = set(terms(query))
        rows = self.connection.execute(
            """SELECT DISTINCT id, kind, label FROM graph_nodes
               WHERE tenant = ? AND collection_name = ?""",
            (scope.tenant, scope.collection),
        )
        seeds = [row for row in rows if query_terms & set(terms(row["label"]))]
        queue = deque((row["id"], 0) for row in seeds[:limit])
        visited = {row["id"] for row in seeds[:limit]}
        visited_edges: set[str] = set()
        edges: list[dict[str, object]] = []
        document_ids: set[str] = set()
        while queue and len(edges) < limit:
            node_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            adjacent = self.connection.execute(
                """SELECT * FROM graph_edges WHERE tenant = ? AND collection_name = ?
                   AND (source_id = ? OR target_id = ?) ORDER BY id LIMIT ?""",
                (scope.tenant, scope.collection, node_id, node_id, limit),
            )
            for row in adjacent:
                if row["id"] in visited_edges:
                    continue
                visited_edges.add(row["id"])
                record = dict(row)
                edges.append(record)
                document_ids.add(row["source_document_id"])
                other = row["target_id"] if row["source_id"] == node_id else row["source_id"]
                if other not in visited:
                    visited.add(other)
                    queue.append((other, current_depth + 1))
                if len(edges) >= limit:
                    break
        return {
            "seed_ids": [row["id"] for row in seeds[:limit]],
            "node_ids": sorted(visited),
            "edges": edges,
            "document_ids": sorted(document_ids),
        }

    def evidence(self, query: str, scope: Scope, depth: int = 2, limit: int = 8) -> list[Evidence]:
        result = self.neighborhood(query, scope, depth, limit * 3)
        evidence: list[Evidence] = []
        locations = sorted(
            {
                (str(edge["source_document_id"]), int(edge["source_start"]))
                for edge in result["edges"]
            }
        )
        for document_id, source_start in locations:
            chunks = self.index.chunks_for_document(str(document_id), scope)
            matching = [
                item for item in chunks if item.start <= source_start < item.end
            ]
            if matching:
                item = matching[0]
                evidence.append(
                    Evidence(
                        chunk_id=item.chunk_id,
                        document_id=item.document_id,
                        tenant=item.tenant,
                        collection=item.collection,
                        text=item.text,
                        start=item.start,
                        end=item.end,
                        score=1.0 / 61.0,
                        channels=("graph",),
                        section=item.section,
                    )
                )
        deduped = {item.chunk_id: item for item in evidence}
        return list(deduped.values())[:limit]

    def path(self, source_label: str, target_label: str, scope: Scope, max_depth: int = 4) -> list[dict[str, object]]:
        def matching_ids(label: str) -> list[str]:
            rows = self.connection.execute(
                """SELECT DISTINCT id FROM graph_nodes WHERE tenant = ?
                   AND collection_name = ? AND lower(label) = lower(?)""",
                (scope.tenant, scope.collection, label),
            )
            return [row[0] for row in rows]

        sources = matching_ids(source_label)
        targets = set(matching_ids(target_label))
        queue = deque((source, []) for source in sources)
        visited = set(sources)
        while queue:
            node_id, path = queue.popleft()
            if node_id in targets:
                return path
            if len(path) >= max_depth:
                continue
            rows = self.connection.execute(
                """SELECT * FROM graph_edges WHERE tenant = ? AND collection_name = ?
                   AND (source_id = ? OR target_id = ?)
                   ORDER BY predicate = 'mentions', id""",
                (scope.tenant, scope.collection, node_id, node_id),
            )
            for row in rows:
                other = row["target_id"] if row["source_id"] == node_id else row["source_id"]
                if other not in visited:
                    visited.add(other)
                    queue.append((other, path + [dict(row)]))
        return []

    def export(self, scope: Scope) -> dict[str, object]:
        nodes = [
            dict(row)
            for row in self.connection.execute(
                """SELECT * FROM graph_nodes WHERE tenant = ? AND collection_name = ?
                   ORDER BY id, source_document_id""",
                (scope.tenant, scope.collection),
            )
        ]
        edges = [
            dict(row)
            for row in self.connection.execute(
                "SELECT * FROM graph_edges WHERE tenant = ? AND collection_name = ? ORDER BY id",
                (scope.tenant, scope.collection),
            )
        ]
        return {"nodes": nodes, "edges": edges, "digest_input": json.dumps([nodes, edges], sort_keys=True)}
