from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tb_ai_lab.contextual_rag import (
    ContextualRagError,
    contextual_challenge_fixture,
    context_generation_messages,
    contextualized_chunks,
    generate_contexts,
    generate_whole_email_contexts,
    validate_generated_context,
    whole_email_context_generation_messages,
    whole_email_contextualized_chunks,
)
from tb_ai_lab.contracts import Document, content_digest
from tb_ai_lab.text import structure_aware_chunks


class FakeContextClient:
    def __init__(self, output: str = '{"context":"A concise source-backed context."}') -> None:
        self.output = output
        self.calls = 0
        self.request_count = 0
        self.request_bytes = 0
        self.response_bytes = 0

    def chat(self, _model: str, messages: list[dict], **_options: object) -> dict:
        self.calls += 1
        self.request_count += 1
        self.request_bytes += len(str(messages).encode("utf-8"))
        self.response_bytes += len(self.output.encode("utf-8"))
        return {
            "message": {"content": self.output},
            "prompt_eval_count": 20,
            "eval_count": 8,
        }


class ContextualRagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = Document(
            id="doc-1",
            tenant="tenant-test",
            collection="synthetic",
            title="Atlas planning record",
            timestamp="2026-09-12T00:00:00Z",
            text="Project ATLAS-101 uses the north site. The approved date is 2027-05-03.",
            metadata={"category": "decision"},
        )
        self.chunks = structure_aware_chunks(
            self.document, chunk_chars=128, overlap=0, limit=10
        )
        self.chunk_map = {
            (self.document.tenant, self.document.collection, self.document.id): self.chunks
        }

    def test_prompt_is_query_independent_and_contains_verified_source(self) -> None:
        messages = context_generation_messages(self.document, self.chunks[0])
        self.assertEqual([item["role"] for item in messages], ["system", "user"])
        self.assertIn(self.document.text, messages[1]["content"])
        self.assertIn(self.chunks[0].text, messages[1]["content"])
        self.assertNotIn("user query", messages[1]["content"].casefold())
        altered = self.chunks[0]
        altered = type(altered)(
            **{**altered.as_dict(), "text": altered.text + " altered"}
        )
        with self.assertRaisesRegex(ContextualRagError, "canonical source span"):
            context_generation_messages(self.document, altered)

    def test_generated_context_rejects_malformed_and_unsupported_entities(self) -> None:
        accepted = validate_generated_context(
            '{"context":"This decision concerns ATLAS-101 and the date 2027-05-03."}',
            self.document,
        )
        self.assertEqual(accepted["unsupported_exact_entities"], [])
        timestamp_context = validate_generated_context(
            '{"context":"The record is dated 2026-09-12."}', self.document
        )
        self.assertEqual(timestamp_context["unsupported_exact_entities"], [])
        with self.assertRaisesRegex(ContextualRagError, "valid JSON"):
            validate_generated_context("not json", self.document)
        with self.assertRaisesRegex(ContextualRagError, "unsupported exact entities"):
            validate_generated_context(
                '{"context":"This decision concerns INVENTED-999."}', self.document
            )

    def test_whole_email_prompt_contains_no_target_chunk_or_query(self) -> None:
        messages = whole_email_context_generation_messages(self.document)
        self.assertEqual([item["role"] for item in messages], ["system", "user"])
        source = json.loads(messages[1]["content"].split("\n", 1)[1])
        self.assertEqual(set(source), {"document"})
        self.assertEqual(source["document"]["text"], self.document.text)
        self.assertNotIn("chunk", source)
        self.assertNotIn("query", source)

    def test_context_cache_is_atomic_reusable_and_preserves_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-context-test-") as temporary:
            cache = Path(temporary) / "cache.json"
            first_client = FakeContextClient(
                '{"context":"This decision situates ATLAS-101 in the planning record."}'
            )
            records, summary = generate_contexts(
                [self.document],
                self.chunk_map,
                first_client,  # type: ignore[arg-type]
                "mock",
                "digest",
                cache,
                content_digest(self.document.as_dict()),
            )
            self.assertEqual(first_client.calls, len(self.chunks))
            self.assertTrue(summary["complete"])
            self.assertTrue(cache.is_file())

            second_client = FakeContextClient()
            reused, reused_summary = generate_contexts(
                [self.document],
                self.chunk_map,
                second_client,  # type: ignore[arg-type]
                "mock",
                "digest",
                cache,
                content_digest(self.document.as_dict()),
            )
            self.assertEqual(second_client.calls, 0)
            self.assertEqual(reused_summary["cache_hits"], len(self.chunks))
            self.assertTrue(all(item["cache_hit"] for item in reused.values()))

            contextual = contextualized_chunks(self.chunk_map, records)
            for original, augmented in zip(
                self.chunks,
                contextual[(self.document.tenant, self.document.collection, self.document.id)],
                strict=True,
            ):
                self.assertEqual(augmented.text, original.text)
                self.assertEqual((augmented.start, augmented.end), (original.start, original.end))
                self.assertIn("Generated retrieval context (untrusted):", augmented.contextual_text)

    def test_whole_email_context_is_cached_once_and_preserves_passages(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tb-ai-whole-email-test-") as temporary:
            cache = Path(temporary) / "cache.json"
            first_client = FakeContextClient(
                '{"context":"The planning decision concerns Project ATLAS-101."}'
            )
            records, summary = generate_whole_email_contexts(
                [self.document],
                first_client,  # type: ignore[arg-type]
                "mock",
                "digest",
                cache,
                content_digest(self.document.as_dict()),
            )
            self.assertEqual(first_client.calls, 1)
            self.assertEqual(summary["document_count"], 1)
            self.assertTrue(summary["complete"])

            second_client = FakeContextClient()
            reused, reused_summary = generate_whole_email_contexts(
                [self.document],
                second_client,  # type: ignore[arg-type]
                "mock",
                "digest",
                cache,
                content_digest(self.document.as_dict()),
            )
            self.assertEqual(second_client.calls, 0)
            self.assertEqual(reused_summary["cache_hits"], 1)

            contextual = whole_email_contextualized_chunks(self.chunk_map, reused)
            augmented = contextual[
                (self.document.tenant, self.document.collection, self.document.id)
            ]
            for original, candidate in zip(self.chunks, augmented, strict=True):
                self.assertEqual(candidate.text, original.text)
                self.assertEqual(
                    (candidate.start, candidate.end),
                    (original.start, original.end),
                )
                self.assertIn(
                    "Whole-email retrieval context (untrusted):",
                    candidate.contextual_text,
                )

    def test_challenge_fact_chunk_requires_earlier_document_context(self) -> None:
        documents, cases = contextual_challenge_fixture()
        chunks = structure_aware_chunks(
            documents[0], chunk_chars=1200, overlap=180, limit=4096
        )
        fact_chunk = next(item for item in chunks if "[FACT C01]" in item.text)
        self.assertNotIn("BOREALIS-204", fact_chunk.text)
        self.assertNotIn("funding", fact_chunk.text.casefold())
        self.assertIn("BOREALIS-204", cases[0].query)
        self.assertGreater(fact_chunk.start, 1200)


if __name__ == "__main__":
    unittest.main()
