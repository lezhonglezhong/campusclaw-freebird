"""Browser contract for safe, authenticated material source preview."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = (ROOT / "campusclaw/static/materials.js").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "campusclaw/templates/materials.html").read_text(encoding="utf-8")
STYLE = (ROOT / "campusclaw/static/app.css").read_text(encoding="utf-8")


def test_detail_has_inline_plain_text_preview_and_keeps_download() -> None:
    assert 'id="material-content-preview"' in TEMPLATE
    assert 'id="material-preview-status"' in TEMPLATE
    assert 'request(`/api/materials/${id}/content`)' in SCRIPT
    assert "contentPreview.textContent = content;" in SCRIPT
    assert "contentPreview.innerHTML" not in SCRIPT
    assert 'download.textContent = "下载材料"' in SCRIPT
    assert 'request(`/api/materials/${material.id}/download`' not in SCRIPT or "downloadMaterial" in SCRIPT
    assert "max-height: 24rem" in STYLE
    assert "white-space: pre-wrap" in STYLE


def test_preview_clears_on_new_selection_unauthorized_and_delete() -> None:
    assert "let detailRequestId = 0;" in SCRIPT
    assert "const requestId = ++detailRequestId;" in SCRIPT
    assert "if (requestId !== detailRequestId) return;" in SCRIPT
    assert "contentPreview.textContent = \"\";" in SCRIPT
    assert 'window.addEventListener("campusclaw:unauthorized", clearProtectedView)' in SCRIPT
    assert "if (response.status === 204) {\n          detailRequestId += 1;" in SCRIPT


def test_both_upload_methods_open_returned_material() -> None:
    assert SCRIPT.count("const { material } = await response.json();") >= 3
    assert SCRIPT.count("await loadDetail(material.id);") == 2
