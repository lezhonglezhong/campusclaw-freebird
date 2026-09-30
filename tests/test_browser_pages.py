"""Browser page shell and static-client contract tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'pages.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    return app


def test_login_page_and_data_free_materials_shell_are_public(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    anonymous = app.test_client()
    login = anonymous.get("/login")
    assert login.status_code == 200
    assert b'id="login-form"' in login.data
    assert b'name="password"' in login.data
    workspace = anonymous.get("/materials")
    assert workspace.status_code == 200
    assert b'id="material-list"' in workspace.data
    assert b'id="material-search-form"' in workspace.data
    assert b'/static/app.css' in workspace.data
    assert b"teacher-a" not in workspace.data
    assert b"access_token" not in workspace.data


def test_login_page_declares_safe_interactive_contract(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    page = app.test_client().get("/login")
    script = (Path(app.static_folder) / "login.js").read_text()

    assert b"/static/login.js" in page.data
    assert b"/static/auth-client.js" in page.data
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


def test_material_workspace_declares_token_list_and_detail_contract(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    page = app.test_client().get("/materials")
    script = (Path(app.static_folder) / "materials.js").read_text()

    assert b"/static/materials.js" in page.data
    assert b"/static/auth-client.js" in page.data
    assert "const request = auth.request;" in script
    assert 'request("/api/me")' in script
    assert 'request("/api/materials")' in script
    assert 'new URLSearchParams({ q: query })' in script
    assert 'request(`/api/materials/${id}`)' in script
    assert 'download.textContent = "下载材料"' in script
    assert 'method: "DELETE"' in script
    assert "该材料已不存在或无权访问。" in script
    assert 'window.location.replace("/login")' in script


def test_workspace_declares_teacher_upload_and_student_read_only_contract(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    script = (Path(app.static_folder) / "materials.js").read_text()
    shell = app.test_client().get("/materials")

    assert 'if (user.role !== "teacher") return;' in script
    assert 'request("/api/materials", {' in script
    assert 'id="text-upload-form"' in script
    assert 'id="file-upload-form"' in script
    assert 'id="file-display-name" name="display_name" required' in script
    assert 'formData.append("display_name", displayName)' in script
    assert "材料上传成功。" in script
    assert "删除材料" in script and "下载材料" in script
    assert "你没有上传材料的权限。" in script
    assert b'id="upload-form"' not in shell.data


def test_material_workspace_uses_simplified_chinese(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    client = app.test_client()
    page = client.get("/materials").get_data(as_text=True)
    script = (Path(app.static_folder) / "materials.js").read_text()

    assert 'lang="zh-CN"' in page
    assert "班级材料" in page
    assert "退出登录" in page
    assert "材料列表" in page
    assert "材料详情" in page
    assert "正在加载材料…" in script
    assert "材料名称" in script
    assert "按材料名称搜索" in page
    assert "材料上传成功。" in script
    assert "教师" in script and "学生" in script
