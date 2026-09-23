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
    assert "Account or password is incorrect." in script
    assert "localStorage" not in script
