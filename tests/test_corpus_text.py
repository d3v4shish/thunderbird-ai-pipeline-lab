from __future__ import annotations

import unittest

from tb_ai_lab.contracts import Document, EvaluationCase
from tb_ai_lab.corpus import LONG_FACTS, cases, documents, long_document_text
from tb_ai_lab.text import (
    detect_pii,
    exact_entities,
    fixed_chunks,
    local_embedding,
    normalize_text,
    sentence_window_chunks,
    structure_aware_chunks,
    vector_bucket_keys,
)


class CorpusAndTextTests(unittest.TestCase):
    def test_long_document_is_exact_and_distributed(self) -> None:
        text = long_document_text()
        self.assertEqual(len(text.encode("utf-8")), 10_240)
        self.assertEqual(len(LONG_FACTS), 32)
        positions = [text.index(f"[FACT {fact_id}]") for fact_id in LONG_FACTS]
        self.assertLess(positions[0], 100)
        self.assertGreater(positions[15], 4_000)
        self.assertGreater(positions[-1], 9_500)
        for value in LONG_FACTS.values():
            self.assertIn(value, text)

    def test_fixtures_are_synthetic_and_versioned(self) -> None:
        records = documents()
        self.assertTrue(records)
        self.assertTrue(all(item["schema_version"] == 1 for item in records))
        self.assertTrue(all(item["tenant"].startswith("tenant-") for item in records))

    def test_answer_expectations_cover_direct_and_abstention_cases(self) -> None:
        records = [EvaluationCase.from_dict(item) for item in cases()]
        scored = [
            item
            for item in records
            if item.expected_answer_values or item.require_abstention
        ]
        self.assertEqual(len(scored), 7)
        graph = next(item for item in records if item.id == "graph-multihop")
        self.assertEqual(graph.expected_answer_values, ("Kestrel Works",))

    def test_fixed_chunks_match_every_reported_source_span(self) -> None:
        document = Document.from_dict(next(item for item in documents() if item["id"] == "long-10240"))
        chunks = fixed_chunks(document)
        self.assertGreater(len(chunks), 8)
        self.assertLessEqual(len(chunks), 24)
        for chunk in chunks:
            self.assertEqual(document.text[chunk.start : chunk.end], chunk.text)

    def test_structure_aware_chunks_cover_final_fact(self) -> None:
        document = Document.from_dict(next(item for item in documents() if item["id"] == "long-10240"))
        chunks = structure_aware_chunks(document, limit=4096)
        self.assertTrue(any("[FACT F32]" in chunk.text for chunk in chunks))
        self.assertEqual(max(chunk.end for chunk in chunks), len(document.text))

    def test_sentence_window_chunks_index_children_and_return_verified_parents(self) -> None:
        document = Document.from_dict(
            next(item for item in documents() if item["id"] == "long-10240")
        )
        chunks = sentence_window_chunks(document, limit=4096)
        self.assertGreater(len(chunks), 32)
        self.assertEqual(
            len({(item.start, item.end) for item in chunks}),
            len(structure_aware_chunks(document, overlap=0, limit=4096)),
        )
        self.assertTrue(
            all(document.text[item.start : item.end] == item.text for item in chunks)
        )
        self.assertTrue(
            all("Retrieval sentence:" in item.contextual_text for item in chunks)
        )
        self.assertTrue(all(item.retrieval_text in item.text for item in chunks))
        for fact_id, value in LONG_FACTS.items():
            self.assertTrue(
                any(
                    f"[FACT {fact_id}]" in item.text and value in item.text
                    for item in chunks
                ),
                fact_id,
            )

    def test_normalization_and_embedding_are_deterministic(self) -> None:
        self.assertEqual(normalize_text("a\r\n b \x00"), "a\n b")
        self.assertEqual(local_embedding("Alpha beta alpha"), local_embedding("Alpha beta alpha"))
        self.assertEqual(len(local_embedding("Alpha beta")), 32)
        self.assertEqual(len(vector_bucket_keys(local_embedding("Alpha beta"))), 4)
        self.assertEqual(len(vector_bucket_keys(local_embedding("Alpha beta"), True)), 36)

    def test_pii_detection_is_bounded_and_deterministic(self) -> None:
        result = detect_pii("Contact qa@example.test or +1 (202) 555-0184.")
        self.assertEqual(result["emails"], ["qa@example.test"])
        self.assertEqual(result["phones"], ["+1 (202) 555-0184"])

    def test_exact_entity_extraction_is_bounded(self) -> None:
        value = " ".join(f"ENTITY-{index:04d}" for index in range(1000))
        self.assertEqual(len(exact_entities(value)), 256)


if __name__ == "__main__":
    unittest.main()
