# Spec Delta

## ADDED Requirements

### Requirement: Class-scoped material source preview

The system SHALL expose `GET /api/materials/<material_id>/content` to Bearer-authenticated teachers and students. For an existing material in the current database class, it SHALL return the retained original text as JSON with the material identifier; it SHALL NOT expose a filesystem path or another class's content. Missing or other-class materials SHALL receive the same HTTP 404 response, and requests without a valid Bearer token SHALL receive HTTP 401. This endpoint SHALL support both direct text uploads and uploaded UTF-8 `.txt`/`.md` materials without changing protected download behavior.

#### Scenario: Class member previews source text
- **WHEN** a class-A member requests the content of an own-class material with a valid Bearer token
- **THEN** the response contains that material's retained original text and no filesystem path

#### Scenario: Another class cannot preview the source
- **WHEN** a class-A member requests the content of a class-B material
- **THEN** the server returns HTTP 404 without class-B content

#### Scenario: Missing authentication cannot preview the source
- **WHEN** a request omits or provides an invalid Bearer token
- **THEN** the server returns HTTP 401 without source text
