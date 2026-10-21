## MODIFIED Requirements

### Requirement: Secure credential and secret storage
The system MUST store passwords only as secure password hashes and MUST NOT persist or expose plaintext passwords. The authentication session secret SHALL be supplied only through the server-side `TOKEN_SIGNING_SECRET` environment variable; it MUST NOT be delivered to browser clients or committed as a real source-controlled value. Application startup SHALL fail when `TOKEN_SIGNING_SECRET` is absent.

#### Scenario: Account credential is persisted
- **WHEN** the system stores or updates an account password
- **THEN** the persisted value is a password hash rather than the submitted plaintext password

#### Scenario: Client receives login experience
- **WHEN** a browser uses the login experience
- **THEN** no server authentication secret is included in the browser-delivered content or configuration

### Requirement: Authentication interface contract
The system SHALL expose POST /login accepting non-empty account and password. Success SHALL return HTTP 200 with user identity, access_token, token_type=Bearer and expires_in. It SHALL NOT establish or accept a login Cookie. Invalid credentials SHALL return 401 and malformed input 400. Browser clients SHALL store tokens in sessionStorage and protected APIs SHALL require Authorization: Bearer.

#### Scenario: Login interface returns the authenticated identity
- **WHEN** a user supplies valid credentials
- **THEN** JSON includes the user and access token and no authentication cookie is set

### Requirement: Protected page login handling
The system SHALL serve the /materials and /apps page shells without server Cookie authentication. Client code SHALL redirect users without a sessionStorage token to /login; protected API requests SHALL return JSON 401 when the Bearer token is missing or invalid.

#### Scenario: Unauthenticated protected-page visit
- **WHEN** a visitor without an access token opens the page shell
- **THEN** the client redirects to login and protected APIs remain inaccessible

### Requirement: Protected-page contract
The system SHALL serve the /materials and /apps page shells without server Cookie authentication. Client code SHALL redirect users without a sessionStorage token to /login; protected API requests SHALL return JSON 401 when the Bearer token is missing or invalid.

#### Scenario: Browser visit to the protected page is redirected
- **WHEN** a visitor without an access token opens the page shell
- **THEN** the client redirects to login and protected APIs remain inaccessible
