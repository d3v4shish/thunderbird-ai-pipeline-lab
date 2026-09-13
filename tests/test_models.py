from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tb_ai_lab.models import (
    GIB,
    ModelError,
    OllamaClient,
    RerankerClient,
    assess_residency,
    prepare_allowlisted_models,
    validate_loopback_url,
)


class FakeOllamaClient(OllamaClient):
    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:11434")
        self.requests: list[tuple[str, str, dict | None]] = []
        self.loaded = True

    def _request(self, method: str, path: str, payload: dict | None = None):
        self.requests.append((method, path, payload))
        if path == "/api/tags":
            return {"models": [{"name": "mock:latest", "digest": "abc", "size": 100}]}
        if path == "/api/show":
            return {
                "details": {"family": "mock"},
                "model_info": {"mock.context_length": 32768},
                "template": "tools",
            }
        if path == "/api/ps":
            return {
                "models": (
                    [{"name": "mock:latest", "size": 100, "size_vram": 100}]
                    if self.loaded
                    else []
                )
            }
        if path == "/api/chat":
            self.loaded = True
            return {
                "message": {
                    "role": "assistant",
                    "content": '{"answer":"ok","facts":{},"citations":[],"abstained":false}',
                },
                "prompt_eval_count": 4,
                "eval_count": 2,
            }
        if path == "/api/embed":
            self.loaded = True
            return {"embeddings": [[1.0, 0.0] for _ in (payload or {}).get("input", [])]}
        if path == "/api/generate":
            self.loaded = False
            return {"done": True}
        raise AssertionError(path)


class FakeRerankerClient(RerankerClient):
    def __init__(self, response: object, api_format: str = "cohere") -> None:
        super().__init__(
            "http://127.0.0.1:8080/v1/rerank",
            "mock-reranker",
            api_format,
        )
        self.response = response

    def _request(self, payload: dict) -> object:
        self.payload = payload
        return self.response


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeOllamaClient()

    def test_non_loopback_endpoint_is_rejected(self) -> None:
        with self.assertRaises(ModelError):
            validate_loopback_url("https://example.com")
        self.assertEqual(validate_loopback_url("http://127.0.0.1:11434"), "http://127.0.0.1:11434")
        with self.assertRaisesRegex(ModelError, "format"):
            RerankerClient("http://127.0.0.1:8080/rerank", api_format="unknown")

    def test_discovery_chat_and_embedding_contracts(self) -> None:
        records = self.client.discover()
        self.assertEqual(records[0]["advertised_context"], 32768)
        self.assertEqual(records[0]["roles"], ["chat"])
        response = self.client.chat("mock:latest", [{"role": "user", "content": "hi"}])
        self.assertIn("message", response)
        self.assertEqual(self.client.embed("mock:latest", ["one", "two"]), [[1.0, 0.0], [1.0, 0.0]])

    def test_embedding_contract_rejects_non_finite_or_wrong_count(self) -> None:
        with patch.object(self.client, "_request", return_value={"embeddings": [[float("nan")]]}):
            with self.assertRaisesRegex(ModelError, "malformed"):
                self.client.embed("mock:latest", ["one"])
        with patch.object(self.client, "_request", return_value={"embeddings": []}):
            with self.assertRaisesRegex(ModelError, "malformed"):
                self.client.embed("mock:latest", ["one"])

    def test_chat_request_is_seeded_and_bounded(self) -> None:
        self.client.chat(
            "mock:latest",
            [{"role": "user", "content": "hi"}],
            context_window=16384,
            max_output_tokens=1024,
            temperature=0.2,
        )
        payload = self.client.requests[-1][2]
        self.assertEqual(payload["options"]["seed"], 0)
        self.assertEqual(payload["options"]["num_ctx"], 16384)
        self.assertEqual(payload["options"]["num_predict"], 1024)
        self.assertFalse(payload["stream"])
        self.assertIs(payload["think"], False)
        self.assertNotIn("think", payload["options"])

    def test_chat_accepts_a_json_schema_but_not_with_tools(self) -> None:
        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        }
        self.client.chat(
            "mock:latest",
            [{"role": "user", "content": "hi"}],
            json_schema=schema,
        )
        self.assertEqual(self.client.requests[-1][2]["format"], schema)
        with self.assertRaisesRegex(ModelError, "cannot be requested together"):
            self.client.chat(
                "mock:latest",
                [{"role": "user", "content": "hi"}],
                json_schema=schema,
                tools=[{"type": "function", "function": {"name": "noop"}}],
            )

    def test_runtime_context_guard_uses_model_capacity_not_selected_window(self) -> None:
        self.client.vram_cap_gib = 17
        response = self.client.chat(
            "mock:latest",
            [{"role": "user", "content": "hi"}],
            context_window=8192,
        )
        self.assertIn("message", response)

    def test_runtime_context_guard_rejects_request_above_model_capacity(self) -> None:
        self.client.vram_cap_gib = 17
        with self.assertRaisesRegex(ModelError, "CONTEXT_INCOMPATIBLE"):
            self.client.chat(
                "mock:latest",
                [{"role": "user", "content": "hi"}],
                context_window=65_536,
            )
        self.assertIn("/api/generate", [item[1] for item in self.client.requests])
        self.assertFalse(self.client.loaded)

    def test_vram_policy_requires_measurement_residency_context_and_cap(self) -> None:
        eligible = assess_residency("model", 10 * GIB, 10 * GIB, None, 32768)
        self.assertTrue(eligible.eligible)
        over = assess_residency("model", 18 * GIB, 18 * GIB, 18 * GIB, 32768)
        self.assertIn("VRAM_CAP_EXCEEDED", over.reason)
        partial = assess_residency("model", 10 * GIB, 5 * GIB, 10 * GIB, 32768)
        self.assertIn("PARTIAL_GPU_RESIDENCY", partial.reason)
        short = assess_residency("model", 10 * GIB, 10 * GIB, 10 * GIB, 8192)
        self.assertIn("CONTEXT_INCOMPATIBLE", short.reason)

    def test_runtime_guard_aborts_and_unloads_over_cap_model(self) -> None:
        self.client.vram_cap_gib = 17
        with patch.object(
            self.client,
            "residency",
            return_value=assess_residency(
                "mock:latest", 18 * GIB, 18 * GIB, 18 * GIB, 32_768
            ),
        ):
            with self.assertRaisesRegex(ModelError, "VRAM_CAP_EXCEEDED"):
                self.client.chat("mock:latest", [{"role": "user", "content": "hi"}])
        self.assertIn("/api/generate", [item[1] for item in self.client.requests])
        self.assertFalse(self.client.loaded)

    def test_reranker_validates_and_orders_endpoint_results(self) -> None:
        client = FakeRerankerClient(
            {"results": [{"index": 1, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.5}]}
        )
        self.assertEqual(client.rerank("query", ["one", "two"]), [(1, 0.9), (0, 0.5)])
        self.assertEqual(client.payload["model"], "mock-reranker")
        with self.assertRaises(ModelError):
            FakeRerankerClient({"results": [{"index": 3, "score": 1.0}]}).rerank("q", ["one"])
        with self.assertRaises(ModelError):
            FakeRerankerClient({"results": [{"index": 0, "score": float("nan")}]}).rerank("q", ["one"])
        with self.assertRaisesRegex(ModelError, "omitted"):
            FakeRerankerClient({"results": [{"index": 0, "score": 1.0}]}).rerank(
                "q", ["one", "two"]
            )

    def test_tei_reranker_contract_uses_joint_query_text_pairs(self) -> None:
        client = FakeRerankerClient(
            [{"index": 1, "score": 0.8}, {"index": 0, "score": 0.2}],
            "tei",
        )
        self.assertEqual(client.rerank("query", ["one", "two"]), [(1, 0.8), (0, 0.2)])
        self.assertEqual(client.payload["texts"], ["one", "two"])
        self.assertNotIn("documents", client.payload)
        self.assertTrue(client.payload["truncate"])

    def test_model_preparation_recognizes_latest_alias_and_writes_manifest(self) -> None:
        config = {
            "download_allowlist": ["mock"],
            "estimated_download_gib": {"mock": 1},
            "minimum_free_disk_gib": 0,
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "nested" / "prepared.json"
            result = prepare_allowlisted_models(
                self.client, config, output, lambda _message: None
            )
            self.assertTrue(output.is_file())
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["pulled"], [])
        self.assertEqual(result["models"][0]["name"], "mock:latest")


if __name__ == "__main__":
    unittest.main()
