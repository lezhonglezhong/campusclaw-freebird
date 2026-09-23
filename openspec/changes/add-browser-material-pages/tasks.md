# Tasks

## 1. Browser session support and page shells

- [x] 1.1 Implement `GET /api/me` and `POST /logout` using the existing server-validated session, with no change to existing login or material API contracts; verify `pytest tests/test_browser_session.py -q` exits successfully
- [x] 1.2 Add an unauthenticated `/login` HTML page and a server-protected `/materials` HTML workspace shell with shared static CSS; verify `pytest tests/test_browser_pages.py::test_login_page_is_public_and_materials_page_requires_session -q` exits successfully

## 2. Interactive browser workflow

- [x] 2.1 Implement the same-origin login-page client flow, including successful navigation to `/materials` and clear invalid-credentials feedback without browser credential storage; verify `pytest tests/test_browser_pages.py::test_login_page_declares_safe_interactive_contract -q` exits successfully
- [x] 2.2 Implement material-workspace initialization, session display, server-filtered list rendering, material basic-detail rendering, and HTTP-401/404 user states; verify `pytest tests/test_browser_pages.py::test_material_workspace_declares_session_list_and_detail_contract -q` exits successfully
- [x] 2.3 Implement teacher-only upload presentation and upload/list-refresh feedback while keeping the existing server HTTP-403 student enforcement; verify `pytest tests/test_browser_pages.py::test_workspace_declares_teacher_upload_and_student_read_only_contract tests/test_upload.py::test_student_upload_is_403_and_creates_no_record -q` exits successfully

## 3. Browser-flow integration and validation

- [x] 3.1 Add end-to-end Flask-client coverage for login-session recovery, protected-page redirect, logout, own-class workspace data, teacher upload, and student read-only behavior; verify `pytest tests/test_browser_flow.py -q` exits successfully
- [ ] 3.2 Run the complete regression suite and strictly validate the frontend change; verify `pytest -q && openspec validate add-browser-material-pages --strict` exits successfully
