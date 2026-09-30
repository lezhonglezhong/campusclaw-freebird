# Design

## Context

See `proposal.md` for motivation. The repository is a small Flask application with SQLAlchemy, signed Flask session cookies, server-side role/class checks, local text/Markdown storage, SQLite FTS5 material-level retrieval, and a plain HTML/CSS/JavaScript workspace. The separate `replace-cookie-session-with-bearer-token-auth` change replaces that legacy cookie session with Bearer access tokens before these protected knowledge APIs are applied. Compose currently starts only the application. The fourth-course contract adds chunk-level relational data, a MySQL full-text path, Qdrant vectors, two model-facing interfaces, three retrieval modes, grounded answers, and additional browser interactions.

The course gateway exposes an OpenAI-compatible API at a configurable base URL ending in `/v1`. Embeddings use `POST /embeddings` with model `course-embedding`; grounded generation uses `POST /chat/completions` with model `course-chat`. The supplied credential is deployment-only and must never be committed. Implementation still needs strict provider contracts and injectable fakes so orchestration, failure, and security behavior remain deterministic in tests.

## Goals / Non-Goals

**Goals:**

- Preserve the existing Flask application, database-backed class authorization, upload/download behavior, and fast SQLite test suite while consuming the shared Bearer-token authentication layer and making Compose match the course MySQL/Qdrant architecture.
- Keep source text authoritative in relational storage and keep Qdrant limited to vectors and identifiers.
- Make chunking, indexing, retrieval, and answer generation separately testable.
- Fail closed on class scope and fail explicitly when vector/model dependencies are unavailable.
- Keep keyword retrieval useful even before the embedding API is configured.

**Non-Goals:**

- Asynchronous job queues, streaming chat, document formats beyond existing UTF-8 text/Markdown, semantic rerankers, or a general conversation platform.
- Browser-managed API keys, direct browser access to Qdrant/model gateways, or migration of the application to the tutorial's Go sample stack.

## Decisions

### 1. Preserve Flask/SQLAlchemy and add a production MySQL profile

The application will continue to use Flask and SQLAlchemy. `DATABASE_URL` becomes environment-driven; Compose supplies a MySQL 8 URL, while tests may continue to use temporary SQLite databases. New `knowledge_entries` and `knowledge_chunks` tables are additive, so existing `materials` rows do not require destructive alteration. MySQL bootstrap creates a UTF-8 `FULLTEXT` index using the ngram parser and token size 2. SQLite tests use an FTS5 companion table or a deterministic literal fallback with the same service contract.

This avoids a framework rewrite and keeps existing tests valuable. The alternative—rewriting to Go because the tutorial diagrams use Go—would add broad unrelated risk without changing the required behavior.

### 2. Persist original bodies and chunks as separate relational records

Each material owns one `KnowledgeEntry` containing the decoded original `body_text`. Each `KnowledgeChunk` stores class/material/entry identifiers, `chunk_index`, `start_offset`, `end_offset`, `chunk_text`, `text_status`, and `vector_status`. A uniqueness constraint on `(knowledge_entry_id, chunk_index)` and foreign-key cascades prevent duplicates and orphaned rows.

Separate text and vector statuses let keyword retrieval remain available when the provider or Qdrant is not configured. Offsets refer to the actual chunking input; custom preprocessing metadata is stored with the entry so the UI does not misrepresent offsets as original-file positions.

The alternative—putting full text into Qdrant payloads—would duplicate protected content and weaken the relational authorization recheck.

### 3. Isolate chunking behind a pure deterministic service

The chunker accepts body text plus a typed strategy object and returns value objects containing text, sequence, and offsets. It performs no database or provider calls. Validation occurs before index replacement. `auto` implements the 800/80 window with preferred boundaries; `custom` validates size, overlap, separator, and preprocessing; `hierarchy` preserves Markdown headings and delegates oversized sections to the automatic window helper.

Keeping chunking pure makes boundary, overlap, Unicode, and preprocessing behavior testable without infrastructure. The alternative—embedding chunk logic in upload handlers—would couple authorization, file I/O, and indexing and make safe reindexing harder.

### 4. Use explicit embedding, chat, and vector-store ports

Define three independent server-side contracts:

- `EmbeddingProvider.embed(texts) -> vectors`
- `ChatProvider.answer(system_instruction, question, history, sources) -> text`
- `VectorStore` collection/upsert/delete/search operations

Production HTTP adapters read base URLs, model names, timeouts, and secrets from environment variables. `EMBEDDING_BASE_URL` is the `/v1` base and the adapter appends exactly `/embeddings`; it sends only `model: "course-embedding"` and `input`, then validates that each `data[*].embedding` is numeric and exactly `EMBEDDING_DIM=2048` elements long. The 2048 dimension is local collection configuration and response validation, never an embedding request field. The chat adapter appends exactly `/chat/completions`, sends `model: "course-chat"` and server-assembled `messages`, and uses the same course gateway credential unless a distinct chat credential is configured. Both adapters authenticate with a Bearer header, reject a serialized request above 20 MB before network I/O, apply bounded timeouts, and never log credentials or raw upstream error bodies. Tests inject deterministic fakes. Missing or invalid configuration raises a typed availability error translated to HTTP 503 without leakage.

Qdrant uses collection `campusclaw_chunks`, cosine distance, and exactly 2048 dimensions. Point ID equals `knowledge_chunks.id`; payload contains identifiers only. The transport serializer supports the OpenAI-compatible `image_url` message part for a future multimodal caller, but this change passes text-only grounded sources and does not add image upload, vision retrieval, or image analysis behavior.

The embedding and chat ports remain separate because they have different inputs, failure modes, and credentials. A monolithic "AI client" would make it easy to call generation on the no-evidence path or accidentally send vectors to chat.

### 5. Index source first, then vectorize with explicit per-chunk outcomes

Upload first commits the material file, material row, original `KnowledgeEntry`, validated chunks, and keyword-search representation. It then embeds chunks and upserts vectors, updating `vector_status` per chunk. An embedding failure keeps the material and keyword-ready chunks, marks vector status failed, and creates no partial point for the failed chunk.

Reindex validates and chunks in memory before changing persisted data. It then removes the material's old Qdrant points and replaces the relational chunk set in one database transaction, followed by vectorization. Deletion removes vector points and relational rows along with the existing material workflow. Seed indexing is idempotent and defaults to `auto`.

This synchronous sequence is sufficient for course-scale documents and exposes status immediately. A background queue would improve latency and retry behavior but would require additional infrastructure outside this change.

### 6. Add a new chunk retrieval API while retaining the old endpoint

`GET /api/retrieval` is the new contract. The existing `/api/materials/retrieve` material-level endpoint remains temporarily available so the earlier completed change and tests do not break; the browser moves to the new endpoint.

The retrieval service implements:

- `keyword`: relational full-text query over text-ready chunks with `class_id = authenticated_user.class_id`, where the user was resolved from the validated Bearer token; no embedding or Qdrant call.
- `vector`: embed the query, search Qdrant with the same database-derived class filter, drop cosine scores below 0.35, then hydrate only vector-ready rows using both chunk IDs and that class.
- `hybrid`: execute both paths, filter first, and fuse ranks with `1 / (60 + rank)`. Stable tie-breaking uses best contributing rank, then chunk ID.

All paths normalize to one hit DTO containing identifiers, title, chunk index, offsets, relational excerpt, authorized material URL, and available scores/ranks. No raw vector is returned. Vector-dependent failures become 503; keyword remains independent.

### 7. Derive class and role from the database user resolved by a validated Bearer token

The authentication change's Bearer decorator is the API boundary. Retrieval, ask, and reindex handlers receive the database user resolved from a valid, unexpired access token; they never accept an authoritative class or role from request fields or JWT claims. Any client `class_id` is ignored. Qdrant filtering and relational hydration both apply the database user's current class, providing defense in depth even if account membership changes after token issuance.

The shared browser request helper reads the access token from `sessionStorage` and attaches `Authorization: Bearer <token>` to every protected API call. Retrieval code never reads authentication cookies and does not copy the token, identity, role, class, provider keys, or vectors into URLs, query parameters, logs, DOM attributes, or longer-lived storage.

### 8. Make answer generation a thin evidence-gated orchestration layer

`POST /api/ask` validates the newest question, bounds prior user/assistant history, drops all client system/class/model fields, and calls hybrid retrieval for the top four hits. With no hits it returns the fixed Chinese message and empty citations before resolving or calling `ChatProvider`. With hits it builds numbered sources containing only title, chunk index, and text; a server-owned instruction requires answers to use only those sources and align `[n]` markers with the citation list.

An unavailable or invalid chat response returns 503 rather than an ungrounded fallback. The chat adapter has no database or vector-store access.

### 9. Extend the existing workspace progressively

The material page gains a retrieval panel with a mode selector, result cards, empty and dependency-error states; a question panel with answer/citation rendering; and teacher-only reindex controls whose fields change with the chosen strategy. All dynamic text is inserted with DOM text APIs rather than unsafe HTML. The shared authenticated fetch helper attaches the Bearer token, clears it and redirects on 401, and also handles JSON errors, request disabling, and stale-response replacement. Students retain retrieval/ask access but never receive reindex controls from the UI; the API still enforces role checks.

## Risks / Trade-offs

- **[MySQL ngram availability differs by deployment]** → Pin a compatible MySQL image, create and verify the index at startup, and keep dialect-specific integration coverage.
- **[Gateway responses or dimensions drift from the course contract]** → Validate status, JSON shape, ordering, and every 2048-dimensional embedding before Qdrant writes; map violations to a stable provider-unavailable error without exposing upstream data.
- **[Large gateway payloads cause resource pressure or rejection]** → Measure the serialized request before sending, reject requests above 20 MB, and keep chunk sizes/history bounds well below that ceiling.
- **[Synchronous embedding increases upload/reindex latency]** → Bound request timeouts and document the course-scale limitation; leave queueing outside this change.
- **[Qdrant deletion succeeds but relational replacement later fails]** → Treat relational text as source of truth, expose failed vector status, and make reindex idempotent so the teacher can retry.
- **[SQLite and MySQL full-text ranking differ]** → Assert filtering, ordering invariants, and provenance rather than identical numeric scores; run a Compose-backed smoke test for MySQL behavior.
- **[Existing unarchived retrieval change overlaps conceptually]** → Keep its endpoint for compatibility and introduce the chunk API separately; archive/sync of completed historical changes remains independent.
- **[Authentication change is applied out of order]** → Treat `replace-cookie-session-with-bearer-token-auth` as an implementation prerequisite and keep token-auth integration tests in this change.

## Migration Plan

1. Apply and verify `replace-cookie-session-with-bearer-token-auth`, then add configuration, dependencies, additive relational tables, provider/vector ports, and tests without changing the active browser path.
2. Add MySQL and Qdrant Compose services and verify health/dependency wiring.
3. Backfill each existing material by reading its stored UTF-8 file into `KnowledgeEntry` and applying `auto` chunking. Keyword data becomes ready even if embedding is not configured; vector status records the unavailable provider.
4. Enable the new retrieval/reindex/ask APIs and migrate the browser to them while retaining the old retrieval endpoint.
5. Configure the private course gateway credential plus `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL=course-embedding`, `EMBEDDING_DIM=2048`, and `CHAT_MODEL=course-chat`, then reindex materials to populate Qdrant and smoke-test grounded answers.

Rollback disables the new routes/UI, returns the browser to the old material retrieval endpoint, and leaves additive tables/Qdrant data unused. Existing material/authentication data and files remain intact.

## Open Questions

- None for the course gateway contract. Deployment-specific timeout values remain environment configurable with safe defaults.
