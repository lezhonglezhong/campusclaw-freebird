# grounded-knowledge-answering Specification

## Purpose

Defines short, evidence-grounded answers whose numbered citations map to authorized chunks and whose generation is skipped completely when evidence is absent.

## Requirements

### Requirement: Ask requests are authenticated and validated

The system SHALL expose `POST /api/ask` to authenticated teachers and students. It SHALL accept a non-empty latest `question` and MAY accept a bounded list of prior user/assistant messages for continuity. It SHALL ignore any client-supplied `class_id`, system message, prompt, role override, or model setting. An unauthenticated request SHALL return HTTP 401, and malformed or empty input SHALL return HTTP 400 without calling retrieval or the chat provider.

#### Scenario: Valid latest question enters the answer workflow
- **WHEN** an authenticated user submits a non-empty question and valid bounded history
- **THEN** the server begins retrieval using the question and the current database class of the user resolved from the Bearer token

#### Scenario: Client system message is discarded
- **WHEN** a request includes a client-authored system message or class override
- **THEN** the server ignores those fields and retains its own system policy and the current database class of the Bearer-token-resolved user

### Requirement: Evidence is retrieved before generation

The ask workflow SHALL run class-scoped hybrid retrieval using only the latest question and SHALL retrieve a bounded candidate pool before selecting answer evidence. It SHALL remove duplicate chunks and exclude candidates with no meaningful lexical relationship to the current question when stronger related candidates exist. For comparison questions, selection SHALL retain the distinct related chunks needed to compare all retrieved alternatives, rather than truncating the prompt to the first four candidates. When lexical selection cannot distinguish semantically retrieved candidates, the workflow MAY retain a bounded rank-ordered fallback set. If there are no surviving candidates, the server SHALL return HTTP 200 with `answer` equal to `资料中未找到相关内容` and `citations` equal to an empty list. It MUST NOT call the chat provider on that path. This answer-specific selection MUST NOT change the independent retrieval endpoint's 0.35 vector cutoff, RRF fusion, or class-scoping rules.

#### Scenario: Irrelevant background is omitted from a comparison prompt
- **WHEN** the bounded candidates contain separate chunks for building decreases of 150, 300, and 40 units plus an unrelated experiment-background chunk
- **THEN** the provider receives all three value-bearing chunks and does not receive the unrelated background chunk

#### Scenario: Semantic fallback remains bounded
- **WHEN** hybrid retrieval returns candidates that have no meaningful literal overlap with the question
- **THEN** the provider receives only a bounded rank-ordered fallback set rather than the whole knowledge base

#### Scenario: Independent retrieval behavior is unchanged
- **WHEN** a client uses keyword, vector, or hybrid retrieval independently of asking
- **THEN** the existing class isolation, 0.35 vector cutoff, and RRF fusion behavior remain in force

#### Scenario: Unrelated question bypasses the chat provider
- **WHEN** hybrid retrieval finds no same-class evidence for the latest question
- **THEN** the fixed no-evidence answer and empty citations are returned and the chat provider receives zero calls

#### Scenario: Only the latest turn drives retrieval
- **WHEN** a valid request contains previous conversation history and a new question
- **THEN** hybrid retrieval uses the new question while the bounded history is reserved for later answer context

### Requirement: Generated answers are grounded and citation ordered

When evidence exists, the server SHALL select a bounded subset of the class-scoped hybrid retrieval candidates that is relevant to the question before calling the configured chat-provider interface. For a comparison question, the subset SHALL retain the distinct chunks containing the values needed to compare the alternatives, while excluding candidates that do not support the answer; a valid comparison answer SHALL cite every selected value-bearing alternative so the returned sources expose the complete comparison evidence. The server SHALL call the provider with a server-authored instruction, the current question, bounded prior history, and for each selected hit only its citation number, material title, chunk index, and chunk text. It MUST NOT send raw vectors, vector-store point payloads, provider secrets, other-class chunks, or client-authored system instructions. The returned answer SHALL be short and use `[1]`, `[2]`, and later markers only for supplied evidence. The response `citations` list SHALL contain only the distinct, valid markers used in the answer, in their first-appearance order, and SHALL renumber both the returned markers and citations consistently. A numerical answer SHALL cite chunk text that contains each reported numeric value; the server SHALL retry once when citations are missing, malformed, unsupported, numerically inconsistent, or omit a selected comparison alternative, and SHALL return HTTP 503 rather than display a second unsupported answer. If the provider declares evidence insufficient for a question explicitly asking for a named material's own content, but an authorized selected chunk contains that material's complete short original text, the system SHALL answer with that literal text and a traceable citation instead of an empty no-evidence response. It SHALL NOT use this exception to explain a concept from the title alone or to present a partial long source as complete.

#### Scenario: Answer returns only sources it cites
- **WHEN** the selected prompt evidence contains four chunks but the generated answer cites only chunks 2 and 4
- **THEN** the response contains only two source cards, renumbered to match the answer markers in their first-appearance order

#### Scenario: Answer markers align with citation order
- **WHEN** valid answer markers refer to selected same-class evidence chunks
- **THEN** the response citations follow first marker appearance and both markers and cards use the same dense numbering

#### Scenario: Comparison retains all cited numeric evidence
- **WHEN** a question asks which building's electricity use decreased the most and separate relevant chunks contain the compared building values
- **THEN** the provider receives those value-bearing chunks and a valid response cites every compared value chunk rather than only the winning value or unrelated experiment background

#### Scenario: Incomplete comparison citations are rejected
- **WHEN** the selected evidence contains building decreases of 150, 300, and 40 units but a generated comparison answer cites only the 300-unit winner
- **THEN** the server retries once and rejects a second answer that still omits the 150-unit or 40-unit evidence

#### Scenario: Unsupported numerical answer is rejected
- **WHEN** a generated answer reports a numeric value absent from its cited chunk text on both attempts
- **THEN** the endpoint returns HTTP 503 with its stable chat error and no answer or citations

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

### Requirement: Provider availability failures are safe and replaceable

Embedding and chat generation SHALL be accessed through separate server-side provider contracts. The chat adapter SHALL append `/chat/completions` to the configured `/v1` base URL, send model `course-chat` with server-assembled `messages`, and authenticate server-side with the configured Bearer credential. Any serialized gateway request exceeding 20 MB SHALL be rejected before network I/O. The message serializer MAY represent a future visual input as an OpenAI-compatible `image_url` content part, but this change SHALL submit text-only knowledge sources and SHALL NOT add image upload or image-answering behavior. If the chat provider is not configured, unavailable, times out, rejects the request, or returns an invalid response after evidence was found, the ask endpoint SHALL return HTTP 503 with a stable error code and no provider credentials, raw response body, stack trace, or ungrounded fallback answer. The endpoint SHALL be non-streaming for this change.

#### Scenario: Missing chat configuration is reported without leakage
- **WHEN** evidence exists but no chat provider is configured
- **THEN** the server returns HTTP 503 with a stable error and does not expose configuration values or fabricate an answer

#### Scenario: Embedding and chat providers remain independent
- **WHEN** retrieval obtains evidence through the embedding provider and answer generation begins
- **THEN** the chat provider is invoked separately and cannot perform additional database or vector-store retrieval

#### Scenario: Oversized chat request is rejected locally
- **WHEN** the serialized chat-completions request would exceed 20 MB
- **THEN** the server returns a stable provider error without sending the request or exposing its content or credentials

