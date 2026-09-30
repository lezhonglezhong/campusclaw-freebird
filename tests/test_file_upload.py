"""Selected text and Markdown material-file upload tests."""

from io import BytesIO
from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def app_and_client(tmp_path: Path, account: str = "teacher-a"):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'file-upload.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "content"),
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    client = app.test_client()
    password = "teacher-a-password" if account == "teacher-a" else "student-a-password"
    login = client.post("/login", json={"account": account, "password": password})
    assert login.status_code == 200
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {login.json['access_token']}"
    return app, client


def test_teacher_can_upload_txt_and_markdown_files(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path)
    text_response = client.post(
        "/api/materials",
        data={"display_name": "教师命名的文本材料", "file": (BytesIO(b"plain lesson"), "lesson.TXT")},
    )
    markdown_response = client.post("/api/materials", data={"file": (BytesIO(b"# Markdown lesson"), "lesson.md")})

    assert text_response.status_code == 201
    assert markdown_response.status_code == 201
    session = app.extensions["sqlalchemy"]["session"]
    text_material = session.get(Material, text_response.json["material"]["id"])
    markdown_material = session.get(Material, markdown_response.json["material"]["id"])
    assert text_material.display_name == "教师命名的文本材料"
    assert Path(text_material.content_path).suffix == ".txt"
    assert Path(text_material.content_path).read_text() == "plain lesson"
    assert markdown_material.display_name == "lesson.md"
    assert Path(markdown_material.content_path).suffix == ".md"
    assert Path(markdown_material.content_path).read_text() == "# Markdown lesson"


def test_file_upload_falls_back_to_filename_without_material_name(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path)
    response = client.post("/api/materials", data={"file": (BytesIO(b"lesson"), "fallback.md")})
    material = app.extensions["sqlalchemy"]["session"].get(Material, response.json["material"]["id"])
    assert response.status_code == 201
    assert material.display_name == "fallback.md"


def test_json_upload_remains_supported(tmp_path: Path) -> None:
    _app, client = app_and_client(tmp_path)
    response = client.post("/api/materials", json={"display_name": "JSON notes", "content": "lesson"})
    assert response.status_code == 201
    assert response.json["material"]["display_name"] == "JSON notes"


def test_invalid_or_empty_file_creates_no_material_or_content(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path)
    session = app.extensions["sqlalchemy"]["session"]
    before = session.query(Material).count()
    storage_dir = Path(app.config["MATERIAL_STORAGE_DIR"])
    before_files = {path.name for path in storage_dir.iterdir()}
    unsupported = client.post("/api/materials", data={"file": (BytesIO(b"not allowed"), "lesson.pdf")})
    empty = client.post("/api/materials", data={"file": (BytesIO(b""), "empty.txt")})
    blank_name = client.post(
        "/api/materials",
        data={"display_name": "   ", "file": (BytesIO(b"content"), "blank.txt")},
    )

    assert unsupported.status_code == 400
    assert empty.status_code == 400
    assert blank_name.status_code == 400
    assert session.query(Material).count() == before
    assert {path.name for path in storage_dir.iterdir()} == before_files


def test_student_file_upload_is_forbidden(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path, "student-a")
    before = app.extensions["sqlalchemy"]["session"].query(Material).count()
    response = client.post("/api/materials", data={"file": (BytesIO(b"student work"), "student.txt")})

    assert response.status_code == 403
    assert app.extensions["sqlalchemy"]["session"].query(Material).count() == before
