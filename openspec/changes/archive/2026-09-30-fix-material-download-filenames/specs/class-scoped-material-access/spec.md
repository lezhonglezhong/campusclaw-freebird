# Spec Delta
## MODIFIED Requirements
### Requirement: Class-scoped material download
The system SHALL expose `GET /api/materials/<material_id>/download` for authenticated teachers and students. For an own-class material with available content, it SHALL return an attachment with a Unicode-preserving display filename and the stored `.txt` or `.md` suffix when the display name lacks that suffix. It SHALL NOT expose the storage path. Missing or cross-class content SHALL return 404.
#### Scenario: User downloads a Chinese named text material
- **WHEN** a user downloads an own-class material named in Chinese without an extension
- **THEN** the attachment filename retains the Chinese name and ends in `.txt` or `.md`

#### Scenario: Student downloads own-class material
- **WHEN** an authenticated student requests download of a material owned by the student's session class
- **THEN** the server returns the material content as a download attachment

#### Scenario: User downloads another class's material
- **WHEN** an authenticated class-A user requests download of a class-B material identifier
- **THEN** the server returns HTTP 404 with no class-B material data
