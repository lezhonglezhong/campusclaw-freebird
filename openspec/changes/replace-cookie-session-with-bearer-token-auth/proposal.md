# Proposal

## Why

CampusClaw currently authenticates browsers through a server-set session cookie, but the revised course requirement requires clients to carry an explicit token on every protected backend request. A Bearer-token contract also makes authentication behavior visible and testable for the browser and future API clients.

## What Changes

- **BREAKING** Replace cookie-session authentication with short-lived JWT access tokens returned by `POST /login`.
- Require `Authorization: Bearer <access-token>` on `/api/me` and every protected material, retrieval, answer, upload, download, delete, and reindex API request.
- Validate the token's signature and expiry, then reload the identified user from the database so current role and class membership remain authoritative.
- Stop setting or accepting an authentication cookie and stop using client-supplied or token-embedded role/class values for authorization.
- Store the browser access token in `sessionStorage`, attach it through one shared request helper, clear it on logout or HTTP 401, and never place it in URLs or persistent local storage.
- Serve `/materials` as a data-free application shell; missing or invalid token state is handled by the browser and protected APIs rather than an HTTP navigation redirect.
- Keep passwords hashed and move signing configuration to a required server-only environment secret with a configurable access-token lifetime.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `user-authentication`: Replace the server cookie-session contract with JWT issuance, Bearer validation, expiry handling, and database user resolution.
- `browser-material-interface`: Replace cookie-based browser login/session behavior with `sessionStorage` token handling and authenticated request headers.

## Non-Goals

- Refresh tokens, remember-me login, OAuth/social identity, password reset, multi-device token management, server-side JWT revocation lists, or authorization based directly on role/class claims.

## Impact

- Affects authentication helpers and decorators, application configuration, all protected APIs, login and workspace JavaScript, direct download behavior, tests, `.env.example`, Compose configuration, and README instructions.
- Existing clients that rely on cookies will receive HTTP 401 until they send the Bearer header.
- `replace-cookie-session-with-bearer-token-auth` becomes an implementation prerequisite for `add-traceable-vector-retrieval`.
