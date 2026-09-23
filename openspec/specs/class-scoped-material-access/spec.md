# class-scoped-material-access Specification

## Purpose

Enforces class membership as a server-side data boundary for knowledge-base material listing and access.

## Requirements

### Requirement: Server-enforced class material boundary
The system SHALL authorize knowledge-base material listing and access on the server using the authenticated user's class membership and the material's owning class. Client-side visibility controls MUST NOT be the sole enforcement mechanism. The authenticated class identifier SHALL be derived only from the server-validated session context.

#### Scenario: Server session is the class authorization source
- **WHEN** an authenticated user requests material data
- **THEN** the server determines the permitted class from that user's validated session context

### Requirement: Class-scoped material-list interface
The system SHALL expose `GET /api/materials` for authenticated users. It SHALL return HTTP 200 with at least `{ "materials": [ ... ] }`, where every item belongs to the current session user's class. An optional `q` parameter SHALL filter only by a case-insensitive match against material `display_name` after the session-class boundary is applied. The endpoint SHALL NOT use any client-supplied `class_id` or equivalent parameter to expand or change the query range; such a parameter MAY be present but the response SHALL still contain only the session user's class materials. An unauthenticated request SHALL return HTTP 401 with at least an `error` field.

#### Scenario: List remains scoped when a client supplies another class identifier
- **WHEN** an authenticated class-A user calls `GET /api/materials?class_id=<class-B-id>`
- **THEN** the response is HTTP 200 and contains only class-A material data

#### Scenario: User searches names within the session class
- **WHEN** an authenticated teacher or student calls `GET /api/materials?q=<name-fragment>`
- **THEN** the response contains only same-class materials whose display names match the fragment, and contains no other-class material data

### Requirement: Class-scoped material-detail interface
The system SHALL expose `GET /api/materials/<material_id>` for authenticated users. For a material owned by the current session user's class, it SHALL return HTTP 200 with at least `{ "material": { "id", "display_name", "class_id", "uploader_id", "status" } }`. If the material does not exist or belongs to another class, it SHALL return the same HTTP 404 response with at least `{ "error": "not_found" }`, without material data. An unauthenticated request SHALL return HTTP 401 with at least an `error` field.

#### Scenario: Member accesses own-class material detail
- **WHEN** an authenticated user requests a material belonging to the user's session class
- **THEN** the server returns HTTP 200 with the material data

#### Scenario: A-class user requests B-class material detail
- **WHEN** an authenticated class-A user requests a class-B material identifier
- **THEN** the server returns HTTP 404 with no class-B material data

### Requirement: Class-scoped material download
The system SHALL expose `GET /api/materials/<material_id>/download` for authenticated teachers and students. For a material owned by the current session user's class with available stored content, it SHALL return HTTP 200 as a download attachment containing that content and SHALL NOT expose the server storage path. If the material does not exist, belongs to another class, or has unavailable stored content, it SHALL return HTTP 404 with at least `{ "error": "not_found" }` and no material data. An unauthenticated request SHALL return HTTP 401 with at least an `error` field.

#### Scenario: Student downloads own-class material
- **WHEN** an authenticated student requests download of a material owned by the student's session class
- **THEN** the server returns the material content as a download attachment

#### Scenario: User downloads another class's material
- **WHEN** an authenticated class-A user requests download of a class-B material identifier
- **THEN** the server returns HTTP 404 with no class-B material data

### Requirement: Development sample classes and materials
The system SHALL provide repeatable development seed data with at least two distinct classes and at least one material record with available locally stored content owned by each class, so class-isolation and download behavior can be verified.

#### Scenario: Seeded cross-class boundary is exercised
- **WHEN** a seeded class-A user requests a seeded class-B material
- **THEN** the server rejects the request and returns no class-B material data

### Requirement: Class ownership is retained for uploaded materials
The system SHALL associate each uploaded material record with the uploader's class context so that later authorization decisions can enforce the class boundary.

#### Scenario: Teacher uploads material from class A
- **WHEN** a teacher authenticated for class A successfully uploads a material
- **THEN** the resulting knowledge-base material record is associated with class A

### Requirement: Human-readable class name is exposed with material context
The system SHALL expose the class name associated with the authenticated user and each returned material, in addition to its stable internal `class_id`, so browser pages can display A or B rather than relying on the numeric identifier. The class name is server-derived display data and SHALL NOT grant the client authority to select a class.

#### Scenario: Class-A material context is displayed
- **WHEN** an authenticated class-A user loads their material context
- **THEN** the returned user or material data identifies the class by its display name A as well as its internal identifier
