from pathlib import Path


def test_browser_ask_uses_bearer_client_and_safe_text_rendering():
    source = (Path(__file__).parents[1] / "campusclaw/static/materials.js").read_text()
    assert 'request("/api/ask", {' in source
    assert 'body: JSON.stringify({ question })' in source
    assert 'askAnswer.textContent = answer;' in source
    assert 'askCitations.replaceChildren();' in source
    assert 'citation.number' in source
    assert 'response.status === 503' in source
