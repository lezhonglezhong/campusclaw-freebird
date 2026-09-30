"""A named material's complete short text can answer a literal content request."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.seed import seed_data


def setup(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'explicit-source.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"),
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    return app


def auth(client, account):
    response = client.post("/login", json={"account": account, "password": f"{account}-password"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['access_token']}"}


class WeakEmbedder:
    def embed(self, texts):
        return [[0.0] * 2048]


class WeakStore:
    def search(self, vector, class_id, limit):
        return []


class InsufficientChat:
    def __init__(self):
        self.calls = []

    def answer(self, instruction, question, history, sources):
        self.calls.append((question, sources))
        return "资料不足。"


def test_exact_user_question_quotes_short_original_after_model_refusal(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    created = client.post("/api/materials", json={"display_name": "物理定理", "content": "1241241"}, headers=teacher)
    assert created.status_code == 201
    material_id = created.json["material"]["id"]
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()
    chat = InsufficientChat()
    app.extensions["chat_provider"] = chat
    student = auth(client, "student-a")
    answer = client.post("/api/ask", json={"question": "物理定理材料的内容是什么"}, headers=student)
    assert answer.status_code == 200
    assert answer.json["answer"] == "《物理定理》的材料原文是：1241241 [1]"
    assert len(answer.json["citations"]) == 1
    assert answer.json["citations"][0]["material_id"] == material_id
    assert answer.json["citations"][0]["excerpt"] == "1241241"
    assert len(chat.calls) == 1
    assert chat.calls[0][1] == [{"citation": 1, "title": "物理定理", "chunk_index": 0, "text": "1241241"}]


def test_concept_question_does_not_treat_title_as_definition(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    assert client.post("/api/materials", json={"display_name": "物理定理", "content": "1241241"}, headers=teacher).status_code == 201
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()
    app.extensions["chat_provider"] = InsufficientChat()
    response = client.post("/api/ask", json={"question": "物理定理是什么"}, headers=teacher)
    assert response.status_code == 200
    assert response.json == {"answer": "资料中未找到相关内容", "citations": []}


def test_partial_or_long_source_is_not_presented_as_complete(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    body = "物理实验数据。" * 100
    assert len(body) > 500
    assert client.post("/api/materials", json={"display_name": "物理定理", "content": body}, headers=teacher).status_code == 201
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()
    app.extensions["chat_provider"] = InsufficientChat()
    response = client.post("/api/ask", json={"question": "物理定理材料的内容是什么"}, headers=teacher)
    assert response.status_code == 200
    assert response.json == {"answer": "资料中未找到相关内容", "citations": []}


def test_provider_failure_still_returns_503(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    assert client.post("/api/materials", json={"display_name": "物理定理", "content": "1241241"}, headers=teacher).status_code == 201
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()

    class Down:
        def answer(self, *args):
            raise ProviderUnavailable("down")

    app.extensions["chat_provider"] = Down()
    response = client.post("/api/ask", json={"question": "物理定理材料的内容是什么"}, headers=teacher)
    assert response.status_code == 503
    assert response.json == {"error": "chat_unavailable"}
