# Design

## Context

See [proposal.md](proposal.md) for the motivation. The Flask application already
uses same-origin, Flask-signed session cookies and exposes JSON login, material
list/detail, and teacher upload APIs. It has no HTML login page, no client
session-recovery endpoint, no logout endpoint, and only a placeholder protected
`/materials` response.

## Goals / Non-Goals

**Goals:**

- Deliver a small browser workflow that preserves the existing server-side role
  and class checks.
- Make seeded teacher and student flows easy to demonstrate without a frontend
  build pipeline.
- Add only the session APIs required for page initialization and logout.

**Non-Goals:**

- React, Vite, Node tooling, a design system, or a separate frontend service.
- Registration, account administration, password recovery, external identity,
  rich text/Markdown rendering, download routes, search, RAG, or chat.
- Replacing the existing JSON material upload contract with file upload.

## Decisions

### Server-rendered page shells with static vanilla assets

Flask will serve `GET /login` and `GET /materials` HTML shells, a shared CSS
file, and small page-specific JavaScript files. JavaScript uses `fetch` with
same-origin default credentials and JSON request bodies. This avoids adding
Node, a package manager, a bundler, or an API-origin/CORS boundary for a small
course demonstration.

React/Vite was considered because the course reference presents a SPA option,
but it would add a toolchain and deployment surface without improving the
server-side authorization behavior required here. Hand-written HTML in each
route was rejected so reusable assets and browser behavior remain testable.

### API contracts remain authoritative

The client will call the existing login and material endpoints unchanged. It
will obtain display identity from a new `GET /api/me`; it will never derive a
role or class from query parameters or browser storage. A new `POST /logout`
clears the existing Flask session. The protected server page and API guards
remain enforcement points; hiding the upload form is presentation only.

Storing user identity in localStorage was rejected because it can be edited.
Duplicating authorization rules in JavaScript was rejected because direct API
requests must continue to be denied by the server.

### Minimal accessible page states

The login and workspace pages will use semantic forms, labels, live status
messages, buttons, and simple responsive CSS. JavaScript will disable actions
while requests are pending, display server-safe errors, redirect on 401, and
refresh the list after a successful upload. Detail information will render only
after a successful detail response, preventing stale protected data from being
shown after a 404 or 401.

Browser automation is intentionally not introduced; Flask test-client tests
will cover page routes and session/API flows, while the final task includes a
repeatable local browser smoke command and checklist.

## Risks / Trade-offs

- [JavaScript disabled] → pages provide clear structure but interactive login
  and material actions require JavaScript; this is acceptable for the minimal
  course demonstration.
- [Stale data after session expiry] → clear displayed data before redirecting to
  the login page on HTTP 401.
- [UI authorization bypass] → retain and test existing server guards; the UI
  only hides teacher controls.
- [Future visual requirements grow] → CSS and JavaScript are isolated under
  Flask static assets and can be replaced by a separate frontend later.

## Migration Plan

1. Add session-support endpoints with focused API tests.
2. Add static assets and page route shells, then connect them to the existing
   APIs and add browser-flow tests.
3. Deploy by restarting the single Flask service; no data migration is needed.
4. Roll back by reverting the frontend change. Existing JSON API consumers and
   persisted material records remain compatible.
