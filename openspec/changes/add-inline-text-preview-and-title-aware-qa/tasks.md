# Tasks

## 1. Inline Source Preview

- [x] 1.1 Add a Bearer-authenticated, database-class-scoped source-text endpoint for typed and file-uploaded materials, with indistinguishable missing/foreign responses and no path leakage; verify with `python -m pytest -q tests/test_material_preview.py tests/test_material_access.py tests/test_material_download.py`.
- [x] 1.2 Render a plain-text preview in the detail panel, clear stale previews, keep authenticated downloads, and open a newly uploaded material automatically; verify with `python -m pytest -q tests/test_browser_preview.py tests/test_browser_flow.py tests/test_browser_token_auth.py`.

## 2. Title-Directed Evidence

- [x] 2.1 Add bounded same-class full-title matching to keyword and hybrid chunk retrieval without changing vector-only cutoff or calling providers from keyword mode; verify with `python -m pytest -q tests/test_title_retrieval.py tests/test_keyword_retrieval.py tests/test_hybrid_retrieval.py tests/test_retrieval_security.py`.
- [x] 2.2 Verify that grounded asking cites the short source when its title appears in a natural-language question, and still refuses foreign or unrelated evidence; verify with `python -m pytest -q tests/test_title_ask.py tests/test_ask_api.py`.

## 3. Acceptance and Deployment

- [ ] 3.1 Update README for preview and title-aware questions, run the full suite, strict OpenSpec validation, and Compose configuration check; verify with `python -m pytest -q && openspec validate add-inline-text-preview-and-title-aware-qa --strict && docker compose config --quiet`.
- [ ] 3.2 Rebuild the GPU3 service and read-only check the existing short material's protected preview, title-directed retrieval, and cited answer; verify with `docker compose up -d --build --wait campusclaw && docker compose ps` plus HTTP 200 checks for preview, retrieval, and ask.
