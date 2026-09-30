from pathlib import Path


def test_browser_ask_uses_bearer_client_and_safe_text_rendering():
    source = (Path(__file__).parents[1] / "campusclaw/static/materials.js").read_text()
    assert 'request("/api/ask", {' in source
    assert 'body: JSON.stringify({ question })' in source
    assert 'askAnswer.textContent = answer;' in source
    assert 'askCitations.replaceChildren();' in source
    assert 'citation.number' in source
    assert 'response.status === 503' in source


def test_answer_sources_use_only_ask_citations_not_retrieval_hits():
    root = Path(__file__).parents[1]
    source = (root / "campusclaw/static/materials.js").read_text()
    template = (root / "campusclaw/templates/materials.html").read_text()
    retrieval_block = source[source.index('retrievalForm.addEventListener'):source.index('askForm.addEventListener')]
    ask_block = source[source.index('askForm.addEventListener'):source.index('initializeWorkspace();')]

    assert 'for (const hit of hits)' in retrieval_block
    assert 'retrievalResults.append(item);' in retrieval_block
    assert 'for (const citation of citations)' in ask_block
    assert 'askCitations.append(item);' in ask_block
    assert 'for (const hit of hits)' not in ask_block
    assert 'retrievalResults.append(item);' not in ask_block
    assert '答案实际引用' in template
    assert '与上方独立检索结果分开' in template
