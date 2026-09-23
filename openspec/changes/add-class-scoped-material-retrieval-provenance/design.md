# Design

## Context

Materials are UTF-8 `.txt`/`.md` files with SQLite metadata and a server-derived class boundary. Existing `q` searches only `display_name`.

## Decisions

Use SQLite FTS5 in the existing SQLite database, with one index record per ready material containing its searchable content and owning `class_id`. This avoids a new service while supporting deterministic text retrieval. Upload creates/replaces its index entry only after stored content and Material persistence succeed; deletion removes it in the same managed workflow. Seeded content is indexed by the seed path.

Expose `GET /api/materials/retrieve?q=<query>` to authenticated users. Require a non-empty query, apply the session class filter in the database query, and return ordered results containing `material_id`, `display_name`, `class_id`, `class_name`, `uploader_id`, `excerpt`, and a stable source download URL. Excerpts are bounded and derived only from same-class indexed text; no storage path is returned. Empty results return 200 with an empty list. Cross-class existence remains undisclosed.

The material page adds a separate Chinese content-retrieval form and renders result excerpts with name, uploader, class, and download source. A 401 redirects to login. Retrieval does not generate answers or alter the existing name search.

## Risks

- FTS syntax errors or unavailable index: return a safe 400 for invalid query and test SQLite FTS availability.
- Index drift: cover upload, delete, and seed paths with integration tests.
- Future semantic retrieval: a vector index can be added in a later change behind the same class-filtered result contract.
