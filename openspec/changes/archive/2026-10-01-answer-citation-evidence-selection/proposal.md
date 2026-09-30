# Proposal

## Why

The ask endpoint currently sends its four highest-ranked retrieval candidates to
`course-chat` and presents all four as answer sources, even when the answer
uses only one. This makes comparative numerical answers hard to audit and can
make irrelevant background material look like supporting evidence.

## What Changes

- Require generated-answer citations to drive the ordered source list returned
  by `POST /api/ask`, rather than returning every prompt candidate.
- Preserve the complete selected numerical evidence needed for comparison
  questions while excluding clearly irrelevant candidates from the chat prompt.
- Validate that numerical answer claims are supported by cited chunk text;
  retry once for unsupported or malformed citations, then reject the answer.
- Keep the independent retrieval endpoint's broader result list, hybrid RRF,
  0.35 vector cutoff, and class isolation unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `grounded-knowledge-answering`: select relevant answer evidence, return only
  actually cited sources, and enforce cited numerical-answer consistency.

## Impact

Updates the ask workflow in `campusclaw/knowledge_api.py`, its API/browser
tests, and the knowledge-base documentation. The retrieval API and provider
configuration remain compatible.
