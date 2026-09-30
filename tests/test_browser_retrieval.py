from campusclaw import create_app

def test_workspace_exposes_chinese_retrieval_controls(tmp_path):
    app=create_app({"TESTING":True,"DATABASE_URL":f"sqlite:///{tmp_path/'b.db'}","TOKEN_SIGNING_SECRET":"test-token-secret"})
    page=app.test_client().get('/materials').get_data(as_text=True)
    assert 'content-retrieval-form' in page
    script=(app.static_folder + '/materials.js')
    source=open(script, encoding='utf-8').read()
    assert '/api/materials/retrieve?' in source
    assert 'const request = auth.request;' in source
