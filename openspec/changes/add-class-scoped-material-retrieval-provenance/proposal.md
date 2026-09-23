# Proposal

## Why

The current material search matches only material names. Class members need to retrieve relevant material body text while preserving the existing server-enforced class boundary and being able to identify the source material and matching excerpt.

## What Changes

- Add authenticated, class-scoped text retrieval over stored `.txt` and `.md` material content.
- Return material-level provenance and a bounded matching excerpt for every result.
- Add a Chinese browser retrieval form and source display to the existing material workspace.
- Keep SQLite as the initial retrieval store using SQLite FTS5; vector databases and embedding generation are explicitly deferred.

## Capabilities

### New Capabilities
- `class-scoped-material-retrieval`: Authenticated retrieval of content matching a query within the session class only.
- `material-content-provenance`: Result source identity and safe excerpts.

### Modified Capabilities
- `browser-material-interface`: Browser retrieval interaction using the authorized retrieval API.

## Non-Goals

- RAG answers, chat, embeddings, external vector databases, cross-class retrieval, PDF/Office ingestion, or user-managed indexing configuration.

## Impact

- Adds a local retrieval index, protected API, browser controls, and tests without changing upload, download, or class authorization contracts.
