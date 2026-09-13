from __future__ import annotations

import unittest

from tb_ai_lab.cli import baseline_variant
from tb_ai_lab.contracts import Scope
from tb_ai_lab.corpus import documents
from tb_ai_lab.graph import Graph
from tb_ai_lab.pipeline import Pipeline
from tb_ai_lab.storage import Index
from tb_ai_lab.tools import ToolError, ToolExecutor
from tb_ai_lab.contracts import Document
from tb_ai_lab.text import fixed_chunks, sentence_window_chunks


class StorageGraphToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = Index()
        self.pipeline = Pipeline(self.index, baseline_variant())
        self.pipeline.ingest([Document.from_dict(item) for item in documents()])
        self.scope = Scope("tenant-alpha", "primary")

    def tearDown(self) -> None:
        self.index.close()

    def test_exact_search_separates_similar_identifiers(self) -> None:
        results = self.index.exact_search("ORBIT-731", self.scope)
        self.assertTrue(results)
        self.assertNotIn("exact-distractor", {item.document_id for item in results})
        self.assertTrue(all(self.index.verify_evidence(item, self.scope) for item in results))

    def test_tenant_scope_is_enforced_in_every_search_lane(self) -> None:
        for mode in ("exact", "lexical", "dense", "hybrid"):
            results = self.index.search("VAULT-440", self.scope, mode)
            self.assertNotIn("other-tenant-secret", {item.document_id for item in results})

    def test_embedding_reranker_uses_stored_vectors(self) -> None:
        first = Document(
            id="rerank-a",
            tenant=self.scope.tenant,
            collection=self.scope.collection,
            title="Shared result A",
            text="Shared retrieval phrase for candidate A.",
        )
        second = Document(
            id="rerank-b",
            tenant=self.scope.tenant,
            collection=self.scope.collection,
            title="Shared result B",
            text="Shared retrieval phrase for candidate B.",
        )
        first_chunks = fixed_chunks(first)
        second_chunks = fixed_chunks(second)
        self.index.add_document(first, first_chunks, {first_chunks[0].id: [1.0, 0.0]})
        self.index.add_document(second, second_chunks, {second_chunks[0].id: [0.0, 1.0]})
        candidates = self.index.lexical_search("shared retrieval phrase", self.scope)
        reranked = self.index.embedding_rerank([0.0, 1.0], candidates)
        self.assertEqual(reranked[0].document_id, "rerank-b")
        self.assertIn("embedding-rerank", reranked[0].channels)

    def test_normalized_parent_storage_preserves_results_without_text_duplication(self) -> None:
        document = Document(
            id="normalized-parent",
            tenant=self.scope.tenant,
            collection=self.scope.collection,
            title="Parent storage",
            text=" ".join(
                f"Sentence {index} discusses PROJECT-{index:03d} and retrieval behavior."
                for index in range(40)
            ),
        )
        chunks = sentence_window_chunks(document, parent_chars=600, limit=4096)
        self.assertGreater(len(chunks), len({(item.start, item.end) for item in chunks}))
        with Index() as legacy, Index(normalized_parent_storage=True) as normalized:
            legacy.add_document(document, chunks)
            normalized.add_document(document, chunks)
            query = "PROJECT-017 retrieval behavior"
            for mode in ("exact", "lexical", "dense", "hybrid"):
                legacy_results = legacy.search(query, self.scope, mode, candidate_mode="full-scan")
                normalized_results = normalized.search(
                    query, self.scope, mode, candidate_mode="full-scan"
                )
                self.assertEqual(
                    [item.as_dict() for item in normalized_results],
                    [item.as_dict() for item in legacy_results],
                )
                self.assertTrue(
                    all(normalized.verify_evidence(item, self.scope) for item in normalized_results)
                )
            legacy_stats = legacy.storage_stats()
            normalized_stats = normalized.storage_stats()
            self.assertEqual(normalized_stats["chunks"], legacy_stats["chunks"])
            self.assertLess(
                normalized_stats["parent_passage_characters"],
                legacy_stats["chunk_passage_characters"],
            )
            self.assertEqual(normalized_stats["chunk_passage_characters"], 0)

    def test_same_document_id_cannot_overwrite_another_scope(self) -> None:
        duplicate = Document(
            id="exact-orbit",
            tenant="tenant-beta",
            collection="private",
            title="Scoped duplicate",
            text="[FACT X02] scoped_value: PRIVATE-222.",
        )
        self.pipeline.ingest([duplicate])
        alpha = self.index.document("exact-orbit", self.scope)
        beta = self.index.document("exact-orbit", Scope("tenant-beta", "private"))
        self.assertIn("ORBIT-731", alpha.text)
        self.assertIn("PRIVATE-222", beta.text)

    def test_scope_delimiters_cannot_collide_chunk_ids(self) -> None:
        first = Document(
            id="same",
            tenant="tenant/a",
            collection="collection",
            title="First",
            text="[FACT Z01] value: FIRST-101.",
        )
        second = Document(
            id="same",
            tenant="tenant",
            collection="a/collection",
            title="Second",
            text="[FACT Z02] value: SECOND-202.",
        )
        self.pipeline.ingest([first, second])
        first_chunks = self.index.chunks_for_document(
            "same", Scope("tenant/a", "collection")
        )
        second_chunks = self.index.chunks_for_document(
            "same", Scope("tenant", "a/collection")
        )
        self.assertNotEqual(first_chunks[0].chunk_id, second_chunks[0].chunk_id)

    def test_graph_finds_source_backed_multihop_path(self) -> None:
        graph = Graph(self.index)
        path = graph.path("Priya Das", "Kestrel Works", self.scope)
        self.assertEqual([item["predicate"] for item in path], ["leads", "works-on", "depends-on"])
        self.assertTrue(all(item["provenance"] == "deterministic-local" for item in path))
        for item in path:
            document = self.index.document(item["source_document_id"], self.scope)
            assertion = document.text[item["source_start"] : item["source_end"]]
            self.assertIn(item["predicate"].replace("-", " "), assertion.casefold())
        neighborhood = graph.neighborhood("Priya Das team supplier", self.scope, 3)
        edge_ids = [item["id"] for item in neighborhood["edges"]]
        self.assertEqual(len(edge_ids), len(set(edge_ids)))

    def test_graph_rejects_relation_not_asserted_in_one_source_sentence(self) -> None:
        spoofed = Document(
            id="graph-spoof",
            tenant=self.scope.tenant,
            collection=self.scope.collection,
            title="Untrusted relation metadata",
            text="Alice appears here. Bob appears elsewhere.",
            metadata={
                "entities": {"person": ["Alice", "Bob"]},
                "relations": [
                    {
                        "source": "Alice",
                        "source_type": "person",
                        "predicate": "manages",
                        "target": "Bob",
                        "target_type": "person",
                    }
                ],
            },
        )
        self.pipeline.ingest([spoofed])
        edges = Graph(self.index).export(self.scope)["edges"]
        self.assertFalse(
            any(
                edge["source_document_id"] == spoofed.id
                and edge["predicate"] == "manages"
                for edge in edges
            )
        )

    def test_clear_removes_retrieval_and_graph_state(self) -> None:
        graph = Graph(self.index)
        self.assertTrue(graph.export(self.scope)["edges"])
        self.index.clear()
        self.assertEqual(self.index.search("ORBIT-731", self.scope, "hybrid"), [])
        self.assertEqual(graph.export(self.scope)["nodes"], [])
        self.assertEqual(graph.export(self.scope)["edges"], [])

    def test_tools_reject_unknown_or_disallowed_calls(self) -> None:
        executor = ToolExecutor(self.index, Graph(self.index), self.scope, allowed=["search_passages"])
        with self.assertRaises(ToolError):
            executor.execute("delete_document", {})
        with self.assertRaises(ToolError):
            executor.execute("graph_path", {"source": "a", "target": "b"})
        self.assertTrue(all(not call["accepted"] for call in executor.calls))

    def test_explicit_empty_tool_allowlist_denies_every_tool(self) -> None:
        executor = ToolExecutor(self.index, Graph(self.index), self.scope, allowed=[])
        self.assertEqual(executor.schemas(), [])
        with self.assertRaisesRegex(ToolError, "not allowed"):
            executor.execute("search_passages", {"query": "ORBIT-731"})
        self.assertFalse(executor.calls[0]["accepted"])

    def test_fetch_cannot_cross_scope(self) -> None:
        beta = Scope("tenant-beta", "private")
        beta_chunk = self.index.chunks_for_document("other-tenant-secret", beta)[0]
        executor = ToolExecutor(self.index, Graph(self.index), self.scope)
        result = executor.execute("fetch_passage", {"chunk_id": beta_chunk.chunk_id})
        self.assertFalse(result["found"])

    def test_tool_budgets_are_hard_limits(self) -> None:
        executor = ToolExecutor(self.index, Graph(self.index), self.scope, max_calls=1)
        executor.execute("search_passages", {"query": "ORBIT-731"})
        with self.assertRaisesRegex(ToolError, "budget"):
            executor.execute("search_passages", {"query": "CEDAR-210"})

    def test_outline_does_not_consume_text_evidence_budget(self) -> None:
        executor = ToolExecutor(
            self.index, Graph(self.index), self.scope, max_calls=2, max_evidence=1
        )
        outline = executor.execute("document_outline", {"document_id": "exact-orbit"})
        self.assertEqual(executor.evidence_returned, 0)
        fetched = executor.execute(
            "fetch_passage", {"chunk_id": outline["passages"][0]["chunk_id"]}
        )
        self.assertTrue(fetched["found"])
        self.assertEqual(executor.evidence_returned, 1)

    def test_tool_arguments_are_strictly_validated(self) -> None:
        executor = ToolExecutor(self.index, Graph(self.index), self.scope)
        invalid = [
            {"query": "ORBIT-731", "limit": 0},
            {"query": "ORBIT-731", "limit": "8"},
            {"query": "ORBIT-731", "unexpected": True},
        ]
        for arguments in invalid:
            with self.assertRaises(ToolError):
                executor.execute("search_passages", arguments)
        self.assertTrue(all(not call["accepted"] for call in executor.calls))

    def test_range_offset_past_end_returns_an_empty_verified_span(self) -> None:
        executor = ToolExecutor(self.index, Graph(self.index), self.scope)
        result = executor.execute(
            "range_coverage", {"document_id": "exact-orbit", "offset": 1_000_000}
        )
        self.assertTrue(result["found"])
        self.assertEqual(result["start"], result["end"])
        self.assertEqual(result["text"], "")


if __name__ == "__main__":
    unittest.main()
