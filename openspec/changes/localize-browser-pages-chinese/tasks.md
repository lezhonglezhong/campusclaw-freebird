# Tasks

## 1. Simplified Chinese browser interface

- [x] 1.1 Translate all visible login-page text and login-flow feedback into Simplified Chinese without changing form names or login API requests; verify `pytest tests/test_browser_pages.py::test_login_page_uses_simplified_chinese tests/test_browser_pages.py::test_login_page_declares_safe_interactive_contract -q` exits successfully
- [x] 1.2 Translate all material-workspace text, dynamic detail labels, upload feedback, and logout controls into Simplified Chinese without changing role, session, or API behavior; verify `pytest tests/test_browser_pages.py::test_material_workspace_uses_simplified_chinese tests/test_browser_flow.py -q` exits successfully
- [x] 1.3 Run full regression and strictly validate the localization change; verify `pytest -q && openspec validate localize-browser-pages-chinese --strict` exits successfully
