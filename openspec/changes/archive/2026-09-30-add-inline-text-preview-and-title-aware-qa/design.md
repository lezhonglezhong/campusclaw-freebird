# Design

## Context

See proposal.md. All accepted material bodies are UTF-8 text, and `KnowledgeEntry.body_text` retains the original even after chunking. Material details currently return metadata only. The newest short material has one ready chunk and vector, but a question naming its title returns no hit because the body does not contain the title and its embedding is below the vector cutoff.

## Goals / Non-Goals

**Goals:**
- Preview both typed and file-uploaded text, including existing materials, with current Bearer and class authorization.
- Retrieve at most the existing bounded number of same-class chunks for title-directed questions.
- Keep downloads, vector cutoff, and the four-source grounded-answer limit intact.

**Non-Goals:**
- Add binary document formats, image preview, or whole-corpus prompting.
- Change the database schema or infer historical upload origin.

## Decisions

1. Add a separate `GET /api/materials/<id>/content` response using the persisted original text, falling back to an available UTF-8 source file for older records without an entry. This avoids expanding every material-detail response with potentially long content and needs no schema migration. Its material lookup uses the token-resolved database class.
2. Render source text in a scrollable `<pre>` using `textContent`, never `innerHTML`. Fetch after metadata selection with the shared Bearer helper and invalidate older requests on a new selection, deletion, or logout. Keep the authenticated download button for both upload methods.
3. After HTTP 201, refresh the list and select the returned material ID. Do not trust a client-supplied title or class to choose a different record.
4. Add a full-title matching score only to the relational keyword path for titles of at least three normalized characters. Rank ready same-class chunks deterministically, cap the returned list, and leave vector-only retrieval unchanged. Hybrid can fuse title-backed keyword ranks with vector ranks; asking still sends at most four selected chunks.

## Risks / Trade-offs

- [A title may name a large document with many chunks] → Keep existing retrieval and answer limits, favor chunks with body matches, and never send every chunk.
- [An authorized source may contain markup or long lines] → Display as literal text in a bounded-height scrollable region.
- [The user selects another material before the preview returns] → Use a request generation counter and clear old content before each fetch.

## Migration Plan

No data migration. Deploy the API and browser together, run tests and a read-only live check against the latest short material, then rebuild the app. Rollback is the prior application image; stored source bodies and vectors remain unchanged.
