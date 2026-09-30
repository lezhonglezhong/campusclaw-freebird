from pathlib import Path

from campusclaw import create_app


def test_workspace_shell_has_retrieval_answer_and_teacher_panels(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'ui.sqlite3'}",
                      "TOKEN_SIGNING_SECRET": "secret"})
    page = app.test_client().get("/materials").get_data(as_text=True)
    for marker in ('id="material-list"', 'id="content-retrieval-form"', 'id="retrieval-mode"',
                   'id="ask-form"', 'id="ask-citations"', 'id="teacher-indexing"',
                   'id="retrieval-status"', 'id="ask-status"'):
        assert marker in page
    assert '<option value="hybrid" selected>' in page
    assert 'aria-live="polite"' in page
    assert '<template id="teacher-indexing-template">' in page
    assert 'id="reindex-form"' in page
    assert '答案来源只显示答案实际引用的相关切片' in page
    assert "EMBEDDING_API_KEY" not in page
    assert "TOKEN_SIGNING_SECRET" not in page

