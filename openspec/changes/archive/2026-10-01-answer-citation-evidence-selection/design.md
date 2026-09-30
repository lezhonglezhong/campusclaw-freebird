# Design

## Context

See `proposal.md` for motivation. The ask endpoint currently requests four hybrid hits, sends all four to `course-chat`, validates only that at least one in-range marker exists, and returns every prompt hit as a citation. The independent retrieval endpoint already enforces database-derived class scope, a 0.35 vector cutoff, and RRF with `k = 60`; those behaviors are constraints, not tuning targets for this change.

## Goals / Non-Goals

**Goals:**

- Select a bounded answer-evidence subset before the chat call, retaining all retrieved alternatives needed by comparison questions.
- Treat the answer's valid markers as the source of truth for response citations and renumber the answer and source cards together.
- Reject answers whose reported Arabic numeric values are not present in the chunks cited for those claims, with exactly one retry.
- Keep the browser's independent retrieval results separate from answer citations.

**Non-Goals:**

- Changing keyword SQL, the vector similarity threshold, RRF scoring, class authorization, chunking, or provider models.
- Adding another model call for evidence selection or sending provider/vector metadata to `course-chat`.
- Proving non-numeric natural-language entailment beyond the existing source-only prompt contract.

## Decisions

### Select answer evidence locally from a wider bounded hybrid pool

The ask path will request a small bounded pool larger than four, de-duplicate it by chunk identity, and score meaningful normalized question terms against each chunk's title and body. When lexical matches exist, only related candidates are retained in retrieval order; comparison questions receive a larger bounded allowance so distinct value-bearing alternatives survive. When no lexical match can distinguish semantic candidates, the selector falls back to a small top-ranked set.

This is preferred over asking `course-chat` to select evidence because a selector model call would still disclose irrelevant candidates and add cost and failure modes. It is preferred over changing retrieval thresholds because those thresholds serve the independent retrieval contract and semantic relevance is not equivalent to literal overlap.

### Validate and project citations after generation

Validation will parse supplied `[n]` markers, reject missing or out-of-range markers, and examine punctuation-bounded numeric claims. Every Arabic number in a claim must occur in at least one source cited by that claim. For a detected comparison whose selected evidence is value-bearing, the marker set must also cover every selected value-bearing chunk, preventing a correct winner from hiding the alternatives needed to audit the comparison. Citation-marker digits themselves are excluded from numeric checking. A failed first answer is retried with the same selected sources and a stricter instruction; a failed second answer returns the stable 503 error.

After validation, distinct markers are collected in first-appearance order. The server maps them to their source hits, rewrites markers to a dense `1..N` sequence, and returns only those sources. This keeps the UI contract simple and prevents uncited prompt candidates from appearing as answer sources.

### Preserve retrieval behavior through characterization tests

Focused tests will cover weak vector omission, RRF ordering, and database class rechecks while answer-selection tests demonstrate that weak/background candidates are filtered only in the ask layer. No retrieval constants or authorization predicates will change.

## Risks / Trade-offs

- [Lexical selection can miss a semantically relevant paraphrase] → Use a bounded rank-ordered fallback when no candidate has meaningful lexical overlap and retain a comparison-sized set when comparison language is detected.
- [Numeric formatting may vary] → Normalize common thousands separators and decimal representations before exact value comparison; keep the check intentionally limited to explicit Arabic numbers.
- [Dense renumbering could corrupt overlapping markers such as `[1]` and `[10]`] → Rewrite markers with a single regular-expression substitution using the completed mapping.
- [A valid answer may cite evidence at sentence rather than phrase granularity] → Validate within punctuation-bounded claims and allow any citation in the same claim to support each number.

## Migration Plan

No data migration is required. Deploy the application code after automated regression and strict OpenSpec validation. Rollback is the prior application image/commit; stored materials, chunks, and vectors are unchanged.
