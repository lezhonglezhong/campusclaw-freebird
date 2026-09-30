from pathlib import Path


def test_teacher_only_reindex_form_uses_bearer_client():
    source = (Path(__file__).parents[1] / "campusclaw/static/materials.js").read_text()
    assert 'if (user.role !== "teacher") return;' in source
    assert 'indexingTemplate.content.cloneNode(true)' in source
    assert 'request(`/api/materials/${materialId}/reindex`, {' in source
    assert 'method: "POST"' in source
    assert 'strategy: strategy.value, options' in source
    assert 'custom.hidden = strategy.value !== "custom";' in source
