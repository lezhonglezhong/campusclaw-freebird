# browser-material-interface Specification

## Purpose

Provide a small same-origin browser interface that lets CampusClaw users sign
in, view only their class materials, and let teachers upload materials through
the already-authorized server APIs.

## Requirements

### Requirement: Browser login and session lifecycle

The system SHALL expose an unauthenticated `GET /login` browser page containing
non-empty account and password inputs and a login action. The page SHALL submit
credentials to the existing `POST /login` endpoint and rely on its server-set
session cookie; it SHALL NOT store a password, role, class identifier, or
session secret in browser storage. A successful login SHALL navigate to
`/materials`. An invalid login SHALL remain on the login page and display a
clear error without exposing credentials or server secrets.

The system SHALL expose `GET /api/me` for a browser to recover the current
server-validated user context. An authenticated request SHALL return HTTP 200
with at least `{ "user": { "id", "account", "role", "class_id" } }`; an
unauthenticated request SHALL return HTTP 401 with at least an `error` field.
The system SHALL expose `POST /logout`, which removes the authenticated session
and returns HTTP 204. After logout, protected browser pages and authenticated
material APIs SHALL no longer be accessible with that session.

#### Scenario: User signs in through the browser
- **WHEN** a visitor submits valid seeded credentials on the login page
- **THEN** the server-recognized session is established and the visitor is
  directed to the material page

#### Scenario: Invalid browser login is explained
- **WHEN** a visitor submits an unknown account or incorrect password
- **THEN** the login page displays an invalid-credentials error and no
  authenticated session is established

#### Scenario: Browser session is recovered or ended
- **WHEN** a browser requests `/api/me` with a valid session and later posts to
  `/logout`
- **THEN** it first receives the current user identity and subsequently receives
  HTTP 204, after which `/api/me` returns HTTP 401

### Requirement: Protected material browser workspace

The system SHALL expose `GET /materials` as a protected browser page. An
unauthenticated request SHALL receive HTTP 302 with `Location: /login`; an
authenticated request SHALL receive an HTML material workspace. The workspace
SHALL obtain the current user and material data only through `GET /api/me`,
`GET /api/materials`, and `GET /api/materials/<material_id>`, so the server's
existing class isolation remains the authorization source.

The workspace SHALL display the current user account, role, and class context,
and a list of materials returned by the server. A user selecting a listed
material SHALL be able to view its `id`, `display_name`, `class_id`,
`uploader_id`, and `status`. A 401 response SHALL return the browser to
`/login`; a 404 response SHALL show a no-longer-available message without
displaying protected material data.

#### Scenario: User views own-class materials in the workspace
- **WHEN** an authenticated class-A user opens `/materials`
- **THEN** the page displays only material data returned by the server for class A

#### Scenario: Expired browser session is redirected
- **WHEN** a material workspace request or its session lookup receives HTTP 401
- **THEN** the browser returns to `/login` without retaining protected material data

### Requirement: Teacher upload and student presentation boundary

The material workspace SHALL display an upload form with non-empty
`display_name` and `content` fields only when `GET /api/me` identifies the
current user as a teacher. The form SHALL submit JSON to the existing
`POST /api/materials` endpoint and, on HTTP 201, refresh the displayed
server-filtered material list. A student workspace SHALL not render an upload
form or upload control. The absence of that control SHALL NOT replace the
existing server-side HTTP-403 authorization requirement.

The workspace SHALL show a clear status message for malformed upload input,
HTTP 403, and failed upload responses, and SHALL not claim success until it
receives HTTP 201.

#### Scenario: Teacher uploads from the browser workspace
- **WHEN** an authenticated teacher submits non-empty material fields through
  the workspace
- **THEN** the page reports success and refreshes the list with the server-created
  material for that teacher's class

#### Scenario: Student sees a read-only workspace
- **WHEN** an authenticated student opens the material workspace
- **THEN** no upload form is rendered and direct use of the existing upload API
  remains HTTP 403
