# Spec Delta

## Purpose

Provides secure account/password authentication and protected-page access control for CampusClaw teachers and students.

## ADDED Requirements

### Requirement: Account/password login
The system SHALL authenticate teacher and student accounts using an account identifier and password, and SHALL establish an authenticated server-recognized user context after successful login.

#### Scenario: Teacher logs in successfully
- **WHEN** a teacher submits valid account credentials
- **THEN** the system authenticates the teacher and establishes a user context identifying the teacher role and class membership

#### Scenario: Invalid credentials are rejected
- **WHEN** a user submits an unknown account or incorrect password
- **THEN** the system rejects the login and does not establish an authenticated user context

### Requirement: Authentication interface contract
The system SHALL expose `POST /login` accepting a JSON body with non-empty `account` and `password` fields. On valid credentials it SHALL return HTTP 200 with at least `{ "user": { "id", "account", "role", "class_id", "class_name" } }` and establish the authenticated server-recognized session context. On unknown or invalid credentials it SHALL return HTTP 401 with at least `{ "error": "invalid_credentials" }`; malformed input SHALL return HTTP 400 with at least an `error` field. This change does not require logout or a client-visible session-inspection endpoint.

#### Scenario: Login interface returns the authenticated identity
- **WHEN** a user posts valid JSON credentials to `POST /login`
- **THEN** the response is HTTP 200, includes the required user identity fields, and establishes the server-recognized context

### Requirement: Protected page login handling
The system SHALL redirect an unauthenticated request for a protected page to the login page.

#### Scenario: Unauthenticated protected-page visit
- **WHEN** a visitor without an authenticated user context requests a protected page
- **THEN** the system directs the visitor to the login page

### Requirement: Protected-page contract
The system SHALL treat `GET /materials` as a protected browser page. An unauthenticated request SHALL receive HTTP 302 with a `Location` header for `/login`. API authentication failures are governed by their individual API contracts and are not browser redirects.

#### Scenario: Browser visit to the protected page is redirected
- **WHEN** a visitor without an authenticated user context sends `GET /materials`
- **THEN** the response is HTTP 302 with a `Location` header for `/login`

### Requirement: Secure credential and secret storage
The system MUST store passwords only as secure password hashes and MUST NOT persist or expose plaintext passwords. The authentication session secret SHALL be supplied only through the server-side `SESSION_SECRET` environment variable; it MUST NOT be delivered to browser clients or committed as a real source-controlled value. Application startup SHALL fail when `SESSION_SECRET` is absent.

#### Scenario: Account credential is persisted
- **WHEN** the system stores or updates an account password
- **THEN** the persisted value is a password hash rather than the submitted plaintext password

#### Scenario: Client receives login experience
- **WHEN** a browser uses the login experience
- **THEN** no server authentication secret is included in the browser-delivered content or configuration

### Requirement: Development sample accounts
The system SHALL provide repeatable development seed data containing `teacher-a` and `student-a` assigned to class A and `teacher-b` and `student-b` assigned to class B, with documented test credentials, role assignments, and class membership. Seeded account passwords MUST be stored as password hashes.

#### Scenario: Fresh development data is seeded
- **WHEN** an operator initializes the development data store
- **THEN** A- and B-class teacher and student accounts are available in their assigned classes and none of their stored passwords is plaintext
