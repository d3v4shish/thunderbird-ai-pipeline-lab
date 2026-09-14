# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0.

"""Scope-locked SQLite/FTS5 storage and retrieval."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Iterable

from .contracts import Chunk, Document, Evidence, Scope, content_digest
from .template_mining import TemplateAssignment, TemplateFamily, TemplateSlot
from .text import cosine, exact_entities, local_embedding, terms, vector_bucket_keys


class Index:
    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        normalized_parent_storage: bool = False,
    ) -> None:
        self.path = str(path)
        self.normalized_parent_storage = normalized_parent_storage
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents(
              id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              title TEXT NOT NULL,
              body TEXT NOT NULL,
              timestamp TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              PRIMARY KEY(tenant, collection_name, id)
            );
            CREATE INDEX IF NOT EXISTS documents_scope
              ON documents(tenant, collection_name);
            CREATE TABLE IF NOT EXISTS parent_passages(
              id TEXT PRIMARY KEY,
              document_id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              passage_text TEXT NOT NULL,
              start_offset INTEGER NOT NULL,
              end_offset INTEGER NOT NULL,
              section_label TEXT NOT NULL,
              FOREIGN KEY(tenant, collection_name, document_id)
                REFERENCES documents(tenant, collection_name, id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS parent_passages_scope
              ON parent_passages(tenant, collection_name, document_id, start_offset);
            CREATE TABLE IF NOT EXISTS chunks(
              id TEXT PRIMARY KEY,
              document_id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              ordinal INTEGER NOT NULL,
              passage_text TEXT NOT NULL,
              contextual_text TEXT NOT NULL,
              start_offset INTEGER NOT NULL,
              end_offset INTEGER NOT NULL,
              section_label TEXT NOT NULL,
              embedding_json TEXT NOT NULL,
              parent_passage_id TEXT,
              FOREIGN KEY(tenant, collection_name, document_id)
                REFERENCES documents(tenant, collection_name, id) ON DELETE CASCADE,
              FOREIGN KEY(parent_passage_id)
                REFERENCES parent_passages(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS chunks_scope
              ON chunks(tenant, collection_name, document_id, ordinal);
            CREATE INDEX IF NOT EXISTS chunks_document
              ON chunks(document_id);
            CREATE TABLE IF NOT EXISTS vector_buckets(
              chunk_id TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              dimension INTEGER NOT NULL,
              bucket_key TEXT NOT NULL,
              PRIMARY KEY(chunk_id, dimension, bucket_key)
            );
            CREATE INDEX IF NOT EXISTS vector_bucket_lookup
              ON vector_buckets(tenant, collection_name, dimension, bucket_key);
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
              chunk_id UNINDEXED,
              tenant UNINDEXED,
              collection_name UNINDEXED,
              text,
              tokenize='unicode61 remove_diacritics 2'
            );
            CREATE TABLE IF NOT EXISTS exact_entities(
              kind TEXT NOT NULL,
              value TEXT NOT NULL,
              chunk_id TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
              document_id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              PRIMARY KEY(kind, value, chunk_id)
            );
            CREATE INDEX IF NOT EXISTS exact_scope_value
              ON exact_entities(tenant, collection_name, value);
            CREATE TABLE IF NOT EXISTS template_families(
              id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              sender_domain TEXT NOT NULL,
              surface TEXT NOT NULL,
              template_tokens_json TEXT NOT NULL,
              regex TEXT NOT NULL,
              observations INTEGER NOT NULL,
              mature INTEGER NOT NULL,
              algorithm_version TEXT NOT NULL,
              schema_version INTEGER NOT NULL,
              PRIMARY KEY(tenant, collection_name, id)
            );
            CREATE TABLE IF NOT EXISTS template_assignments(
              document_id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              source_digest TEXT NOT NULL,
              family_id TEXT NOT NULL,
              score REAL NOT NULL,
              analysis_text TEXT NOT NULL,
              schema_version INTEGER NOT NULL,
              PRIMARY KEY(tenant, collection_name, document_id),
              FOREIGN KEY(tenant, collection_name, document_id)
                REFERENCES documents(tenant, collection_name, id) ON DELETE CASCADE,
              FOREIGN KEY(tenant, collection_name, family_id)
                REFERENCES template_families(tenant, collection_name, id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS template_assignment_family
              ON template_assignments(tenant, collection_name, family_id);
            CREATE TABLE IF NOT EXISTS template_slots(
              document_id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              collection_name TEXT NOT NULL,
              ordinal INTEGER NOT NULL,
              slot_type TEXT NOT NULL,
              value TEXT NOT NULL,
              start_offset INTEGER NOT NULL,
              end_offset INTEGER NOT NULL,
              schema_version INTEGER NOT NULL,
              PRIMARY KEY(tenant, collection_name, document_id, ordinal),
              FOREIGN KEY(tenant, collection_name, document_id)
                REFERENCES template_assignments(tenant, collection_name, document_id)
                ON DELETE CASCADE
            );
            """
        )
        columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(chunks)")
        }
        if "parent_passage_id" not in columns:
            self.connection.execute(
                "ALTER TABLE chunks ADD COLUMN parent_passage_id TEXT"
            )

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Index":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def clear(self) -> None:
        with self.connection:
            tables = {
                row[0]
                for row in self.connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "graph_edges" in tables:
                self.connection.execute("DELETE FROM graph_edges")
            if "graph_nodes" in tables:
                self.connection.execute("DELETE FROM graph_nodes")
            if "template_slots" in tables:
                self.connection.execute("DELETE FROM template_slots")
            if "template_assignments" in tables:
                self.connection.execute("DELETE FROM template_assignments")
            if "template_families" in tables:
                self.connection.execute("DELETE FROM template_families")
            self.connection.execute("DELETE FROM chunks_fts")
            self.connection.execute("DELETE FROM documents")

    def add_document(
        self,
        document: Document,
        chunks: Iterable[Chunk],
        embeddings: dict[str, list[float]] | None = None,
        build_vector_buckets: bool = True,
    ) -> int:
        chunk_list = list(chunks)
        with self.connection:
            self.connection.execute(
                """DELETE FROM template_assignments
                   WHERE document_id = ? AND tenant = ? AND collection_name = ?
                     AND source_digest != ?""",
                (
                    document.id,
                    document.tenant,
                    document.collection,
                    content_digest(document.text),
                ),
            )
            old_ids = [
                row[0]
                for row in self.connection.execute(
                    """SELECT id FROM chunks WHERE document_id = ?
                       AND tenant = ? AND collection_name = ?""",
                    (document.id, document.tenant, document.collection),
                )
            ]
            if old_ids:
                self.connection.executemany(
                    "DELETE FROM chunks_fts WHERE chunk_id = ?",
                    ((chunk_id,) for chunk_id in old_ids),
                )
            old_parent_ids = [
                row[0]
                for row in self.connection.execute(
                    """SELECT id FROM parent_passages WHERE document_id = ?
                       AND tenant = ? AND collection_name = ?""",
                    (document.id, document.tenant, document.collection),
                )
            ]
            self.connection.execute(
                """INSERT INTO documents(
                     id, tenant, collection_name, title, body, timestamp, metadata_json
                   ) VALUES(?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant, collection_name, id) DO UPDATE SET
                     title=excluded.title,
                     body=excluded.body,
                     timestamp=excluded.timestamp,
                     metadata_json=excluded.metadata_json""",
                (
                    document.id,
                    document.tenant,
                    document.collection,
                    document.title,
                    document.text,
                    document.timestamp,
                    json.dumps(document.metadata, ensure_ascii=False, sort_keys=True),
                ),
            )
            self.connection.execute(
                """DELETE FROM chunks WHERE document_id = ?
                   AND tenant = ? AND collection_name = ?""",
                (document.id, document.tenant, document.collection),
            )
            if old_parent_ids:
                self.connection.executemany(
                    "DELETE FROM parent_passages WHERE id = ?",
                    ((parent_id,) for parent_id in old_parent_ids),
                )
            for chunk in chunk_list:
                vector = (embeddings or {}).get(
                    chunk.id, local_embedding(chunk.contextual_text)
                )
                parent_id = None
                passage_text = chunk.text
                if self.normalized_parent_storage:
                    identity = "\0".join(
                        (
                            chunk.tenant,
                            chunk.collection,
                            chunk.document_id,
                            str(chunk.start),
                            str(chunk.end),
                        )
                    )
                    parent_id = sha256(identity.encode("utf-8")).hexdigest()
                    self.connection.execute(
                        """INSERT OR IGNORE INTO parent_passages VALUES(
                             ?, ?, ?, ?, ?, ?, ?, ?
                           )""",
                        (
                            parent_id,
                            chunk.document_id,
                            chunk.tenant,
                            chunk.collection,
                            chunk.text,
                            chunk.start,
                            chunk.end,
                            chunk.section,
                        ),
                    )
                    passage_text = ""
                self.connection.execute(
                    """INSERT INTO chunks(
                         id, document_id, tenant, collection_name, ordinal,
                         passage_text, contextual_text, start_offset, end_offset,
                         section_label, embedding_json, parent_passage_id
                       ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.tenant,
                        chunk.collection,
                        chunk.ordinal,
                        passage_text,
                        chunk.contextual_text,
                        chunk.start,
                        chunk.end,
                        chunk.section,
                        json.dumps(
                            vector,
                            separators=(",", ":"),
                        ),
                        parent_id,
                    ),
                )
                self.connection.execute(
                    "INSERT INTO chunks_fts(chunk_id, tenant, collection_name, text) VALUES(?, ?, ?, ?)",
                    (chunk.id, chunk.tenant, chunk.collection, chunk.contextual_text),
                )
                for kind, value in exact_entities(
                    chunk.retrieval_text or chunk.text
                ):
                    self.connection.execute(
                        "INSERT OR IGNORE INTO exact_entities VALUES(?, ?, ?, ?, ?, ?)",
                        (kind, value, chunk.id, document.id, document.tenant, document.collection),
                    )
                if build_vector_buckets:
                    self.connection.executemany(
                        "INSERT INTO vector_buckets VALUES(?, ?, ?, ?, ?)",
                        (
                            (
                                chunk.id,
                                document.tenant,
                                document.collection,
                                len(vector),
                                bucket_key,
                            )
                            for bucket_key in vector_bucket_keys(vector)
                        ),
                    )
        return len(chunk_list)

    def put_template_family(self, family: TemplateFamily) -> None:
        with self.connection:
            self.connection.execute(
                """INSERT INTO template_families VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant, collection_name, id) DO UPDATE SET
                     sender_domain=excluded.sender_domain,
                     surface=excluded.surface,
                     template_tokens_json=excluded.template_tokens_json,
                     regex=excluded.regex,
                     observations=excluded.observations,
                     mature=excluded.mature,
                     algorithm_version=excluded.algorithm_version,
                     schema_version=excluded.schema_version""",
                (
                    family.id,
                    family.tenant,
                    family.collection,
                    family.sender_domain,
                    family.surface,
                    json.dumps(family.template_tokens, separators=(",", ":")),
                    family.regex,
                    family.observations,
                    int(family.mature),
                    family.algorithm_version,
                    family.schema_version,
                ),
            )

    def put_template_assignment(self, assignment: TemplateAssignment) -> None:
        row = self.connection.execute(
            """SELECT body FROM documents
               WHERE id = ? AND tenant = ? AND collection_name = ?""",
            (assignment.document_id, assignment.tenant, assignment.collection),
        ).fetchone()
        if not row:
            raise ValueError("template assignment source document is unavailable")
        source = str(row["body"])
        if content_digest(source) != assignment.source_digest:
            raise ValueError("template assignment source digest does not match")
        if not self.connection.execute(
            """SELECT 1 FROM template_families
               WHERE id = ? AND tenant = ? AND collection_name = ?""",
            (assignment.family_id, assignment.tenant, assignment.collection),
        ).fetchone():
            raise ValueError("template assignment family is unavailable in scope")
        for slot in assignment.slots:
            if source[slot.start : slot.end] != slot.value:
                raise ValueError("template slot does not match its source span")
        with self.connection:
            self.connection.execute(
                """INSERT INTO template_assignments VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tenant, collection_name, document_id) DO UPDATE SET
                     source_digest=excluded.source_digest,
                     family_id=excluded.family_id,
                     score=excluded.score,
                     analysis_text=excluded.analysis_text,
                     schema_version=excluded.schema_version""",
                (
                    assignment.document_id,
                    assignment.tenant,
                    assignment.collection,
                    assignment.source_digest,
                    assignment.family_id,
                    assignment.score,
                    assignment.analysis_text,
                    assignment.schema_version,
                ),
            )
            self.connection.execute(
                """DELETE FROM template_slots
                   WHERE document_id = ? AND tenant = ? AND collection_name = ?""",
                (assignment.document_id, assignment.tenant, assignment.collection),
            )
            self.connection.executemany(
                "INSERT INTO template_slots VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        assignment.document_id,
                        assignment.tenant,
                        assignment.collection,
                        ordinal,
                        slot.slot_type,
                        slot.value,
                        slot.start,
                        slot.end,
                        slot.schema_version,
                    )
                    for ordinal, slot in enumerate(assignment.slots)
                ),
            )

    def template_assignment(
        self, document_id: str, scope: Scope
    ) -> TemplateAssignment | None:
        row = self.connection.execute(
            """SELECT * FROM template_assignments
               WHERE document_id = ? AND tenant = ? AND collection_name = ?""",
            (document_id, scope.tenant, scope.collection),
        ).fetchone()
        if not row:
            return None
        source = self.connection.execute(
            """SELECT body FROM documents
               WHERE id = ? AND tenant = ? AND collection_name = ?""",
            (document_id, scope.tenant, scope.collection),
        ).fetchone()
        if not source or content_digest(str(source["body"])) != row["source_digest"]:
            return None
        slots = tuple(
            TemplateSlot(
                slot_type=item["slot_type"],
                value=item["value"],
                start=item["start_offset"],
                end=item["end_offset"],
                schema_version=item["schema_version"],
            )
            for item in self.connection.execute(
                """SELECT * FROM template_slots
                   WHERE document_id = ? AND tenant = ? AND collection_name = ?
                   ORDER BY ordinal""",
                (document_id, scope.tenant, scope.collection),
            )
        )
        return TemplateAssignment(
            tenant=row["tenant"],
            collection=row["collection_name"],
            document_id=row["document_id"],
            source_digest=row["source_digest"],
            family_id=row["family_id"],
            score=float(row["score"]),
            slots=slots,
            analysis_text=row["analysis_text"],
            schema_version=row["schema_version"],
        )

    def template_family_document_ids(
        self, family_id: str, scope: Scope
    ) -> list[str]:
        """Return current source-backed family members in canonical order."""
        rows = self.connection.execute(
            """SELECT a.document_id, a.source_digest, d.body, d.timestamp
               FROM template_assignments a
               JOIN documents d
                 ON d.id = a.document_id
                AND d.tenant = a.tenant
                AND d.collection_name = a.collection_name
               WHERE a.family_id = ? AND a.tenant = ?
                 AND a.collection_name = ?
               ORDER BY d.timestamp, a.document_id""",
            (family_id, scope.tenant, scope.collection),
        )
        return [
            str(row["document_id"])
            for row in rows
            if content_digest(str(row["body"])) == row["source_digest"]
        ]

    def thread_document_ids(self, thread_id: str, scope: Scope) -> list[str]:
        """Return same-scope thread members in canonical order."""
        rows = self.connection.execute(
            """SELECT id, timestamp, metadata_json FROM documents
               WHERE tenant = ? AND collection_name = ?
               ORDER BY timestamp, id""",
            (scope.tenant, scope.collection),
        )
        result = []
        for row in rows:
            metadata = json.loads(row["metadata_json"])
            if str(metadata.get("thread_id", "")) == thread_id:
                result.append(str(row["id"]))
        return result

    def delete_document(self, document_id: str, scope: Scope) -> None:
        with self.connection:
            chunk_ids = [
                row[0]
                for row in self.connection.execute(
                    """SELECT id FROM chunks
                       WHERE document_id = ? AND tenant = ? AND collection_name = ?""",
                    (document_id, scope.tenant, scope.collection),
                )
            ]
            self.connection.executemany(
                "DELETE FROM chunks_fts WHERE chunk_id = ?",
                ((chunk_id,) for chunk_id in chunk_ids),
            )
            self.connection.execute(
                """DELETE FROM documents
                   WHERE id = ? AND tenant = ? AND collection_name = ?""",
                (document_id, scope.tenant, scope.collection),
            )

    def document(self, document_id: str, scope: Scope) -> Document | None:
        row = self.connection.execute(
            """SELECT * FROM documents
               WHERE id = ? AND tenant = ? AND collection_name = ?""",
            (document_id, scope.tenant, scope.collection),
        ).fetchone()
        if not row:
            return None
        return Document(
            id=row["id"],
            tenant=row["tenant"],
            collection=row["collection_name"],
            title=row["title"],
            text=row["body"],
            timestamp=row["timestamp"],
            metadata=json.loads(row["metadata_json"]),
        )

    def chunk(self, chunk_id: str, scope: Scope) -> Evidence | None:
        row = self.connection.execute(
            """SELECT c.*,
                      COALESCE(p.passage_text, c.passage_text) AS resolved_passage_text
               FROM chunks c LEFT JOIN parent_passages p
                 ON p.id = c.parent_passage_id
               WHERE c.id = ? AND c.tenant = ? AND c.collection_name = ?""",
            (chunk_id, scope.tenant, scope.collection),
        ).fetchone()
        return self._evidence(row, 1.0, ("fetch",)) if row else None

    def chunks_for_document(self, document_id: str, scope: Scope) -> list[Evidence]:
        rows = self.connection.execute(
            """SELECT c.*,
                      COALESCE(p.passage_text, c.passage_text) AS resolved_passage_text
               FROM chunks c LEFT JOIN parent_passages p
                 ON p.id = c.parent_passage_id
               WHERE c.document_id = ? AND c.tenant = ?
                 AND c.collection_name = ? ORDER BY c.ordinal""",
            (document_id, scope.tenant, scope.collection),
        )
        return [self._evidence(row, 1.0, ("outline",)) for row in rows]

    def exact_search(self, query: str, scope: Scope, limit: int = 24) -> list[Evidence]:
        values = [value for _, value in exact_entities(query)]
        if not values:
            return []
        placeholders = ",".join("?" for _ in values)
        rows = self.connection.execute(
            f"""SELECT c.*,
                       COALESCE(p.passage_text, c.passage_text) AS resolved_passage_text,
                       COUNT(*) AS match_count
                FROM exact_entities e JOIN chunks c ON c.id = e.chunk_id
                LEFT JOIN parent_passages p ON p.id = c.parent_passage_id
                WHERE e.tenant = ? AND e.collection_name = ?
                  AND e.value IN ({placeholders})
                GROUP BY c.id ORDER BY match_count DESC, c.ordinal LIMIT ?""",
            (scope.tenant, scope.collection, *values, limit),
        )
        return [self._evidence(row, float(row["match_count"]), ("exact",)) for row in rows]

    @staticmethod
    def _fts_query(query: str) -> str:
        unique = list(dict.fromkeys(terms(query)))[:32]
        return " OR ".join(f'"{word.replace(chr(34), "")}"' for word in unique)

    def lexical_search(self, query: str, scope: Scope, limit: int = 24) -> list[Evidence]:
        fts_query = self._fts_query(query)
        if not fts_query:
            return []
        rows = self.connection.execute(
            """SELECT c.*,
                      COALESCE(p.passage_text, c.passage_text) AS resolved_passage_text,
                      bm25(chunks_fts) AS rank
               FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.chunk_id
               LEFT JOIN parent_passages p ON p.id = c.parent_passage_id
               WHERE chunks_fts MATCH ? AND chunks_fts.tenant = ?
                 AND chunks_fts.collection_name = ?
               ORDER BY rank LIMIT ?""",
            (fts_query, scope.tenant, scope.collection, limit),
        )
        return [
            self._evidence(row, 1.0 / (index + 1), ("lexical",))
            for index, row in enumerate(rows)
        ]

    def dense_search(
        self,
        query: str,
        scope: Scope,
        limit: int = 24,
        query_vector: list[float] | None = None,
        candidate_mode: str = "lsh",
    ) -> list[Evidence]:
        query_vector = query_vector or local_embedding(query)
        if candidate_mode == "lsh":
            bucket_keys = vector_bucket_keys(query_vector, include_neighbors=True)
            if not bucket_keys:
                return []
            placeholders = ",".join("?" for _ in bucket_keys)
            rows = self.connection.execute(
                f"""SELECT DISTINCT c.*,
                           COALESCE(p.passage_text, c.passage_text) AS resolved_passage_text
                    FROM vector_buckets b
                    JOIN chunks c ON c.id = b.chunk_id
                    LEFT JOIN parent_passages p ON p.id = c.parent_passage_id
                    WHERE b.tenant = ? AND b.collection_name = ?
                      AND b.dimension = ? AND b.bucket_key IN ({placeholders})""",
                (scope.tenant, scope.collection, len(query_vector), *bucket_keys),
            )
        elif candidate_mode == "full-scan":
            rows = self.connection.execute(
                """SELECT c.*,
                          COALESCE(p.passage_text, c.passage_text) AS resolved_passage_text
                   FROM chunks c LEFT JOIN parent_passages p
                     ON p.id = c.parent_passage_id
                   WHERE c.tenant = ? AND c.collection_name = ?""",
                (scope.tenant, scope.collection),
            )
        else:
            raise ValueError(f"Unsupported dense candidate mode: {candidate_mode}")
        scored = [
            (cosine(query_vector, json.loads(row["embedding_json"])), row)
            for row in rows
        ]
        scored.sort(key=lambda item: (-item[0], item[1]["id"]))
        return [
            self._evidence(row, score, ("dense",))
            for score, row in scored[:limit]
            if score > 0
        ]

    def hybrid_search(
        self,
        query: str,
        scope: Scope,
        limit: int = 24,
        rrf_k: int = 60,
        query_vector: list[float] | None = None,
        candidate_mode: str = "lsh",
    ) -> list[Evidence]:
        channels = [
            self.exact_search(query, scope, limit * 2),
            self.lexical_search(query, scope, limit * 2),
            self.dense_search(query, scope, limit * 2, query_vector, candidate_mode),
        ]
        scores: defaultdict[str, float] = defaultdict(float)
        evidence: dict[str, Evidence] = {}
        seen_channels: defaultdict[str, list[str]] = defaultdict(list)
        for results in channels:
            for rank, item in enumerate(results):
                scores[item.chunk_id] += 1.0 / (rrf_k + rank + 1)
                evidence[item.chunk_id] = item
                for channel in item.channels:
                    if channel not in seen_channels[item.chunk_id]:
                        seen_channels[item.chunk_id].append(channel)
        ranked = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
        return [
            Evidence(
                chunk_id=evidence[key].chunk_id,
                document_id=evidence[key].document_id,
                tenant=evidence[key].tenant,
                collection=evidence[key].collection,
                text=evidence[key].text,
                start=evidence[key].start,
                end=evidence[key].end,
                score=scores[key],
                channels=tuple(seen_channels[key]),
                section=evidence[key].section,
            )
            for key in ranked
        ]

    def search(
        self,
        query: str,
        scope: Scope,
        mode: str,
        limit: int = 24,
        rrf_k: int = 60,
        query_vector: list[float] | None = None,
        candidate_mode: str = "lsh",
    ) -> list[Evidence]:
        if mode == "hybrid":
            return self.hybrid_search(
                query, scope, limit, rrf_k, query_vector, candidate_mode
            )
        if mode == "exact":
            return self.exact_search(query, scope, limit)
        if mode == "lexical":
            return self.lexical_search(query, scope, limit)
        if mode == "dense":
            return self.dense_search(
                query, scope, limit, query_vector, candidate_mode
            )
        if mode not in {"exact", "lexical", "dense"}:
            raise ValueError(f"Unsupported retrieval mode: {mode}")
        raise AssertionError("unreachable retrieval mode")

    def embedding_rerank(
        self, query_vector: list[float], evidence: list[Evidence]
    ) -> list[Evidence]:
        if not evidence:
            return []
        chunk_ids = [item.chunk_id for item in evidence]
        placeholders = ",".join("?" for _ in chunk_ids)
        rows = self.connection.execute(
            f"SELECT id, embedding_json FROM chunks WHERE id IN ({placeholders})",
            chunk_ids,
        )
        vectors = {row["id"]: json.loads(row["embedding_json"]) for row in rows}
        reranked = [
            Evidence(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                tenant=item.tenant,
                collection=item.collection,
                text=item.text,
                start=item.start,
                end=item.end,
                score=cosine(query_vector, vectors.get(item.chunk_id, [])),
                channels=item.channels + ("embedding-rerank",),
                section=item.section,
            )
            for item in evidence
        ]
        return sorted(reranked, key=lambda item: (-item.score, item.chunk_id))

    def verify_evidence(self, item: Evidence, scope: Scope) -> bool:
        if item.tenant != scope.tenant or item.collection != scope.collection:
            return False
        document = self.document(item.document_id, scope)
        return bool(document and document.text[item.start : item.end] == item.text)

    def storage_stats(self) -> dict[str, int]:
        """Return deterministic logical storage counts for paired benchmarks."""
        row = self.connection.execute(
            """SELECT
                 (SELECT COUNT(*) FROM chunks) AS chunks,
                 (SELECT COUNT(*) FROM parent_passages) AS parents,
                 (SELECT COALESCE(SUM(LENGTH(passage_text)), 0) FROM chunks)
                   AS chunk_passage_characters,
                 (SELECT COALESCE(SUM(LENGTH(passage_text)), 0)
                    FROM parent_passages) AS parent_passage_characters,
                 (SELECT COALESCE(SUM(LENGTH(contextual_text)), 0) FROM chunks)
                   AS contextual_characters"""
        ).fetchone()
        return {key: int(row[key]) for key in row.keys()}

    @staticmethod
    def _evidence(row: sqlite3.Row, score: float, channels: tuple[str, ...]) -> Evidence:
        text = (
            row["resolved_passage_text"]
            if "resolved_passage_text" in row.keys()
            else row["passage_text"]
        )
        return Evidence(
            chunk_id=row["id"],
            document_id=row["document_id"],
            tenant=row["tenant"],
            collection=row["collection_name"],
            text=text,
            start=row["start_offset"],
            end=row["end_offset"],
            score=score,
            channels=channels,
            section=row["section_label"],
        )


def deterministic_rerank(query: str, evidence: list[Evidence]) -> list[Evidence]:
    query_terms = set(terms(query))
    exact_values = {value for _, value in exact_entities(query)}
    rescored: list[Evidence] = []
    for item in evidence:
        item_terms = set(terms(item.text))
        overlap = len(query_terms & item_terms) / max(1, len(query_terms))
        exact_bonus = sum(value.casefold() in item.text.casefold() for value in exact_values)
        rescored.append(
            Evidence(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                tenant=item.tenant,
                collection=item.collection,
                text=item.text,
                start=item.start,
                end=item.end,
                score=item.score + overlap + exact_bonus,
                channels=item.channels + ("rerank",),
                section=item.section,
            )
        )
    return sorted(rescored, key=lambda item: (-item.score, item.chunk_id))
