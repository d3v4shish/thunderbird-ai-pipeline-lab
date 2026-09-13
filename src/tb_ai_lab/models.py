# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Loopback-only Ollama access, capability discovery, and GPU policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


GIB = 1024**3


class ModelError(RuntimeError):
    pass


def _same_model_tag(left: str, right: str) -> bool:
    return left == right or left.removesuffix(":latest") == right.removesuffix(
        ":latest"
    )


def validate_loopback_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ModelError("Ollama URL must use HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise ModelError("Credentials are not allowed in the Ollama URL")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ModelError("Only loopback Ollama endpoints are allowed")
    return value.rstrip("/")


@dataclass(frozen=True, slots=True)
class Residency:
    model: str
    artifact_bytes: int
    ollama_vram_bytes: int
    total_gpu_used_bytes: int | None
    full_gpu_residency: bool
    within_vram_cap: bool
    advertised_context: int
    context_compatible: bool
    eligible: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def nvidia_total_used_bytes() -> int | None:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    values: list[int] = []
    for line in result.stdout.splitlines():
        try:
            values.append(int(line.strip()) * 1024**2)
        except ValueError:
            continue
    return sum(values) if values else None


def assess_residency(
    model: str,
    artifact_bytes: int,
    ollama_vram_bytes: int,
    total_gpu_used_bytes: int | None,
    advertised_context: int,
    required_context: int = 16_384,
    cap_gib: float = 17,
) -> Residency:
    full = artifact_bytes > 0 and ollama_vram_bytes >= artifact_bytes * 0.98
    within = ollama_vram_bytes > 0 and ollama_vram_bytes <= cap_gib * GIB
    context_ok = advertised_context >= required_context
    reasons = []
    if not full:
        reasons.append("PARTIAL_GPU_RESIDENCY")
    if not within:
        reasons.append("VRAM_CAP_EXCEEDED")
    if not context_ok:
        reasons.append("CONTEXT_INCOMPATIBLE")
    return Residency(
        model=model,
        artifact_bytes=artifact_bytes,
        ollama_vram_bytes=ollama_vram_bytes,
        total_gpu_used_bytes=total_gpu_used_bytes,
        full_gpu_residency=full,
        within_vram_cap=within,
        advertised_context=advertised_context,
        context_compatible=context_ok,
        eligible=not reasons,
        reason="ELIGIBLE" if not reasons else ",".join(reasons),
    )


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        self.base_url = validate_loopback_url(base_url)
        self.timeout = timeout
        self.vram_cap_gib: float | None = None
        self.peak_gpu_used_bytes: int | None = None
        self.peak_ollama_vram_bytes: int = 0
        self.active_models: set[str] = set()
        self.request_count = 0
        self.request_bytes = 0
        self.response_bytes = 0

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        self.request_count += 1
        self.request_bytes += len(body or b"")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(32 * 1024 * 1024 + 1)
                if len(raw) > 32 * 1024 * 1024:
                    raise ModelError("Ollama JSON response exceeds 32 MiB")
                self.response_bytes += len(raw)
                return json.loads(raw.decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ModelError(f"Ollama request failed for {path}: {error}") from error

    def tags(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/tags")
        models = response.get("models", []) if isinstance(response, dict) else []
        return models if isinstance(models, list) else []

    def show(self, model: str) -> dict[str, Any]:
        response = self._request("POST", "/api/show", {"model": model})
        if not isinstance(response, dict):
            raise ModelError("Ollama show returned a non-object")
        return response

    def ps(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/ps")
        models = response.get("models", []) if isinstance(response, dict) else []
        return models if isinstance(models, list) else []

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        json_schema: dict[str, Any] | None = None,
        context_window: int = 16_384,
        max_output_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if tools and json_schema is not None:
            raise ModelError("JSON schema and tools cannot be requested together")
        if json_schema is not None and not isinstance(json_schema, dict):
            raise ModelError("JSON schema must be an object")
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "format": json_schema if json_schema is not None else "json",
            "options": {
                "num_ctx": context_window,
                "num_predict": max_output_tokens,
                "temperature": temperature,
                "seed": 0,
            },
        }
        if tools:
            payload["tools"] = tools
            payload.pop("format", None)
        response = self._request("POST", "/api/chat", payload)
        if not isinstance(response, dict) or not isinstance(response.get("message"), dict):
            raise ModelError("Ollama chat response has no message")
        response["_lab_request_bytes"] = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        response["_lab_response_bytes"] = len(json.dumps(response, ensure_ascii=False).encode("utf-8"))
        advertised = (
            self.advertised_context(self.show(model))
            if self.vram_cap_gib is not None
            else context_window
        )
        self._guard_runtime(model, advertised, required_context=context_window)
        return response

    def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        if not inputs or len(inputs) > 128 or any(
            not isinstance(item, str) or len(item.encode("utf-8")) > 1024 * 1024
            for item in inputs
        ):
            raise ModelError("Embedding inputs exceed the count or size limit")
        response = self._request("POST", "/api/embed", {"model": model, "input": inputs})
        vectors = response.get("embeddings", []) if isinstance(response, dict) else []
        if not isinstance(vectors, list) or not all(
            isinstance(item, list) for item in vectors
        ):
            raise ModelError("Ollama embedding response is malformed")
        dimensions = {len(item) for item in vectors}
        if (
            len(vectors) != len(inputs)
            or len(dimensions) != 1
            or not dimensions
            or not 1 <= next(iter(dimensions)) <= 16_384
            or not all(
                all(
                    isinstance(component, (int, float))
                    and not isinstance(component, bool)
                    and math.isfinite(component)
                    for component in item
                )
                for item in vectors
            )
        ):
            raise ModelError("Ollama embedding response is malformed")
        advertised = self.advertised_context(self.show(model)) if self.vram_cap_gib is not None else 16_384
        self._guard_runtime(model, advertised)
        return vectors

    def _guard_runtime(
        self,
        model: str,
        advertised_context: int,
        *,
        required_context: int = 16_384,
    ) -> None:
        self.active_models.add(model)
        if self.vram_cap_gib is None:
            return
        residency = self.residency(
            model,
            advertised_context,
            self.vram_cap_gib,
            required_context=required_context,
        )
        if residency.total_gpu_used_bytes is not None:
            self.peak_gpu_used_bytes = max(
                self.peak_gpu_used_bytes or 0, residency.total_gpu_used_bytes
            )
        loaded = self.ps()
        active_vram = sum(
            int(item.get("size_vram", 0) or 0)
            for item in loaded
            if any(
                _same_model_tag(
                    str(item.get("name") or item.get("model") or ""), active
                )
                for active in self.active_models
            )
        )
        self.peak_ollama_vram_bytes = max(self.peak_ollama_vram_bytes, active_vram)
        configuration_within_cap = active_vram <= self.vram_cap_gib * GIB
        if residency.eligible and configuration_within_cap:
            return
        try:
            self.unload(model)
        except ModelError:
            pass
        reason = (
            residency.reason
            if not residency.eligible
            else "CONFIGURATION_VRAM_CAP_EXCEEDED"
        )
        raise ModelError(reason)

    @staticmethod
    def advertised_context(show: dict[str, Any]) -> int:
        model_info = show.get("model_info", {})
        if not isinstance(model_info, dict):
            return 0
        values = [
            int(value)
            for key, value in model_info.items()
            if key.endswith(".context_length") and isinstance(value, (int, float))
        ]
        return max(values, default=0)

    def discover(self) -> list[dict[str, Any]]:
        records = []
        for item in self.tags():
            name = str(item.get("name") or item.get("model") or "")
            if not name:
                continue
            try:
                show = self.show(name)
            except ModelError as error:
                records.append(
                    {
                        "name": name,
                        "digest": item.get("digest", ""),
                        "size": int(item.get("size", 0) or 0),
                        "family": "",
                        "parameter_size": "",
                        "quantization": "",
                        "advertised_context": 0,
                        "roles": [],
                        "capabilities": [],
                        "tool_template": False,
                        "discovery_error": str(error),
                    }
                )
                continue
            details = show.get("details", {}) if isinstance(show.get("details"), dict) else {}
            capabilities = show.get("capabilities", [])
            if not isinstance(capabilities, list):
                capabilities = []
            capabilities = [str(item).casefold() for item in capabilities]
            lower_name = name.casefold()
            embedding_only = "embedding" in capabilities or any(
                marker in lower_name
                for marker in ("embed", "bge", "nomic", "mxbai", "snowflake-arctic")
            )
            records.append(
                {
                    "name": name,
                    "digest": item.get("digest", ""),
                    "size": int(item.get("size", 0) or 0),
                    "family": details.get("family", ""),
                    "parameter_size": details.get("parameter_size", ""),
                    "quantization": details.get("quantization_level", ""),
                    "advertised_context": self.advertised_context(show),
                    "roles": ["embedding"] if embedding_only else ["chat"],
                    "capabilities": capabilities,
                    "tool_template": (
                        "tools" in capabilities
                        or "tools" in str(show.get("template", "")).casefold()
                    ),
                }
            )
        return records

    def unload(self, model: str) -> None:
        self._request(
            "POST",
            "/api/generate",
            {"model": model, "prompt": "", "stream": False, "keep_alive": 0},
        )
        self.active_models.discard(model)
        deadline = time.monotonic() + 15.0
        while any(
            _same_model_tag(
                str(item.get("name") or item.get("model") or ""), model
            )
            for item in self.ps()
        ):
            if time.monotonic() >= deadline:
                raise ModelError(f"Timed out waiting for Ollama to unload {model}")
            time.sleep(0.05)

    def residency(
        self,
        model: str,
        advertised_context: int,
        cap_gib: float = 17,
        *,
        required_context: int = 16_384,
    ) -> Residency:
        loaded = next(
            (
                item
                for item in self.ps()
                if item.get("name") == model or item.get("model") == model
            ),
            {},
        )
        return assess_residency(
            model,
            int(loaded.get("size", 0) or 0),
            int(loaded.get("size_vram", 0) or 0),
            nvidia_total_used_bytes(),
            advertised_context,
            required_context=required_context,
            cap_gib=cap_gib,
        )

    def pull(self, model: str, progress: Callable[[dict[str, Any]], None] | None = None) -> None:
        request = Request(
            f"{self.base_url}/api/pull",
            data=json.dumps({"model": model, "stream": True}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        succeeded = False
        try:
            with urlopen(request, timeout=max(self.timeout, 3600)) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    if len(raw_line) > 1024 * 1024:
                        raise ModelError("Ollama pull event exceeds 1 MiB")
                    event = json.loads(raw_line.decode("utf-8"))
                    if not isinstance(event, dict):
                        raise ModelError("Ollama pull event is not an object")
                    if progress:
                        progress(event)
                    if event.get("error"):
                        raise ModelError(str(event["error"]))
                    if event.get("status") == "success":
                        succeeded = True
            if not succeeded:
                raise ModelError(f"Ollama pull ended without success for {model}")
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ModelError(f"Ollama pull failed for {model}: {error}") from error


class RerankerClient:
    """Client for a bounded loopback Cohere- or TEI-compatible rerank endpoint."""

    def __init__(
        self,
        endpoint_url: str,
        model: str = "",
        api_format: str = "cohere",
    ) -> None:
        parsed = urlparse(endpoint_url)
        validate_loopback_url(f"{parsed.scheme}://{parsed.netloc}")
        if api_format not in {"cohere", "tei"}:
            raise ModelError("Reranker API format must be cohere or tei")
        self.endpoint_url = endpoint_url
        self.model = model
        self.api_format = api_format
        self.request_count = 0
        self.request_bytes = 0
        self.response_bytes = 0

    def _request(self, payload: dict[str, Any]) -> Any:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.endpoint_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        self.request_count += 1
        self.request_bytes += len(body)
        try:
            with urlopen(request, timeout=120) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
                if len(raw) > 16 * 1024 * 1024:
                    raise ModelError("Reranker response exceeds 16 MiB")
                self.response_bytes += len(raw)
                value = json.loads(raw.decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ModelError(f"Reranker request failed: {error}") from error
        return value

    def info(self) -> dict[str, Any]:
        parsed = urlparse(self.endpoint_url)
        request = Request(
            f"{parsed.scheme}://{parsed.netloc}/info",
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise ModelError("Reranker info response exceeds 1 MiB")
                value = json.loads(raw.decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ModelError(f"Reranker info request failed: {error}") from error
        if not isinstance(value, dict):
            raise ModelError("Reranker info response must be an object")
        return value

    def rerank(self, query: str, documents: list[str]) -> list[tuple[int, float]]:
        if (
            not isinstance(query, str)
            or not query.strip()
            or len(query.encode("utf-8")) > 64 * 1024
            or not 1 <= len(documents) <= 100
            or any(
                not isinstance(item, str)
                or not item
                or len(item.encode("utf-8")) > 256 * 1024
                for item in documents
            )
        ):
            raise ModelError("Reranker inputs exceed the count or size limit")
        if self.api_format == "tei":
            payload: dict[str, Any] = {
                "query": query,
                "texts": documents,
                "truncate": True,
                "raw_scores": False,
                "return_text": False,
            }
        else:
            payload = {
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            }
            if self.model:
                payload["model"] = self.model
        value = self._request(payload)
        if isinstance(value, list):
            results = value
        elif isinstance(value, dict):
            results = value.get("results", value.get("ranks"))
        else:
            results = None
        if not isinstance(results, list):
            raise ModelError("Reranker response has no results")
        ranked: list[tuple[int, float]] = []
        seen: set[int] = set()
        for item in results:
            if not isinstance(item, dict):
                raise ModelError("Reranker result must be an object")
            index = item.get("index")
            score = item.get("relevance_score", item.get("score"))
            if (
                not isinstance(index, int)
                or index < 0
                or index >= len(documents)
                or index in seen
                or not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not math.isfinite(score)
            ):
                raise ModelError("Reranker result index or score is invalid")
            seen.add(index)
            ranked.append((index, float(score)))
        if len(seen) != len(documents):
            raise ModelError("Reranker response omitted one or more documents")
        return ranked


def prepare_allowlisted_models(
    client: OllamaClient,
    config: dict[str, Any],
    output_path: Path,
    progress: Callable[[str], None] = print,
) -> dict[str, Any]:
    allowlist = config.get("download_allowlist", [])
    if not isinstance(allowlist, list) or not all(isinstance(item, str) for item in allowlist):
        raise ModelError("download_allowlist is invalid")
    estimates = config.get("estimated_download_gib", {})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    installed = {str(item.get("name") or item.get("model")) for item in client.tags()}
    installed_aliases = installed | {name.removesuffix(":latest") for name in installed}
    missing = [model for model in allowlist if model not in installed_aliases]
    projected = sum(float(estimates.get(model, 0)) for model in missing)
    free_gib = shutil.disk_usage(output_path.parent).free / GIB
    minimum = float(config.get("minimum_free_disk_gib", 64))
    if free_gib - projected < minimum:
        raise ModelError(
            f"Projected free disk would be {free_gib - projected:.1f} GiB; minimum is {minimum:.1f} GiB"
        )
    pulled: list[str] = []
    for model in missing:
        progress(f"pulling {model}")
        last_progress: tuple[str, int] | None = None

        def report_event(event: dict[str, Any]) -> None:
            nonlocal last_progress
            status = str(event.get("status", ""))
            completed = int(event.get("completed", 0) or 0)
            total = int(event.get("total", 0) or 0)
            percent = int(completed * 100 / total) if total else -1
            bucket = percent // 5 if percent >= 0 else -1
            current = (status, bucket)
            if current == last_progress:
                return
            last_progress = current
            suffix = f" {percent}%" if percent >= 0 else ""
            progress(f"{model}: {status}{suffix}")

        client.pull(model, report_event)
        pulled.append(model)
        if shutil.disk_usage(output_path.parent).free / GIB < minimum:
            raise ModelError("Free disk fell below the configured safety floor")
    records = client.discover()
    selected = [
        record
        for record in records
        if record["name"] in set(allowlist)
        or record["name"].removesuffix(":latest") in set(allowlist)
    ]
    result = {
        "schema_version": 1,
        "allowlist": allowlist,
        "pulled": pulled,
        "models": selected,
    }
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result
