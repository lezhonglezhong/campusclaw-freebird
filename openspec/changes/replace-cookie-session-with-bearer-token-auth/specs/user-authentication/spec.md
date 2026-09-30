# Spec Delta

## MODIFIED Requirements

### Requirement: Account/password login

The system SHALL authenticate teacher and student accounts using an account identifier and password and, after successful login, SHALL issue a short-lived signed access token that identifies the user. The system MUST NOT establish or accept an authentication cookie. Role and class authorization SHALL be derived from the current database record loaded after token validation rather than from client input or token claims.

#### Scenario: Teacher logs in successfully
- **WHEN** a teacher submits valid account credentials
- **THEN** the system authenticates the teacher, returns a Bearer access token, and can resolve that token to the teacher's current database role and class membership

#### Scenario: Invalid credentials are rejected
- **WHEN** a user submits an unknown account or incorrect password
- **THEN** the system rejects the login, returns no access token, and establishes no authenticated context

### Requirement: Authentication interface contract

The system SHALL expose `POST /login` accepting a JSON body with non-empty `account` and `password` fields. On valid credentials it SHALL return HTTP 200 with at least `{ "access_token", "token_type": "Bearer", "expires_in", "user": { "id", "account", "role", "class_id", "class_name" } }`. It SHALL NOT set an authentication cookie. On unknown or invalid credentials it SHALL return HTTP 401 with at least `{ "error": "invalid_credentials" }`; malformed input SHALL return HTTP 400 with at least an `error` field. Access tokens SHALL expire after the configured positive lifetime.

#### Scenario: Login interface returns the authenticated identity
- **WHEN** a user posts valid JSON credentials to `POST /login`
- **THEN** the response is HTTP 200, includes the required user identity and Bearer-token fields, and sets no authentication cookie

### Requirement: Protected page login handling

The system SHALL serve protected-workspace HTML as a data-free application shell because a browser navigation cannot attach the Bearer header. The browser SHALL determine login state from the presence of the access token and an authenticated `/api/me` request. A missing token or HTTP 401 SHALL direct the visitor to the login page without rendering protected data.

#### Scenario: Unauthenticated protected-page visit
- **WHEN** a visitor without an access token opens the material workspace shell
- **THEN** the browser displays no protected data and directs the visitor to the login page

### Requirement: Protected-page contract

The system SHALL return HTTP 200 and a data-free HTML shell for `GET /materials` regardless of authentication state. The shell MUST NOT embed user, role, class, material, or access-token data. Protected APIs SHALL require `Authorization: Bearer <access-token>` and SHALL return HTTP 401 rather than a browser redirect when the header is missing, malformed, expired, incorrectly signed, or identifies no current user.

#### Scenario: Browser visit to the protected page is redirected
- **WHEN** a visitor without a usable access token loads `GET /materials`
- **THEN** the shell contains no protected data and its browser authentication guard navigates to `/login`

### Requirement: Secure credential and secret storage

The system MUST store passwords only as secure password hashes and MUST NOT persist or expose plaintext passwords. The JWT signing secret SHALL be supplied only through the server-side `TOKEN_SIGNING_SECRET` environment variable; it MUST NOT be delivered to browser clients, included in tokens, logged, or committed as a real source-controlled value. Application startup SHALL fail when `TOKEN_SIGNING_SECRET` is absent or empty.

#### Scenario: Account credential is persisted
- **WHEN** the system stores or updates an account password
- **THEN** the persisted value is a password hash rather than the submitted plaintext password

#### Scenario: Client receives login experience
- **WHEN** a browser uses the login experience
- **THEN** no password, signing secret, or server authentication configuration is included in browser-delivered content or configuration

## ADDED Requirements

### Requirement: Protected APIs validate Bearer tokens and reload users

Every protected API SHALL require exactly one `Authorization` header using the `Bearer` scheme. After verifying the JWT signature and expiry, the server SHALL load the identified user from the database and use that record's current role and class for authorization. Missing, malformed, expired, invalidly signed, or unknown-user tokens SHALL produce HTTP 401 with `{ "error": "unauthorized" }`, a `WWW-Authenticate: Bearer` response header, and no protected data. A token MUST NOT be accepted from a query parameter, form field, JSON property, or authentication cookie.

#### Scenario: Valid token authorizes with current database membership
- **WHEN** a request carries a valid unexpired Bearer token for an existing user
- **THEN** the protected endpoint authorizes using that user's current database role and class

#### Scenario: Token claims cannot override changed membership
- **WHEN** a user's role or class changes after a token was issued
- **THEN** subsequent protected requests use the updated database values rather than stale token or client values

#### Scenario: Invalid token is rejected uniformly
- **WHEN** a protected request has no Bearer token or has a malformed, expired, incorrectly signed, or unknown-user token
- **THEN** the server returns HTTP 401 with the stable unauthorized response and no protected data

### Requirement: Logout is client-side token disposal

The system SHALL expose `POST /logout` for compatibility and return HTTP 204 without setting or clearing authentication cookies. The browser SHALL end its local login state by removing the access token from `sessionStorage`. Because this change does not maintain a revocation list, a copied token remains valid until expiry; no interface SHALL claim that server-side revocation occurred.

#### Scenario: Browser logout removes subsequent authorization
- **WHEN** a logged-in browser clears its access token during logout and then calls a protected API
- **THEN** the request contains no Bearer token and the server returns HTTP 401

#### Scenario: Logout response does not imply revocation
- **WHEN** a client posts to `/logout`
- **THEN** the server returns HTTP 204 without an authentication cookie or a claim that the already-issued JWT was revoked
