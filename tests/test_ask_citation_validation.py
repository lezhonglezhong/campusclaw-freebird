"""Generated answers expose only citations that support their claims."""

from pathlib import Path
from types import SimpleNamespace

from campusclaw import create_app
from campusclaw.knowledge_api import validated_answer_response
from campusclaw.seed import seed_data


def candidate(chunk_id: int, text: str, title: str):
    return SimpleNamespace(
        chunk=SimpleNamespace(id=chunk_id, chunk_index=0, chunk_text=text),
        title=title,
    )


def public_source(session, hit):
    return {
        "chunk_id": hit.chunk.id,
        "material_id": hit.chunk.id,
        "material_title": hit.title,
        "chunk_index": hit.chunk.chunk_index,
        "start_offset": 0,
        "end_offset": len(hit.chunk.chunk_text),
        "excerpt": hit.chunk.chunk_text,
        "material_url": f"/api/materials/{hit.chunk.id}",
    }


def test_only_used_sources_are_returned_and_renumbered(monkeypatch):
    monkeypatch.setattr("campusclaw.knowledge_api.public_hit", public_source)
    chosen = [
        candidate(1, "first", "one"),
        candidate(2, "second", "two"),
        candidate(3, "third", "three"),
        candidate(4, "fourth", "four"),
    ]

    result = validated_answer_response(None, "Uses fourth [4], then second [2] and fourth [4].", chosen)

    assert result["answer"] == "Uses fourth [1], then second [2] and fourth [1]."
    assert [(item["number"], item["chunk_id"]) for item in result["citations"]] == [(1, 4), (2, 2)]


def test_numeric_claim_requires_support_from_its_own_citation(monkeypatch):
    monkeypatch.setattr("campusclaw.knowledge_api.public_hit", public_source)
    chosen = [
        candidate(1, "一号楼下降150度", "one"),
        candidate(2, "三号楼下降300度", "three"),
        candidate(3, "四号楼下降40度", "four"),
    ]

    valid = validated_answer_response(
        None,
        "一号楼下降150度[1]，三号楼下降300度[2]，四号楼下降40度[3]，所以三号楼最多[2]。",
        chosen,
    )
    invalid = validated_answer_response(None, "三号楼下降300度[1]。", chosen)

    assert valid is not None
    assert invalid is None


def test_citation_after_sentence_punctuation_supports_preceding_number(monkeypatch):
    monkeypatch.setattr("campusclaw.knowledge_api.public_hit", public_source)
    chosen = [candidate(1, "123456", "A班资料")]

    result = validated_answer_response(None, "A班资料的内容是 123456。[1]", chosen)

    assert result is not None
    assert result["answer"] == "A班资料的内容是 123456。[1]"


def make_app(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'citation.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"),
        "TOKEN_SIGNING_SECRET": "secret",
    })
    seed_data(app)
    return app


def login(client):
    response = client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    return {"Authorization": f"Bearer {response.json['access_token']}"}


def test_unsupported_numbers_retry_once_then_return_safe_503(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    client = app.test_client()
    headers = login(client)
    chosen = [
        candidate(1, "一号楼的用电量下降了150度。", "能耗"),
        candidate(2, "三号楼的用电量下降了300度。", "能耗"),
        candidate(3, "四号楼的用电量下降了40度。", "能耗"),
    ]
    monkeypatch.setattr("campusclaw.knowledge_api.hybrid_retrieve", lambda *args, **kwargs: chosen)
    monkeypatch.setattr("campusclaw.knowledge_api.public_hit", public_source)
    calls = []

    class Chat:
        def answer(self, instruction, question, history, sources):
            calls.append((instruction, sources))
            return "三号楼下降500度[2]。"

    app.extensions["chat_provider"] = Chat()
    response = client.post("/api/ask", json={"question": "哪个楼的用电量下降最多？"}, headers=headers)

    assert response.status_code == 503
    assert response.json == {"error": "chat_unavailable"}
    assert len(calls) == 2
    assert calls[0][1] == calls[1][1]
    assert [source["text"] for source in calls[0][1]] == [hit.chunk.chunk_text for hit in chosen]


def test_invalid_first_answer_can_retry_with_supported_numbers(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    client = app.test_client()
    headers = login(client)
    chosen = [candidate(1, "三号楼的用电量下降了300度。", "能耗")]
    monkeypatch.setattr("campusclaw.knowledge_api.hybrid_retrieve", lambda *args, **kwargs: chosen)
    monkeypatch.setattr("campusclaw.knowledge_api.public_hit", public_source)
    answers = iter(["三号楼下降500度[1]。", "三号楼下降300度[1]。"])

    class Chat:
        def answer(self, *args):
            return next(answers)

    app.extensions["chat_provider"] = Chat()
    response = client.post("/api/ask", json={"question": "三号楼下降了多少？"}, headers=headers)

    assert response.status_code == 200
    assert response.json["answer"] == "三号楼下降300度[1]。"
    assert len(response.json["citations"]) == 1
