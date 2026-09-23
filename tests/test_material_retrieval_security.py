from campusclaw import create_app
from campusclaw.seed import seed_data


def test_retrieval_enforces_session_class_authentication_and_query_validation(tmp_path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'security.sqlite3'}", "SESSION_SECRET": "test-secret"})
    seed_data(app)
    anonymous = app.test_client()
    assert anonymous.get("/api/materials/retrieve?q=content").status_code == 401
    client = app.test_client()
    client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    assert client.get("/api/materials/retrieve?q=Class+B").json == {"results": []}
    assert client.get("/api/materials/retrieve?q=").status_code == 400
    assert client.get("/api/materials/retrieve?q=\"").status_code == 400
