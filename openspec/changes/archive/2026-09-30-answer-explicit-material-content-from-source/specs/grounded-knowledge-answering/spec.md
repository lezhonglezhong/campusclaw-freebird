# Spec Delta

## MODIFIED Requirements

### Requirement: Generated answers are grounded and citation ordered

When evidence exists, the server SHALL call the configured chat-provider interface with a server-authored instruction, the current question, bounded prior history, and for each selected hit only its citation number, material title, chunk index, and chunk text. It MUST NOT send raw vectors, vector-store point payloads, provider secrets, other-class chunks, or client-authored system instructions. The returned answer SHALL be short and use `[1]`, `[2]`, and later markers only for supplied evidence. The response `citations` list SHALL preserve the exact numbering and order used in the prompt and SHALL expose the same traceable fields as retrieval hits. If the provider declares evidence insufficient for a question explicitly asking for a named material's own content, but an authorized selected chunk contains that material's complete short original text, the system SHALL answer with that literal text and a traceable citation instead of an empty no-evidence response. It SHALL NOT use this exception to explain a concept from the title alone or to present a partial long source as complete.

#### Scenario: Answer markers align with citation order
- **WHEN** the top same-class evidence chunks are numbered 1 through N for the provider
- **THEN** the response citations use that same order and every answer marker refers to the citation at that position

#### Scenario: Provider receives no foreign or vector data
- **WHEN** the server assembles an answer-provider request
- **THEN** it contains only authorized source titles, chunk indices, chunk text, bounded history, and the current question, with no raw vectors or other-class data

#### Scenario: Provider finds supplied evidence insufficient
- **WHEN** the chat provider explicitly states that the supplied sources cannot support an answer other than an eligible direct request for a named material's complete short content
- **THEN** the server returns the fixed no-evidence message with empty citations instead of an ungrounded answer or an error

#### Scenario: Provider omits or misnumbers a citation
- **WHEN** the first generated answer does not cite one of the supplied source numbers correctly
- **THEN** the server retries once with the same bounded sources and rejects a second invalid answer with HTTP 503

#### Scenario: Literal source-content question survives model refusal
- **WHEN** a user asks what the complete short content of an explicitly named own-class material is and the provider incorrectly reports insufficient evidence
- **THEN** the answer quotes only that retained original text and cites the matching material

#### Scenario: Title alone cannot prove a subject-matter answer
- **WHEN** a user asks what a concept named by the material title means but the source body does not explain it
- **THEN** the server does not treat the title as a definition or fabricate a cited explanation
