# Tasks

## 0. Authentication Prerequisite

- [x] 0.1 Apply `replace-cookie-session-with-bearer-token-auth` first and verify login returns a JWT while protected APIs reject missing/invalid Bearer headers and resolve role/class from the database; verify with `python -m pytest -q tests/test_token_auth.py tests/test_browser_token_auth.py`.

## 1. Foundations

- [ ] 1.1 Add environment-driven database, Qdrant, gateway, timeout, and vector-dimension configuration; implement independent embedding/chat/vector-store contracts and OpenAI-compatible adapters that append `/embeddings` or `/chat/completions` to the `/v1` base, use `course-embedding` and `course-chat`, send only `model` plus `input` for embeddings, validate 2048 numeric dimensions, reject serialized requests above 20 MB, authenticate without logging secrets, and remain injectable for tests; verify with `python -m pytest -q tests/test_config.py tests/test_ai_providers.py tests/test_vector_store.py tests/test_token_auth.py`.
- [ ] 1.2 Add `KnowledgeEntry` and `KnowledgeChunk` persistence models, relationships, uniqueness/cascade rules, separate text/vector statuses, and dialect-aware full-text index bootstrap without altering existing material records; verify with `python -m pytest -q tests/test_models.py tests/test_knowledge_models.py tests/test_retrieval_index.py`.
- [ ] 1.3 Implement the pure `auto`, `custom`, and `hierarchy` chunking service, including boundary preference, overlap, Markdown-heading retention, preprocessing, offsets, and parameter validation; verify with `python -m pytest -q tests/test_chunking.py`.

## 2. Index Lifecycle

- [ ] 2.1 Implement source-body persistence and idempotent automatic chunk creation for upload and seed paths, keeping keyword-ready text when embedding is unavailable and never exposing provider details; verify with `python -m pytest -q tests/test_upload.py tests/test_seed.py tests/test_knowledge_indexing.py`.
- [ ] 2.2 Implement vector upsert/delete orchestration with point IDs equal to chunk IDs, identifier-only payloads, per-chunk vector status, and no partial point on failed embedding; verify with `python -m pytest -q tests/test_vector_indexing.py`.
- [ ] 2.3 Implement `POST /api/materials/<material_id>/reindex` with Bearer-token teacher authorization, database-resolved class ownership, strategy validation before replacement, retry-safe replacement, and cross-class 404 behavior; verify with `python -m pytest -q tests/test_material_reindex.py tests/test_authorization.py tests/test_token_auth.py`.
- [ ] 2.4 Extend material deletion and seed/backfill behavior to remove or create relational chunks and Qdrant points without duplicates or orphans; verify with `python -m pytest -q tests/test_material_delete.py tests/test_seed.py tests/test_vector_indexing.py`.

## 3. Traceable Retrieval API

- [ ] 3.1 Implement keyword chunk retrieval and `GET /api/retrieval` request/authentication validation, requiring an `Authorization: Bearer` header and using the token-resolved user's current database class, relational text-ready filtering, Chinese matching, and normalized provenance hits without any embedding/vector call; verify with `python -m pytest -q tests/test_keyword_retrieval.py tests/test_retrieval_api.py tests/test_token_auth.py`.
- [ ] 3.2 Implement vector retrieval with query embedding, Qdrant filtering by the token-resolved database class, the 0.35 cosine cutoff, relational class/status recheck, ordered scores/ranks, and safe 503 mapping; verify with `python -m pytest -q tests/test_vector_retrieval.py tests/test_retrieval_security.py`.
- [ ] 3.3 Implement hybrid retrieval with pre-fusion filtering, RRF `k = 60`, deterministic tie-breaking, default-mode behavior, bounded provenance excerpts, and no weak-result padding; verify with `python -m pytest -q tests/test_hybrid_retrieval.py tests/test_retrieval_api.py`.
- [ ] 3.4 Preserve the legacy `/api/materials/retrieve` behavior while proving all new retrieval modes ignore request-supplied class identifiers and do not leak raw vectors, filesystem paths, foreign metadata, upstream bodies, or secrets; verify with `python -m pytest -q tests/test_material_retrieval.py tests/test_material_retrieval_security.py tests/test_retrieval_security.py`.

## 4. Grounded Answer API

- [ ] 4.1 Implement `POST /api/ask` Bearer authentication, validation, and history sanitization, retrieving only the latest question with the token-resolved user's current database class and ignoring client/token system/class/model overrides; verify with `python -m pytest -q tests/test_ask_api.py -k "validation or sanitization or authentication"`.
- [ ] 4.2 Implement the no-evidence short circuit so it returns `资料中未找到相关内容` with empty citations and zero chat-provider calls; verify with `python -m pytest -q tests/test_ask_api.py -k "no_evidence"`.
- [ ] 4.3 Implement evidence-gated `course-chat` orchestration through `/chat/completions` with at most four numbered text sources, server-owned instructions, bounded history, ordered traceable citations, provider-response validation, local 20 MB enforcement, and safe 503 errors; keep `image_url` serialization available only at the provider boundary without adding image UI or image retrieval; verify with `python -m pytest -q tests/test_ask_api.py tests/test_ai_providers.py -k "grounded or citation or provider or payload or image_url"`.

## 5. Browser Workspace

- [ ] 5.1 Restructure the protected workspace and styles into clear material, retrieval, grounded-answer, and teacher indexing panels with responsive result/citation cards, mode and strategy controls, accessible labels/status regions, and no client-side secret/vector fields; verify with `python -m pytest -q tests/test_browser_pages.py tests/test_browser_knowledge_ui.py`.
- [ ] 5.2 Implement browser behavior using the shared `sessionStorage` Bearer client for mode-aware retrieval, stale-result clearing, provenance links, empty/400/401/503 states, answer/citation alignment, and teacher-only strategy/reindex controls while preserving token-authenticated upload/download/delete flows; verify with `python -m pytest -q tests/test_browser_flow.py tests/test_browser_token_auth.py tests/test_browser_retrieval.py tests/test_browser_ask.py tests/test_browser_reindex.py`.

## 6. Reproducible Runtime and Documentation

- [ ] 6.1 Add required Python dependencies and extend Compose with healthy MySQL 8 and Qdrant services, persistent volumes, internal-only dependency ports, application dependency checks, MySQL ngram configuration, and documented environment placeholders without real secrets; verify with `docker compose config --quiet`.
- [ ] 6.2 Update seed/backfill commands and README instructions for first startup, JWT Bearer login and request headers, private course gateway configuration (`course-embedding`, 2048 dimensions, and `course-chat`) without a real key, reindexing after configuration, the 20 MB request ceiling, three retrieval modes, grounded answers, and dependency failure behavior; verify with `python -m pytest -q tests/test_seed.py tests/test_config.py tests/test_health.py tests/test_token_auth.py`.

## 7. Acceptance

- [ ] 7.1 Run the complete automated suite and fix regressions across authentication, role checks, class isolation, upload/download/delete, legacy retrieval, new indexing/retrieval/ask APIs, and browser behavior; verify with `python -m pytest -q`.
- [ ] 7.2 Validate the OpenSpec change strictly and verify the final Compose model after all documentation and configuration updates; verify with `openspec validate add-traceable-vector-retrieval --strict && docker compose config --quiet`.
