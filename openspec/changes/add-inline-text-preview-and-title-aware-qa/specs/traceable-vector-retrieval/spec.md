# Spec Delta

## ADDED Requirements

### Requirement: Explicit material-title questions find bounded evidence

Keyword retrieval SHALL treat a nontrivial full material title explicitly present in the query as a same-class source-location signal, even when the query does not repeat the chunk body. It SHALL return only text-ready chunks of that material with the usual traceable provenance and bounded result limit; it MUST NOT call embedding or vector services. Hybrid retrieval and grounded asking SHALL be able to use these keyword hits without relaxing the vector mode's 0.35 similarity cutoff, bypassing class checks, or sending the whole knowledge base to the chat provider. Generic short titles and unrelated questions SHALL NOT fabricate evidence.

#### Scenario: A question naming a short-text material finds its chunk
- **WHEN** an authenticated class-A user asks what is in an own-class material whose full title appears in the question but whose short body does not share the question words
- **THEN** keyword and hybrid retrieval include a bounded source chunk for that material, allowing grounded asking to cite it

#### Scenario: Foreign title does not reveal another class
- **WHEN** a class-A user names a class-B-only material title
- **THEN** keyword and hybrid retrieval return no class-B chunk or title

#### Scenario: Vector-only cutoff remains unchanged
- **WHEN** a title-naming query has no vector candidate at or above 0.35 similarity and vector mode is selected
- **THEN** vector mode returns no hit rather than using title matching to bypass its cutoff
