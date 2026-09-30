"""Grounded Q&A follows title-directed retrieval without expanding source scope."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def setup(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'title-ask.sqlite3'}",
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


def test_title_question_cites_short_source_and_sends_only_selected_chunk(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    uploaded = client.post("/api/materials", json={"display_name": "A班资料", "content": "123456"}, headers=teacher)
    assert uploaded.status_code == 201
    material_id = uploaded.json["material"]["id"]
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()
    seen = []

    class Chat:
        def answer(self, instruction, question, history, sources):
            seen.append((question, sources))
            return "A班资料的内容是 123456。[1]"

    app.extensions["chat_provider"] = Chat()
    student = auth(client, "student-a")
    response = client.post("/api/ask", json={"question": "A班资料的内容是什么？"}, headers=student)
    assert response.status_code == 200
    assert response.json["answer"] == "A班资料的内容是 123456。[1]"
    assert len(response.json["citations"]) == 1
    assert response.json["citations"][0]["material_id"] == material_id
    assert response.json["citations"][0]["excerpt"] == "123456"
    assert seen == [("A班资料的内容是什么？", [{"citation": 1, "title": "A班资料", "chunk_index": 0, "text": "123456"}])]


def test_foreign_title_and_unrelated_question_do_not_call_chat(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher_b = auth(client, "teacher-b")
    assert client.post("/api/materials", json={"display_name": "B班机密材料", "content": "987654"}, headers=teacher_b).status_code == 201
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()

    class NoChat:
        def answer(self, *args):
            raise AssertionError("chat must not run without own-class evidence")

    app.extensions["chat_provider"] = NoChat()
    student_a = auth(client, "student-a")
    for question in ("B班机密材料内容是什么？", "今天有什么作业？"):
        response = client.post("/api/ask", json={"question": question}, headers=student_a)
        assert response.status_code == 200
        assert response.json == {"answer": "资料中未找到相关内容", "citations": []}
