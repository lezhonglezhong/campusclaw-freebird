# Tasks

## 1. Retrieval persistence
- [x] 1.1 Add SQLite FTS5 retrieval-index initialization and lifecycle helpers for seed, successful upload, and deletion; verify `pytest tests/test_material_retrieval_index.py -q` succeeds

## 2. Protected retrieval API
- [x] 2.1 Implement `GET /api/materials/retrieve` with validated query, server-derived class filtering, bounded excerpts, and provenance payloads; verify `pytest tests/test_material_retrieval.py -q` succeeds
- [x] 2.2 Verify cross-class concealment, authentication, and invalid-query behavior; verify `pytest tests/test_material_retrieval_security.py -q` succeeds
- [x] 2.3 Add Chinese-content retrieval fallback while retaining session-class filtering and provenance; verify `pytest tests/test_material_retrieval.py tests/test_material_retrieval_security.py -q` succeeds

## 3. Browser retrieval
- [x] 3.1 Add a Simplified Chinese retrieval form and provenance-result rendering to the protected material workspace; verify `pytest tests/test_browser_retrieval.py -q` succeeds

## 4. Validation
- [ ] 4.1 Run full regression and strict change validation; verify `pytest -q && openspec validate add-class-scoped-material-retrieval-provenance --strict` succeeds
