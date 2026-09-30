from campusclaw import create_app
from campusclaw.seed import seed_data


def test_retrieve_returns_class_scoped_provenance(tmp_path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'retrieval.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    client = app.test_client()
    login = client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {login.json['access_token']}"
    response = client.get("/api/materials/retrieve?q=content")
    assert response.status_code == 200
    assert len(response.json["results"]) == 1
    result = response.json["results"][0]
    assert result["class_name"] == "A"
    assert result["download_url"].startswith("/api/materials/")
    assert "content_path" not in result


def test_retrieve_falls_back_for_chinese_content(tmp_path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'chinese.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    client = app.test_client()
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {login.json['access_token']}"
    client.post("/api/materials", json={"display_name": "中文", "content": "量子物理课程"})
    assert client.get("/api/materials/retrieve?q=量子物理").json["results"][0]["display_name"] == "中文"
