# Spec Delta

## MODIFIED Requirements

### Requirement: Browser login and session lifecycle

The system SHALL expose an unauthenticated `GET /login` browser page containing non-empty account and password inputs and a login action. The page SHALL submit credentials to `POST /login`; on success it SHALL store only the returned `access_token` in `sessionStorage`, discard the password, and navigate to `/materials`. It SHALL NOT store the password, role, class identifier, signing secret, or token in persistent local storage, a cookie, a URL, or DOM content. An invalid login SHALL remain on the login page and display a clear error without exposing credentials or server secrets.

The browser SHALL call `GET /api/me` with `Authorization: Bearer <access-token>` to recover the current server-validated user context. An authenticated request SHALL return HTTP 200 with at least `{ "user": { "id", "account", "role", "class_id", "class_name" } }`; an unauthenticated request SHALL return HTTP 401 with at least an `error` field. Logout SHALL remove the token from `sessionStorage`, clear protected views, optionally post to `/logout` for compatibility, and navigate to `/login`.

#### Scenario: User signs in through the browser
- **WHEN** a visitor submits valid seeded credentials on the login page
- **THEN** the access token is stored in `sessionStorage` and the visitor is directed to the material workspace

#### Scenario: Invalid browser login is explained
- **WHEN** a visitor submits an unknown account or incorrect password
- **THEN** the login page displays an invalid-credentials error and stores no access token

#### Scenario: Browser session is recovered or ended
- **WHEN** a browser requests `/api/me` with its Bearer token and later logs out
- **THEN** it first receives the current database identity and subsequently clears the token, after which `/api/me` without a Bearer header returns HTTP 401

### Requirement: Protected material browser workspace

The system SHALL expose `GET /materials` as a data-free browser application shell. The workspace SHALL read the access token from `sessionStorage` and obtain current user and material data only through `GET /api/me`, `GET /api/materials`, and `GET /api/materials/<material_id>` requests carrying `Authorization: Bearer <access-token>`, so server-side role and class checks remain authoritative.

The workspace SHALL display the current database user account, role, and class context and a list of materials returned by the server. A user selecting a listed material SHALL be able to view its `id`, `display_name`, `class_id`, `uploader_id`, and `status`. A missing token or 401 response SHALL remove the token, clear protected material data, and return the browser to `/login`; a 404 response SHALL show a no-longer-available message without displaying protected material data.

#### Scenario: User views own-class materials in the workspace
- **WHEN** a class-A user's browser sends a valid Bearer token and opens `/materials`
- **THEN** the page displays only material data returned by the server for the user's current database class A

#### Scenario: Expired browser session is redirected
- **WHEN** a material workspace request receives HTTP 401 for a missing, invalid, or expired token
- **THEN** the browser removes token state and returns to `/login` without retaining protected material data

### Requirement: Teacher upload and student presentation boundary

The material workspace SHALL display an upload form with non-empty `display_name` and `content` fields only when Bearer-authenticated `GET /api/me` identifies the current database user as a teacher. The form SHALL submit JSON or multipart data to `POST /api/materials` with the same Bearer header and, on HTTP 201, refresh the displayed server-filtered material list. A student workspace SHALL not render an upload form or upload control. The absence of that control SHALL NOT replace the server-side HTTP-403 authorization requirement.

The workspace SHALL show a clear status message for malformed upload input, HTTP 401, HTTP 403, and failed upload responses, and SHALL not claim success until it receives HTTP 201.

#### Scenario: Teacher uploads from the browser workspace
- **WHEN** a Bearer-authenticated teacher submits non-empty material fields through the workspace
- **THEN** the page reports success and refreshes the list with the server-created material for that teacher's current database class

#### Scenario: Student sees a read-only workspace
- **WHEN** a Bearer-authenticated student opens the material workspace
- **THEN** no upload form is rendered and direct use of the upload API with that token remains HTTP 403

## ADDED Requirements

### Requirement: Shared browser client attaches Bearer authorization

The browser SHALL use one shared authenticated request helper for every protected JSON and multipart API call. The helper SHALL attach `Authorization: Bearer <access-token>` without replacing existing request headers or bodies, and SHALL handle HTTP 401 by clearing the token and protected views before navigating to `/login`. It MUST NOT append the token to a URL or log it.

#### Scenario: Protected request carries the access token
- **WHEN** a logged-in browser lists, uploads, deletes, retrieves, asks, or reindexes material data
- **THEN** the request carries the current access token in the Authorization header and not in its URL or body

### Requirement: Protected downloads use authenticated fetch

The workspace SHALL download protected material content through an authenticated request carrying the Bearer header, create a temporary browser download from the successful response, preserve the server-provided filename, and revoke temporary object URLs afterward. It MUST NOT navigate directly to a protected download URL because browser navigation cannot attach the header.

#### Scenario: User downloads an own-class material with a token
- **WHEN** a logged-in user activates a material download action
- **THEN** the browser fetches the file with the Bearer header and starts a download using the server-provided filename

#### Scenario: Download token is rejected
- **WHEN** the authenticated download request returns HTTP 401
- **THEN** no file is created and the browser clears token state and returns to `/login`
