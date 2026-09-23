"""Browser page shell and static-client contract tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'pages.sqlite3'}", "SESSION_SECRET": "test-secret"})
    seed_data(app)
    return app


def test_login_page_is_public_and_materials_page_requires_session(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    anonymous = app.test_client()
    login = anonymous.get("/login")
    assert login.status_code == 200
    assert b'id="login-form"' in login.data
    assert b'name="password"' in login.data
    assert anonymous.get("/materials").status_code == 302

    authenticated = app.test_client()
    authenticated.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    workspace = authenticated.get("/materials")
    assert workspace.status_code == 200
    assert b'id="material-list"' in workspace.data
    assert b'/static/app.css' in workspace.data


def test_login_page_declares_safe_interactive_contract(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    page = app.test_client().get("/login")
    script = (Path(app.static_folder) / "login.js").read_text()

    assert b"/static/login.js" in page.data
    assert 'fetch("/login"' in script
    assert 'window.location.assign("/materials")' in script
    assert "账号或密码错误。" in script
    assert "localStorage" not in script


def test_login_page_uses_simplified_chinese(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    page = app.test_client().get("/login")
    script = (Path(app.static_folder) / "login.js").read_text()

    assert b'lang="zh-CN"' in page.data
    assert "欢迎登录" in page.get_data(as_text=True)
    assert "账号" in page.get_data(as_text=True)
    assert "密码" in page.get_data(as_text=True)
    assert "正在登录…" in script
    assert "暂时无法登录，请稍后重试。" in script


def test_material_workspace_declares_session_list_and_detail_contract(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    workspace = app.test_client()
    workspace.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    page = workspace.get("/materials")
    script = (Path(app.static_folder) / "materials.js").read_text()

    assert b"/static/materials.js" in page.data
    assert 'request("/api/me")' in script
    assert 'request("/api/materials")' in script
    assert 'request(`/api/materials/${id}`)' in script
    assert "That material is no longer available." in script
    assert 'window.location.replace("/login")' in script


def test_workspace_declares_teacher_upload_and_student_read_only_contract(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    script = (Path(app.static_folder) / "materials.js").read_text()
    teacher = app.test_client()
    teacher.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    student = app.test_client()
    student.post("/login", json={"account": "student-a", "password": "student-a-password"})

    assert 'if (user.role !== "teacher") return;' in script
    assert 'request("/api/materials", {' in script
    assert "Material uploaded." in script
    assert "You do not have permission to upload materials." in script
    assert b'id="upload-form"' not in student.get("/materials").data
    assert b'id="upload-form"' not in teacher.get("/materials").data
