# Spec Delta

## ADDED Requirements

### Requirement: Browser previews material text without forcing a download

The material detail panel SHALL fetch own-class retained source text through the shared Bearer client and display it below the metadata as plain text for both direct text and uploaded `.txt`/`.md` materials. The existing authenticated download action SHALL remain available. After a successful upload, the browser SHALL refresh the list and open the new material detail so the text is visible without another selection. While loading a different material, after HTTP 401/404, or after deletion, it SHALL clear the previous preview rather than displaying stale or foreign content. Source text MUST NOT be interpreted as HTML.

#### Scenario: Direct text upload appears immediately
- **WHEN** a teacher successfully submits a direct-text material
- **THEN** the refreshed workspace opens its detail and displays the saved original text below the metadata

#### Scenario: Uploaded file can be read and downloaded
- **WHEN** a class member opens an own-class `.txt` or `.md` material
- **THEN** the text appears inline and the download action remains available

#### Scenario: Source markup is displayed literally
- **WHEN** an authorized source contains HTML-like markup
- **THEN** the workspace renders it as text without executing or interpreting it

#### Scenario: Failed or superseded preview clears prior content
- **WHEN** a new detail selection fails, is unauthorized, or is replaced by another selection
- **THEN** no content from the previously selected material remains visible
