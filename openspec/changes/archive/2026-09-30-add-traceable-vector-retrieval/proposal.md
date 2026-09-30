# Proposal

## Why

CampusClaw currently retrieves whole materials by literal text only, so semantically equivalent questions can miss useful content and results cannot be traced to a precise source chunk. The fourth course assignment requires class-isolated, traceable keyword/vector/hybrid retrieval and grounded answers that never invent evidence.

## What Changes

- Split each material body into persisted knowledge chunks with stable sequence numbers, character ranges, indexing status, and configurable `auto`, `custom`, or `hierarchy` strategies.
- Add server-side embedding and vector-store interfaces, store chunk text and provenance in the relational database, and store only vectors plus identifiers in Qdrant.
- Integrate the course OpenAI-compatible gateway: append `/embeddings` to the configured `/v1` embedding base URL for `course-embedding`, validate every returned vector at 2048 dimensions, and send grounded generation to `/chat/completions` with `course-chat`.
- Extend authenticated retrieval with `keyword`, `vector`, and default `hybrid` modes, absolute-score filtering, reciprocal-rank fusion, and class filtering derived only from the database user resolved from a validated Bearer access token.
- Return chunk-level provenance for every hit, including the material title, chunk index, character range, excerpt, ranks/scores, and an authorized material URL.
- Add `POST /api/ask`, which retrieves the current question against the user's class, calls a replaceable chat-provider interface only when evidence exists, and returns citations aligned with `[1]`, `[2]`, and later markers.
- Upgrade the browser workspace with retrieval-mode controls, traceable result cards, a grounded question form, citation display, clear empty/error states, and teacher-only reindex controls.
- Add MySQL and Qdrant services to the reproducible Compose environment while retaining injectable test doubles and SQLite-compatible test execution.

## Capabilities

### New Capabilities

- `knowledge-chunk-indexing`: Material-body persistence, configurable chunking, embedding status, Qdrant identifier linkage, and explicit reindex lifecycle.
- `traceable-vector-retrieval`: Bearer-token-authenticated keyword, vector, and hybrid retrieval with score filtering, RRF ordering, graceful dependency errors, and chunk provenance.
- `grounded-knowledge-answering`: Evidence-gated answer generation through a replaceable server-side provider interface with ordered citations and prompt-injection boundaries.

### Modified Capabilities

- `browser-material-interface`: Extend the protected material workspace with retrieval modes, traceable hits, grounded questions, citations, and teacher-only reindex controls.

## Non-Goals

- Streaming responses, unrestricted general-purpose chat, cross-class search, PDF/Office OCR, reranking models, client access to Qdrant or model gateways, and production high-availability deployment.
- Image upload, image-grounded retrieval, OCR, or other multimodal browser features. The gateway transport may serialize a future `image_url` message part, but this text-material assignment does not expose or invoke that path.

## Impact

- Affects persistence models and migrations, material upload/delete/seed flows, retrieval and answer services, authenticated APIs, the material workspace, tests, environment configuration, dependencies, and Docker Compose.
- Adds MySQL and Qdrant runtime dependencies plus server-only embedding/chat provider configuration. Gateway requests use Bearer authentication, remain below 20 MB, and never expose provider secrets or raw vectors to the browser or repository.
- Depends on the separate `replace-cookie-session-with-bearer-token-auth` change. Every protected browser/API request carries `Authorization: Bearer <access-token>`; the backend validates the token and reloads the user, role, and class from the database. Request-supplied or token-embedded `class_id` values never become authorization inputs.
