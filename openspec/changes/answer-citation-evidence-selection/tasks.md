# Tasks

## 1. Answer Evidence and Citation Integrity

- [x] 1.1 Add bounded, duplicate-free answer-evidence selection that excludes clearly unrelated candidates while retaining all retrieved value-bearing alternatives for comparison questions; verify with `python -m pytest -q tests/test_ask_evidence_selection.py tests/test_ask_api.py -k "selection or comparison or latest_question or no_evidence"`.
- [ ] 1.2 Return only distinct sources actually cited by the answer in first-appearance order, densely renumber markers and cards, and retry/reject missing, malformed, or numerically unsupported citations; verify with `python -m pytest -q tests/test_ask_citation_validation.py tests/test_ask_api.py tests/test_explicit_material_content_ask.py`.

## 2. Retrieval and Browser Boundaries

- [ ] 2.1 Confirm the browser renders answer citations only from the ask response while keeping the independent retrieval list separate; verify with `python -m pytest -q tests/test_browser_ask.py tests/test_browser_retrieval.py tests/test_browser_knowledge_ui.py`.
- [ ] 2.2 Add or retain characterization coverage showing weak vector candidates are omitted, hybrid RRF ordering is unchanged, and class isolation is preserved without changing the 0.35 cutoff or RRF formula; verify with `python -m pytest -q tests/test_vector_retrieval.py tests/test_hybrid_retrieval.py tests/test_retrieval_security.py tests/test_material_retrieval_security.py`.

## 3. Documentation and Full Acceptance

- [ ] 3.1 Update README with answer-evidence selection, cited-source projection, and numeric citation rejection behavior, then run the complete regression and project validation; verify with `python -m pytest -q && openspec validate answer-citation-evidence-selection --strict && openspec validate --specs && docker compose config --quiet`.
