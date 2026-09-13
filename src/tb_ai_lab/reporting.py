# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Atomic machine-readable and human-reviewable evaluation reports."""

from __future__ import annotations

from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

from .evaluation import summarize_matrix


def environment_record() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pid": os.getpid(),
    }


def _atomic_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# {report.get('title', 'AI Pipeline Evaluation')}",
        "",
        f"- Results: {summary['result_count']}",
        f"- Hard-gate passing: {summary['hard_gate_passing']}",
        f"- Quality passing: {summary['quality_passing']}",
        f"- Maximum quality: {summary['max_quality'] or 'none'}",
        f"- Fastest passing: {summary['fastest_passing'] or 'none'}",
        f"- VRAM-efficient passing: {summary['vram_efficient'] or 'none'}",
        f"- Pareto frontier: {', '.join(summary['pareto_frontier']) or 'none'}",
        f"- Production ready: {summary['production_ready']}",
        "",
        "## Variants",
        "",
        "| Variant | Quality | Recall@8 | MRR | Facts | Answer | p50 ms | Hard gate | Quality gate |",
        "|---|---:|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for result in report["results"]:
        aggregate = result.get("aggregate", {})
        lines.append(
            "| {id} | {quality:.3f} | {recall:.3f} | {mrr:.3f} | {facts:.3f} | {answer:.3f} | {latency:.2f} | {hard} | {gate} |".format(
                id=result.get("variant", {}).get("id", "unknown"),
                quality=aggregate.get("quality_score", 0),
                recall=aggregate.get("recall_at_8", 0),
                mrr=aggregate.get("mrr", 0),
                facts=aggregate.get("required_fact_recall", 0),
                answer=aggregate.get("answer_correctness", 0),
                latency=aggregate.get("latency_p50_ms", 0),
                hard="pass" if aggregate.get("hard_gate_pass") else "fail",
                gate="pass" if aggregate.get("quality_pass") else "fail",
            )
        )
        for case in result.get("cases", []):
            lines.extend(
                [
                    "",
                    f"### {result.get('variant', {}).get('id', 'unknown')} / {case['case_id']}",
                    "",
                    f"Query: `{case.get('query', '')}`",
                    "",
                    f"Expected facts: `{json.dumps(case.get('expected_facts', {}), ensure_ascii=False, sort_keys=True)}`",
                    "",
                    f"Expected answer values: `{json.dumps(case.get('expected_answer_values', []), ensure_ascii=False)}`",
                    "",
                    f"Hard failures: `{json.dumps(case.get('hard_failures', []))}`",
                ]
            )
            output = case.get("output")
            if output:
                lines.extend(
                    [
                        "",
                        f"Retrieved documents: `{json.dumps(case.get('retrieved_document_ids', []))}`",
                        "",
                        f"Metrics: `{json.dumps(case.get('metrics', {}), sort_keys=True)}`",
                        "",
                        f"Stage traces: `{json.dumps(output.get('traces', []), ensure_ascii=False, sort_keys=True)}`",
                        "",
                        "Evidence:",
                        "",
                        "```text",
                        "\n\n".join(
                            f"{item.get('citation', '')}\n{item.get('text', '')}"
                            for item in output.get("evidence", [])
                        ),
                        "```",
                        "",
                        "Prompt:",
                        "",
                        "```text",
                        output.get("prompt", ""),
                        "```",
                        "",
                        f"Tool calls: `{json.dumps(output.get('tool_calls', []), ensure_ascii=False, sort_keys=True)}`",
                        "",
                        f"Graph context: `{json.dumps(output.get('graph_context', {}), ensure_ascii=False, sort_keys=True)}`",
                        "",
                        "Original output:",
                        "",
                        "```json",
                        output.get("raw_output", ""),
                        "```",
                        "",
                        f"Validated facts: `{json.dumps(output.get('facts', {}), ensure_ascii=False, sort_keys=True)}`",
                        "",
                        f"Validated citations: `{json.dumps(output.get('citations', []), ensure_ascii=False)}`",
                    ]
                )
    return "\n".join(lines) + "\n"


def html_report(report: dict[str, Any]) -> str:
    def escaped(value: Any) -> str:
        return html.escape(str(value))

    def json_block(value: Any) -> str:
        return f"<pre>{html.escape(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))}</pre>"

    summary = report["summary"]
    rows = []
    case_sections = []
    for result in report["results"]:
        variant_id = result.get("variant", {}).get("id", "unknown")
        aggregate = result.get("aggregate", {})
        rows.append(
            "<tr>"
            f"<td><code>{escaped(variant_id)}</code></td>"
            f"<td>{aggregate.get('quality_score', 0):.3f}</td>"
            f"<td>{aggregate.get('recall_at_8', 0):.3f}</td>"
            f"<td>{aggregate.get('mrr', 0):.3f}</td>"
            f"<td>{aggregate.get('required_fact_recall', 0):.3f}</td>"
            f"<td>{aggregate.get('answer_correctness', 0):.3f}</td>"
            f"<td>{aggregate.get('latency_p50_ms', 0):.2f}</td>"
            f"<td class={'pass' if aggregate.get('hard_gate_pass') else 'fail'}>"
            f"{'pass' if aggregate.get('hard_gate_pass') else 'fail'}</td>"
            f"<td class={'pass' if aggregate.get('quality_pass') else 'fail'}>"
            f"{'pass' if aggregate.get('quality_pass') else 'fail'}</td>"
            "</tr>"
        )
        for case in result.get("cases", []):
            output = case.get("output")
            body = [
                f"<p><strong>Query:</strong> {escaped(case.get('query', ''))}</p>",
                "<h4>Expected</h4>",
                json_block(
                    {
                        "documents": case.get("expected_document_ids", []),
                        "facts": case.get("expected_facts", {}),
                        "answer_values": case.get("expected_answer_values", []),
                        "relations": case.get("expected_relations", []),
                    }
                ),
                "<h4>Metrics and failures</h4>",
                json_block(
                    {
                        "metrics": case.get("metrics", {}),
                        "hard_failures": case.get("hard_failures", []),
                    }
                ),
            ]
            if output:
                evidence_text = "\n\n".join(
                    f"{item.get('citation', '')}\n{item.get('text', '')}"
                    for item in output.get("evidence", [])
                )
                body.extend(
                    [
                        "<h4>Evidence</h4>",
                        f"<pre>{html.escape(evidence_text)}</pre>",
                        "<h4>Prompt</h4>",
                        f"<pre>{html.escape(output.get('prompt', ''))}</pre>",
                        "<h4>Tool calls</h4>",
                        json_block(output.get("tool_calls", [])),
                        "<h4>Graph context</h4>",
                        json_block(output.get("graph_context", {})),
                        "<h4>Stage traces</h4>",
                        json_block(output.get("traces", [])),
                        "<h4>Original model output</h4>",
                        f"<pre>{html.escape(output.get('raw_output', ''))}</pre>",
                        "<h4>Validated output</h4>",
                        json_block(
                            {
                                "answer": output.get("answer", ""),
                                "facts": output.get("facts", {}),
                                "citations": output.get("citations", []),
                                "abstained": output.get("abstained", False),
                                "errors": output.get("errors", []),
                            }
                        ),
                    ]
                )
            case_sections.append(
                f"<details><summary>{escaped(variant_id)} / {escaped(case.get('case_id', 'unknown'))}</summary>"
                f"{''.join(body)}</details>"
            )
    summary_items = [
        ("Results", summary["result_count"]),
        ("Hard-gate passing", summary["hard_gate_passing"]),
        ("Quality passing", summary["quality_passing"]),
        ("Maximum quality", summary["max_quality"] or "none"),
        ("Fastest passing", summary["fastest_passing"] or "none"),
        ("VRAM-efficient passing", summary["vram_efficient"] or "none"),
        ("Production ready", summary["production_ready"]),
    ]
    cards = "".join(
        f"<div class='card'><span>{escaped(label)}</span><strong>{escaped(value)}</strong></div>"
        for label, value in summary_items
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>AI Pipeline Evaluation</title><style>"
        ":root{color-scheme:light dark}body{font:15px system-ui;max-width:1440px;margin:auto;padding:2rem;line-height:1.45}"
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.75rem}.card{border:1px solid #7775;border-radius:8px;padding:.8rem}"
        ".card span{display:block;opacity:.7}.card strong{font-size:1.15rem}table{border-collapse:collapse;width:100%;margin:1rem 0 2rem}"
        "th,td{border:1px solid #7775;padding:.55rem;text-align:left}th{position:sticky;top:0;background:Canvas}.pass{color:#198754;font-weight:700}.fail{color:#dc3545;font-weight:700}"
        "details{border:1px solid #7775;border-radius:8px;margin:.7rem 0;padding:.7rem}summary{cursor:pointer;font-weight:700}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#7771;border-radius:6px;padding:.75rem;max-height:34rem;overflow:auto}code{overflow-wrap:anywhere}"
        "</style></head><body>"
        f"<h1>{escaped(report.get('title', 'AI Pipeline Evaluation'))}</h1>"
        f"<div class='cards'>{cards}</div><h2>Variants</h2>"
        "<table><thead><tr><th>Variant</th><th>Quality</th><th>Recall@8</th><th>MRR</th><th>Facts</th><th>Answer</th><th>p50 ms</th><th>Hard</th><th>Quality</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table><h2>Case evidence and traces</h2>"
        f"{''.join(case_sections)}</body></html>\n"
    )


def write_report(directory: Path, name: str, results: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Path]:
    report = {
        "schema_version": 1,
        "title": "Thunderbird AI Pipeline Evaluation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "environment": environment_record(),
        "manifest": manifest,
        "summary": summarize_matrix(results),
        "results": results,
    }
    json_path = directory / f"{name}.json"
    jsonl_path = directory / f"{name}.jsonl"
    markdown_path = directory / f"{name}.md"
    html_path = directory / f"{name}.html"
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_text(json_path, payload)
    _atomic_text(
        jsonl_path,
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in results),
    )
    markdown = markdown_report(report)
    _atomic_text(markdown_path, markdown)
    _atomic_text(html_path, html_report(report))
    return {"json": json_path, "jsonl": jsonl_path, "markdown": markdown_path, "html": html_path}


def checkpoint(path: Path, record: dict[str, Any]) -> None:
    _atomic_text(path, json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
