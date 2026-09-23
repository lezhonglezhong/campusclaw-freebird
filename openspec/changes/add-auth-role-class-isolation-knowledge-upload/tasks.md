# Tasks

## 1. Application skeleton

- [x] 1.1 Scaffold the Flask application, SQLAlchemy persistence layer, SQLite configuration, server entry point, and pytest tooling; verify `pytest tests/test_app.py -q` exits successfully
- [x] 1.2 Define `Class`, `User`, and `Material` persistence models with role, class ownership, uploader, local content reference, and ingestion status fields; verify `pytest tests/test_models.py -q` creates and relates all three models

## 2. Development seed data

- [x] 2.1 Implement an idempotent development/test seed command or initialization path that creates classes A and B, named teacher and student test accounts with documented test credentials, and one class-owned material per class; verify `pytest tests/test_seed.py::test_seed_is_idempotent -q` exits successfully
- [x] 2.2 Route seeded account credentials through the normal password-hashing path; verify `pytest tests/test_seed.py::test_seeded_passwords_are_hashed -q` exits successfully

## 3. Login and session security

- [x] 3.1 Implement `POST /login` using an adaptive password hash and `SESSION_SECRET`; verify `pytest tests/test_auth.py::test_login_contract_and_password_hashing -q` covers HTTP-200 login response, session creation, and non-plaintext persistence
- [x] 3.2 Implement the server-validated session context and the protected `GET /materials` redirect contract; verify `pytest tests/test_auth.py::test_unauthenticated_materials_redirects_and_invalid_login_has_no_session -q` exits successfully
- [x] 3.3 Enforce startup failure without `SESSION_SECRET` and keep secrets out of responses and source-controlled defaults; verify `pytest tests/test_config.py::test_missing_session_secret_fails_startup tests/test_auth.py::test_responses_do_not_expose_session_secret -q` exits successfully

## 4. Server-side role and class isolation

- [x] 4.1 Implement reusable server-side authentication and teacher-role authorization guards/middleware without creating the upload API; verify `pytest tests/test_authorization.py::test_teacher_role_guard_allows_teacher_and_denies_student -q` exits successfully
- [x] 4.2 Implement authenticated `GET /api/materials` and `GET /api/materials/<material_id>` using only the server session class for filtering; verify `pytest tests/test_material_access.py::test_class_a_user_lists_and_reads_class_a_material -q` exits successfully
- [x] 4.3 Enforce list parameter isolation and cross-class detail concealment; verify `pytest tests/test_material_access.py::test_class_id_parameter_cannot_expand_list_scope tests/test_material_access.py::test_cross_class_detail_returns_404_without_material_data -q` exits successfully

## 5. Teacher upload and knowledge-base ingestion

- [x] 5.1 Implement `POST /api/materials` using the 4.1 teacher guard and server-derived class; write local content and commit a complete Material record atomically with cleanup on failure; verify `pytest tests/test_upload.py::test_teacher_upload_creates_class_owned_local_material tests/test_upload.py::test_student_upload_is_403_and_creates_no_record tests/test_upload.py::test_failed_upload_leaves_no_record_or_file -q` exits successfully
- [x] 5.2 Verify the existing server-filtered list exposes a successful upload only to its owning class; verify `pytest tests/test_upload.py::test_successful_upload_appears_in_own_class_list -q` exits successfully

## 6. Docker Compose and health checks

- [ ] 6.1 Add Docker Compose configuration and `.env.example` documentation for required `SESSION_SECRET` without a real secret; verify `SESSION_SECRET=test-only-secret docker compose config` exits successfully and `pytest tests/test_config.py::test_compose_and_example_contain_no_real_secret -q` exits successfully
- [ ] 6.2 Implement unauthenticated `GET /health` and configure the Compose healthcheck to call it; verify `pytest tests/test_health.py -q` and `SESSION_SECRET=test-only-secret docker compose up --build -d && curl -fsS http://localhost:8000/health` succeed

## 7. Validation

- [ ] 7.1 Add integration coverage for seeded login, protected-page redirect, teacher upload, HTTP-403 student upload denial, own-class listing, list-parameter isolation, and A-to-B detail HTTP-404 concealment; verify `pytest -q` exits successfully
- [ ] 7.2 Validate the completed OpenSpec change; verify `openspec validate add-auth-role-class-isolation-knowledge-upload --strict` exits successfully
