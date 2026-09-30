# browser-material-interface Specification

## Purpose

Provide a same-origin browser interface for signing in, viewing only the user's
class materials, and teacher uploads through authorized server APIs.

## Requirements

### Requirement: Browser login and session lifecycle

The system SHALL expose an unauthenticated `GET /login` page with non-empty
account and password inputs and a login action. The page SHALL submit
credentials to `POST /login`; on success it SHALL store only the returned
`access_token` in `sessionStorage`, discard the password, and navigate to
`/materials`. It SHALL NOT store the password, role, class identifier, signing
secret, or token in persistent local storage, a cookie, a URL, or DOM content.
An invalid login SHALL remain on the login page and display a clear error
without exposing credentials or server secrets.

The browser SHALL call `GET /api/me` with `Authorization: Bearer
<access-token>` to recover current server-validated user context. An
authenticated request SHALL return HTTP 200 with at least `{ "user": { "id",
"account", "role", "class_id", "class_name" } }`; an unauthenticated request
SHALL return HTTP 401 with at least an `error` field. Logout SHALL remove the
token from `sessionStorage`, clear protected views, optionally post to
`/logout` for compatibility, and navigate to `/login`.

#### Scenario: User signs in through the browser
- **WHEN** a visitor submits valid seeded credentials on the login page
- **THEN** the access token is stored in `sessionStorage` and the visitor is
  directed to the material workspace

#### Scenario: Invalid browser login is explained
- **WHEN** a visitor submits an unknown account or incorrect password
- **THEN** the login page displays an invalid-credentials error and stores no access token

#### Scenario: Browser session is recovered or ended
- **WHEN** a browser requests `/api/me` with its Bearer token and later logs out
- **THEN** it first receives the current database identity and subsequently
  clears the token, after which `/api/me` without a Bearer header returns HTTP 401

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
### Requirement: Teacher upload and student presentation boundary

The material workspace SHALL display an upload form with non-empty
`display_name` and `content` fields only when Bearer-authenticated `GET /api/me`
identifies the current database user as a teacher. The form SHALL submit JSON
or multipart data to `POST /api/materials` with the same Bearer header and, on
HTTP 201, refresh the displayed server-filtered material list. A student
workspace SHALL not render an upload form or upload control. The absence of
that control SHALL NOT replace the server-side HTTP-403 authorization requirement.

The workspace SHALL show a clear status message for malformed upload input,
HTTP 401, HTTP 403, and failed upload responses, and SHALL not claim success
until it receives HTTP 201.

#### Scenario: Teacher uploads from the browser workspace
- **WHEN** a Bearer-authenticated teacher submits non-empty material fields through the workspace
- **THEN** the page reports success and refreshes the list with the server-created
  material for that teacher's current database class

#### Scenario: Student sees a read-only workspace
- **WHEN** a Bearer-authenticated student opens the material workspace
- **THEN** no upload form is rendered and direct use of the upload API with that token remains HTTP 403

### Requirement: Shared browser client attaches Bearer authorization

The browser SHALL use one shared authenticated request helper for every
protected JSON and multipart API call. The helper SHALL attach
`Authorization: Bearer <access-token>` without replacing existing request
headers or bodies, and SHALL handle HTTP 401 by clearing the token and
protected views before navigating to `/login`. It MUST NOT append the token to
a URL or log it.

#### Scenario: Protected request carries the access token
- **WHEN** a logged-in browser lists, uploads, deletes, retrieves, asks, or reindexes material data
- **THEN** the request carries the current access token in the Authorization header and not in its URL or body

### Requirement: Protected downloads use authenticated fetch

The workspace SHALL download protected material content through an authenticated
request carrying the Bearer header, create a temporary browser download from the
successful response, preserve the server-provided filename, and revoke temporary
object URLs afterward. It MUST NOT navigate directly to a protected download URL
because browser navigation cannot attach the header.

#### Scenario: User downloads an own-class material with a token
- **WHEN** a logged-in user activates a material download action
- **THEN** the browser fetches the file with the Bearer header and starts a
  download using the server-provided filename

#### Scenario: Download token is rejected
- **WHEN** the authenticated download request returns HTTP 401
- **THEN** no file is created and the browser clears token state and returns to `/login`

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

### Requirement: Browser previews material text without forcing a download

The material detail panel SHALL fetch own-class retained source text through the shared Bearer client and display it below the metadata as plain text for both direct text and uploaded `.txt`/`.md` materials. The existing authenticated download action SHALL remain available. After a successful upload, the browser SHALL refresh the list and open the new material detail so the text is visible without another selection. While loading a different material, after HTTP 401/404, or after deletion, it SHALL clear the previous preview rather than displaying stale or foreign content. Source text MUST NOT be interpreted as HTML.

#### Scenario: Direct text upload appears immediately
- **WHEN** a teacher successfully submits a direct-text material
- **THEN** the refreshed workspace opens its detail and displays the saved original text below the metadata

#### Scenario: Uploaded file can be read and downloaded
- **WHEN** a class member opens an own-class `.txt` or `.md` material
- **THEN** the text appears inline and the download action remains available

#### Scenario: Source markup is displayed literally
- **WHEN** an authorized source contains HTML-like markup
- **THEN** the workspace renders it as text without executing or interpreting it

#### Scenario: Failed or superseded preview clears prior content
- **WHEN** a new detail selection fails, is unauthorized, or is replaced by another selection
- **THEN** no content from the previously selected material remains visible

