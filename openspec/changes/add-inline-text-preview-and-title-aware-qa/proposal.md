# Proposal

## Why

Material details currently offer only a download action even though all accepted sources are readable text. A newly uploaded short material can also be indexed correctly yet remain invisible to a natural-language question naming its title, because retrieval ranks only body text and applies a semantic cutoff.

## What Changes

- Add a Bearer-protected, class-scoped source-text endpoint and render the returned content inline for both typed text and uploaded `.txt`/`.md` files while retaining download actions.
- Open the newly uploaded material in the detail panel after a successful upload, so the content appears without a second search or download.
- Let keyword and hybrid retrieval use an exact full-title mention in the question as a bounded route to the material's ready chunks; preserve existing vector-mode similarity cutoff and class isolation.
- Verify short numeric material content, title-directed questions, cross-class and unauthenticated denial, browser preview safety, and live GPU3 behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `class-scoped-material-access`: add authorized inline source-content access without exposing filesystem paths.
- `browser-material-interface`: show source text in the detail panel for both input methods and retain downloads.
- `traceable-vector-retrieval`: use an explicit own-class material-title mention to find bounded chunks for keyword/hybrid and grounded asking.

## Impact

`campusclaw/materials.py`, `campusclaw/knowledge_retrieval.py`, the browser template/script/styles, API and browser tests, README, and the running GPU3 service. No database migration, token change, or raw-vector disclosure.
