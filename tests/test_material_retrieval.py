from campusclaw import create_app
from campusclaw.seed import seed_data


def test_retrieve_returns_class_scoped_provenance(tmp_path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'retrieval.sqlite3'}", "SESSION_SECRET": "test-secret"})
    seed_data(app)
    client = app.test_client()
    client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    response = client.get("/api/materials/retrieve?q=content")
    assert response.status_code == 200
    assert len(response.json["results"]) == 1
    result = response.json["results"][0]
    assert result["class_name"] == "A"
    assert result["download_url"].startswith("/api/materials/")
    assert "content_path" not in result
