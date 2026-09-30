# traceable-vector-retrieval Specification

## Purpose

Provides authenticated keyword, semantic, and hybrid retrieval over the current class while making every result traceable to an exact source chunk.

## Requirements

### Requirement: Authenticated retrieval exposes three explicit modes

The system SHALL expose `GET /api/retrieval?q=<query>&mode=<mode>` to authenticated teachers and students. `mode` SHALL accept `keyword`, `vector`, or `hybrid` and SHALL default to `hybrid`. A missing or whitespace-only query or an unknown mode SHALL return HTTP 400 with an error field and no hits. An unauthenticated request SHALL return HTTP 401. A successful request SHALL return HTTP 200 with at least `{ "mode", "hits": [ ... ] }`.

#### Scenario: Omitted mode selects hybrid retrieval
- **WHEN** an authenticated user submits a non-empty query without a mode
- **THEN** the server executes hybrid retrieval and identifies `hybrid` in the response

#### Scenario: Empty query is rejected
- **WHEN** an authenticated user submits an empty or whitespace-only query
- **THEN** the server returns HTTP 400 without searching or returning material data

#### Scenario: Unauthenticated retrieval is rejected
- **WHEN** a client without a valid `Authorization: Bearer <access-token>` header requests any retrieval mode
- **THEN** the server returns HTTP 401 without hits

### Requirement: Keyword retrieval uses only relational full-text data

Keyword mode SHALL query chunks whose text-index status is ready in the relational database, apply the current database class of the Bearer-token-resolved user as a predicate, and rank matches by full-text relevance. It MUST NOT call the embedding provider or vector store. Chinese keyword matching SHALL be supported by the deployed relational index configuration.

#### Scenario: Literal phrase is found without model dependencies
- **WHEN** a same-class ready chunk contains the query terms and keyword mode is selected
- **THEN** the matching chunk is returned in full-text relevance order without an embedding or vector-store call

#### Scenario: Keyword mode remains available during vector outage
- **WHEN** the vector store or embedding provider is unavailable and a valid keyword request is made
- **THEN** the server still returns relational keyword results normally

### Requirement: Vector retrieval filters weak and cross-class candidates

Vector mode SHALL embed the query on the server, search vector-ready chunks using cosine similarity with a `class_id` filter derived from the current database class of the Bearer-token-resolved user, discard candidates below 0.35 similarity, and fetch source text by chunk identifier from the relational database with the same class predicate applied again. The browser SHALL NOT receive raw vector components or provider credentials.

#### Scenario: Semantic paraphrase retrieves a same-class chunk
- **WHEN** a query is semantically similar to a ready same-class chunk, despite not sharing its literal terms, and its cosine similarity is at least 0.35
- **THEN** vector mode returns that chunk ordered by descending cosine similarity

#### Scenario: Weak vector candidate is omitted
- **WHEN** every candidate has cosine similarity below 0.35
- **THEN** vector mode returns HTTP 200 with an empty hit list

#### Scenario: Relational recheck blocks an incorrectly returned foreign point
- **WHEN** the vector store returns a chunk identifier outside the Bearer-token-resolved user's current database class
- **THEN** the relational class predicate removes it and no foreign text or metadata appears in the response

### Requirement: Hybrid retrieval fuses filtered ranks with RRF

Hybrid mode SHALL execute the keyword and vector paths, apply each path's absolute filtering before fusion, and combine the remaining ranks using reciprocal rank fusion with `k = 60`. A hit absent from one path SHALL receive no contribution from that path. Results SHALL be ordered by descending RRF score, with deterministic tie-breaking.

#### Scenario: Dual-path hit ranks ahead of a one-path peer
- **WHEN** comparable candidates include a chunk ranked by both paths and another ranked by only one path
- **THEN** RRF gives the dual-path chunk contributions from both ranks and orders the final hits by the fused score

#### Scenario: Incomparable absolute scores are not added
- **WHEN** keyword and vector candidates have different score scales
- **THEN** hybrid ordering uses their filtered ranks rather than directly adding their absolute scores

### Requirement: Every hit carries bounded source provenance

Each hit SHALL include `chunk_id`, `material_id`, material title, chunk index, character start and end offsets, a bounded excerpt taken from relational chunk text, an authorized material URL, and the applicable keyword/vector/RRF scores and ranks. It MUST NOT include a filesystem path, source text from another class, or a raw vector. If no candidate survives filtering, the response SHALL contain an empty `hits` list and SHALL NOT pad the result with weak matches.

#### Scenario: User can trace a hit to the material and chunk
- **WHEN** retrieval returns a hit
- **THEN** the response identifies the source material, exact chunk sequence and character range, includes a bounded relational excerpt, and provides an authorized URL for that material

#### Scenario: Unrelated question returns no fabricated hit
- **WHEN** no same-class candidate survives the selected mode's filters
- **THEN** the server returns HTTP 200 with `hits` empty

### Requirement: Class scope comes only from the database user resolved by the Bearer token

All retrieval modes SHALL require `Authorization: Bearer <access-token>`, validate the token, load the identified user from the database, and derive `class_id` from that current database record. Any `class_id` in token claims, query parameters, JSON, or request headers SHALL be ignored for authorization. Keyword SQL, vector filtering, and relational hydration SHALL all use the database value. Searching for text that exists only in another class SHALL look identical to no match and SHALL NOT reveal that the other material exists.

#### Scenario: Request-supplied class identifier cannot expand scope
- **WHEN** a class-A user submits a class-B `class_id` with a retrieval request
- **THEN** all retrieval paths still use class A and return no class-B hit

#### Scenario: Cross-class-only term appears as no match
- **WHEN** a class-A user searches for a term found only in class-B chunks
- **THEN** the server returns HTTP 200 with `hits` empty rather than HTTP 403 or 404

### Requirement: Vector-dependent failures are explicit

If query embedding or Qdrant is unavailable, vector and hybrid modes SHALL return HTTP 503 with a stable error code and no invented score or hit. Provider error bodies, credentials, and stack traces MUST NOT be returned to the client.

#### Scenario: Vector store outage does not fabricate semantic results
- **WHEN** Qdrant is unavailable during vector or hybrid retrieval
- **THEN** the server returns HTTP 503 with a stable error and no hits, raw exception, or fabricated similarity

