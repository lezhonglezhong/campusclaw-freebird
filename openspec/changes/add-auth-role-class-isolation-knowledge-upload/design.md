# Design

## Context

The repository is at the specification-only course stage and contains no application implementation. See [proposal.md](proposal.md) for the change motivation. The initial implementation will use Flask as the HTTP application framework, SQLite as the local relational data store, SQLAlchemy (or an equivalent ORM) for persistence, and Docker Compose for local startup. This change introduces identity, authorization, class ownership, knowledge-base material records, deployment configuration, and a health-check contract together; their security decisions must be consistent across pages and APIs.

## Goals / Non-Goals

**Goals:**

- Establish one server-recognized authenticated context containing user identity, role, and class membership.
- Enforce teacher upload permissions and class material boundaries in server request handling.
- Persist a class-owned local knowledge-base material record only after an authorized teacher upload and complete local content write.
- Make runtime secrets server-configured and make the application runnable and checkable in Compose.
- Supply repeatable local seed data for two classes, one teacher and one student in each class, and class-owned materials.
- Support browser-selected plain-text and Markdown uploads and class-scoped material-name search.
- Let class members download stored material content and let teachers delete content belonging to their session class.

**Non-Goals:**

- Account self-registration, password recovery, third-party sign-in, or account administration.
- Cross-class sharing, multi-class enrollment, delegation of upload privileges, or teacher selection of a class other than their own.
- Malware scanning, full-text retrieval, vector retrieval, embeddings, RAG, or knowledge-base question answering.

## Decisions

### Server-authenticated session context

Use Flask's server-signed session mechanism (or an equivalently server-validated credential) to derive identity, role, and class membership for every protected page and API request. Password verification uses Werkzeug's adaptive password-hashing support (or an equivalent approved algorithm); plaintext passwords are never logged or persisted. The secret used to sign or protect the authentication state is injected only through the server-side `SESSION_SECRET` environment variable, and startup fails when it is absent.

This keeps authorization facts authoritative on the server and supports redirecting browser navigation to login. A browser-only role/class claim was rejected because users could alter it. Stateless signed tokens are an acceptable implementation variant only if every request validates them server-side and their signing secret remains server-only.

### Central authorization policies

Route handling will use shared authentication, role, and class-ownership checks before executing protected behavior. Upload requires an authenticated teacher. Material list and material-detail operations derive the permitted class from the authenticated context, rather than trusting a client-supplied class identifier. The list endpoint ignores a client-supplied `class_id` (or equivalent) for range selection and returns only the session class. Detail access to a missing or cross-class material returns the identical HTTP 404 response, preventing resource-existence disclosure.

Centralizing these checks prevents an API from accidentally relying on hidden UI controls. Endpoint-by-endpoint checks were rejected because they risk inconsistent enforcement as routes grow.

### Class-owned material record and knowledge-base ingestion

Model `Class`, `User`, and `Material` in SQLite: a user has one role and belongs to one class; a material has one owning class and one uploader. `Material` contains at least a stable identifier, `display_name`, owning `class_id`, `uploader_id`, local `content_path`/ingestion reference, ingestion `status`, and creation timestamp. For this course project, the Material persistence layer plus content files under the configured, non-source-controlled local `MATERIAL_STORAGE_DIR` form the knowledge-base implementation; no external service is used.

On a valid teacher upload, derive the teacher's class and uploader identity from the server session, validate the role and request fields, write content first to a temporary file in `MATERIAL_STORAGE_DIR`, atomically promote it to its stable final path, and then create and commit the successful `Material` database record. A failure before database commit removes any temporary or promoted file and rolls back the database transaction; a failure while writing content creates no Material record. Therefore no incomplete Material record or unreferenced residual content file remains after a failed upload. The client cannot set `class_id` or `uploader_id`.

Keep the established JSON `{ "display_name", "content" }` upload form for API compatibility. Add a multipart form with one selected `.txt` or `.md` file; validate the extension case-insensitively, use its safe original filename as the material display name, and reject unsupported or empty files with HTTP 400. The server stores only server-generated paths and never trusts a browser-provided path. The class material list queries `Material` through the server-derived class filter and can apply an optional case-insensitive substring filter only to `display_name`.

The browser renders both forms for a teacher: text entry sends the established JSON payload and file selection sends multipart form data. A material detail control downloads through a server route, not by exposing `content_path`. The download route uses the same session-class lookup as detail access and sends the stored content as an attachment using the safe display filename.

Teacher deletion uses the same server-derived teacher role and class boundary. It looks up the material by identifier and session class, stages its local file outside its final name, deletes the database record, and removes the staged file only after the database transaction succeeds; on a database failure it restores the staged file. Missing or cross-class records return the same 404 response. Seed initialization writes actual local content files for seeded records so their download behavior is demonstrable.

Storing material only in application-local metadata was rejected because it would not meet the knowledge-base persistence requirement. Introducing an external knowledge-base product was rejected for this course scope; the local database record and managed content storage preserve the record and list contracts.

### Minimum HTTP interface

The implementation uses JSON request/response bodies for the APIs below. Error responses contain at least an `error` field and never contain authentication secrets or unauthorized material data.

| Operation | Method and path | Request | Success | Main failures |
| --- | --- | --- | --- | --- |
| Login | `POST /login` | `{ "account", "password" }`, both non-empty | `200`, `{ "user": { "id", "account", "role", "class_id", "class_name" } }`, establishes session | `400` malformed input; `401 { "error": "invalid_credentials" }` |
| Protected page | `GET /materials` | none | `200` page for an authenticated user | unauthenticated: `302` to `/login` |
| Material list | `GET /api/materials` | optional `q` filters only material `display_name`; any `class_id` is ignored for scope | `200 { "materials": [...] }`, all items in session class | `401` unauthenticated |
| Material detail | `GET /api/materials/<material_id>` | path identifier | `200 { "material": { "id", "display_name", "class_id", "class_name", "uploader_id", "status" } }` | `401` unauthenticated; `404 { "error": "not_found" }` for missing or cross-class material |
| Material download | `GET /api/materials/<material_id>/download` | path identifier | `200` attachment containing the material content | `401` unauthenticated; `404 { "error": "not_found" }` for missing, cross-class, or unavailable content |
| Teacher upload | `POST /api/materials` | existing JSON `{ "display_name", "content" }`, or multipart one `.txt`/`.md` file | `201 { "material": { "id", "display_name", "class_id", "class_name", "uploader_id", "status" } }` | `400` malformed/unsupported/empty input; `401` unauthenticated; `403 { "error": "forbidden" }` student |
| Teacher deletion | `DELETE /api/materials/<material_id>` | path identifier | `204`, removes material record and stored content | `401` unauthenticated; `403 { "error": "forbidden" }` student; `404 { "error": "not_found" }` missing or cross-class material |
| Health | `GET /health` | none, unauthenticated | `200 { "status": "ok" }` | no application-level failure contract beyond normal server errors |

Logout and a client-visible session-inspection endpoint are deliberately not introduced: neither is necessary to satisfy the current proposal or authorization flows.

### Repeatable development seed data

Provide an idempotent seed command or initialization path that creates classes A and B, `teacher-a` and `student-a` in class A, `teacher-b` and `student-b` in class B, and one material per class. Seed credentials flow through the same password-hashing path as normal credentials; sample data exists only for local development and test verification.

Hard-coding plaintext passwords directly in the database was rejected because it conflicts with the credential-storage requirement. Manually created test data was rejected because it makes the acceptance scenarios difficult to reproduce.

### Containerized configuration and liveness

Provide a Compose service for the Flask application with required non-secret configuration documented via environment-variable names. `SESSION_SECRET` is required at runtime and excluded from client bundles and source-controlled defaults; `.env.example` documents only a placeholder. `SESSION_SECRET=test-only-secret docker compose config` is the non-secret configuration validation command. Configure a Compose healthcheck that calls the unauthenticated, lightweight `GET /health` endpoint so Compose or external tooling can verify application liveness.

Embedding secrets in Compose files was rejected because it risks disclosure. Making the health route authenticated was rejected because it prevents ordinary infrastructure checks.

## Risks / Trade-offs

- [Session secret missing or weak in a deployment] → fail startup/configuration validation and document the required environment variable without a secret value.
- [A route omits the authorization policy] → organize protected routes behind shared middleware/guards and test direct API requests, not only UI behavior.
- [Knowledge-base ingestion fails after upload begins] → do not expose a successful material record until ingestion succeeds; return a failure that permits a retry.
- [Class identifiers supplied by clients are tampered with] → ignore them for authorization and derive class scope from the validated server context.
- [Seed data leaks into a non-development deployment] → gate seed execution behind an explicit development/test configuration and document that it is not production startup behavior.
- [Health endpoint reveals operational details] → return only minimal status information and no credentials, configuration, or material data.

## Migration Plan

1. Add Flask/SQLite configuration validation, persistence schema, and Compose definitions with no existing user data to migrate.
2. Initialize repeatable development seed data and deploy with the server authentication secret supplied through the deployment environment.
3. Verify `GET /health`, authenticated teacher upload, HTTP-403 student upload rejection, and cross-class denial before exposing protected pages.
4. Roll back by stopping the new Compose deployment; because this is a new capability, no compatibility migration is required. Preserve any created knowledge-base records according to the chosen deployment's backup policy.
