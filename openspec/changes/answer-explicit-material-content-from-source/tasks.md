# Tasks

## 1. Grounded Source-Content Answer

- [x] 1.1 Add a narrow literal-source fallback after provider insufficiency for an explicit full-title content question with one complete short own-class source, preserving normal and error paths; verify with `python -m pytest -q tests/test_explicit_material_content_ask.py tests/test_ask_api.py tests/test_title_ask.py`.

## 2. Acceptance and Delivery

- [ ] 2.1 Document the distinction between asking for a material's own text and asking for a concept explanation; verify with `python -m pytest -q && openspec validate answer-explicit-material-content-from-source --strict && docker compose config --quiet`.
- [ ] 2.2 Rebuild GPU3 and read-only verify material 13 answers the user's exact question with its original text and citation while concept inference remains unsupported; verify with `docker compose up -d --build --wait campusclaw && docker compose ps` plus HTTP checks.
