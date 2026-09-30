## 1. Token configuration and primitives

- [x] 1.1 Add the JWT runtime dependency and validate `TOKEN_SIGNING_SECRET` plus a positive, bounded `TOKEN_TTL_SECONDS` (default `3600`) during application startup.
  - Verification: `pytest -q tests/test_config.py tests/test_token_auth.py -k "configuration or ttl"`
- [x] 1.2 Implement access-token issue and verification helpers using HS256 with only `jti`, `sub`, `iat`, and `exp` claims, mapping malformed, expired, or incorrectly signed tokens to stable authentication failures.
  - Verification: `pytest -q tests/test_token_auth.py -k "claims or expired or malformed or signature"`

## 2. Backend authentication migration

- [x] 2.1 Change `POST /login` to return `access_token`, `token_type: "Bearer"`, `expires_in`, and the authenticated user without setting an authentication cookie.
  - Verification: `pytest -q tests/test_auth.py tests/test_token_auth.py -k "login"`
- [x] 2.2 Replace session-based protection with a shared Bearer-token resolver that accepts tokens only from the `Authorization` header, verifies the token, reloads the user from the database, and returns a stable `401` response with `WWW-Authenticate: Bearer` for every authentication failure.
  - Verification: `pytest -q tests/test_token_auth.py -k "missing or malformed or expired or signature or unknown or reload or bearer"`
- [x] 2.3 Migrate `/api/me` and every existing protected API to the shared resolver so current database role and class membership govern authorization, never client input or token claims.
  - Verification: `pytest -q tests/test_auth.py tests/test_authorization.py tests/test_material_list.py tests/test_file_upload.py tests/test_material_download.py`
- [x] 2.4 Make `/materials` a data-free browser shell, make `/logout` return `204` without server-side revocation, remove Flask session authentication state, and explicitly reject cookie-only fallback.
  - Verification: `pytest -q tests/test_browser_session.py tests/test_token_auth.py -k "materials or logout or cookie"`
- [x] 2.5 Update backend test helpers and fixtures to authenticate with Bearer tokens, then retain regression coverage for teacher/student permissions and class isolation.
  - Verification: `pytest -q tests/test_auth.py tests/test_authorization.py tests/test_material_list.py tests/test_file_upload.py tests/test_material_download.py`

## 3. Browser token lifecycle

- [x] 3.1 Add a shared browser authentication client that owns the access token in `sessionStorage`, attaches `Authorization: Bearer <access-token>` to protected JSON, multipart, and blob requests, and clears the token plus redirects to login on `401`.
  - Verification: `pytest -q tests/test_browser_token_auth.py -k "storage or authorization or unauthorized"`
- [x] 3.2 Update the login page to store only the returned access token in `sessionStorage`, handle invalid credentials without navigation, and enter the material workspace after successful authentication.
  - Verification: `pytest -q tests/test_browser_token_auth.py tests/test_browser_flow.py -k "login"`
- [ ] 3.3 Update the material workspace to recover identity from `/api/me`, route all protected reads and uploads through the shared client, clear the token on logout, and preserve the teacher/student presentation boundary.
  - Verification: `pytest -q tests/test_browser_token_auth.py tests/test_browser_flow.py tests/test_file_upload.py`
- [ ] 3.4 Replace direct protected download links with authenticated blob downloads that preserve the server-provided filename.
  - Verification: `pytest -q tests/test_browser_token_auth.py tests/test_material_download.py -k "download or filename"`

## 4. Operations and documentation

- [ ] 4.1 Update example environment, deployment configuration, and README instructions for `TOKEN_SIGNING_SECRET` and `TOKEN_TTL_SECONDS`, removing `SESSION_SECRET` as an authentication requirement.
  - Verification: `pytest -q tests/test_config.py -k "token"`

## 5. Acceptance

- [ ] 5.1 Run the complete automated test suite and resolve all regressions introduced by the authentication migration.
  - Verification: `pytest -q`
- [ ] 5.2 Strictly validate this OpenSpec change and the dependent traceable-retrieval change after implementation.
  - Verification: `openspec validate replace-cookie-session-with-bearer-token-auth --strict && openspec validate add-traceable-vector-retrieval --strict`
