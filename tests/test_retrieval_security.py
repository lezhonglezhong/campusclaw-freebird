from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def test_missing_bearer_never_returns_chunks(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'security.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    client = app.test_client()
    for mode in ("keyword", "vector", "hybrid"):
        response = client.get(f"/api/retrieval?q=sample&mode={mode}")
        assert response.status_code == 401
        assert "hits" not in response.json

