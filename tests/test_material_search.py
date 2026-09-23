"""Class-scoped material name-search tests for teacher and student sessions."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'search.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "content"),
        "SESSION_SECRET": "test-secret",
    })
    seed_data(app)
    return app


def login(client, account: str, password: str) -> None:
    assert client.post("/login", json={"account": account, "password": password}).status_code == 200


def test_teacher_and_student_search_only_material_names_in_own_class(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    teacher_a = app.test_client()
    teacher_b = app.test_client()
    login(teacher_a, "teacher-a", "teacher-a-password")
    login(teacher_b, "teacher-b", "teacher-b-password")
    assert teacher_a.post("/api/materials", json={"display_name": "Chemistry Notes", "content": "A"}).status_code == 201
    assert teacher_b.post("/api/materials", json={"display_name": "Chemistry Notes B", "content": "B"}).status_code == 201

    student_a = app.test_client()
    student_b = app.test_client()
    login(student_a, "student-a", "student-a-password")
    login(student_b, "student-b", "student-b-password")
    a_result = student_a.get("/api/materials?q=CHEMISTRY&class_id=2")
    b_result = student_b.get("/api/materials?q=chemistry")

    assert a_result.status_code == 200
    assert [(item["display_name"], item["class_name"]) for item in a_result.json["materials"]] == [("Chemistry Notes", "A")]
    assert b_result.status_code == 200
    assert [(item["display_name"], item["class_name"]) for item in b_result.json["materials"]] == [("Chemistry Notes B", "B")]


def test_search_matches_name_only_and_requires_authentication(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    anonymous = app.test_client()
    assert anonymous.get("/api/materials?q=class").status_code == 401

    student = app.test_client()
    login(student, "student-a", "student-a-password")
    assert student.get("/api/materials?q=not-present").json == {"materials": []}
