# Design

## Context

See proposal.md. `material_retrieval` is a SQLite FTS5 companion table created only for SQLite. MySQL legacy retrieval already reads class-scoped `KnowledgeEntry.body_text`, while upload, delete, and seed still invoke the unconditional FTS write helpers. New chunk keyword indexing already branches by dialect.

## Goals / Non-Goals

**Goals:**
- Keep SQLite FTS behavior unchanged while making legacy index writes no-ops on MySQL.
- Verify JSON and multipart upload, deletion, seed, reindex, and both retrieval families against the relevant database paths.
- Restore derived vectors for materials whose deletion failed after Qdrant deletion.

**Non-Goals:**
- Change API contracts, authentication, schema, or search ranking.
- Delete or overwrite user materials during diagnosis.

## Decisions

1. Guard both legacy index write helpers by SQLAlchemy dialect at the helper boundary. This covers every caller, including future seed paths, without duplicating checks at each endpoint. The alternative of creating a legacy FTS table on MySQL would duplicate source text and conflict with the existing MySQL retrieval path.
2. Keep the successful delete flow's existing vector cleanup, but ensure the dialect error cannot happen after vector deletion. A broader distributed transaction/outbox redesign is outside this compatibility fix.
3. Add unit regression tests that fail if MySQL-bound helpers issue SQLite FTS SQL, retain SQLite FTS tests, and perform a controlled server-side MySQL canary upload/retrieval/delete after deployment. This closes the SQLite-only test gap without modifying existing user materials for the canary.
4. For materials 3 and 5, inspect stored indexing strategy/options, then reindex only if their ready relational chunks lack vector points. Preserve their strategy and source body.

## Risks / Trade-offs

- [A failure between vector deletion and database commit can still leave a missing point] → Verify the reported failed deletions and repair their points; treat a broader cross-store transaction redesign as separate work.
- [A live canary touches production-like services] → Use a uniquely named temporary material, verify its identity before deletion, and report any cleanup failure rather than deleting a different record.

## Migration Plan

No schema migration. Deploy the guarded helpers, run the full suite and live canary, compare affected relational chunk IDs with Qdrant, repair only missing derived indexes, and confirm all services remain healthy. Rollback is the previous application image/commit; persisted source materials remain authoritative.
