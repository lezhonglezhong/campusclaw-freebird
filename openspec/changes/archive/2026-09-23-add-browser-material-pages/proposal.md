# Proposal

## Why

CampusClaw already provides authenticated, class-scoped material APIs, but users
cannot complete the workflow in a browser because there is no login or material
management interface. A small same-origin browser interface is needed to make
the existing teacher and student flows demonstrable without weakening the
server-side authorization boundary.

## What Changes

- Add server-rendered login and protected material pages with a small vanilla
  JavaScript and CSS client.
- Add minimal session-support endpoints for the browser: current authenticated
  identity lookup and logout. Existing login and material API contracts remain
  unchanged.
- Render class-scoped material lists and basic material detail information using
  the existing authenticated APIs.
- Provide a teacher-only material upload form that uses the existing JSON upload
  endpoint; students neither see nor can enable the form through the UI.
- Provide clear browser feedback for invalid login, loading, upload, and API
  authorization failures.

## Capabilities

### New Capabilities
- `browser-material-interface`: Same-origin browser pages for session-aware
  login, class-scoped material viewing, teacher upload, and user-visible error
  handling.

### Modified Capabilities
- None.

## Impact

- Affects Flask route registration and adds static HTML, CSS, and JavaScript
  assets plus browser-flow tests.
- Adds `GET /api/me` and `POST /logout` for browser session recovery and
  termination; it reuses the current Flask-signed session and does not expose
  secrets.
- Reuses `POST /login`, `GET /api/materials`, `GET /api/materials/<id>`, and
  `POST /api/materials` without changing their request or response contracts.
- Introduces no frontend framework or build tool; no RAG, registration, account
  administration, cross-class access, or new storage backend is included.
