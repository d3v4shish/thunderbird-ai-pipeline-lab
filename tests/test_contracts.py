from __future__ import annotations

import unittest

from tb_ai_lab.contracts import (
    ContractError,
    Document,
    EvaluationCase,
    PipelineVariant,
    Scope,
    canonical_json,
)


class ContractTests(unittest.TestCase):
    def test_document_and_scope_require_identity(self) -> None:
        document = Document.from_dict(
            {
                "schema_version": 1,
                "id": "doc-1",
                "tenant": "tenant-a",
                "collection": "primary",
                "title": "Title",
                "text": "Body",
                "metadata": {},
            }
        )
        self.assertEqual(document.scope, Scope("tenant-a", "primary"))
        self.assertIn('"id":"doc-1"', canonical_json(document))

    def test_unknown_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractError, "schema_version"):
            Document.from_dict(
                {
                    "schema_version": 2,
                    "id": "doc",
                    "tenant": "tenant",
                    "collection": "collection",
                    "text": "body",
                }
            )
        with self.assertRaisesRegex(ContractError, "schema_version"):
            Document.from_dict(
                {
                    "schema_version": True,
                    "id": "doc",
                    "tenant": "tenant",
                    "collection": "collection",
                    "text": "body",
                }
            )

    def test_variant_rejects_invalid_chunk_limits(self) -> None:
        with self.assertRaisesRegex(ContractError, "chunk_overlap"):
            PipelineVariant.from_dict(
                {
                    "schema_version": 1,
                    "id": "bad",
                    "chunk_chars": 500,
                    "chunk_overlap": 500,
                }
            )
        with self.assertRaisesRegex(ContractError, "context_total_chars"):
            PipelineVariant.from_dict(
                {"schema_version": 1, "id": "bad", "context_total_chars": -1}
            )
        with self.assertRaisesRegex(ContractError, "retrieval_candidates"):
            PipelineVariant.from_dict(
                {"schema_version": 1, "id": "bad", "retrieval_candidates": 401}
            )

    def test_document_rejects_oversized_payload(self) -> None:
        with self.assertRaisesRegex(ContractError, "16 MiB"):
            Document.from_dict(
                {
                    "schema_version": 1,
                    "id": "large",
                    "tenant": "tenant",
                    "collection": "collection",
                    "text": "x" * (16 * 1024 * 1024 + 1),
                }
            )

    def test_document_rejects_non_json_metadata(self) -> None:
        with self.assertRaisesRegex(ContractError, "JSON-compatible"):
            Document.from_dict(
                {
                    "schema_version": 1,
                    "id": "metadata",
                    "tenant": "tenant",
                    "collection": "collection",
                    "text": "body",
                    "metadata": {"invalid": object()},
                }
            )
        with self.assertRaisesRegex(ContractError, "JSON-compatible"):
            Document.from_dict(
                {
                    "schema_version": 1,
                    "id": "metadata-nan",
                    "tenant": "tenant",
                    "collection": "collection",
                    "text": "body",
                    "metadata": {"invalid": float("nan")},
                }
            )

    def test_variant_rejects_unknown_fields_and_modes(self) -> None:
        with self.assertRaisesRegex(ContractError, "invalid pipeline variant"):
            PipelineVariant.from_dict(
                {"schema_version": 1, "id": "bad", "unknown_option": True}
            )
        with self.assertRaisesRegex(ContractError, "retrieval"):
            PipelineVariant.from_dict(
                {"schema_version": 1, "id": "bad", "retrieval": "magic"}
            )

    def test_case_rejects_coerced_boolean_and_truncated_tools(self) -> None:
        base = {
            "schema_version": 1,
            "id": "case",
            "query": "question",
            "scope": {"tenant": "tenant", "collection": "collection"},
        }
        with self.assertRaisesRegex(ContractError, "boolean"):
            EvaluationCase.from_dict({**base, "require_abstention": "false"})
        with self.assertRaisesRegex(ContractError, "size limit"):
            EvaluationCase.from_dict({**base, "allowed_tools": ["x" * 201]})
        with self.assertRaisesRegex(ContractError, "list of strings"):
            EvaluationCase.from_dict({**base, "expected_answer_values": "answer"})


if __name__ == "__main__":
    unittest.main()
