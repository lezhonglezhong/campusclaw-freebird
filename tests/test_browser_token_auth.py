"""Static browser contract tests for the shared Bearer client."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
AUTH_CLIENT = (ROOT / "campusclaw" / "static" / "auth-client.js").read_text(encoding="utf-8")


def test_session_storage_owns_only_access_token() -> None:
    assert 'const TOKEN_STORAGE_KEY = "campusclaw.access_token"' in AUTH_CLIENT
    assert "window.sessionStorage.getItem(TOKEN_STORAGE_KEY)" in AUTH_CLIENT
    assert "window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token)" in AUTH_CLIENT
    assert "window.sessionStorage.removeItem(TOKEN_STORAGE_KEY)" in AUTH_CLIENT
    assert "localStorage" not in AUTH_CLIENT


def test_authorization_header_is_added_without_replacing_request_options() -> None:
    assert "new Headers(options.headers || {})" in AUTH_CLIENT
    assert 'headers.set("Authorization", `Bearer ${token}`)' in AUTH_CLIENT
    assert "{ ...options, headers }" in AUTH_CLIENT
    assert "body:" not in AUTH_CLIENT


def test_unauthorized_response_clears_token_and_redirects() -> None:
    assert "response.status === 401" in AUTH_CLIENT
    assert "clearToken();" in AUTH_CLIENT
    assert 'new CustomEvent("campusclaw:unauthorized")' in AUTH_CLIENT
    assert 'window.location.replace("/login")' in AUTH_CLIENT


def test_login_and_workspace_load_shared_authorization_client_first() -> None:
    for template_name, page_script in (("login.html", "login.js"), ("materials.html", "materials.js")):
        template = (ROOT / "campusclaw" / "templates" / template_name).read_text(encoding="utf-8")
        assert "auth-client.js" in template
        assert template.index("auth-client.js") < template.index(page_script)


def test_login_stores_only_returned_access_token_before_navigation() -> None:
    login_script = (ROOT / "campusclaw" / "static" / "login.js").read_text(encoding="utf-8")
    assert "auth.clearToken();" in login_script
    assert "const payload = await response.json();" in login_script
    assert "auth.setToken(payload.access_token);" in login_script
    assert 'window.location.assign("/materials")' in login_script
    assert 'form.elements.password.value = ""' in login_script
    assert "payload.user" not in login_script


def test_workspace_routes_protected_calls_through_shared_client() -> None:
    workspace = (ROOT / "campusclaw" / "static" / "materials.js").read_text(encoding="utf-8")
    assert "const auth = window.CampusClawAuth;" in workspace
    assert "const request = auth.request;" in workspace
    assert 'request("/api/me")' in workspace
    assert 'request("/api/materials"' in workspace
    assert 'request(`/api/materials/${id}`)' in workspace
    assert 'request("/logout", { method: "POST" })' in workspace
    assert 'fetch("/api/' not in workspace


def test_workspace_logout_and_unauthorized_clear_protected_state() -> None:
    workspace = (ROOT / "campusclaw" / "static" / "materials.js").read_text(encoding="utf-8")
    assert 'window.addEventListener("campusclaw:unauthorized", clearProtectedView)' in workspace
    assert "list.replaceChildren();" in workspace
    assert "retrievalResults.replaceChildren();" in workspace
    assert "teacherUpload.replaceChildren();" in workspace
    assert "auth.clearToken();" in workspace
    assert 'window.location.replace("/login")' in workspace


def test_download_uses_authenticated_blob_request_and_temporary_url() -> None:
    workspace = (ROOT / "campusclaw" / "static" / "materials.js").read_text(encoding="utf-8")
    assert "const response = await request(url);" in workspace
    assert "const blob = await response.blob();" in workspace
    assert "URL.createObjectURL(blob)" in workspace
    assert "anchor.click();" in workspace
    assert "URL.revokeObjectURL(objectUrl);" in workspace
    assert "download.href = `/api/materials/" not in workspace


def test_download_filename_prefers_content_disposition() -> None:
    workspace = (ROOT / "campusclaw" / "static" / "materials.js").read_text(encoding="utf-8")
    assert 'response.headers.get("Content-Disposition")' in workspace
    assert "filename\\*=UTF-8''" in workspace
    assert "decodeURIComponent(encoded[1])" in workspace
    assert "anchor.download = downloadFilename(response, fallbackName);" in workspace
