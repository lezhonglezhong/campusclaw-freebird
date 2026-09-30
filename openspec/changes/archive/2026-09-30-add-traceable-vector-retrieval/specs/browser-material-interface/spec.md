# Spec Delta

## MODIFIED Requirements

### Requirement: Protected material browser workspace

The system SHALL expose `GET /materials` as an HTML application shell that contains no protected data. The workspace SHALL obtain the current user, material, retrieval, answer, and reindex data only through same-origin APIs carrying `Authorization: Bearer <access-token>`. The server SHALL validate the token and resolve the current user, role, and class from the database before returning protected data.

The workspace SHALL display the current user account, role, and class context, and a list of materials returned by the server. A user selecting a listed material SHALL be able to view its `id`, `display_name`, `class_id`, `uploader_id`, and `status`. It SHALL also provide traceable retrieval and grounded-question areas without storing role, class, provider keys, or raw vectors in browser storage. The access token SHALL be read only through the shared authentication client from `sessionStorage`; it MUST NOT be placed in URLs, DOM content, or persistent local storage. A missing token or HTTP 401 response SHALL clear protected views and return the browser to `/login`; a 404 response SHALL show a no-longer-available message without displaying protected material data.

#### Scenario: User views own-class materials in the workspace
- **WHEN** an authenticated class-A user opens `/materials`
- **THEN** the page displays only material data returned by the server for class A

#### Scenario: User retrieves content in the workspace
- **WHEN** an authenticated user submits a non-empty content query with a valid Bearer token
- **THEN** the workspace displays only server-returned same-class results with their source material and chunk provenance

#### Scenario: User accesses retrieval and question controls
- **WHEN** an authenticated teacher or student opens the material workspace
- **THEN** the page offers same-origin knowledge retrieval and grounded-question controls without exposing server credentials or raw vectors

#### Scenario: Expired browser session is redirected
- **WHEN** the workspace has no access token or any protected API request receives HTTP 401
- **THEN** the browser clears token state and protected result views and returns to `/login`

## ADDED Requirements

### Requirement: Browser retrieval presents modes and traceable hits

The workspace SHALL provide a non-empty query input and a mode selector for `keyword`, `vector`, and `hybrid`, with `hybrid` selected initially. It SHALL render each returned hit as a result card containing the material title, chunk number, character range, bounded excerpt, applicable scores/ranks, and an authorized source-material action. Empty hits SHALL display `资料中未找到相关内容`. HTTP 400, 401, and 503 responses SHALL have distinct user-facing states, and stale results SHALL not remain presented as if they belonged to a failed new query.

#### Scenario: User compares retrieval modes
- **WHEN** a user submits the same non-empty query with different selected modes
- **THEN** each request carries the selected mode and the workspace renders only the hits returned for that request

#### Scenario: Empty retrieval is explained without fake cards
- **WHEN** retrieval succeeds with no hits
- **THEN** the fixed no-content message appears and no prior or fabricated result card remains

#### Scenario: Vector dependency outage is actionable
- **WHEN** vector or hybrid retrieval returns HTTP 503
- **THEN** the workspace explains that semantic retrieval is temporarily unavailable and keeps keyword mode available for a new request

### Requirement: Browser ask flow aligns answers and citations

The workspace SHALL provide a non-empty question input and submit the current question to `POST /api/ask`. It SHALL display the returned answer and render ordered citation cards whose numbering matches the answer markers. Each citation SHALL show the source title, chunk number, character range, excerpt, and authorized material action. A no-evidence response SHALL show the fixed answer with no citation cards. The interface SHALL not permit the user to submit a system message or class identifier.

#### Scenario: Grounded answer displays matching citations
- **WHEN** the ask endpoint returns an answer containing `[1]` and an ordered citation list
- **THEN** the workspace displays citation 1 as the first source card with its traceable material and chunk fields

#### Scenario: No-evidence answer has no citations
- **WHEN** the ask endpoint returns `资料中未找到相关内容` and an empty citation list
- **THEN** the workspace displays that answer and no citation card

### Requirement: Browser reindex controls remain teacher-only

The workspace SHALL render reindex controls only when the server-validated current user is a teacher. The controls SHALL support the three chunking strategies, reveal only the parameters applicable to the selected strategy, submit to the authorized reindex endpoint, and clearly report validation, forbidden, not-found, provider, and success outcomes. Students SHALL see retrieval and ask controls but no reindex action; server-side authorization SHALL remain mandatory.

#### Scenario: Teacher selects and applies a chunking strategy
- **WHEN** a teacher opens an own-class material, chooses valid reindex options, and submits them
- **THEN** the workspace reports the server result and refreshes the displayed material/index status

#### Scenario: Student workspace has no reindex action
- **WHEN** a student opens the material workspace
- **THEN** retrieval and ask controls are available but no reindex form or button is rendered
