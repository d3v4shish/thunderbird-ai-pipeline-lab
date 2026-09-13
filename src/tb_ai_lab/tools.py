# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Bounded, scope-locked, read-only document tools."""

from __future__ import annotations

from collections import Counter
from typing import Any
from urllib.parse import quote

from .contracts import Evidence, Scope
from .graph import Graph
from .storage import Index


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "document_outline",
            "description": "List source-backed passage ranges for one document.",
            "parameters": {
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_passages",
            "description": "Search untrusted document evidence within the locked scope.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "mode": {"type": "string", "enum": ["exact", "lexical", "dense", "hybrid"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 24},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_passage",
            "description": "Fetch one passage by its exact identifier in the locked scope.",
            "parameters": {
                "type": "object",
                "properties": {"chunk_id": {"type": "string"}},
                "required": ["chunk_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "range_coverage",
            "description": "Page through source ranges for one document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "offset": {"type": "integer", "minimum": 0},
                    "length": {"type": "integer", "minimum": 1, "maximum": 4000},
                },
                "required": ["document_id", "offset"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "graph_neighborhood",
            "description": "Return deterministic graph relations matching a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "depth": {"type": "integer", "minimum": 1, "maximum": 4},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "graph_path",
            "description": "Find a deterministic source-backed path between two labels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                },
                "required": ["source", "target"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "document_aggregate",
            "description": "Count documents by a canonical metadata field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": ["category", "status"]}
                },
                "required": ["field"],
                "additionalProperties": False,
            },
        },
    },
]


class ToolError(ValueError):
    pass


class ToolExecutor:
    def __init__(
        self,
        index: Index,
        graph: Graph,
        scope: Scope,
        allowed: tuple[str, ...] | list[str] | None = None,
        max_calls: int = 6,
        max_evidence: int = 24,
    ) -> None:
        self.index = index
        self.graph = graph
        self.scope = scope
        self.allowed = set(self.names() if allowed is None else allowed)
        self.max_calls = max_calls
        self.max_evidence = max_evidence
        self.calls: list[dict[str, Any]] = []
        self.evidence: list[Evidence] = []
        self.evidence_returned = 0

    @staticmethod
    def names() -> tuple[str, ...]:
        return tuple(item["function"]["name"] for item in TOOL_SCHEMAS)

    def schemas(self) -> list[dict[str, Any]]:
        return [item for item in TOOL_SCHEMAS if item["function"]["name"] in self.allowed]

    def execute(self, name: str, arguments: Any) -> dict[str, Any]:
        record: dict[str, Any] = {"name": name, "arguments": arguments}
        try:
            if len(self.calls) >= self.max_calls:
                raise ToolError("Tool call budget exhausted")
            if name not in self.names() or name not in self.allowed:
                raise ToolError(f"Tool is not allowed: {name}")
            if not isinstance(arguments, dict):
                raise ToolError("Tool arguments must be an object")
            schema = next(
                item["function"]["parameters"]
                for item in TOOL_SCHEMAS
                if item["function"]["name"] == name
            )
            properties = set(schema["properties"])
            extras = sorted(set(arguments) - properties)
            missing = sorted(set(schema.get("required", [])) - set(arguments))
            if extras:
                raise ToolError(f"Unknown tool arguments: {', '.join(extras)}")
            if missing:
                raise ToolError(f"Missing tool arguments: {', '.join(missing)}")
            handler = getattr(self, f"_tool_{name}")
            result = handler(arguments)
        except ToolError as error:
            record.update({"accepted": False, "error": str(error)})
            self.calls.append(record)
            raise
        record.update({"accepted": True, "result": result})
        self.calls.append(record)
        return result

    def _remember_evidence(self, items: list[Evidence]) -> None:
        known = {item.citation for item in self.evidence}
        for item in items:
            if item.citation not in known and len(self.evidence) < self.max_evidence:
                self.evidence.append(item)
                known.add(item.citation)
        self.evidence_returned = len(self.evidence)

    @staticmethod
    def _bounded_string(arguments: dict[str, Any], name: str, limit: int = 2000) -> str:
        value = arguments.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ToolError(f"{name} must be a non-empty string")
        value = value.strip()
        if len(value) > limit:
            raise ToolError(f"{name} exceeds {limit} characters")
        return value

    @staticmethod
    def _bounded_integer(
        arguments: dict[str, Any], name: str, default: int, minimum: int, maximum: int
    ) -> int:
        value = arguments.get(name, default)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ToolError(f"{name} must be an integer")
        if value < minimum or value > maximum:
            raise ToolError(f"{name} must be between {minimum} and {maximum}")
        return value

    def _available_evidence(self, requested: int) -> int:
        remaining = self.max_evidence - self.evidence_returned
        return max(0, min(requested, remaining))

    def _tool_document_outline(self, arguments: dict[str, Any]) -> dict[str, Any]:
        document_id = self._bounded_string(arguments, "document_id", 1000)
        document = self.index.document(document_id, self.scope)
        if not document:
            return {"document_id": document_id, "found": False, "passages": []}
        chunks = self.index.chunks_for_document(document_id, self.scope)
        count = min(len(chunks), self.max_evidence)
        return {
            "document_id": document_id,
            "found": True,
            "bytes": len(document.text.encode("utf-8")),
            "characters": len(document.text),
            "passages": [
                {"chunk_id": item.chunk_id, "start": item.start, "end": item.end, "section": item.section}
                for item in chunks[:count]
            ],
            "untrusted_evidence": True,
        }

    def _tool_search_passages(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = self._bounded_string(arguments, "query", 10_000)
        mode = arguments.get("mode", "hybrid")
        if mode not in {"exact", "lexical", "dense", "hybrid"}:
            raise ToolError("mode is invalid")
        requested = self._bounded_integer(arguments, "limit", 8, 1, 24)
        limit = self._available_evidence(requested)
        items = self.index.search(query, self.scope, mode, limit)
        self._remember_evidence(items)
        return {"results": [item.as_dict() for item in items], "untrusted_evidence": True}

    def _tool_fetch_passage(self, arguments: dict[str, Any]) -> dict[str, Any]:
        chunk_id = self._bounded_string(arguments, "chunk_id", 1200)
        if not self._available_evidence(1):
            return {"found": False, "budget_exhausted": True}
        item = self.index.chunk(chunk_id, self.scope)
        if item:
            self._remember_evidence([item])
        return {"found": bool(item), "passage": item.as_dict() if item else None, "untrusted_evidence": True}

    def _tool_range_coverage(self, arguments: dict[str, Any]) -> dict[str, Any]:
        document_id = self._bounded_string(arguments, "document_id", 1000)
        offset = self._bounded_integer(arguments, "offset", 0, 0, 16 * 1024 * 1024)
        length = self._bounded_integer(arguments, "length", 2000, 1, 4000)
        if not self._available_evidence(1):
            return {"found": False, "budget_exhausted": True}
        document = self.index.document(document_id, self.scope)
        if not document:
            return {"found": False}
        offset = min(offset, len(document.text))
        end = min(len(document.text), offset + length)
        evidence = Evidence(
            chunk_id=(
                f"{quote(self.scope.tenant, safe='')}/"
                f"{quote(self.scope.collection, safe='')}/"
                f"{quote(document_id, safe='')}:"
                f"range:{offset}-{end}"
            ),
            document_id=document_id,
            tenant=self.scope.tenant,
            collection=self.scope.collection,
            text=document.text[offset:end],
            start=offset,
            end=end,
            score=1.0,
            channels=("tool-range",),
        )
        self._remember_evidence([evidence])
        return {
            "found": True,
            "document_id": document_id,
            "start": offset,
            "end": end,
            "text": evidence.text,
            "next_offset": end if end < len(document.text) else None,
            "complete": end >= len(document.text),
            "citation": evidence.citation,
            "untrusted_evidence": True,
        }

    def _tool_graph_neighborhood(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = self._bounded_string(arguments, "query", 2000)
        depth = self._bounded_integer(arguments, "depth", 2, 1, 4)
        return {**self.graph.neighborhood(query, self.scope, depth), "untrusted_evidence": True}

    def _tool_graph_path(self, arguments: dict[str, Any]) -> dict[str, Any]:
        source = self._bounded_string(arguments, "source", 300)
        target = self._bounded_string(arguments, "target", 300)
        return {"path": self.graph.path(source, target, self.scope), "untrusted_evidence": True}

    def _tool_document_aggregate(self, arguments: dict[str, Any]) -> dict[str, Any]:
        field = arguments.get("field")
        if field not in {"category", "status"}:
            raise ToolError("field is invalid")
        rows = self.index.connection.execute(
            """SELECT metadata_json FROM documents WHERE tenant = ? AND collection_name = ?""",
            (self.scope.tenant, self.scope.collection),
        )
        counts: Counter[str] = Counter()
        import json

        for row in rows:
            value = json.loads(row[0]).get(field, "unknown")
            counts[str(value)] += 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        visible = ranked[:100]
        omitted = sum(count for _, count in ranked[100:])
        return {
            "field": field,
            "counts": dict(visible),
            "omitted_category_count": max(0, len(ranked) - len(visible)),
            "omitted_document_count": omitted,
            "source": "canonical-metadata",
        }
