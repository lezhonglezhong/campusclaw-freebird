# knowledge-chunk-indexing Specification

## Purpose

Defines how uploaded knowledge material becomes durable, traceable chunks whose text remains in relational storage and whose vectors can be rebuilt safely.

## Requirements

### Requirement: Original body and traceable chunks are persisted separately

The system SHALL retain each uploaded material's original UTF-8 body unchanged and SHALL persist every generated chunk with its material, knowledge-entry, class, zero-based chunk index, character start and end offsets, chunk text, text-index status, and vector-index status. Preprocessing for chunking or embedding MUST NOT rewrite the retained original body. If preprocessing changes text length or whitespace, the stored offsets SHALL be defined relative to the preprocessed chunking input.

#### Scenario: Upload preserves original text and chunk provenance
- **WHEN** a teacher uploads a valid text or Markdown material
- **THEN** the original body remains available unchanged and each generated chunk identifies its source material, sequence, character range, and class

#### Scenario: Preprocessing does not mutate the source body
- **WHEN** custom chunking removes URLs or email addresses or collapses whitespace
- **THEN** only the chunking input is transformed and the retained original body remains byte-for-byte equivalent to the decoded upload text

### Requirement: Supported chunking strategies are deterministic and validated

The system SHALL support `auto`, `custom`, and `hierarchy` chunking strategies. Omitting the strategy SHALL select `auto`. `auto` SHALL target at most 800 characters with 80 characters of overlap and prefer boundaries at blank lines, line breaks, or Chinese/English sentence punctuation. `custom` SHALL accept a maximum length from 100 through 2000 characters, an overlap from 0% through 50%, a separator of newline, blank line, or sentence punctuation, and optional URL/email removal and whitespace collapsing. `hierarchy` SHALL split at Markdown `#`, `##`, or `###` headings, retain each heading in its section, and apply the automatic window rule to an oversized section. Invalid strategy parameters SHALL return HTTP 400 without replacing an existing index.

#### Scenario: Omitted strategy uses the automatic window
- **WHEN** a material is uploaded or seeded without chunking options
- **THEN** it is chunked using the automatic 800-character window and 80-character overlap rules

#### Scenario: Custom strategy applies accepted controls
- **WHEN** a teacher requests custom chunking with valid length, overlap, separator, and preprocessing controls
- **THEN** the resulting chunks reflect those controls and preserve forced maximum-length splits where no separator exists

#### Scenario: Markdown hierarchy retains headings
- **WHEN** a teacher indexes Markdown containing supported heading levels with the hierarchy strategy
- **THEN** each section chunk contains its heading and oversized sections are further divided by the automatic window rule

#### Scenario: Invalid custom strategy is rejected safely
- **WHEN** a teacher supplies a maximum length or overlap outside the accepted range
- **THEN** the server returns HTTP 400 and leaves the material's existing chunks and vectors unchanged

### Requirement: Chunk vectors have stable relational identifiers

For each successfully embedded chunk, the system SHALL call the configured `/v1/embeddings` gateway path with only the `course-embedding` model and chunk input, and SHALL validate that each returned embedding contains exactly 2048 numeric dimensions before persistence. `EMBEDDING_DIM=2048` SHALL configure and validate the vector collection but MUST NOT be included in the gateway request. The system SHALL store one accepted vector whose point identifier equals the relational chunk identifier. Vector metadata SHALL contain only `class_id`, `material_id`, `knowledge_entry_id`, `chunk_id`, and `chunk_index`; it MUST NOT contain the chunk text, original body, secrets, or user credentials. Cosine similarity SHALL be used.

#### Scenario: Embedded chunk can be traced back by identifier
- **WHEN** embedding and vector persistence succeed for a chunk
- **THEN** its vector point identifier and metadata `chunk_id` equal the relational chunk identifier and the point contains no source text

#### Scenario: Embedding request and dimension follow the course gateway contract
- **WHEN** the system requests an embedding for one or more chunks
- **THEN** it appends `/embeddings` to the configured `/v1` base URL, sends only `model` and `input`, and accepts the response only when every embedding has exactly 2048 numeric elements

#### Scenario: Embedding failure does not invent a vector
- **WHEN** the embedding provider fails for a chunk
- **THEN** the material and relational source data remain stored, the affected chunk's vector-index status is marked failed while its text remains available to keyword indexing, and no partial vector point is written for that chunk

### Requirement: Teachers can rebuild an own-class material index atomically

The system SHALL expose `POST /api/materials/<material_id>/reindex` to teachers authenticated by a valid Bearer access token. The request SHALL accept one supported chunking strategy and its applicable options. It SHALL resolve role and class ownership exclusively from the current database user identified by the validated token, return HTTP 403 for students, and return the same HTTP 404 response for a missing or other-class material. A successful rebuild SHALL replace all old chunks and vector points for that material with data created from the retained original body. A failed validation SHALL preserve the old index; a processing failure SHALL leave the original material available and report a non-ready indexing status without exposing provider secrets.

#### Scenario: Teacher rebuilds an own-class material
- **WHEN** a teacher presents a valid Bearer token and requests a valid new strategy for a material owned by the teacher's current database class
- **THEN** the old chunks and vectors are removed and replaced by a complete new index derived from the retained original body

#### Scenario: Student cannot rebuild an index
- **WHEN** an authenticated student posts a reindex request
- **THEN** the server returns HTTP 403 and changes no chunks or vector points

#### Scenario: Cross-class material is indistinguishable from missing
- **WHEN** a class-A teacher requests reindexing of a class-B material identifier
- **THEN** the server returns HTTP 404 without revealing class-B material information

### Requirement: Index lifecycle follows material lifecycle

Seeded materials SHALL receive an automatic-strategy index when missing. Deleting a material SHALL delete its relational knowledge entry and chunks and SHALL remove the corresponding vector points. Repeating seed or rebuild operations SHALL not create duplicate chunks or orphaned vector points.

#### Scenario: Seed fills a missing index idempotently
- **WHEN** development seed data is applied more than once
- **THEN** each seeded material has one current automatic-strategy chunk set without duplicates

#### Scenario: Material deletion removes both index representations
- **WHEN** an authorized teacher deletes an own-class material
- **THEN** its source file, relational knowledge entry and chunks, and vector points are no longer retrievable

