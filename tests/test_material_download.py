"""Class-scoped material download and downloadable seed-content tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'download.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "content"),
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    return app


def login(client, account: str, password: str) -> None:
    response = client.post("/login", json={"account": account, "password": password})
    assert response.status_code == 200
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {response.json['access_token']}"


def test_teacher_and_student_download_own_class_seed_content(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    session = app.extensions["sqlalchemy"]["session"]
    material = session.query(Material).filter_by(class_id=1).one()
    assert Path(material.content_path).read_text(encoding="utf-8") == "Class A sample material content.\n"

    for account, password in (("teacher-a", "teacher-a-password"), ("student-a", "student-a-password")):
        client = app.test_client()
        login(client, account, password)
        response = client.get(f"/api/materials/{material.id}/download")
        assert response.status_code == 200
        assert response.data == b"Class A sample material content.\n"
        assert "attachment" in response.headers["Content-Disposition"]
        assert material.content_path not in response.headers["Content-Disposition"]


def test_download_preserves_chinese_name_and_suffix(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    teacher = app.test_client()
    login(teacher, "teacher-a", "teacher-a-password")
    created = teacher.post("/api/materials", json={"display_name": "中文材料", "content": "正文"})
    response = teacher.get(f"/api/materials/{created.json['material']['id']}/download")
    assert "filename*=UTF-8''" in response.headers["Content-Disposition"]
    assert "%E4%B8%AD%E6%96%87%E6%9D%90%E6%96%99.txt" in response.headers["Content-Disposition"]


def test_download_hides_cross_class_and_missing_content(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    session = app.extensions["sqlalchemy"]["session"]
    class_a_material = session.query(Material).filter_by(class_id=1).one()
    class_b_material = session.query(Material).filter_by(class_id=2).one()
    student_a = app.test_client()
    login(student_a, "student-a", "student-a-password")

    cross_class = student_a.get(f"/api/materials/{class_b_material.id}/download")
    assert cross_class.status_code == 404
    assert cross_class.json == {"error": "not_found"}

    Path(class_a_material.content_path).unlink()
    missing = student_a.get(f"/api/materials/{class_a_material.id}/download")
    assert missing.status_code == 404
    assert missing.json == {"error": "not_found"}


def test_download_requires_bearer_token(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=1).one()
    response = app.test_client().get(f"/api/materials/{material.id}/download")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
