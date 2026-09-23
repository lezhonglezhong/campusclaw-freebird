# Spec Delta

## Purpose

Allows authorized teachers to add teaching materials to the knowledge base while denying material uploads by students.

## ADDED Requirements

### Requirement: Teacher-only material upload
The system SHALL expose `POST /api/materials` accepting an authenticated teacher's JSON body with non-empty `display_name` and `content` fields. It SHALL accept a material-upload request only from an authenticated teacher and SHALL derive ownership solely from the teacher's server-validated session class. On success it SHALL return HTTP 201 with at least `{ "material": { "id", "display_name", "class_id", "uploader_id", "status" } }`. An upload request from an authenticated student MUST return HTTP 403 with at least `{ "error": "forbidden" }`, and an unauthenticated caller MUST return HTTP 401 with at least an `error` field; neither failure may create a material record or stored content. Malformed input SHALL return HTTP 400 with at least an `error` field.

#### Scenario: Teacher uploads a material
- **WHEN** an authenticated teacher submits a valid teaching material upload
- **THEN** the server accepts the request for knowledge-base ingestion

#### Scenario: Student calls upload API
- **WHEN** an authenticated student calls the material-upload API
- **THEN** the server responds with HTTP 403 and does not create a material record

### Requirement: Uploaded material is available in the class knowledge base
The system SHALL write each successfully accepted teacher upload to the project's local knowledge-base implementation with its owning class, and SHALL expose the resulting material record through that class's material list. In this change, the local knowledge base consists of the persisted `Material` record and its managed local content storage; no external knowledge-base service is required.

#### Scenario: Successful upload appears in material list
- **WHEN** a teacher successfully uploads a material for a class
- **THEN** a subsequent material-list request by an authorized user of that class includes the uploaded material record
