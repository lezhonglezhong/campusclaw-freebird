"""Bearer-protected material source preview tests."""

from io import BytesIO
from pathlib import Path

from campusclaw import create_app
from campusclaw.models import KnowledgeEntry, Material
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'preview.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "content"),
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    return app


def login(client, account: str, password: str) -> None:
    response = client.post("/login", json={"account": account, "password": password})
    assert response.status_code == 200
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {response.json['access_token']}"


def test_teacher_and_student_preview_direct_and_file_text(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    teacher = app.test_client()
    login(teacher, "teacher-a", "teacher-a-password")
    direct = teacher.post("/api/materials", json={"display_name": "Direct", "content": "<b>literal</b>"})
    txt = teacher.post("/api/materials", data={"file": (BytesIO(b"plain txt"), "notes.txt")})
    md = teacher.post("/api/materials", data={"file": (BytesIO(b"# heading"), "notes.md")})
    assert all(response.status_code == 201 for response in (direct, txt, md))
    student = app.test_client()
    login(student, "student-a", "student-a-password")
    for response, content in ((direct, "<b>literal</b>"), (txt, "plain txt"), (md, "# heading")):
        material_id = response.json["material"]["id"]
        preview = student.get(f"/api/materials/{material_id}/content")
        assert preview.status_code == 200
        assert preview.json == {"material_id": material_id, "content": content}
        assert "content_path" not in preview.get_data(as_text=True)


def test_preview_does_not_expose_foreign_or_missing_material(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    foreign = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=2).one()
    student = app.test_client()
    login(student, "student-a", "student-a-password")
    for material_id in (foreign.id, 999999):
        response = student.get(f"/api/materials/{material_id}/content")
        assert response.status_code == 404
        assert response.json == {"error": "not_found"}


def test_preview_requires_valid_bearer_token(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=1).one()
    for token in (None, "Bearer wrong"):
        client = app.test_client()
        if token:
            client.environ_base["HTTP_AUTHORIZATION"] = token
        response = client.get(f"/api/materials/{material.id}/content")
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_preview_uses_retained_body_and_falls_back_for_old_records(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    session = app.extensions["sqlalchemy"]["session"]
    material = session.query(Material).filter_by(class_id=1).one()
    client = app.test_client()
    login(client, "student-a", "student-a-password")
    Path(material.content_path).unlink()
    response = client.get(f"/api/materials/{material.id}/content")
    assert response.status_code == 200
    assert response.json["content"] == "Class A sample material content.\n"
    session.query(KnowledgeEntry).filter_by(material_id=material.id).delete()
    session.commit()
    response = client.get(f"/api/materials/{material.id}/content")
    assert response.status_code == 404
    assert response.json == {"error": "not_found"}
