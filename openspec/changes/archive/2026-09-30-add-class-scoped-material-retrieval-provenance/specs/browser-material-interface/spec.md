# Spec Delta

## MODIFIED Requirements

### Requirement: Protected material browser workspace
The system SHALL expose `GET /materials` as a protected browser page. An unauthenticated request SHALL receive HTTP 302 with `Location: /login`; an authenticated request SHALL receive an HTML material workspace. The workspace SHALL obtain user, material, and content-retrieval data only through authorized same-origin APIs, so server-side class isolation remains authoritative. It SHALL provide a Chinese content-retrieval form and display each result's excerpt and material provenance, including an authorized download control.

#### Scenario: User views own-class materials in the workspace
- **WHEN** an authenticated class-A user opens `/materials`
- **THEN** the page displays only material data returned by the server for class A

#### Scenario: User retrieves content in the workspace
- **WHEN** an authenticated user submits a non-empty content query
- **THEN** the workspace displays only server-returned same-class results with their source material information

#### Scenario: Expired browser session is redirected
- **WHEN** a material workspace request or its session lookup receives HTTP 401
- **THEN** the browser returns to `/login` without retaining protected material data
