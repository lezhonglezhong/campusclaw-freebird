"""Reusable authorization-guard tests."""

from pathlib import Path

from flask import jsonify

from campusclaw import create_app
from campusclaw.auth import require_teacher
from campusclaw.seed import seed_data


def test_teacher_role_guard_allows_teacher_and_denies_student(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'authz.sqlite3'}", "SESSION_SECRET": "test-secret"})
    seed_data(app)

    @app.get("/_teacher-only")
    @require_teacher
    def teacher_only(_user):
        return jsonify(ok=True)

    teacher = app.test_client()
    teacher.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    assert teacher.get("/_teacher-only").status_code == 200

    student = app.test_client()
    student.post("/login", json={"account": "student-a", "password": "student-a-password"})
    response = student.get("/_teacher-only")
    assert response.status_code == 403
    assert response.json == {"error": "forbidden"}
