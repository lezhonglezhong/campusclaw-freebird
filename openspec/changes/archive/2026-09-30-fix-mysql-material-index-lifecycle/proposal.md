# Proposal

## Why

The MySQL deployment returns HTTP 500 for teacher uploads and deletions because legacy material-index helpers still issue SQL against a SQLite-only FTS table. The same helper is used by development seeding, so the material lifecycle needs a dialect-aware correction and a live regression check.

## What Changes

- Make legacy FTS writes run only for SQLite; MySQL continues to use persisted knowledge entries and its existing retrieval path.
- Audit upload, deletion, seed, reindex, and retrieval for the same SQLite-only dependency, and add regression coverage for both dialects.
- Verify a controlled upload/retrieval/deletion cycle on the MySQL deployment, then repair vector indexes for materials affected by the failed deletion attempts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This restores existing upload, deletion, seed, and indexing requirements without changing their behavior contract.

## Impact

`campusclaw/retrieval.py`, material lifecycle tests, the GPU3 MySQL/Qdrant deployment, and the affected materials' derived vector indexes. No API shape or authentication change.
