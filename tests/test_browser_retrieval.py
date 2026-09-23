from campusclaw import create_app

def test_workspace_exposes_chinese_retrieval_controls(tmp_path):
    app=create_app({"TESTING":True,"DATABASE_URL":f"sqlite:///{tmp_path/'b.db'}","SESSION_SECRET":"x"})
    page=app.test_client().get('/materials').get_data(as_text=True)
    assert 'content-retrieval-form' not in page
    script=(app.static_folder + '/materials.js')
    assert '/api/materials/retrieve?' in open(script).read()
