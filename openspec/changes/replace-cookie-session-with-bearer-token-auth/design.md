# Design

## Context

See `proposal.md` for motivation. Authentication currently stores `user_id` in Flask's signed session cookie; decorators load that session user, `/materials` redirects before rendering, and browser `fetch` relies on cookies automatically. The change crosses authentication helpers, every protected API, direct downloads, both browser scripts, tests, environment configuration, and the pending traceable-retrieval change.

The deployment is one CampusClaw service, so asymmetric key distribution and a separate authorization server would add no current benefit. There is no requirement for refresh tokens or immediate server-side revocation.

## Goals / Non-Goals

**Goals:**

- Make the authentication credential explicit on every protected backend request.
- Keep current database role/class membership authoritative after token validation.
- Preserve password hashing, seeded accounts, API 401/403/404 boundaries, and the existing Chinese browser flow.
- Centralize browser token storage and request handling so new retrieval/answer APIs inherit the same behavior.

**Non-Goals:**

- Refresh tokens, long-lived login, revocation lists, OAuth/OIDC, public-key/JWKS distribution, or authorization from JWT role/class claims.
- Supporting cookie and Bearer authentication simultaneously after cutover.

## Decisions

### 1. Issue short-lived HS256 JWT access tokens

`POST /login` verifies the existing password hash and issues a JWT signed with `TOKEN_SIGNING_SECRET`. Claims are limited to a token ID, user identifier subject, issued-at time, and expiry. Role, class, account name, and password data are omitted because they can change and are not authorization sources. The response includes the token, `Bearer` type, configured lifetime, and the current public user payload.

HS256 is appropriate for the current single service and keeps configuration small. The alternative—opaque database tokens—would provide revocation but add token persistence and cleanup; asymmetric JWTs would help multiple independent verifiers but are unnecessary here.

Use a mature JWT library rather than custom signing. `TOKEN_SIGNING_SECRET` is required and must be non-empty; `TOKEN_TTL_SECONDS` defaults to 3600 and is validated as a positive bounded integer. The accepted algorithm is fixed server-side and never selected from request data.

### 2. Resolve the current database user for every protected request

The authentication decorator parses exactly one Bearer credential, verifies signature and expiry, validates the subject shape, and loads the user by primary key. Handlers receive this database object. Role and `class_id` come only from the loaded record; any claims or request fields with those names are ignored.

All authentication failures return the same 401 JSON and `WWW-Authenticate: Bearer` header so callers can recover without learning whether a token was expired, forged, or referenced a deleted user. Authorization failures after authentication continue to use the existing 403/404 contracts.

Accepting tokens from query strings, JSON, forms, or cookies is deliberately forbidden because URLs and bodies are more likely to be logged or accidentally forwarded.

### 3. Remove Flask authentication session state at cutover

Login does not write `session["user_id"]` or send a session cookie. Protected decorators do not inspect `flask.session`. `SESSION_SECRET` is replaced by `TOKEN_SIGNING_SECRET` for application startup configuration. The application does not run a dual-auth transition: existing cookie-only clients receive 401 and must log in again.

This produces one auditable authentication path and prevents stale cookie behavior from hiding missing Bearer headers in tests.

### 4. Serve `/materials` as a data-free shell

Top-level browser navigation cannot set an Authorization header, so `/materials` returns the same shell without embedding identity or material data. Its script checks `sessionStorage` and immediately redirects to `/login` if no token exists; otherwise it calls `/api/me` with the Bearer header before rendering protected controls or data. Any 401 clears the token and visible protected state, then redirects.

Server-side 302 protection is not retained because it cannot distinguish a valid browser token during navigation. Security remains on the APIs; the shell is treated as public static structure.

### 5. Centralize browser token storage and fetch behavior

A small shared browser auth module owns the `sessionStorage` key, stores only the access token, builds Authorization headers without dropping caller-supplied content headers, and handles 401 cleanup. Login stores the returned token only after a successful response. Workspace code uses the helper for JSON, multipart, retrieval, answer, delete, reindex, and identity requests.

`sessionStorage` meets the requested explicit-token model while limiting persistence to one browser tab/session. `localStorage` is rejected because it outlives the session. In-memory-only storage is safer against persistence but would log users out on every reload. The token is never inserted into the DOM, URL, console output, or analytics.

### 6. Fetch protected downloads and create temporary browser files

An ordinary download link cannot attach a Bearer header. The workspace therefore fetches the download endpoint through the authenticated helper, reads the response blob and `Content-Disposition` filename, creates a temporary object URL, programmatically activates a download, and revokes the URL. A 401 creates no file and follows normal token cleanup.

### 7. Keep logout honest about stateless tokens

The browser logout action clears `sessionStorage` and protected UI state before navigating to `/login`. `POST /logout` remains as a 204 compatibility endpoint but does not revoke JWTs or imply revocation. The one-hour default lifetime bounds exposure of a copied token; true immediate revocation is explicitly outside scope.

### 8. Test headers, expiry, and absence of cookie fallback

Tests obtain a token from login and explicitly attach it to protected requests. Coverage includes login response/claims, no `Set-Cookie`, missing/malformed/expired/bad-signature/unknown-user tokens, database role/class changes after issuance, protected JSON/multipart/download calls, browser storage/header behavior, logout cleanup, and rejection of a valid legacy cookie without a Bearer header.

## Risks / Trade-offs

- **[XSS can read `sessionStorage`]** → Keep dynamic rendering on safe text APIs, never interpolate untrusted HTML, avoid third-party scripts, use a restrictive Content Security Policy where deployment permits, and keep tokens short-lived.
- **[Stateless logout cannot revoke a copied token]** → Use a one-hour default lifetime, document the limitation, and add server-side revocation only in a future explicitly scoped change.
- **[Public workspace shell may be mistaken for protected content]** → Keep it data-free and enforce authentication on every API; test the rendered HTML for absence of user/material/token data.
- **[Legacy tests can pass accidentally through cookies]** → Remove all session writes/reads and add tests proving a cookie without a Bearer header is rejected.
- **[Direct download links stop working]** → Replace them with authenticated blob downloads and preserve filenames from response headers.

## Migration Plan

1. Add JWT dependency and validated token configuration while retaining existing password verification.
2. Implement token issuance and Bearer parsing/user resolution with focused tests.
3. Switch all protected decorators and API tests to Bearer headers; remove session reads/writes and cookie assertions.
4. Add the shared browser auth client, migrate login/workspace/API/download flows, and verify 401 cleanup.
5. Update `.env.example`, Compose, README, and dependent retrieval planning references.
6. Deploy as a breaking cutover; users with old cookies log in again to receive a token.

Rollback restores the previous code and `SESSION_SECRET` configuration. JWTs issued during the failed rollout are ignored by the old cookie-only version and naturally expire.
