# Tasks

## 1. Application catalog and templates
- [x] 1.1 Add distinct application catalog, class-scoped prompt persistence and teacher CRUD, variable rendering and authorization tests. Verify: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_platform_catalog.py`

## 2. Declarative skills
- [ ] 2.1 Add two built-in skills, strict JSON upload/inspection/deletion, class authorization and sequential callback executor with complete manifest context. Verify: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_platform_skills.py`

## 3. External connectors
- [ ] 3.1 Add configured HTTP/MCP clients, class enablement/discovery, schema validation, JSON/SSE/session handling and model exchange/tool loop with bounded calls. Verify: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_platform_connectors.py`

## 4. Application execution
- [ ] 4.1 Connect selected application/template/skill/knowledge/tools to execution and owner-scoped exact traces, citations, errors and integration coverage. Verify: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_platform_runs.py`

## 5. Usable browser and deployable tools
- [ ] 5.1 Add Chinese workspace, template editor, skill upload/inspection, connector controls, output/trace viewer, navigation and separate demonstration HTTP/MCP service with deployment docs. Verify actual browser interactions and protocol service: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_platform_browser.py tests/test_platform_demo.py`

## 6. Acceptance and report
- [ ] 6.1 Run full regression, capture controlled and real model/tool evidence, build updated PDF in docs and verify report integrity; deploy additive application/demo update without replacing private configuration or volumes. Verify: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider && PYTHONDONTWRITEBYTECODE=1 python docs/verification/verify_platform_report.py`

After all tasks pass, sync all deltas to main specs, run `openspec validate --specs`, and archive the change. Keep unrelated files and secrets out of all task commits. Each checkbox uses the repository's verify/mark/review/reverify/commit/report procedure.
