# Spec Delta

## Purpose

Allows authorized teachers to add teaching materials to the knowledge base while denying material uploads by students.

## ADDED Requirements

### Requirement: Teacher-only material upload
The system SHALL expose `POST /api/materials` accepting either an authenticated teacher's JSON body with non-empty `display_name` and `content` fields or a multipart form containing one non-empty `.txt` or `.md` file and an optional non-empty `display_name`. For multipart input, the server SHALL use a supplied `display_name` as the material name and otherwise fall back to the safe original filename for compatibility. The browser file-upload form SHALL require the teacher to enter a material name. The file extension check SHALL be case-insensitive, and an unsupported or empty selected file SHALL return HTTP 400 with at least an `error` field. It SHALL accept a material-upload request only from an authenticated teacher and SHALL derive ownership solely from the teacher's server-validated session class and uploader identity. The client SHALL NOT select or override the class or uploader. On success it SHALL return HTTP 201 with at least `{ "material": { "id", "display_name", "class_id", "class_name", "uploader_id", "status" } }`. An upload request from an authenticated student MUST return HTTP 403 with at least `{ "error": "forbidden" }`, and an unauthenticated caller MUST return HTTP 401 with at least an `error` field; neither failure may create a material record or stored content. Malformed input SHALL return HTTP 400 with at least an `error` field.

#### Scenario: Teacher uploads a material
- **WHEN** an authenticated teacher submits a valid teaching material upload
- **THEN** the server accepts the request for knowledge-base ingestion

#### Scenario: Student calls upload API
- **WHEN** an authenticated student calls the material-upload API
- **THEN** the server responds with HTTP 403 and does not create a material record

#### Scenario: Teacher uploads a selected Markdown file
- **WHEN** an authenticated teacher submits one non-empty `.md` file through the browser upload form
- **THEN** the server stores it as material owned by that teacher's session class and uploader identity

#### Scenario: Teacher names a selected file
- **WHEN** an authenticated teacher submits a selected file with a non-empty material name
- **THEN** the stored material display name is the teacher-provided name rather than the filename

#### Scenario: Teacher submits an unsupported file
- **WHEN** an authenticated teacher submits a selected file that is not `.txt` or `.md`
- **THEN** the server returns HTTP 400 and creates neither a material record nor stored content

### Requirement: Uploaded material is available in the class knowledge base
The system SHALL write each successfully accepted teacher upload to the project's local knowledge-base implementation with its owning class, and SHALL expose the resulting material record through that class's material list. In this change, the local knowledge base consists of the persisted `Material` record and its managed local content storage; no external knowledge-base service is required.

#### Scenario: Successful upload appears in material list
- **WHEN** a teacher successfully uploads a material for a class
- **THEN** a subsequent material-list request by an authorized user of that class includes the uploaded material record

### Requirement: Teacher-only material deletion
The system SHALL expose `DELETE /api/materials/<material_id>` only to an authenticated teacher and SHALL derive the permitted class only from that teacher's server-validated session. On successful deletion it SHALL return HTTP 204 and remove both the Material record and its managed local content. An authenticated student MUST receive HTTP 403 with at least `{ "error": "forbidden" }`. A missing or another-class material MUST receive HTTP 404 with at least `{ "error": "not_found" }`; neither response may remove a record or content.

#### Scenario: Teacher deletes own-class material
- **WHEN** an authenticated teacher deletes a material owned by the teacher's session class
- **THEN** the material record and its stored content are removed and the server returns HTTP 204

#### Scenario: Student attempts deletion
- **WHEN** an authenticated student calls the material deletion API
- **THEN** the server returns HTTP 403 and the material remains available

### Requirement: Browser exposes both teacher upload methods
The teacher material page SHALL provide a text-entry upload form with a material name and content, and a separate `.txt`/`.md` file-selection upload form. A student material page SHALL expose neither upload form.

#### Scenario: Teacher sees both upload methods
- **WHEN** an authenticated teacher loads the material page
- **THEN** the page presents text-entry and file-selection upload controls

#### Scenario: Student sees read-only material page
- **WHEN** an authenticated student loads the material page
- **THEN** the page does not present either upload control
