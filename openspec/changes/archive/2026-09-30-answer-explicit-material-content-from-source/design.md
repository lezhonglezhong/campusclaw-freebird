# Design

## Context

See proposal.md. Hybrid retrieval already returns the correct same-class ready chunk for the user's exact title question. The provider receives the title and body but sometimes says the source is insufficient. Existing ask behavior maps that response to an empty citation list.

## Goals / Non-Goals

**Goals:**
- Answer explicit “what is the content of material X” questions from a complete short source when the model refuses, with one citation.
- Preserve the existing four-chunk bound, class authorization, provider-failure behavior, and no-evidence behavior.

**Non-Goals:**
- Guess a material's subject-matter definition from its title.
- Echo a partial long document as if it were the whole original.
- Replace model-assisted reasoning or make the old full-text material search a second source.

## Decisions

1. Keep the existing hybrid retrieval and provider call. On a provider insufficiency response only, inspect its already-selected same-class chunks and the current question. This preserves normal answers and existing provider-failure contracts; an unconditional shortcut would change provider behavior more broadly.
2. Require one unambiguous full-title mention of at least three normalized characters, an explicit source-content phrase, and a chunk exactly covering the retained original text of no more than 500 characters. Respond with the literal text and one provenance citation. If any condition fails, retain the provider's insufficiency result. A short complete source is distinguishable from one retrieved page of a large document.
3. Render no title-derived inference: a question such as “物理定理是什么” does not ask for source text and remains on the provider path. The response includes the material title as provenance, not as a claim that the title defines its subject.

## Risks / Trade-offs

- [A title may be part of a different phrase] → Require explicit content intent and a unique eligible material.
- [A source can contain markup or instruction-like text] → Return it as literal text; the browser already uses `textContent`.
- [The provider is unavailable] → Keep HTTP 503; the fallback applies only to an actual insufficiency answer.

## Migration Plan

No data migration or reindexing. Run focused and full tests, rebuild the application container, and read-only check the user's exact question against material 13. Roll back to the prior image if needed.
