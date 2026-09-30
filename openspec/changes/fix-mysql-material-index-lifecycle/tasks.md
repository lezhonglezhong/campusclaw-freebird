# Tasks

## 1. Dialect-Aware Lifecycle

- [x] 1.1 Guard legacy material FTS writes for SQLite only, preserve SQLite behavior, and add MySQL-path regression tests for upload/delete/seed helpers; verify with `python -m pytest -q tests/test_mysql_material_lifecycle.py tests/test_material_retrieval_index.py tests/test_upload.py tests/test_material_delete.py tests/test_seed.py`.
- [ ] 1.2 Audit all SQLite-specific SQL call sites and verify JSON/multipart upload, delete, seed, reindex, legacy retrieval, and new retrieval test coverage; verify with `python -m pytest -q tests/test_file_upload.py tests/test_material_reindex.py tests/test_material_retrieval.py tests/test_retrieval_api.py tests/test_keyword_retrieval.py tests/test_vector_indexing.py`.

## 2. Deployment and Recovery

- [ ] 2.1 Rebuild the GPU3 app, run a uniquely named MySQL canary through authenticated upload, legacy/new retrieval and deletion, and verify the canary has no remaining record, file, chunks, or vector points; verify with `docker compose up -d --build --wait campusclaw && docker compose ps` plus recorded canary HTTP 201/200/204 results.
- [ ] 2.2 Compare ready relational chunk IDs for failed-deletion materials 3 and 5 with Qdrant points, reindex only affected materials using their saved strategies/options, and verify no missing ready points and preserved source files; verify with a read-only ID comparison after repair.

## 3. Final Acceptance

- [ ] 3.1 Run the full suite, validate the change strictly, and check Compose and service health; verify with `python -m pytest -q && openspec validate fix-mysql-material-index-lifecycle --strict && docker compose config --quiet`.
